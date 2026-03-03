from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from database.db import get_or_create_user, set_user_lang, get_user_lang
from keyboards.kb import language_keyboard, persistent_menu_keyboard
from locales import t
from handlers.common import send_main_menu

router = Router()

HELP_TEXT_UK = (
    "<b>Game Space \"Clock\" — команди бота</b>\n\n"
    "/start — головне меню\n"
    "/myid — дізнатися свій Telegram ID\n"
    "/help — ця довідка\n\n"
    "<b>Розділи меню:</b>\n"
    "📅 Забронювати столик\n"
    "🎂 День народження\n"
    "📸 Фото закладу\n"
    "🎮 Ігри (PS5 / PS4)\n"
    "📖 Інструкції до настолок\n"
    "💡 Пропозиції\n"
    "👤 Мій профіль\n\n"
    "Питання? Пишіть у @Clock_Anticafe"
)

HELP_TEXT_RU = (
    "<b>Game Space \"Clock\" — команды бота</b>\n\n"
    "/start — главное меню\n"
    "/myid — узнать свой Telegram ID\n"
    "/help — эта справка\n\n"
    "<b>Разделы меню:</b>\n"
    "📅 Забронировать столик\n"
    "🎂 День рождения\n"
    "📸 Фото заведения\n"
    "🎮 Игры (PS5 / PS4)\n"
    "📖 Инструкции к настолкам\n"
    "💡 Предложения\n"
    "👤 Мой профиль\n\n"
    "Вопросы? Пишите в @Clock_Anticafe"
)


# ─────────────────────────── /start ───────────────────────────

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    # Clear any active FSM state on /start
    await state.clear()

    user = await get_or_create_user(
        tg_id=message.from_user.id,
        username=message.from_user.username,
        full_name=message.from_user.full_name,
    )
    lang = user.get("lang", "uk")

    # Show persistent bottom keyboard with atmospheric greeting
    greeting = "🌌 <b>Game Space Clock</b> ✨" if lang == "uk" else "🌌 <b>Game Space Clock</b> ✨"
    await message.answer(greeting, reply_markup=persistent_menu_keyboard(lang), parse_mode="HTML")

    # New user — choose language first
    if user.get("lang") == "uk" and not message.from_user.language_code:
        await message.answer(
            t("choose_language", lang),
            reply_markup=language_keyboard(),
            parse_mode="HTML",
        )
    else:
        await send_main_menu(message, lang)


# ─────────────────────────── Language selection ───────────────────────────

@router.callback_query(F.data.startswith("lang:"))
async def cb_set_language(callback: CallbackQuery) -> None:
    lang = callback.data.split(":")[1]
    await set_user_lang(callback.from_user.id, lang)
    await callback.answer(t("lang_set", lang))
    await send_main_menu(callback, lang)


# ─────────────────────────── Language change from profile ───────────────────────────

@router.callback_query(F.data == "menu:lang_change")
async def cb_lang_change(callback: CallbackQuery) -> None:
    lang = await get_user_lang(callback.from_user.id)
    await callback.message.edit_text(
        t("choose_language", lang),
        reply_markup=language_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


# ─────────────────────────── Persistent "🏠 Меню" reply button ───────────────────────────

@router.message(F.text == "🏠 Меню")
async def msg_persistent_menu(message: Message, state: FSMContext) -> None:
    await state.clear()
    await send_main_menu(message)


# ─────────────────────────── Back to main menu ───────────────────────────

@router.callback_query(F.data == "menu:main")
async def cb_main_menu(callback: CallbackQuery) -> None:
    await send_main_menu(callback)


# ─────────────────────────── No-op (non-clickable UI cells) ───────────────────────────

@router.callback_query(F.data == "noop")
async def cb_noop(callback: CallbackQuery) -> None:
    """Silently acknowledge non-clickable calendar cells, page indicators, etc."""
    await callback.answer()


# ─────────────────────────── /myid ───────────────────────────

@router.message(Command("myid"))
async def cmd_myid(message: Message) -> None:
    await message.answer(
        f"🆔 Ваш Telegram ID: <code>{message.from_user.id}</code>\n"
        f"👤 Username: @{message.from_user.username or '—'}",
        parse_mode="HTML",
    )


# ─────────────────────────── /help ───────────────────────────

@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    lang = await get_user_lang(message.from_user.id)
    text = HELP_TEXT_UK if lang == "uk" else HELP_TEXT_RU
    from keyboards.kb import back_to_menu_keyboard
    await message.answer(text, reply_markup=back_to_menu_keyboard(lang), parse_mode="HTML")
