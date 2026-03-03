from aiogram import Router, F
from aiogram.types import CallbackQuery

from database.db import get_user_lang, get_games
from keyboards.kb import games_menu_keyboard, games_list_keyboard, back_to_menu_keyboard
from locales import t

router = Router()


@router.callback_query(F.data == "menu:games")
async def cb_games_menu(callback: CallbackQuery) -> None:
    lang = await get_user_lang(callback.from_user.id)
    await callback.message.edit_text(
        t("games_menu", lang),
        reply_markup=games_menu_keyboard(lang),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("games:"))
async def cb_games_list(callback: CallbackQuery) -> None:
    lang     = await get_user_lang(callback.from_user.id)
    platform = callback.data.split(":")[1]
    games    = await get_games(platform)

    title_key = "ps5_games_title" if platform == "PS5" else "ps4_games_title"
    icon      = "🎮" if platform == "PS5" else "🕹"

    if not games:
        await callback.message.edit_text(
            f"{t(title_key, lang)}\n\n{t('games_empty', lang)}",
            reply_markup=games_list_keyboard(lang),
            parse_mode="HTML",
        )
        await callback.answer()
        return

    lines = "\n".join(f"{icon} {g['title']}" for g in games)
    await callback.message.edit_text(
        f"{t(title_key, lang)}\n\n{lines}",
        reply_markup=games_list_keyboard(lang),
        parse_mode="HTML",
    )
    await callback.answer()
