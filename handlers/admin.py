import asyncio
import logging
from datetime import date as _date, timedelta

from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest

from config import ADMIN_IDS, ZONES, WALLET_BONUS_PCT
from database.db import (
    get_user_lang,
    get_all_bookings,
    get_all_birthday_orders,
    get_booking,
    get_birthday_order,
    update_booking_status,
    update_birthday_status,
    get_stats,
    get_all_users,
    get_all_users_for_broadcast,
    block_user,
    unblock_user,
    count_user_bookings,
    create_booking,
    add_game,
    add_gallery_photo,
    add_instruction,
    get_pending_topups,
    confirm_wallet_topup,
    cancel_wallet_topup,
    delete_booking,
    delete_birthday_order,
    calc_and_award_referral_bonuses,
)
from keyboards.kb import (
    admin_panel_keyboard,
    admin_platform_keyboard,
    admin_bookings_list_keyboard,
    admin_booking_detail_keyboard,
    admin_birthdays_list_keyboard,
    admin_birthday_detail_keyboard,
    admin_users_list_keyboard,
    admin_user_detail_keyboard,
    back_to_admin_keyboard,
    broadcast_confirm_keyboard,
    back_to_menu_keyboard,
    zones_keyboard,
    payment_keyboard,
    cancel_keyboard,
    admin_topups_list_keyboard,
    admin_topup_detail_keyboard,
    admin_ref_confirm_keyboard,
)
from locales import t
from states.forms import (
    AdminAddGame, AdminAddPhoto, AdminAddInstruction,
    AdminBroadcast, AdminAddBooking,)

_MONTH_NAMES_UK = [
    "Січень", "Лютий", "Березень", "Квітень", "Травень", "Червень",
    "Липень", "Серпень", "Вересень", "Жовтень", "Листопад", "Грудень",
]
_MONTH_NAMES_RU = [
    "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
    "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь",
]

router = Router()


# ─────────────────────────── Helpers ───────────────────────────

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


def _zone_label(zone_id: str, lang: str = "uk") -> str:
    for zid, uk, ru in ZONES:
        if zid == zone_id:
            return uk if lang == "uk" else ru
    return zone_id


def _payment_label(payment: str, lang: str = "uk") -> str:
    if lang == "ru":
        return "IBAN (онлайн)" if payment == "iban" else "Наличными"
    return "IBAN (онлайн)" if payment == "iban" else "Готівка"


def _status_text(status: str, lang: str = "uk") -> str:
    labels = {
        "uk": {"pending": "🕐 Очікує", "confirmed": "✅ Підтверджено", "cancelled": "❌ Скасовано"},
        "ru": {"pending": "🕐 Ожидает", "confirmed": "✅ Подтверждено", "cancelled": "❌ Отменено"},
    }
    return labels.get(lang, labels["uk"]).get(status, status)


# ─────────────────────────── /admin + panel ───────────────────────────

@router.message(Command("admin"))
async def cmd_admin(message: Message) -> None:
    if not is_admin(message.from_user.id):
        lang = await get_user_lang(message.from_user.id)
        await message.answer(t("not_admin", lang))
        return
    lang = await get_user_lang(message.from_user.id)
    await message.answer(
        t("admin_panel", lang),
        reply_markup=admin_panel_keyboard(lang),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "admin:panel")
