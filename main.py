"""
Telegram Earning Bot - Main Entry Point
Optimized for Railway Free Plan (single instance, polling mode)
"""
import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from config import BOT_TOKEN
from database import Database
from middlewares.auth import AuthMiddleware, ForceJoinMiddleware
from handlers import user, referral, daily, withdraw, leaderboard, help as help_handler
from handlers import forcejoin, admin, moderator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

db = Database()


async def on_startup(bot: Bot):
    """Delete webhook to avoid TelegramConflictError, then init DB."""
    await bot.delete_webhook(drop_pending_updates=True)
    await db.connect()
    await db.create_tables()
    await db.seed_settings()
    logger.info("Bot started successfully ✅")


async def on_shutdown(bot: Bot):
    await db.close()
    logger.info("Bot shut down gracefully 🛑")


async def main():
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    try:
        dp = Dispatcher()
        dp["db"] = db

        # Middlewares
        dp.message.middleware(AuthMiddleware(db))
        dp.callback_query.middleware(AuthMiddleware(db))
        dp.message.middleware(ForceJoinMiddleware(db, bot))
        dp.callback_query.middleware(ForceJoinMiddleware(db, bot))

        # Register routers
        dp.include_routers(
            admin.router,
            moderator.router,
            user.router,
            referral.router,
            daily.router,
            withdraw.router,
            leaderboard.router,
            help_handler.router,
            forcejoin.router,
        )

        dp.startup.register(on_startup)
        dp.shutdown.register(on_shutdown)

        logger.info("Starting polling...")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        # Prevent "Unclosed client session" if startup crashes
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
