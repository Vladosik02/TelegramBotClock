import logging
from datetime import datetime

from aiogram import Bot
from config import ADMIN_IDS


async def notify_admins(bot: Bot, text: str) -> None:
    if not ADMIN_IDS:
        logging.warning("ADMIN_IDS is empty — notification not sent:\n%s", text)
        return
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, text, parse_mode="HTML")
        except Exception as e:
            logging.error("Failed to notify admin %s: %s", admin_id, e)


def booking_notification(
    booking_id: int,
    user_tg_id: int,
    username: str | None,
    zone_label: str,
    date: str,
    time: str,
    people: int,
    name: str,
    phone: str,
    payment: str,
    price_str: str = "",
) -> str:
    user_link = f"<a href='tg://user?id={user_tg_id}'>@{username}</a>" if username else f"ID: {user_tg_id}"
    payment_label = "🏦 IBAN (онлайн)" if payment == "iban" else "💵 Готівка (≤3 дні)"
    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    price_line = f"💰 Вартість: <b>{price_str}</b>\n" if price_str else ""

    return (
        f"🔔 <b>НОВЕ БРОНЮВАННЯ #{booking_id}</b>\n\n"
        f"🎯 Зона: <b>{zone_label}</b>\n"
        f"📆 Дата: <b>{date}</b>\n"
        f"⏰ Час: <b>{time}</b>\n"
        f"{price_line}"
        f"👥 Людей: <b>{people}</b>\n\n"
        f"👤 Клієнт:\n"
        f"• Ім'я: <b>{name}</b>\n"
        f"• Телефон: <b>{phone}</b>\n"
        f"• Оплата: {payment_label}\n\n"
        f"🔗 Telegram: {user_link}\n"
        f"🆔 ID: <code>{user_tg_id}</code>\n"
        f"🕐 {now}"
    )


def birthday_notification(
    order_id: int,
    user_tg_id: int,
    username: str | None,
    birthday_date: str,
    guests: str,
    contact_name: str,
    phone: str,
    wishes: str,
) -> str:
    user_link = f"<a href='tg://user?id={user_tg_id}'>@{username}</a>" if username else f"ID: {user_tg_id}"
    now = datetime.now().strftime("%d.%m.%Y %H:%M")

    return (
        f"🎂 <b>НОВА ЗАЯВКА НА ДЕНЬ НАРОДЖЕННЯ #{order_id}</b>\n\n"
        f"📆 Дата свята: <b>{birthday_date}</b>\n"
        f"👥 Гостей: <b>{guests}</b>\n"
        f"👤 Іменинник: <b>{contact_name}</b>\n"
        f"📱 Телефон: <b>{phone}</b>\n"
        f"💬 Побажання: <b>{wishes}</b>\n\n"
        f"🔗 Telegram: {user_link}\n"
        f"🆔 ID: <code>{user_tg_id}</code>\n"
        f"🕐 {now}"
    )


def suggestion_notification(
    suggestion_id: int,
    user_tg_id: int,
    username: str | None,
    text: str,
) -> str:
    user_link = f"<a href='tg://user?id={user_tg_id}'>@{username}</a>" if username else f"ID: {user_tg_id}"
    now = datetime.now().strftime("%d.%m.%Y %H:%M")

    return (
        f"💡 <b>НОВА ПРОПОЗИЦІЯ #{suggestion_id}</b>\n\n"
        f"📝 {text}\n\n"
        f"🔗 Від: {user_link}\n"
        f"🕐 {now}"
    )
