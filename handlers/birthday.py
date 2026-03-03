import re
from datetime import date as _date

from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from config import BIRTHDAY_DEPOSIT, BIRTHDAY_IBAN, BIRTHDAY_CLEANUP_MINUTES, BIRTHDAY_RATE, POINTS_PCT
from database.db import (
    get_user_lang,
    get_user,
    create_birthday_order,
    get_fully_booked_birthday_dates,
    get_birthday_blocks_for_date,
    add_points_with_history,
)
from keyboards.kb import (
    birthday_calendar_keyboard,
    birthday_time_keyboard,
    birthday_gender_keyboard,
    birthday_payment_keyboard,
    cancel_keyboard,
    back_to_menu_keyboard,
    calc_blocked_start_times,
    calc_blocked_end_times,
    use_saved_name_keyboard,
    use_saved_phone_keyboard,
)
from locales import t
from states.forms import BirthdayForm
from utils.notify import notify_admins

PHONE_RE = re.compile(r"^\+?[\d\s\-\(\)]{7,15}$")

router = Router()

# ─────────────────────────────────────────────────────────────
#  STEP 1 — Calendar
# ─────────────────────────────────────────────────────────────

@router.callback_query(F.data == "menu:birthday")
async def cb_birthday_start(callback: CallbackQuery, state: FSMContext) -> None:
    lang = await get_user_lang(callback.from_user.id)
    await state.set_state(BirthdayForm.selecting_date)
    await state.update_data(lang=lang)

    fully_booked = await get_fully_booked_birthday_dates()
    today = _date.today()
    kb = birthday_calendar_keyboard(today.year, today.month, fully_booked, lang)

    title = (
        "🎂 <b>День народження</b>\n\n"
        "✨ Обери дату свята на календарі:\n"
        "<i>🔴 — день повністю зайнятий</i>"
    ) if lang == "uk" else (
        "🎂 <b>День рождения</b>\n\n"
        "✨ Выбери дату праздника на календаре:\n"
        "<i>🔴 — день полностью занят</i>"
    )

    await callback.message.edit_text(title, reply_markup=kb, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("bday_cal:"))
async def cb_birthday_calendar_nav(callback: CallbackQuery, state: FSMContext) -> None:
    parts = callback.data.split(":")
    year, month = int(parts[1]), int(parts[2])

    data = await state.get_data()
    lang = data.get("lang") or await get_user_lang(callback.from_user.id)

    fully_booked = await get_fully_booked_birthday_dates()
    kb = birthday_calendar_keyboard(year, month, fully_booked, lang)
    await callback.message.edit_reply_markup(reply_markup=kb)
    await callback.answer()


# ─────────────────────────────────────────────────────────────
#  STEP 2 — Time picker (start)
# ─────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("bday_date:"))
async def cb_birthday_date_selected(callback: CallbackQuery, state: FSMContext) -> None:
    date_str = callback.data.split(":", 1)[1]  # YYYY-MM-DD

    data = await state.get_data()
    lang = data.get("lang") or await get_user_lang(callback.from_user.id)

    d = _date.fromisoformat(date_str)
    display_date = d.strftime("%d.%m.%Y")

    # Load existing birthday blocks for this date
    blocks = await get_birthday_blocks_for_date(date_str)
    skip_start = calc_blocked_start_times(blocks) if blocks else None

    await state.update_data(
        birthday_date=date_str,
        display_date=display_date,
        birthday_blocks=blocks,
    )
    await state.set_state(BirthdayForm.selecting_time)

    header = (
        f"🎉 <b>{display_date}</b> — чудовий день для свята!\n\n"
    ) if lang == "uk" else (
        f"🎉 <b>{display_date}</b> — отличный день для праздника!\n\n"
    )

    await callback.message.edit_text(
        header + t("bday_time_pick", lang),
        reply_markup=birthday_time_keyboard(lang, skip_times=skip_start),
        parse_mode="HTML",
    )
    await callback.answer()


# ─────────────────────────────────────────────────────────────
#  STEP 2b — Start time selected → pick end time
# ─────────────────────────────────────────────────────────────

@router.callback_query(BirthdayForm.selecting_time, F.data.startswith("bday_time:"))
async def cb_birthday_time_start(callback: CallbackQuery, state: FSMContext) -> None:
    time_start = callback.data.split(":", 1)[1]  # "HH:MM"

    data = await state.get_data()
    lang = data.get("lang") or await get_user_lang(callback.from_user.id)
    blocks: list[tuple[int, int]] = data.get("birthday_blocks", [])

    # Compute which end times are blocked
    sh, sm = map(int, time_start.split(":"))
    start_min = sh * 60 + sm
    skip_end = calc_blocked_end_times(start_min, blocks, BIRTHDAY_CLEANUP_MINUTES) if blocks else None

    await state.update_data(
        birthday_time_start=time_start,
        birthday_start_min=start_min,
    )
    await state.set_state(BirthdayForm.selecting_time_end)

    await callback.message.edit_text(
        t("bday_time_pick_end", lang).format(start=time_start),
        reply_markup=birthday_time_keyboard(lang, after=time_start, skip_times=skip_end),
        parse_mode="HTML",
    )
    await callback.answer()


