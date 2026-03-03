"""
FSM Guard Middleware.

1. If user sends a non-text message while a form is in progress → politely ask for text.
2. If user presses a main menu callback while a form is in progress → clear FSM, proceed normally.
"""
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, TelegramObject

# FSM states that expect plain text input (not buttons)
_TEXT_STATES = {
    "BookingForm:date", "BookingForm:time", "BookingForm:people",
    "BookingForm:name", "BookingForm:phone",
    "BirthdayForm:filling_form",  # calendar is callback-based, only form text needs guard
    "SuggestionForm:text",
    "AdminAddGame:title",
    "AdminAddInstruction:game_name",
    # Admin manual booking
    "AdminAddBooking:date", "AdminAddBooking:time",
    "AdminAddBooking:name", "AdminAddBooking:phone",
    "AdminAddBooking:people", "AdminAddBooking:notes",
    # Broadcast
    "AdminBroadcast:typing",
}

_HINT_UK = "✏️ Будь ласка, введіть відповідь текстом."
_HINT_RU = "✏️ Пожалуйста, введите ответ текстом."


class NonTextGuardMiddleware(BaseMiddleware):
    """Block non-text messages when the FSM expects text, with a friendly hint."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if not isinstance(event, Message):
            return await handler(event, data)

        # Only intercept when there's an active FSM state expecting text
        state: FSMContext = data.get("state")
        if state is None:
            return await handler(event, data)

        current = await state.get_state()
        if current not in _TEXT_STATES:
            return await handler(event, data)

        # If the message has no text (photo, sticker, voice, etc.) — hint the user
        if not event.text:
            fsm_data = await state.get_data()
            lang = fsm_data.get("lang", "uk")
            await event.answer(_HINT_UK if lang == "uk" else _HINT_RU)
            return  # Don't pass to handler

        return await handler(event, data)