async def cb_admin_panel(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔", show_alert=True)
        return
    lang = await get_user_lang(callback.from_user.id)
    await callback.message.edit_text(
        t("admin_panel", lang),
        reply_markup=admin_panel_keyboard(lang),
        parse_mode="HTML",
    )
    await callback.answer()


# ─────────────────────────── Bookings list (paginated) ───────────────────────────

@router.callback_query(F.data.startswith("admin:bookings:"))
async def cb_admin_bookings(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔", show_alert=True)
        return
    lang = await get_user_lang(callback.from_user.id)
    page = int(callback.data.split(":")[2])
    bookings = await get_all_bookings(limit=500)

    if not bookings:
        await callback.message.edit_text(
            t("no_bookings", lang),
            reply_markup=back_to_admin_keyboard(lang),
        )
        await callback.answer()
        return

    await callback.message.edit_text(
        t("admin_bookings_title", lang),
        reply_markup=admin_bookings_list_keyboard(bookings, lang, page),
        parse_mode="HTML",
    )
    await callback.answer()


# ─────────────────────────── Booking detail helpers ───────────────────────────

def _booking_detail_text(b: dict, lang: str) -> str:
    zone_label = _zone_label(b["zone"], lang)
    payment    = _payment_label(b.get("payment_type", ""), lang)
    status     = _status_text(b["status"], lang)
    user_link  = (
        f'<a href="tg://user?id={b["user_tg_id"]}">ID {b["user_tg_id"]}</a>'
        if b.get("user_tg_id") else "—"
    )
    return (
        f"📋 <b>Бронювання #{b['id']}</b>\n\n"
        f"🎯 Зона: <b>{zone_label}</b>\n"
        f"📆 Дата: <b>{b['booking_date']}</b>\n"
        f"⏰ Час: <b>{b['booking_time']}</b>\n"
        f"👥 Людей: <b>{b['people_count']}</b>\n"
        f"👤 Ім'я: <b>{b['user_name'] or '—'}</b>\n"
        f"📱 Телефон: <b>{b['user_phone'] or '—'}</b>\n"
        f"💳 Оплата: <b>{payment}</b>\n"
        f"📝 Примітки: <b>{b['notes'] or '—'}</b>\n"
        f"🔗 Telegram: {user_link}\n"
        f"📌 Статус: <b>{status}</b>\n"
        f"🕐 Створено: {b['created_at']}"
    )


async def _refresh_booking_detail(
    callback: CallbackQuery, booking_id: int, lang: str
) -> None:
    b = await get_booking(booking_id)
    if not b:
        return
    try:
        await callback.message.edit_text(
            _booking_detail_text(b, lang),
            reply_markup=admin_booking_detail_keyboard(booking_id, b["status"], lang),
            parse_mode="HTML",
        )
    except TelegramBadRequest:
        pass


# ─────────────────────────── Booking detail ───────────────────────────

@router.callback_query(F.data.regexp(r"^admin:booking:\d+$"))
async def cb_admin_booking_detail(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔", show_alert=True)
        return

    lang = await get_user_lang(callback.from_user.id)
    booking_id = int(callback.data.split(":")[2])
    b = await get_booking(booking_id)
    if not b:
        await callback.answer(t("not_found", lang), show_alert=True)
        return

    await callback.message.edit_text(
        _booking_detail_text(b, lang),
        reply_markup=admin_booking_detail_keyboard(booking_id, b["status"], lang),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin:booking_confirm:"))
async def cb_booking_confirm(callback: CallbackQuery, bot: Bot) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔", show_alert=True)
        return
    lang = await get_user_lang(callback.from_user.id)
    booking_id = int(callback.data.split(":")[2])
    b = await get_booking(booking_id)
    if not b:
        await callback.answer(t("not_found", lang), show_alert=True)
        return

    await update_booking_status(booking_id, "confirmed")

    if b["user_tg_id"] and b["user_tg_id"] > 0:
        try:
            user_lang = await get_user_lang(b["user_tg_id"])
            await bot.send_message(
                b["user_tg_id"],
                t("booking_confirmed_notify", user_lang).format(id=booking_id),
                parse_mode="HTML",
            )
        except Exception:
            pass

    await callback.answer(t("booking_confirmed_ok", lang), show_alert=True)
    await _refresh_booking_detail(callback, booking_id, lang)


@router.callback_query(F.data.startswith("admin:booking_cancel:"))
async def cb_booking_cancel(callback: CallbackQuery, bot: Bot) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔", show_alert=True)
        return
    lang = await get_user_lang(callback.from_user.id)
    booking_id = int(callback.data.split(":")[2])
    b = await get_booking(booking_id)
    if not b:
        await callback.answer(t("not_found", lang), show_alert=True)
        return

    await update_booking_status(booking_id, "cancelled")

    if b["user_tg_id"] and b["user_tg_id"] > 0:
        try:
            user_lang = await get_user_lang(b["user_tg_id"])
            await bot.send_message(
                b["user_tg_id"],
                t("booking_cancelled_notify", user_lang).format(id=booking_id),
                parse_mode="HTML",
            )
        except Exception:
            pass

    await callback.answer(t("booking_cancelled_ok", lang), show_alert=True)
    await _refresh_booking_detail(callback, booking_id, lang)


# ─────────────────────────── Birthday orders list ───────────────────────────

@router.callback_query(F.data.startswith("admin:birthdays:"))
async def cb_admin_birthdays(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔", show_alert=True)
        return
    lang = await get_user_lang(callback.from_user.id)
    page = int(callback.data.split(":")[2])
    orders = await get_all_birthday_orders(limit=500)

    if not orders:
        await callback.message.edit_text(
            t("no_birthday_orders", lang),
            reply_markup=back_to_admin_keyboard(lang),
        )
        await callback.answer()
        return

    await callback.message.edit_text(
        t("admin_birthdays_title", lang),
        reply_markup=admin_birthdays_list_keyboard(orders, lang, page),
        parse_mode="HTML",
    )
    await callback.answer()


# ─────────────────────────── Birthday order detail ───────────────────────────

@router.callback_query(F.data.regexp(r"^admin:birthday:\d+$"))
async def cb_admin_birthday_detail(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔", show_alert=True)
        return

    lang = await get_user_lang(callback.from_user.id)
    order_id = int(callback.data.split(":")[2])
    o = await get_birthday_order(order_id)
    if not o:
        await callback.answer(t("not_found", lang), show_alert=True)
        return

    payment = _payment_label(o.get("payment_type", ""), lang)
    status  = _status_text(o["status"], lang)
    user_link = (
        f'<a href="tg://user?id={o["user_tg_id"]}">ID {o["user_tg_id"]}</a>'
        if o["user_tg_id"] else "—"
    )

    time_range = ""
    if o.get("birthday_time"):
        time_range = f"⏰ Час: <b>{o['birthday_time']}</b>\n"

    text = (
        f"🎂 <b>Заявка ДН #{o['id']}</b>\n\n"
        f"📅 Дата: <b>{o['birthday_date']}</b>\n"
        f"{time_range}"
        f"👤 Іменинник: <b>{o.get('contact_name') or '—'}</b>\n"
        f"🎂 Вік: <b>{o.get('celebrant_age') or '—'}</b>\n"
        f"⚥ Стать: <b>{o.get('celebrant_gender') or '—'}</b>\n"
        f"🎨 Колір: <b>{o.get('fav_color') or '—'}</b>\n"
        f"👥 Гостей: <b>{o.get('guests_count') or '—'}</b>\n"
        f"📱 Телефон: <b>{o.get('contact_phone') or '—'}</b>\n"
        f"💬 Побажання: <b>{o.get('wishes') or '—'}</b>\n"
        f"💳 Оплата: <b>{payment}</b>\n"
        f"🔗 Telegram: {user_link}\n"
        f"📌 Статус: <b>{status}</b>\n"
        f"🕐 Створено: {o['created_at']}"
    )
    await callback.message.edit_text(
        text,
        reply_markup=admin_birthday_detail_keyboard(order_id, o["status"], lang),
        parse_mode="HTML",
    )
    await callback.answer()


async def _refresh_birthday_detail(
    callback: CallbackQuery, order_id: int, lang: str
) -> None:
    o = await get_birthday_order(order_id)
    if not o:
        return
    payment = _payment_label(o.get("payment_type", ""), lang)
    status  = _status_text(o["status"], lang)
    user_link = (
        f'<a href="tg://user?id={o["user_tg_id"]}">ID {o["user_tg_id"]}</a>'
        if o["user_tg_id"] else "—"
    )
    time_range = f"⏰ Час: <b>{o['birthday_time']}</b>\n" if o.get("birthday_time") else ""
    text = (
        f"🎂 <b>Заявка ДН #{o['id']}</b>\n\n"
        f"📅 Дата: <b>{o['birthday_date']}</b>\n"
        f"{time_range}"
        f"👤 Іменинник: <b>{o.get('contact_name') or '—'}</b>\n"
        f"🎂 Вік: <b>{o.get('celebrant_age') or '—'}</b>\n"
        f"⚥ Стать: <b>{o.get('celebrant_gender') or '—'}</b>\n"
        f"🎨 Колір: <b>{o.get('fav_color') or '—'}</b>\n"
        f"👥 Гостей: <b>{o.get('guests_count') or '—'}</b>\n"
        f"📱 Телефон: <b>{o.get('contact_phone') or '—'}</b>\n"
        f"💬 Побажання: <b>{o.get('wishes') or '—'}</b>\n"
        f"💳 Оплата: <b>{payment}</b>\n"
        f"🔗 Telegram: {user_link}\n"
        f"📌 Статус: <b>{status}</b>\n"
        f"🕐 Створено: {o['created_at']}"
    )
    try:
        await callback.message.edit_text(
            text,
            reply_markup=admin_birthday_detail_keyboard(order_id, o["status"], lang),
            parse_mode="HTML",
        )
    except TelegramBadRequest:
        pass


@router.callback_query(F.data.startswith("admin:birthday_confirm:"))
async def cb_birthday_confirm(callback: CallbackQuery, bot: Bot) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔", show_alert=True)
        return
    lang = await get_user_lang(callback.from_user.id)
    order_id = int(callback.data.split(":")[2])
    o = await get_birthday_order(order_id)
    if not o:
        await callback.answer(t("not_found", lang), show_alert=True)
        return

    await update_birthday_status(order_id, "confirmed")
    if o["user_tg_id"] and o["user_tg_id"] > 0:
        try:
            user_lang = await get_user_lang(o["user_tg_id"])
            await bot.send_message(
                o["user_tg_id"],
                t("birthday_confirmed_notify", user_lang).format(id=order_id),
                parse_mode="HTML",
            )
        except Exception:
            pass

    await callback.answer(t("booking_confirmed_ok", lang), show_alert=True)
    await _refresh_birthday_detail(callback, order_id, lang)


@router.callback_query(F.data.startswith("admin:birthday_cancel:"))
async def cb_birthday_cancel(callback: CallbackQuery, bot: Bot) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔", show_alert=True)
        return
    lang = await get_user_lang(callback.from_user.id)
    order_id = int(callback.data.split(":")[2])
    o = await get_birthday_order(order_id)
    if not o:
        await callback.answer(t("not_found", lang), show_alert=True)
        return

    await update_birthday_status(order_id, "cancelled")
    if o["user_tg_id"] and o["user_tg_id"] > 0:
        try:
            user_lang = await get_user_lang(o["user_tg_id"])
            await bot.send_message(
                o["user_tg_id"],
                t("birthday_cancelled_notify", user_lang).format(id=order_id),
                parse_mode="HTML",
            )
        except Exception:
            pass

    await callback.answer(t("booking_cancelled_ok", lang), show_alert=True)
    await _refresh_birthday_detail(callback, order_id, lang)


# ─────────────────────────── Delete booking / birthday ───────────────────────────

@router.callback_query(F.data.regexp(r"^admin:booking_delete:\d+$"))
async def cb_booking_delete(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔", show_alert=True)
        return
    lang = await get_user_lang(callback.from_user.id)
    booking_id = int(callback.data.split(":")[-1])
    await delete_booking(booking_id)
    await callback.message.edit_text(
        t("entry_deleted_ok", lang),
        reply_markup=back_to_admin_keyboard(lang),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.regexp(r"^admin:birthday_delete:\d+$"))
async def cb_birthday_delete(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔", show_alert=True)
        return
    lang = await get_user_lang(callback.from_user.id)
    order_id = int(callback.data.split(":")[-1])
    await delete_birthday_order(order_id)
    await callback.message.edit_text(
        t("entry_deleted_ok", lang),
        reply_markup=back_to_admin_keyboard(lang),
        parse_mode="HTML",
    )
    await callback.answer()


# ─────────────────────────── Statistics ───────────────────────────

@router.callback_query(F.data == "admin:stats")
async def cb_admin_stats(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔", show_alert=True)
        return
    lang  = await get_user_lang(callback.from_user.id)
    stats = await get_stats()

    zone_lines = ""
    for i, (zone_id, cnt) in enumerate(stats["zones"], 1):
        zone_lines += f"  {i}. {_zone_label(zone_id, lang)} — {cnt}\n"
    if not zone_lines:
        zone_lines = "  —\n"

    text = (
        f"📊 <b>Статистика Game Space «Clock»</b>\n\n"
        f"👥 <b>Користувачі:</b>\n"
        f"  • Всього: <b>{stats['total_users']}</b>\n"
        f"  • Нових за 7 днів: <b>{stats['new_week_users']}</b>\n"
        f"  • Заблоковано: <b>{stats['blocked_users']}</b>\n\n"
        f"📋 <b>Бронювання:</b>\n"
        f"  • Всього: <b>{stats['total_bookings']}</b>\n"
        f"  • Очікують: <b>{stats['pending_bookings']}</b>\n"
        f"  • Підтверджено: <b>{stats['confirmed_bookings']}</b>\n"
        f"  • Скасовано: <b>{stats['cancelled_bookings']}</b>\n"
        f"  • За 7 днів: <b>{stats['week_bookings']}</b>\n"
        f"  • За 30 днів: <b>{stats['month_bookings']}</b>\n\n"
        f"🎯 <b>Топ зон:</b>\n{zone_lines}\n"
        f"🎂 <b>Дні народження:</b>\n"
        f"  • Всього: <b>{stats['total_birthdays']}</b>\n"
        f"  • Очікують: <b>{stats['pending_birthdays']}</b>\n"
        f"  • Підтверджено: <b>{stats['confirmed_birthdays']}</b>\n"
        f"  • Скасовано: <b>{stats['cancelled_birthdays']}</b>\n"
        f"  • За 7 днів: <b>{stats['week_birthdays']}</b>\n"
        f"  • За 30 днів: <b>{stats['month_birthdays']}</b>\n\n"
        f"💡 <b>Пропозицій:</b> <b>{stats['total_suggestions']}</b>"
    )
    await callback.message.edit_text(
        text,
        reply_markup=back_to_admin_keyboard(lang),
        parse_mode="HTML",
    )
    await callback.answer()


# ─────────────────────────── Add Booking (admin manual) ───────────────────────────

@router.callback_query(F.data == "admin:add_booking")
async def cb_admin_add_booking_start(callback: CallbackQuery, state: FSMContext) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔", show_alert=True)
        return
    lang = await get_user_lang(callback.from_user.id)
    await state.set_state(AdminAddBooking.zone)
    await state.update_data(lang=lang)
    await callback.message.edit_text(
        t("admin_add_booking_zone", lang),
        reply_markup=zones_keyboard(lang),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(AdminAddBooking.zone, F.data.startswith("zone:"))
async def cb_admin_booking_zone(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "uk")
    zone = callback.data.split(":")[1]
    await state.update_data(zone=zone)
    await state.set_state(AdminAddBooking.date)
    await callback.message.edit_text(t("booking_date", lang), parse_mode="HTML")
    await callback.answer()


@router.message(AdminAddBooking.date)
async def msg_admin_booking_date(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "uk")
    await state.update_data(date=message.text.strip())
    await state.set_state(AdminAddBooking.time)
    await message.answer(t("booking_time", lang), parse_mode="HTML")


@router.message(AdminAddBooking.time)
async def msg_admin_booking_time(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "uk")
    await state.update_data(time=message.text.strip())
    await state.set_state(AdminAddBooking.name)
    await message.answer(t("booking_name", lang), parse_mode="HTML")


@router.message(AdminAddBooking.name)
async def msg_admin_booking_name(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "uk")
    await state.update_data(name=message.text.strip())
    await state.set_state(AdminAddBooking.phone)
    await message.answer(t("booking_phone", lang), parse_mode="HTML")


@router.message(AdminAddBooking.phone)
async def msg_admin_booking_phone(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "uk")
    await state.update_data(phone=message.text.strip())
    await state.set_state(AdminAddBooking.people)
    await message.answer(t("booking_people", lang), parse_mode="HTML")


@router.message(AdminAddBooking.people)
async def msg_admin_booking_people(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "uk")
    text = message.text.strip()
    if text.isdigit():
        await state.update_data(people=int(text))
    else:
        await state.update_data(people=1)
    await state.set_state(AdminAddBooking.payment)
    await message.answer(t("booking_payment", lang), reply_markup=payment_keyboard(lang))


@router.callback_query(AdminAddBooking.payment, F.data.startswith("payment:"))
async def cb_admin_booking_payment(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "uk")
    payment = callback.data.split(":")[1]
    await state.update_data(payment=payment)
    await state.set_state(AdminAddBooking.notes)
    await callback.message.edit_text(t("admin_add_booking_notes", lang), parse_mode="HTML")
    await callback.answer()


@router.message(AdminAddBooking.notes)
async def msg_admin_booking_notes(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "uk")
    notes = "" if message.text.strip() == "/skip" else message.text.strip()

    booking_id = await create_booking(
        user_tg_id=0,
        user_name=data["name"],
        user_phone=data["phone"],
        zone=data["zone"],
        booking_date=data["date"],
        booking_time=data["time"],
        people_count=data.get("people", 1),
        payment_type=data["payment"],
        notes=notes,
    )
    await update_booking_status(booking_id, "confirmed")

    await state.clear()
    await message.answer(
        t("admin_add_booking_done", lang).format(id=booking_id),
        reply_markup=back_to_admin_keyboard(lang),
        parse_mode="HTML",
    )


# ─────────────────────────── Users list ───────────────────────────

@router.callback_query(F.data.startswith("admin:users:"))
async def cb_admin_users(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔", show_alert=True)
        return
    lang = await get_user_lang(callback.from_user.id)
    page = int(callback.data.split(":")[2])
    users = await get_all_users()

    if not users:
        await callback.message.edit_text(
            t("no_users", lang),
            reply_markup=back_to_admin_keyboard(lang),
        )
        await callback.answer()
        return

    total = len(users)
    blocked = sum(1 for u in users if u.get("is_blocked"))
    header = t("admin_users_title", lang).format(total=total, blocked=blocked)

    await callback.message.edit_text(
        header,
        reply_markup=admin_users_list_keyboard(users, lang, page),
        parse_mode="HTML",
    )
    await callback.answer()


# ─────────────────────────── User detail ───────────────────────────

@router.callback_query(F.data.regexp(r"^admin:user:\d+$"))
async def cb_admin_user_detail(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔", show_alert=True)
        return

    lang = await get_user_lang(callback.from_user.id)
    target_tg_id = int(callback.data.split(":")[2])

    # Find user in DB
    all_users = await get_all_users()
    user = next((u for u in all_users if u["tg_id"] == target_tg_id), None)
    if not user:
        await callback.answer(t("not_found", lang), show_alert=True)
        return

    booking_count = await count_user_bookings(target_tg_id)
    is_blocked_flag = bool(user.get("is_blocked"))
    status_text = "🔴 Заблоковано" if is_blocked_flag else "🟢 Активний"
    username = f"@{user['username']}" if user.get("username") else "—"

    text = (
        f"👤 <b>{user.get('full_name') or '—'}</b>\n\n"
        f"🆔 ID: <code>{user['tg_id']}</code>\n"
        f"📱 Username: {username}\n"
        f"🌐 Мова: {user.get('lang', 'uk')}\n"
        f"⭐ Балів: <b>{user.get('points', 0)}</b>\n"
        f"📋 Бронювань: <b>{booking_count}</b>\n"
        f"🔗 Реф. код: <code>{user.get('referral_code') or '—'}</code>\n"
        f"📅 Реєстрація: {user.get('created_at', '—')}\n"
        f"📌 Статус: <b>{status_text}</b>"
    )
    await callback.message.edit_text(
        text,
        reply_markup=admin_user_detail_keyboard(target_tg_id, is_blocked_flag, lang),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin:user_block:"))
async def cb_user_block(callback: CallbackQuery, bot: Bot) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔", show_alert=True)
        return
    lang = await get_user_lang(callback.from_user.id)
    target_tg_id = int(callback.data.split(":")[2])
    await block_user(target_tg_id)

    try:
        user_lang = await get_user_lang(target_tg_id)
        await bot.send_message(
            target_tg_id, t("you_are_blocked", user_lang), parse_mode="HTML",
        )
    except Exception:
        pass

    await callback.answer(t("user_blocked_ok", lang), show_alert=True)
    # Refresh user detail
    all_users = await get_all_users()
    user = next((u for u in all_users if u["tg_id"] == target_tg_id), None)
    if user:
        booking_count = await count_user_bookings(target_tg_id)
        username = f"@{user['username']}" if user.get("username") else "—"
        text = (
            f"👤 <b>{user.get('full_name') or '—'}</b>\n\n"
            f"🆔 ID: <code>{user['tg_id']}</code>\n"
            f"📱 Username: {username}\n"
            f"🌐 Мова: {user.get('lang', 'uk')}\n"
            f"⭐ Балів: <b>{user.get('points', 0)}</b>\n"
            f"📋 Бронювань: <b>{booking_count}</b>\n"
            f"🔗 Реф. код: <code>{user.get('referral_code') or '—'}</code>\n"
            f"📅 Реєстрація: {user.get('created_at', '—')}\n"
            f"📌 Статус: <b>🔴 Заблоковано</b>"
        )
        try:
            await callback.message.edit_text(
                text,
                reply_markup=admin_user_detail_keyboard(target_tg_id, True, lang),
                parse_mode="HTML",
            )
        except TelegramBadRequest:
            pass


@router.callback_query(F.data.startswith("admin:user_unblock:"))
async def cb_user_unblock(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔", show_alert=True)
        return
    lang = await get_user_lang(callback.from_user.id)
    target_tg_id = int(callback.data.split(":")[2])
    await unblock_user(target_tg_id)

    await callback.answer(t("user_unblocked_ok", lang), show_alert=True)
    all_users = await get_all_users()
    user = next((u for u in all_users if u["tg_id"] == target_tg_id), None)
    if user:
        booking_count = await count_user_bookings(target_tg_id)
        username = f"@{user['username']}" if user.get("username") else "—"
        text = (
            f"👤 <b>{user.get('full_name') or '—'}</b>\n\n"
            f"🆔 ID: <code>{user['tg_id']}</code>\n"
            f"📱 Username: {username}\n"
            f"🌐 Мова: {user.get('lang', 'uk')}\n"
            f"⭐ Балів: <b>{user.get('points', 0)}</b>\n"
            f"📋 Бронювань: <b>{booking_count}</b>\n"
            f"🔗 Реф. код: <code>{user.get('referral_code') or '—'}</code>\n"
            f"📅 Реєстрація: {user.get('created_at', '—')}\n"
            f"📌 Статус: <b>🟢 Активний</b>"
        )
        try:
            await callback.message.edit_text(
                text,
                reply_markup=admin_user_detail_keyboard(target_tg_id, False, lang),
                parse_mode="HTML",
            )
        except TelegramBadRequest:
            pass


# ─────────────────────────── Broadcast ───────────────────────────

@router.callback_query(F.data == "admin:broadcast")
async def cb_admin_broadcast_start(callback: CallbackQuery, state: FSMContext) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔", show_alert=True)
        return
    lang = await get_user_lang(callback.from_user.id)
    await state.set_state(AdminBroadcast.typing)
    await state.update_data(lang=lang)
    await callback.message.edit_text(t("admin_broadcast_enter", lang), parse_mode="HTML")
    await callback.answer()


@router.message(AdminBroadcast.typing)
async def msg_admin_broadcast_text(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "uk")
    text = message.text or message.caption or ""
    if not text.strip():
        await message.answer(t("admin_broadcast_empty", lang))
        return

    await state.update_data(broadcast_text=text)
    await state.set_state(AdminBroadcast.confirm)

    recipients = await get_all_users_for_broadcast()
    preview = t("admin_broadcast_preview", lang).format(
        count=len(recipients), text=text[:300]
    )
    await message.answer(
        preview,
        reply_markup=broadcast_confirm_keyboard(lang),
        parse_mode="HTML",
    )


@router.callback_query(AdminBroadcast.confirm, F.data == "admin:broadcast_confirm")
async def cb_broadcast_confirm(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔", show_alert=True)
        return
    data = await state.get_data()
    lang = data.get("lang", "uk")
    text = data.get("broadcast_text", "")
    await state.clear()

    recipients = await get_all_users_for_broadcast()
    await callback.message.edit_text(
        t("admin_broadcast_sending", lang).format(count=len(recipients)),
        parse_mode="HTML",
    )
    await callback.answer()

    sent = 0
    failed = 0
    for tg_id in recipients:
        try:
            await bot.send_message(tg_id, text, parse_mode="HTML")
            sent += 1
        except (TelegramForbiddenError, TelegramBadRequest):
            failed += 1
        except Exception:
            failed += 1
        await asyncio.sleep(0.05)

    await callback.message.answer(
        t("admin_broadcast_done", lang).format(sent=sent, failed=failed),
        reply_markup=back_to_admin_keyboard(lang),
        parse_mode="HTML",
    )


@router.callback_query(AdminBroadcast.confirm, F.data == "admin:broadcast_cancel")
async def cb_broadcast_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    lang = await get_user_lang(callback.from_user.id)
    await callback.message.edit_text(
        t("admin_panel", lang),
        reply_markup=admin_panel_keyboard(lang),
        parse_mode="HTML",
    )
    await callback.answer()


# ─────────────────────────── Add Game ───────────────────────────

@router.callback_query(F.data == "admin:add_game")
async def cb_admin_add_game_start(callback: CallbackQuery, state: FSMContext) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔", show_alert=True)
        return
    lang = await get_user_lang(callback.from_user.id)
    await state.set_state(AdminAddGame.platform)
    await state.update_data(lang=lang)
    await callback.message.edit_text(
        t("admin_game_platform", lang),
        reply_markup=admin_platform_keyboard(),
    )
    await callback.answer()


@router.callback_query(AdminAddGame.platform, F.data.startswith("platform:"))
async def cb_admin_game_platform(callback: CallbackQuery, state: FSMContext) -> None:
    data     = await state.get_data()
    lang     = data.get("lang", "uk")
    platform = callback.data.split(":")[1]
    await state.update_data(platform=platform)
    await state.set_state(AdminAddGame.title)
    await callback.message.edit_text(t("admin_game_title", lang))
    await callback.answer()


@router.message(AdminAddGame.title)
async def msg_admin_game_title(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "uk")
    await state.update_data(title=message.text.strip())
    await state.set_state(AdminAddGame.image)
    await message.answer(t("admin_game_image", lang))


@router.message(AdminAddGame.image)
async def msg_admin_game_image(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "uk")
    image_file_id = message.photo[-1].file_id if message.photo else ""
    await add_game(data["platform"], data["title"], image_file_id)
    await state.clear()
    await message.answer(t("admin_game_added", lang))


# ─────────────────────────── Add Photo ───────────────────────────

@router.callback_query(F.data == "admin:add_photo")
async def cb_admin_add_photo_start(callback: CallbackQuery, state: FSMContext) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔", show_alert=True)
        return
    lang = await get_user_lang(callback.from_user.id)
    await state.set_state(AdminAddPhoto.photo)
    await state.update_data(lang=lang)
    await callback.message.answer(t("admin_photo_send", lang))
    await callback.answer()


@router.message(AdminAddPhoto.photo, F.photo)
async def msg_admin_photo(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "uk")
    file_id = message.photo[-1].file_id
    await state.update_data(file_id=file_id)
    await state.set_state(AdminAddPhoto.caption)
    await message.answer(t("admin_photo_caption", lang))


@router.message(AdminAddPhoto.caption)
async def msg_admin_photo_caption(message: Message, state: FSMContext) -> None:
    data    = await state.get_data()
    lang    = data.get("lang", "uk")
    caption = "" if message.text.strip() == "/skip" else message.text.strip()
    await add_gallery_photo(data["file_id"], caption)
    await state.clear()
    await message.answer(t("admin_photo_added", lang))


# ─────────────────────────── Add Instruction ───────────────────────────

@router.callback_query(F.data == "admin:add_instruction")
async def cb_admin_add_instruction_start(callback: CallbackQuery, state: FSMContext) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔", show_alert=True)
        return
    lang = await get_user_lang(callback.from_user.id)
    await state.set_state(AdminAddInstruction.game_name)
    await state.update_data(lang=lang)
    await callback.message.answer(t("admin_instr_name", lang))
    await callback.answer()


@router.message(AdminAddInstruction.game_name)
async def msg_admin_instruction_name(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "uk")
    await state.update_data(game_name=message.text.strip())
    await state.set_state(AdminAddInstruction.content)
    await message.answer(t("admin_instr_content", lang))


@router.message(AdminAddInstruction.content)
async def msg_admin_instruction_content(message: Message, state: FSMContext) -> None:
    data      = await state.get_data()
    lang      = data.get("lang", "uk")
    game_name = data["game_name"]

    if message.document:
        await add_instruction(game_name, "file", file_id=message.document.file_id)
    elif message.photo:
        await add_instruction(game_name, "file", file_id=message.photo[-1].file_id)
    else:
        await add_instruction(game_name, "text", text_content=message.text.strip())

    await state.clear()
    await message.answer(t("admin_instr_added", lang))


# ─────────────────────────── Wallet Topups ───────────────────────────

@router.callback_query(F.data == "admin:topups")
async def cb_admin_topups(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔", show_alert=True)
        return
    lang = await get_user_lang(callback.from_user.id)
    topups = await get_pending_topups()
    if not topups:
        await callback.message.edit_text(
            t("no_pending_topups", lang),
            reply_markup=back_to_admin_keyboard(lang),
            parse_mode="HTML",
        )
    else:
        await callback.message.edit_text(
            t("admin_topups_title", lang),
            reply_markup=admin_topups_list_keyboard(topups, lang),
            parse_mode="HTML",
        )
    await callback.answer()


@router.callback_query(F.data.regexp(r"^admin:topup:\d+$"))
async def cb_admin_topup_detail(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔", show_alert=True)
        return
    tx_id = int(callback.data.split(":")[-1])
    lang = await get_user_lang(callback.from_user.id)

    topups = await get_pending_topups()
    tx = next((t_ for t_ in topups if t_["id"] == tx_id), None)
    if not tx:
        await callback.answer(t("not_found", lang), show_alert=True)
        return

    bonus = round(tx["amount"] * WALLET_BONUS_PCT / 100)
    total = tx["amount"] + bonus
    name = tx.get("full_name") or tx.get("username") or str(tx["tg_id"])
    comment = tx.get("comment") or "—"
    text = t("topup_detail", lang,
             id=tx["id"],
             name=name,
             tg_id=tx["tg_id"],
             amount=tx["amount"],
             bonus=bonus,
             total=total,
             comment=comment,
             date=tx["created_at"][:10])
    await callback.message.edit_text(
        text,
        reply_markup=admin_topup_detail_keyboard(tx_id, lang),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.regexp(r"^admin:topup_confirm:\d+$"))
async def cb_admin_topup_confirm(callback: CallbackQuery, bot: Bot) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔", show_alert=True)
        return
    tx_id = int(callback.data.split(":")[-1])
    lang = await get_user_lang(callback.from_user.id)

    result = await confirm_wallet_topup(tx_id)
    if not result:
        await callback.answer(t("not_found", lang), show_alert=True)
        return

    amount = result["amount"]
    bonus  = result["bonus"]
    total  = amount + bonus
    tg_id  = result["tg_id"]

    await callback.message.edit_text(
        t("topup_confirmed_ok", lang, total=total),
        reply_markup=back_to_admin_keyboard(lang),
        parse_mode="HTML",
    )

    # Notify user
    try:
        user_lang = await get_user_lang(tg_id)
        await bot.send_message(
            tg_id,
            t("wallet_topup_confirmed", user_lang, total=total, bonus=bonus),
            parse_mode="HTML",
        )
    except Exception:
        pass

    await callback.answer()


@router.callback_query(F.data.regexp(r"^admin:topup_cancel:\d+$"))
async def cb_admin_topup_cancel(callback: CallbackQuery, bot: Bot) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔", show_alert=True)
        return
    tx_id = int(callback.data.split(":")[-1])
    lang = await get_user_lang(callback.from_user.id)

    result = await cancel_wallet_topup(tx_id)
    if not result:
        await callback.answer(t("not_found", lang), show_alert=True)
        return

    amount = result["amount"]
    tg_id  = result["tg_id"]

    await callback.message.edit_text(
        t("topup_cancelled_ok", lang),
        reply_markup=back_to_admin_keyboard(lang),
        parse_mode="HTML",
    )

    # Notify user
    try:
        user_lang = await get_user_lang(tg_id)
        await bot.send_message(
            tg_id,
            t("wallet_topup_rejected", user_lang, amount=amount),
            parse_mode="HTML",
        )
    except Exception:
        pass

    await callback.answer()


# ─────────────────────────── Referral Bonuses ───────────────────────────

@router.callback_query(F.data == "admin:ref_bonuses")
async def cb_admin_ref_bonuses(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔", show_alert=True)
        return
    lang = await get_user_lang(callback.from_user.id)

    today = _date.today()
    first_of_this_month = today.replace(day=1)
    last_month = first_of_this_month - timedelta(days=1)
    year, month = last_month.year, last_month.month

    month_names = _MONTH_NAMES_UK if lang == "uk" else _MONTH_NAMES_RU
    month_name = month_names[month - 1]

    text = t("admin_ref_confirm", lang, month_name=month_name, year=year)
    await callback.message.edit_text(
        text,
        reply_markup=admin_ref_confirm_keyboard(lang),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "admin:ref_bonuses_confirm")
async def cb_admin_ref_bonuses_confirm(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔", show_alert=True)
        return
    lang = await get_user_lang(callback.from_user.id)

    today = _date.today()
    first_of_this_month = today.replace(day=1)
    last_month = first_of_this_month - timedelta(days=1)
    year, month = last_month.year, last_month.month

    result = await calc_and_award_referral_bonuses(year, month)
    referrers = result.get("referrers", 0)
    total_points = result.get("total_points", 0)

    await callback.message.edit_text(
        t("admin_ref_done", lang, referrers=referrers, total_points=total_points),
        reply_markup=back_to_admin_keyboard(lang),
        parse_mode="HTML",
    )
    await callback.answer()
