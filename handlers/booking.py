import re
from datetime import date as _date

from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from config import get_zone_label, POINTS_PCT
from database.db import (
    get_user_lang,
    get_user,
    create_booking,
    get_or_create_user,
    get_birthday_blocks_for_date,
    get_zone_date_statuses_for_month,
    add_points_with_history,
)
from keyboards.kb import (
    zones_keyboard,
    payment_keyboard,
    confirm_cancel_keyboard,
    cancel_keyboard,
    back_to_menu_keyboard,
    booking_calendar_keyboard,
    booking_time_keyboard,
    calc_booking_blocked_start_times,
    use_saved_name_keyboard,
    use_saved_phone_keyboard,
)
from locales import t
from states.forms import BookingForm
from utils.notify import notify_admins, booking_notification
from handlers.common import send_main_menu

router = Router()

PHONE_RE = re.compile(r"^\+?[\d\s\-\(\)]{7,15}$")

# ── Pricing constants ──────────────────────────────────────────
_EVE_MIN       = 18 * 60   # 18:00 — boundary between day/evening rate
_RATE_DAY      = 100       # грн/ос/год  (13:00 – 18:00)
_RATE_EVE      = 150       # грн/ос/год  (18:00 – 23:00)
_MIN_RATE_DAY  = 50        # group discount floor — day
_MIN_RATE_EVE  = 100       # group discount floor — evening
_DISCOUNT_STEP = 10        # грн off per extra person above 3

# ── VR-specific pricing (no day/evening split, no group discount) ──
_VR_ZONE_ID      = "vr"
_VR_RATE_HOUR    = 200     # грн/ос/год
_VR_RATE_SESSION = 75      # грн/ос за мінімальний сеанс 20 хв


def _get_rate(start_min: int) -> tuple[int, int, str]:
    """Returns (base_rate, min_rate, period_emoji) based on start time."""
    if start_min < _EVE_MIN:
        return _RATE_DAY, _MIN_RATE_DAY, "☀️"
    return _RATE_EVE, _MIN_RATE_EVE, "🌙"


def _calc_group_rate(base_rate: int, min_rate: int, people: int) -> tuple[int, int]:
    """Apply group discount for 4+ people.
    Returns (effective_rate_per_person, discount_per_person).
    4 ppl → -10, 5 → -20, …, until floor is reached.
    """
    if people < 4:
        return base_rate, 0
    extra = people - 3
    discount = extra * _DISCOUNT_STEP
    effective = max(base_rate - discount, min_rate)
    return effective, base_rate - effective


# ─────────────────────────── Entry (with perks) ───────────────────────────

@router.callback_query(F.data == "menu:booking")
async def cb_booking_start(callback: CallbackQuery, state: FSMContext) -> None:
    lang = await get_user_lang(callback.from_user.id)
    await state.set_state(BookingForm.zone)
    await state.update_data(lang=lang)
    await callback.message.edit_text(
        t("booking_title", lang),
        reply_markup=zones_keyboard(lang),
        parse_mode="HTML",
    )
    await callback.answer()


# ─────────────────────────── Zone → Calendar ───────────────────────────

@router.callback_query(BookingForm.zone, F.data.startswith("zone:"))
async def cb_booking_zone(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "uk")
    zone_id = callback.data.split(":")[1]
    zone_label = get_zone_label(zone_id, lang)

    await state.update_data(zone=zone_id)
    await state.set_state(BookingForm.selecting_date)

    today = _date.today()
    statuses = await get_zone_date_statuses_for_month(zone_id, today.year, today.month)
    kb = booking_calendar_keyboard(today.year, today.month, statuses, zone_id, lang)

    title = (
        f"📅 <b>{zone_label}</b>\n\n"
        "Оберіть дату бронювання:\n"
        "<i>🔴 — зайнято  ·  🟡 — є бронювання</i>"
    ) if lang == "uk" else (
        f"📅 <b>{zone_label}</b>\n\n"
        "Выберите дату бронирования:\n"
        "<i>🔴 — занято  ·  🟡 — есть бронирования</i>"
    )

    await callback.message.edit_text(title, reply_markup=kb, parse_mode="HTML")
    await callback.answer()


