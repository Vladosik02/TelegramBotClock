"""Shared helpers used across multiple handlers."""
from aiogram.types import Message, CallbackQuery

from database.db import get_user_lang
from keyboards.kb import main_menu_keyboard
from locales import t


async def send_main_menu(target: Message | CallbackQuery, lang: str | None = None) -> None:
    """Send / edit message to show the main menu."""
    if lang is None:
        tg_id = target.from_user.id
        lang = await get_user_lang(tg_id)

    text = t("main_menu_text", lang)
    kb   = main_menu_keyboard(lang)

    if isinstance(target, CallbackQuery):
        try:
            await target.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
        except Exception:
            await target.message.answer(text, reply_markup=kb, parse_mode="HTML")
        await target.answer()
    else:
        await target.answer(text, reply_markup=kb, parse_mode="HTML")
