"""
Notification helper — sends messages to users with error handling.
"""
import logging
from aiogram import Bot

logger = logging.getLogger(__name__)


async def notify_user(bot: Bot, user_id: int, text: str):
    try:
        await bot.send_message(user_id, text)
    except Exception as e:
        logger.warning(f"Failed to notify {user_id}: {e}")