# ─────────────────────────── Calendar navigation ───────────────────────────

@router.callback_query(BookingForm.selecting_date, F.data.startswith("book_cal:"))
async def cb_booking_cal_nav(callback: CallbackQuery, state: FSMContext) -> None:
    # callback_data = "book_cal:{zone_id}:{year}:{month}"
    parts = callback.data.split(":")
    zone_id = parts[1]
    year, month = int(parts[2]), int(parts[3])

    data = await state.get_data()
    lang = data.get("lang", "uk")

    statuses = await get_zone_date_statuses_for_month(zone_id, year, month)
    kb = booking_calendar_keyboard(year, month, statuses, zone_id, lang)
    await callback.message.edit_reply_markup(reply_markup=kb)
    await callback.answer()


# ─────────────────────────── Date selected → Start time picker ───────────────────────────

@router.callback_query(BookingForm.selecting_date, F.data.startswith("book_date:"))
async def cb_booking_date_selected(callback: CallbackQuery, state: FSMContext) -> None:
    date_iso = callback.data.split(":", 1)[1]   # YYYY-MM-DD

    data = await state.get_data()
    lang = data.get("lang", "uk")

    d = _date.fromisoformat(date_iso)
    display_date = d.strftime("%d.%m.%Y")

    # Only birthday blocks restrict time slot availability for regular bookings
    bday_blocks = await get_birthday_blocks_for_date(date_iso)
    skip_start = calc_booking_blocked_start_times(list(bday_blocks)) if bday_blocks else None

    await state.update_data(date_iso=date_iso, display_date=display_date)
    await state.set_state(BookingForm.selecting_time)

    zone_id = data.get("zone", "")
    if zone_id == _VR_ZONE_ID:
        header = (
            f"📅 <b>{display_date}</b>\n\n"
            "⏰ Оберіть час початку:\n"
            f"<i>🥽 VR-тариф: {_VR_RATE_SESSION} грн/20 хв · {_VR_RATE_HOUR} грн/год/ос</i>"
        ) if lang == "uk" else (
            f"📅 <b>{display_date}</b>\n\n"
            "⏰ Выберите время начала:\n"
            f"<i>🥽 VR-тариф: {_VR_RATE_SESSION} грн/20 мин · {_VR_RATE_HOUR} грн/час/чел</i>"
        )
    else:
        header = (
            f"📅 <b>{display_date}</b>\n\n"
            "⏰ Оберіть час початку:\n"
            "<i>☀️ День: 100 грн/ос/год · 🌙 Вечір: 150 грн/ос/год</i>\n"
            "<i>💡 Компанія від 4 осіб — вигідніший тариф!</i>"
        ) if lang == "uk" else (
            f"📅 <b>{display_date}</b>\n\n"
            "⏰ Выберите время начала:\n"
            "<i>☀️ День: 100 грн/чел/час · 🌙 Вечер: 150 грн/чел/час</i>\n"
            "<i>💡 Компания от 4 человек — выгоднее!</i>"
        )

    await callback.message.edit_text(
        header,
        reply_markup=booking_time_keyboard(lang, skip_times=skip_start),
        parse_mode="HTML",
    )
    await callback.answer()


# ─────────────────────────── Start time selected → People ───────────────────────────

