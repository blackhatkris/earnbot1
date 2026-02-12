"""
Middlewares:
1. AuthMiddleware — registers user on first interaction, blocks banned users.
2. ForceJoinMiddleware — blocks usage until user has joined all required channels.
"""
import logging
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware, Bot
from aiogram.types import Message, CallbackQuery, Update
from database import Database

logger = logging.getLogger(__name__)


class AuthMiddleware(BaseMiddleware):
    def __init__(self, db: Database):
        self.db = db

    async def __call__(
        self,
        handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any],
    ):
        user = event.from_user
        if not user:
            return

        data["db"] = self.db

        await self.db.ensure_pool()

        db_user = await self.db.get_user(user.id)
        is_start = isinstance(event, Message) and event.text and event.text.startswith("/start")
        if not db_user and not is_start:
            await self.db.add_user(user.id, user.username or "", user.full_name or "")
            db_user = await self.db.get_user(user.id)

        if db_user and db_user["is_banned"]:
            if isinstance(event, Message):
                await event.answer("🚫 You are banned from using this bot.")
            return

        from config import SUPER_ADMINS
        maint = await self.db.get_setting("maintenance_mode")
        if maint == "1" and user.id not in SUPER_ADMINS:
            if isinstance(event, Message):
                await event.answer("🔧 Bot is under maintenance. Please try again later.")
            return

        data["db_user"] = db_user
        return await handler(event, data)


class ForceJoinMiddleware(BaseMiddleware):
    """Block usage until user joins all required channels."""

    EXEMPT_COMMANDS = {"/start", "/help"}

    def __init__(self, db: Database, bot: Bot):
        self.db = db
        self.bot = bot

    async def __call__(
        self,
        handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any],
    ):
        if isinstance(event, Message) and event.text:
            cmd = event.text.split()[0].split("@")[0]
            if cmd in self.EXEMPT_COMMANDS:
                return await handler(event, data)

        if isinstance(event, CallbackQuery) and event.data == "check_joined":
            return await handler(event, data)

        user = event.from_user
        if not user:
            return

        db_user = data.get("db_user")

        channels = await self.db.get_active_channels()

        if not channels:
            return await handler(event, data)

        # If user already verified, skip API calls
        if db_user:
            try:
                if bool(db_user.get("joined_channels")):
                    return await handler(event, data)
            except Exception:
                pass

        not_joined = []
        for ch in channels:
            try:
                member = await self.bot.get_chat_member(int(ch["channel_id"]), user.id)
                logger.info(
                    "Force-join check: user=%s channel=%s status=%s",
                    user.id, ch["channel_id"], member.status,
                )
                if member.status in ("left", "kicked"):
                    not_joined.append(ch)
            except Exception as e:
                logger.error(
                    "Force-join API error: user=%s channel=%s error=%r",
                    user.id, ch["channel_id"], e,
                )
                not_joined.append(ch)

        if not_joined:
            await self.db.set_joined_channels(user.id, False)
            from keyboards.user_menu import force_join_keyboard
            kb = await force_join_keyboard(self.db)
            if isinstance(event, Message):
                await event.answer(
                    "⚠️ <b>You must join all our channels to use this bot!</b>\n\n"
                    "Join below and tap <b>✅ I Have Joined</b>.",
                    reply_markup=kb,
                )
            elif isinstance(event, CallbackQuery):
                await event.answer("Join all channels first!", show_alert=True)
            return

        await self.db.set_joined_channels(user.id, True)
        return await handler(event, data)