# ─────────────────────────────────────────────────────────────
#  STEP 3 — End time selected → ask name
# ─────────────────────────────────────────────────────────────

@router.callback_query(BirthdayForm.selecting_time_end, F.data.startswith("bday_time:"))
async def cb_birthday_time_end(callback: CallbackQuery, state: FSMContext) -> None:
    time_end = callback.data.split(":", 1)[1]  # "HH:MM"

    data = await state.get_data()
    lang = data.get("lang") or await get_user_lang(callback.from_user.id)

    time_start = data.get("birthday_time_start", "—")
    time_range = f"{time_start} – {time_end}"

    eh, em = map(int, time_end.split(":"))
    end_min = eh * 60 + em
    start_min = data.get("birthday_start_min", 0)
    duration_hours = (end_min - start_min) / 60
    bday_price = round(duration_hours * BIRTHDAY_RATE)

    await state.update_data(
        birthday_time=time_range,
        birthday_time_end=time_end,
        birthday_end_min=end_min,
        bday_price=bday_price,
    )
    await state.set_state(BirthdayForm.entering_name)

    # Check if user has saved name → offer choice
    user = await get_user(callback.from_user.id)
    saved_name = user.get("saved_name") if user else None
    header = f"⏰ <b>{time_range}</b> ✓\n\n"
    if saved_name:
        await callback.message.edit_text(
            header + t("use_saved_name_prompt", lang, name=saved_name),
            reply_markup=use_saved_name_keyboard(saved_name, lang, prefix="bday"),
            parse_mode="HTML",
        )
    else:
        await callback.message.edit_text(
            header + t("bday_enter_name", lang),
            reply_markup=cancel_keyboard(lang),
            parse_mode="HTML",
        )
    await callback.answer()


# ─────────────────────────────────────────────────────────────
#  STEP 3b — Name saved / enter another
# ─────────────────────────────────────────────────────────────

