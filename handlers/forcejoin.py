"""
Force-join check callback handler.
"""
import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery
from database import Database
from keyboards.user_menu import main_menu_keyboard, force_join_keyboard

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(F.data == "check_joined")
async def check_joined(callback: CallbackQuery, db: Database):
    user_id = callback.from_user.id
    channels = await db.get_active_channels()

    if not channels:
        await db.set_joined_channels(user_id, True)
        await callback.message.edit_text(
            "✅ <b>Verified!</b> No channels required.\n\nWelcome! Use the menu below 👇",
        )
        await callback.message.answer("🎉 Let's go!", reply_markup=main_menu_keyboard())
        await callback.answer()
        return

    not_joined = []
    for ch in channels:
        try:
            member = await callback.bot.get_chat_member(int(ch["channel_id"]), user_id)
            logger.info(
                "check_joined: user=%s channel=%s status=%s",
                user_id, ch["channel_id"], member.status,
            )
            if member.status in ("left", "kicked"):
                not_joined.append(ch)
        except Exception as e:
            logger.error(
                "check_joined API error: user=%s channel=%s error=%r",
                user_id, ch["channel_id"], e,
            )
            not_joined.append(ch)

    if not_joined:
        names = ", ".join(ch["channel_name"] for ch in not_joined)
        await callback.answer(
            f"❌ You haven't joined: {names}",
            show_alert=True,
        )
        return

    await db.set_joined_channels(user_id, True)
    await callback.message.edit_text(
        "✅ <b>Verified!</b> You've joined all channels.\n\nWelcome! Use the menu below 👇",
    )
    await callback.message.answer("🎉 Let's go!", reply_markup=main_menu_keyboard())
    await callback.answer()