@router.callback_query(BookingForm.selecting_time, F.data.startswith("book_time:"))
async def cb_booking_time_start(callback: CallbackQuery, state: FSMContext) -> None:
    time_start = callback.data.split(":", 1)[1]   # "HH:MM"

    data = await state.get_data()
    lang = data.get("lang", "uk")
    display_date = data.get("display_date", "—")

    sh, sm = int(time_start[:2]), int(time_start[3:])
    start_min = sh * 60 + sm

    zone_id = data.get("zone", "")
    is_vr = zone_id == _VR_ZONE_ID

    if is_vr:
        base_rate, min_rate = _VR_RATE_HOUR, _VR_RATE_HOUR
    else:
        base_rate, min_rate, _ = _get_rate(start_min)

    await state.update_data(
        time=time_start,
        start_min=start_min,
        base_rate=base_rate,
        min_rate=min_rate,
        is_vr=is_vr,
    )
    await state.set_state(BookingForm.people)

    if is_vr:
        if lang == "uk":
            prompt = (
                f"📅 <b>{display_date}</b>  ·  ⏰ Від: <b>{time_start}</b>\n"
                f"🥽 VR-тариф: <b>{_VR_RATE_SESSION} грн/20 хв</b> · <b>{_VR_RATE_HOUR} грн/год/ос</b>\n\n"
                "👥 Скільки людей? Введіть кількість:"
            )
        else:
            prompt = (
                f"📅 <b>{display_date}</b>  ·  ⏰ С: <b>{time_start}</b>\n"
                f"🥽 VR-тариф: <b>{_VR_RATE_SESSION} грн/20 мин</b> · <b>{_VR_RATE_HOUR} грн/час/чел</b>\n\n"
                "👥 Сколько человек? Введите количество:"
            )
    elif lang == "uk":
        _, _, period_emoji = _get_rate(start_min)
        prompt = (
            f"📅 <b>{display_date}</b>  ·  ⏰ Від: <b>{time_start}</b>\n"
            f"{period_emoji} Тариф: <b>{base_rate} грн/ос/год</b>\n\n"
            "👥 Скільки людей? Введіть кількість:\n"
            "<i>💡 Від 4 осіб — знижка на тариф!</i>"
        )
    else:
        _, _, period_emoji = _get_rate(start_min)
        prompt = (
            f"📅 <b>{display_date}</b>  ·  ⏰ С: <b>{time_start}</b>\n"
            f"{period_emoji} Тариф: <b>{base_rate} грн/чел/час</b>\n\n"
            "👥 Сколько человек? Введите количество:\n"
            "<i>💡 От 4 человек — скидка на тариф!</i>"
        )

    await callback.message.edit_text(
        prompt,
        reply_markup=cancel_keyboard(lang),
        parse_mode="HTML",
    )
    await callback.answer()


# ─────────────────────────── People (with group discount) ───────────────────────────

@router.message(BookingForm.people)
async def msg_booking_people(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "uk")
    if not message.text.strip().isdigit() or int(message.text.strip()) < 1:
        await message.answer(t("invalid_people", lang))
        return

    people = int(message.text.strip())
    base_rate = data.get("base_rate", _RATE_DAY)
    min_rate  = data.get("min_rate",  _MIN_RATE_DAY)
    is_vr     = data.get("is_vr", False)

    await state.set_state(BookingForm.name)

    if is_vr:
        # VR: flat rate, no group discount
        group_per_hour = _VR_RATE_HOUR * people
        price_raw = group_per_hour
        if lang == "uk":
            price_str = (
                f"{_VR_RATE_HOUR} грн/ос/год × {people} ос = {group_per_hour} грн/год\n"
                f"<i>(мінімум: {_VR_RATE_SESSION} грн/ос за 20 хв)</i>"
            )
        else:
            price_str = (
                f"{_VR_RATE_HOUR} грн/ос/час × {people} чел = {group_per_hour} грн/час\n"
                f"<i>(минимум: {_VR_RATE_SESSION} грн/чел за 20 мин)</i>"
            )
        await state.update_data(people=people, price_str=price_str, price_raw=price_raw)
    else:
        # Standard zones: apply group discount if 4+ people
        effective_rate, discount = _calc_group_rate(base_rate, min_rate, people)
        group_per_hour = effective_rate * people
        price_raw = group_per_hour
        if lang == "uk":
            price_str = f"{effective_rate} грн/ос/год × {people} ос = {group_per_hour} грн/год"
        else:
            price_str = f"{effective_rate} грн/чел/час × {people} чел = {group_per_hour} грн/час"
        await state.update_data(people=people, price_str=price_str, price_raw=price_raw)
        if discount > 0:
            if lang == "uk":
                reply = (
                    f"🎉 <b>Групова знижка активована!</b>\n"
                    f"💰 <b>{effective_rate} грн/ос/год</b> × {people} ос = <b>{group_per_hour} грн/год</b>\n"
                    f"<i>(знижка {discount} грн/ос/год — замість {base_rate} грн)</i>"
                )
            else:
                reply = (
                    f"🎉 <b>Групповая скидка активирована!</b>\n"
                    f"💰 <b>{effective_rate} грн/чел/час</b> × {people} чел = <b>{group_per_hour} грн/час</b>\n"
                    f"<i>(скидка {discount} грн/чел/час — вместо {base_rate} грн)</i>"
                )
            await message.answer(reply, parse_mode="HTML")

    # Check if user has saved name → offer choice
    user = await get_user(message.from_user.id)
    saved_name = user.get("saved_name") if user else None
    if saved_name:
        await message.answer(
            t("use_saved_name_prompt", lang, name=saved_name),
            reply_markup=use_saved_name_keyboard(saved_name, lang, prefix="booking"),
            parse_mode="HTML",
        )
    else:
        await message.answer(t("booking_name", lang), parse_mode="HTML")


