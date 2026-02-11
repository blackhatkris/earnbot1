"""
Force-join check callback handler.
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery
from database import Database
from keyboards.user_menu import main_menu_keyboard

router = Router()


@router.callback_query(F.data == "check_joined")
async def check_joined(callback: CallbackQuery, db: Database):
    user_id = callback.from_user.id
    channels = await db.get_active_channels()

    for ch in channels:
        try:
            member = await callback.bot.get_chat_member(int(ch["channel_id"]), user_id)
            if member.status in ("left", "kicked"):
                return await callback.answer("❌ You haven't joined all channels!", show_alert=True)
        except Exception:
            pass

    await db.set_joined_channels(user_id, True)
    await callback.message.edit_text(
        "✅ <b>Verified!</b> You've joined all channels.\n\nWelcome! Use the menu below 👇",
    )
    await callback.message.answer("🎉 Let's go!", reply_markup=main_menu_keyboard())
    await callback.answer()
