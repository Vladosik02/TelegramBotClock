import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ErrorEvent, BotCommand, BotCommandScopeDefault
from aiogram.exceptions import TelegramBadRequest

from config import BOT_TOKEN
from database.db import init_db, close_db
from handlers import start, booking, birthday, suggestions, gallery, games, instructions, profile, admin, bunker
from middlewares.fsm_guard import NonTextGuardMiddleware
from middlewares.blocked import BlockedUserMiddleware


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


async def main() -> None:
    bot = Bot(token=BOT_TOKEN)
    dp  = Dispatcher(storage=MemoryStorage())

    @dp.errors()
    async def error_handler(event: ErrorEvent) -> bool:
        exc = event.exception
        # Ignore expired/invalid callback query answers — happens after bot restart
        if isinstance(exc, TelegramBadRequest) and "query is too old" in str(exc):
            return True
        logging.exception("Unhandled error: %s", exc)
        return True

    # Middlewares
    dp.update.outer_middleware(BlockedUserMiddleware())
    dp.message.middleware(NonTextGuardMiddleware())

    # Register routers (order matters — more specific first)
    dp.include_router(admin.router)
    dp.include_router(bunker.router)
    dp.include_router(start.router)
    dp.include_router(booking.router)
    dp.include_router(birthday.router)
    dp.include_router(suggestions.router)
    dp.include_router(gallery.router)
    dp.include_router(games.router)
    dp.include_router(instructions.router)
    dp.include_router(profile.router)

    await init_db()

    # Set bot command menu (shown in Telegram "/" menu)
    await bot.set_my_commands([
        BotCommand(command="start",  description="Головне меню / Главное меню"),
        BotCommand(command="help",   description="Довідка / Справка"),
        BotCommand(command="myid",   description="Мій Telegram ID"),
    ], scope=BotCommandScopeDefault())

    logging.info("Bot started. Game Space Clock is online!")

    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await close_db()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