# ─────────────────────────── Name — callbacks ───────────────────────────

@router.callback_query(BookingForm.name, F.data == "booking:use_name")
async def cb_booking_use_name(callback: CallbackQuery, state: FSMContext) -> None:
    """User tapped '✅ Use saved name'."""
    data = await state.get_data()
    lang = data.get("lang", "uk")
    user = await get_user(callback.from_user.id)
    saved_name = user.get("saved_name", "") if user else ""
    await state.update_data(name=saved_name)
    await state.set_state(BookingForm.phone)
    await _ask_phone(callback.message, state, lang, callback.from_user.id)
    await callback.answer()


@router.callback_query(BookingForm.name, F.data == "booking:enter_name")
async def cb_booking_enter_name(callback: CallbackQuery, state: FSMContext) -> None:
    """User tapped '✏️ Enter another name' — just show text prompt."""
    data = await state.get_data()
    lang = data.get("lang", "uk")
    await callback.message.edit_text(
        t("booking_name", lang),
        reply_markup=cancel_keyboard(lang),
        parse_mode="HTML",
    )
    await callback.answer()


# ─────────────────────────── Name — text input ───────────────────────────

@router.message(BookingForm.name)
async def msg_booking_name(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "uk")
    await state.update_data(name=message.text.strip())
    await state.set_state(BookingForm.phone)
    await _ask_phone(message, state, lang, message.from_user.id)


# ─────────────────────────── Phone — helper ───────────────────────────

async def _ask_phone(target, state: FSMContext, lang: str, tg_id: int) -> None:
    """Show saved_phone choice or plain text prompt."""
    user = await get_user(tg_id)
    saved_phone = user.get("saved_phone") if user else None
    if saved_phone:
        kb = use_saved_phone_keyboard(saved_phone, lang, prefix="booking")
        prompt = t("use_saved_phone_prompt", lang, phone=saved_phone)
    else:
        kb = cancel_keyboard(lang)
        prompt = t("booking_phone", lang)
    if hasattr(target, "edit_text"):
        await target.edit_text(prompt, reply_markup=kb, parse_mode="HTML")
    else:
        await target.answer(prompt, reply_markup=kb, parse_mode="HTML")


# ─────────────────────────── Phone — callbacks ───────────────────────────

