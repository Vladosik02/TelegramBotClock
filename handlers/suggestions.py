from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from database.db import get_user_lang, create_suggestion, get_or_create_user
from keyboards.kb import back_to_menu_keyboard, cancel_keyboard
from locales import t
from states.forms import SuggestionForm
from utils.notify import notify_admins, suggestion_notification

router = Router()


# ─────────────────────────── Entry ───────────────────────────

@router.callback_query(F.data == "menu:suggestions")
async def cb_suggestions_start(callback: CallbackQuery, state: FSMContext) -> None:
    lang = await get_user_lang(callback.from_user.id)
    await state.set_state(SuggestionForm.text)
    await state.update_data(lang=lang)
    await callback.message.edit_text(
        t("suggestions_title", lang),
        reply_markup=cancel_keyboard(lang),
        parse_mode="HTML",
    )
    await callback.answer()


# ─────────────────────────── Text ───────────────────────────

@router.message(SuggestionForm.text)
async def msg_suggestion_text(message: Message, state: FSMContext, bot: Bot) -> None:
    data = await state.get_data()
    lang = data.get("lang", "uk")

    await get_or_create_user(
        message.from_user.id,
        message.from_user.username,
        message.from_user.full_name,
    )

    suggestion_id = await create_suggestion(message.from_user.id, message.text.strip())

    msg = suggestion_notification(
        suggestion_id=suggestion_id,
        user_tg_id=message.from_user.id,
        username=message.from_user.username,
        text=message.text.strip(),
    )
    await notify_admins(bot, msg)
    await state.clear()

    await message.answer(
        t("suggestions_success", lang),
        reply_markup=back_to_menu_keyboard(lang),
        parse_mode="HTML",
    )
