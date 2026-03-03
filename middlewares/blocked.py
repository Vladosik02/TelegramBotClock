"""
Blocked user middleware.

Intercepts every update from a blocked user and silently drops it,
sending a one-time "you are blocked" alert on messages/callbacks.
Admins are never blocked.
"""
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update

from config import ADMIN_IDS


class BlockedUserMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        if user is None or user.id in ADMIN_IDS:
            return await handler(event, data)

        from database.db import is_user_blocked
        if not await is_user_blocked(user.id):
            return await handler(event, data)

        # User is blocked — respond politely and drop the update
        bot = data.get("bot")
        if bot and isinstance(event, Update):
            try:
                if event.message:
                    from database.db import get_user_lang
                    from locales import t
                    lang = await get_user_lang(user.id)
                    await event.message.answer(
                        t("you_are_blocked", lang), parse_mode="HTML"
                    )
                elif event.callback_query:
                    await event.callback_query.answer(
                        "🚫 Акаунт заблоковано.", show_alert=True
                    )
            except Exception:
                pass
        # Do NOT call handler — drop the update