@router.callback_query(BirthdayForm.entering_name, F.data == "bday:use_name")
async def cb_bday_use_name(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "uk")
    user = await get_user(callback.from_user.id)
    saved_name = user.get("saved_name", "") if user else ""
    await state.update_data(celebrant_name=saved_name)
    await state.set_state(BirthdayForm.entering_age)
    await callback.message.edit_text(
        f"👤 <b>{saved_name}</b> ✓\n\n" + t("bday_enter_age", lang),
        reply_markup=cancel_keyboard(lang),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(BirthdayForm.entering_name, F.data == "bday:enter_name")
async def cb_bday_enter_name(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "uk")
    await callback.message.edit_text(
        t("bday_enter_name", lang),
        reply_markup=cancel_keyboard(lang),
        parse_mode="HTML",
    )
    await callback.answer()


# ─────────────────────────────────────────────────────────────
#  STEP 4 — Age
# ─────────────────────────────────────────────────────────────

@router.message(BirthdayForm.entering_name)
async def msg_birthday_name(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "uk")

    name = message.text.strip()
    await state.update_data(celebrant_name=name)
    await state.set_state(BirthdayForm.entering_age)

    await message.answer(
        f"👤 <b>{name}</b> ✓\n\n" + t("bday_enter_age", lang),
        reply_markup=cancel_keyboard(lang),
        parse_mode="HTML",
    )


# ─────────────────────────────────────────────────────────────
#  STEP 5 — Gender (or auto-skip if age < 6)
# ─────────────────────────────────────────────────────────────

@router.message(BirthdayForm.entering_age)
async def msg_birthday_age(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "uk")

    raw = message.text.strip()
    if not raw.isdigit() or not (1 <= int(raw) <= 120):
        await message.answer(t("bday_age_invalid", lang), parse_mode="HTML")
        return

    age = int(raw)
    await state.update_data(celebrant_age=raw)

    if 6 <= age <= 14:
        # Kid gender picker
        await state.set_state(BirthdayForm.selecting_gender)
        await message.answer(
            f"🎂 <b>{age}</b> ✓\n\n" + t("bday_gender_pick_kid", lang),
            reply_markup=birthday_gender_keyboard(age, lang),
            parse_mode="HTML",
        )
    elif age >= 15:
        # Adult gender picker
        await state.set_state(BirthdayForm.selecting_gender)
        await message.answer(
            f"🎂 <b>{age}</b> ✓\n\n" + t("bday_gender_pick_adult", lang),
            reply_markup=birthday_gender_keyboard(age, lang),
            parse_mode="HTML",
        )
    else:
        # age < 6 — skip gender, go straight to colour
        await state.update_data(celebrant_gender="—")
        await state.set_state(BirthdayForm.entering_color)
        await message.answer(
            f"🎂 <b>{age}</b> ✓\n\n" + t("bday_enter_color", lang),
            reply_markup=cancel_keyboard(lang),
            parse_mode="HTML",
        )


# ─────────────────────────────────────────────────────────────
#  STEP 5b — Gender selected (callback)
# ─────────────────────────────────────────────────────────────

_GENDER_LABELS = {
    "uk": {"boy": "Хлопчик 🧒", "girl": "Дівчинка 👧",
           "man": "Чоловік 👨", "woman": "Дівчина 👩", "skip": "—"},
    "ru": {"boy": "Мальчик 🧒", "girl": "Девочка 👧",
           "man": "Мужчина 👨", "woman": "Девушка 👩", "skip": "—"},
}


@router.callback_query(BirthdayForm.selecting_gender, F.data.startswith("bday_gender:"))
async def cb_birthday_gender(callback: CallbackQuery, state: FSMContext) -> None:
    choice = callback.data.split(":")[1]  # boy | girl | man | woman | skip

    data = await state.get_data()
    lang = data.get("lang", "uk")

    label = _GENDER_LABELS.get(lang, _GENDER_LABELS["uk"]).get(choice, "—")
    await state.update_data(celebrant_gender=label)
    await state.set_state(BirthdayForm.entering_color)

    await callback.message.edit_text(
        f"⚥ <b>{label}</b> ✓\n\n" + t("bday_enter_color", lang),
        reply_markup=cancel_keyboard(lang),
        parse_mode="HTML",
    )
    await callback.answer()


# ─────────────────────────────────────────────────────────────
#  STEP 6 — Favourite colour
# ─────────────────────────────────────────────────────────────

@router.message(BirthdayForm.entering_color)
async def msg_birthday_color(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "uk")

    color = message.text.strip()
    await state.update_data(fav_color=color)
    await state.set_state(BirthdayForm.entering_phone)

    # Check if user has saved phone → offer choice
    user = await get_user(message.from_user.id)
    saved_phone = user.get("saved_phone") if user else None
    header = f"🎨 <b>{color}</b> ✓\n\n"
    if saved_phone:
        await message.answer(
            header + t("use_saved_phone_prompt", lang, phone=saved_phone),
            reply_markup=use_saved_phone_keyboard(saved_phone, lang, prefix="bday"),
            parse_mode="HTML",
        )
    else:
        await message.answer(
            header + t("bday_enter_phone", lang),
            reply_markup=cancel_keyboard(lang),
            parse_mode="HTML",
        )


# ─────────────────────────────────────────────────────────────
#  STEP 6b — Phone saved / enter another
# ─────────────────────────────────────────────────────────────

@router.callback_query(BirthdayForm.entering_phone, F.data == "bday:use_phone")
async def cb_bday_use_phone(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "uk")
    user = await get_user(callback.from_user.id)
    saved_phone = user.get("saved_phone", "") if user else ""
    await state.update_data(contact_phone=saved_phone)
    await state.set_state(BirthdayForm.entering_wishes)
    await callback.message.edit_text(
        f"📱 <b>{saved_phone}</b> ✓\n\n" + t("bday_enter_wishes", lang),
        reply_markup=cancel_keyboard(lang),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(BirthdayForm.entering_phone, F.data == "bday:enter_phone")
async def cb_bday_enter_phone(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "uk")
    await callback.message.edit_text(
        t("bday_enter_phone", lang),
        reply_markup=cancel_keyboard(lang),
        parse_mode="HTML",
    )
    await callback.answer()


# ─────────────────────────────────────────────────────────────
#  STEP 7 — Phone (text input)
# ─────────────────────────────────────────────────────────────

@router.message(BirthdayForm.entering_phone)
async def msg_birthday_phone(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "uk")

    phone = message.text.strip()
    if not PHONE_RE.match(phone):
        await message.answer(t("bday_enter_phone", lang), reply_markup=cancel_keyboard(lang), parse_mode="HTML")
        return
    await state.update_data(contact_phone=phone)
    await state.set_state(BirthdayForm.entering_wishes)

    await message.answer(
        f"📱 <b>{phone}</b> ✓\n\n" + t("bday_enter_wishes", lang),
        reply_markup=cancel_keyboard(lang),
        parse_mode="HTML",
    )


# ─────────────────────────────────────────────────────────────
#  STEP 8 — Wishes → show summary + payment picker
# ─────────────────────────────────────────────────────────────

@router.message(BirthdayForm.entering_wishes)
async def msg_birthday_wishes(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "uk")

    wishes = message.text.strip()
    await state.update_data(wishes=wishes)
    await state.set_state(BirthdayForm.selecting_payment)

    summary = t("bday_payment_summary", lang).format(
        date=data.get("display_date", "—"),
        time=data.get("birthday_time", "—"),
        name=data.get("celebrant_name", "—"),
        age=data.get("celebrant_age", "—"),
        gender=data.get("celebrant_gender", "—"),
        color=data.get("fav_color", "—"),
        phone=data.get("contact_phone", "—"),
        wishes=wishes,
        deposit=BIRTHDAY_DEPOSIT,
    )

    await message.answer(
        summary,
        reply_markup=birthday_payment_keyboard(lang),
        parse_mode="HTML",
    )


# ─────────────────────────────────────────────────────────────
#  STEP 9 — Payment chosen → save + notify
# ─────────────────────────────────────────────────────────────

@router.callback_query(BirthdayForm.selecting_payment, F.data.startswith("bday_pay:"))
async def cb_birthday_payment(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    pay_choice = callback.data.split(":")[1]  # "iban" | "cash"

    data = await state.get_data()
    lang = data.get("lang", "uk")

    display_date     = data.get("display_date", "—")
    birthday_date    = data.get("birthday_date", "")
    birthday_time    = data.get("birthday_time", "—")
    birthday_time_start = data.get("birthday_time_start", "")
    birthday_time_end   = data.get("birthday_time_end", "")
    celebrant_name   = data.get("celebrant_name", "—")
    celebrant_age    = data.get("celebrant_age", "—")
    celebrant_gender = data.get("celebrant_gender", "—")
    fav_color        = data.get("fav_color", "—")
    contact_phone    = data.get("contact_phone", "—")
    wishes           = data.get("wishes", "—")

    pay_label_uk = "🏦 IBAN (передоплата)" if pay_choice == "iban" else "💵 Готівка (3 дні)"
    pay_label_ru = "🏦 IBAN (предоплата)"  if pay_choice == "iban" else "💵 Наличные (3 дня)"
    pay_label    = pay_label_uk if lang == "uk" else pay_label_ru

    bday_price = data.get("bday_price", 0)

    # ── Save to DB ──
    order_id = await create_birthday_order(
        user_tg_id=callback.from_user.id,
        contact_name=celebrant_name,
        contact_phone=contact_phone,
        birthday_date=birthday_date,
        birthday_time=birthday_time,
        birthday_time_start=birthday_time_start,
        birthday_time_end=birthday_time_end,
        celebrant_age=celebrant_age,
        celebrant_gender=celebrant_gender,
        fav_color=fav_color,
        payment_type=pay_choice,
        wishes=wishes,
        price=bday_price,
    )

    # ── Award points (10% of birthday price) ──
    if bday_price > 0 and callback.from_user.id != 0:
        points_earned = round(bday_price * POINTS_PCT / 100)
        if points_earned > 0:
            await add_points_with_history(
                callback.from_user.id,
                points_earned,
                "birthday",
                f"День народження #{order_id} — {celebrant_name}",
                ref_id=order_id,
            )

    # ── Admin notification ──
    username = f"@{callback.from_user.username}" if callback.from_user.username else "—"
    notif = (
        f"🎂 <b>Нова заявка на День Народження</b> #{order_id}\n\n"
        f"👤 {username} (ID: <code>{callback.from_user.id}</code>)\n\n"
        f"📅 Дата: <b>{display_date}</b>\n"
        f"⏰ Час: <b>{birthday_time}</b>\n"
        f"👤 Ім'я: <b>{celebrant_name}</b>\n"
        f"🎂 Вік: <b>{celebrant_age}</b>\n"
        f"⚥ Стать: <b>{celebrant_gender}</b>\n"
        f"🎨 Колір: <b>{fav_color}</b>\n"
        f"📱 Телефон: <b>{contact_phone}</b>\n"
        f"💬 Побажання: <b>{wishes}</b>\n\n"
        f"💳 <b>Оплата: {pay_label_uk}</b>"
    )
    await notify_admins(bot, notif)
    await state.clear()

    # ── User success message ──
    if pay_choice == "iban":
        if BIRTHDAY_IBAN:
            success = t("bday_success_iban", lang).format(
                deposit=BIRTHDAY_DEPOSIT,
                iban=BIRTHDAY_IBAN,
                name=celebrant_name,
                date=display_date,
            )
        else:
            success = t("bday_success_iban_no_iban", lang).format(
                deposit=BIRTHDAY_DEPOSIT,
            )
    else:
        success = t("bday_success_cash", lang).format(deposit=BIRTHDAY_DEPOSIT)

    await callback.message.edit_text(
        success,
        reply_markup=back_to_menu_keyboard(lang),
        parse_mode="HTML",
    )
    await callback.answer()