@router.callback_query(BookingForm.phone, F.data == "booking:use_phone")
async def cb_booking_use_phone(callback: CallbackQuery, state: FSMContext) -> None:
    """User tapped '✅ Use saved phone'."""
    data = await state.get_data()
    lang = data.get("lang", "uk")
    user = await get_user(callback.from_user.id)
    saved_phone = user.get("saved_phone", "") if user else ""
    await state.update_data(phone=saved_phone)
    await state.set_state(BookingForm.payment)
    await callback.message.edit_text(
        t("booking_payment", lang),
        reply_markup=payment_keyboard(lang),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(BookingForm.phone, F.data == "booking:enter_phone")
async def cb_booking_enter_phone(callback: CallbackQuery, state: FSMContext) -> None:
    """User tapped '✏️ Enter another phone'."""
    data = await state.get_data()
    lang = data.get("lang", "uk")
    await callback.message.edit_text(
        t("booking_phone", lang),
        reply_markup=cancel_keyboard(lang),
        parse_mode="HTML",
    )
    await callback.answer()


# ─────────────────────────── Phone — text input ───────────────────────────

@router.message(BookingForm.phone)
async def msg_booking_phone(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "uk")
    phone = message.text.strip()
    if not PHONE_RE.match(phone):
        await message.answer(t("booking_phone", lang), parse_mode="HTML")
        return
    await state.update_data(phone=phone)
    await state.set_state(BookingForm.payment)
    await message.answer(
        t("booking_payment", lang),
        reply_markup=payment_keyboard(lang),
        parse_mode="HTML",
    )


# ─────────────────────────── Payment ───────────────────────────

@router.callback_query(BookingForm.payment, F.data.startswith("payment:"))
async def cb_booking_payment(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "uk")
    payment = callback.data.split(":")[1]
    await state.update_data(payment=payment)
    await state.set_state(BookingForm.confirm)

    zone_label   = get_zone_label(data["zone"], lang)
    payment_text = t("payment_iban", lang) if payment == "iban" else t("payment_cash", lang)
    price_str    = data.get("price_str", "—")
    display_date = data.get("display_date", data.get("date_iso", "—"))

    text = t(
        "booking_confirm", lang,
        zone=zone_label,
        date=display_date,
        time=data["time"],
        price=price_str,
        people=data["people"],
        name=data["name"],
        phone=data["phone"],
        payment=payment_text,
    )
    await callback.message.edit_text(
        text,
        reply_markup=confirm_cancel_keyboard(lang),
        parse_mode="HTML",
    )
    await callback.answer()


# ─────────────────────────── Confirm ───────────────────────────

@router.callback_query(BookingForm.confirm, F.data == "confirm")
async def cb_booking_confirm(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    data = await state.get_data()
    lang = data.get("lang", "uk")

    await get_or_create_user(
        callback.from_user.id,
        callback.from_user.username,
        callback.from_user.full_name,
    )

    display_date = data.get("display_date", data.get("date_iso", "—"))

    price_raw = data.get("price_raw", 0)
    booking_id = await create_booking(
        user_tg_id=callback.from_user.id,
        user_name=data["name"],
        user_phone=data["phone"],
        zone=data["zone"],
        booking_date=data["date_iso"],   # ISO format for calendar queries
        booking_time=data["time"],       # start time only, e.g. "14:00"
        people_count=data["people"],
        payment_type=data["payment"],
        price=price_raw,
    )

    # Award points (10% of hourly group cost)
    if price_raw > 0 and callback.from_user.id != 0:
        points_earned = round(price_raw * POINTS_PCT / 100)
        if points_earned > 0:
            zone_label_for_pts = get_zone_label(data["zone"], lang)
            await add_points_with_history(
                callback.from_user.id,
                points_earned,
                "booking",
                f"Бронювання #{booking_id} — {zone_label_for_pts}",
                ref_id=booking_id,
            )

    zone_label = get_zone_label(data["zone"], lang)
    msg = booking_notification(
        booking_id=booking_id,
        user_tg_id=callback.from_user.id,
        username=callback.from_user.username,
        zone_label=zone_label,
        date=display_date,
        time=data["time"],
        people=data["people"],
        name=data["name"],
        phone=data["phone"],
        payment=data["payment"],
        price_str=data.get("price_str", ""),
    )
    await notify_admins(bot, msg)
    await state.clear()

    await callback.message.edit_text(
        t("booking_success", lang),
        reply_markup=back_to_menu_keyboard(lang),
        parse_mode="HTML",
    )
    await callback.answer()


# ─────────────────────────── Cancel (any step) ───────────────────────────

@router.callback_query(F.data == "cancel")
async def cb_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    current = await state.get_state()
    if current:
        data = await state.get_data()
        lang = data.get("lang", "uk")
        await state.clear()
        await callback.message.edit_text(t("cancelled", lang), parse_mode="HTML")
        await callback.answer()
        await send_main_menu(callback)
    else:
        await callback.answer()
