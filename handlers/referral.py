"""
Referral info handler.
Actual referral processing is in services/rewards.py and triggered from /start.
"""
from aiogram import Router, F
from aiogram.types import Message
from database import Database

router = Router()


@router.message(F.text == "👥 My Referrals")
async def my_referrals(message: Message, db: Database):
    uid = message.from_user.id
    user = await db.get_user(uid)
    if not user:
        return await message.answer("Please /start first.")

    bot_info = await message.bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={uid}"
    count = user["referral_count"]
    next_milestone = ((count // 10) + 1) * 10
    remaining = next_milestone - count

    text = (
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "👥 <b>MY REFERRALS</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"✅ Total Referrals: <b>{count}</b>\n"
        f"🎯 Next Bonus at: <b>{next_milestone} referrals</b>\n"
        f"📍 Remaining: <b>{remaining}</b>\n\n"
        f"🔗 <code>{ref_link}</code>\n\n"
        "Share and earn <b>₹15</b> per friend!\n"
        "Every 10 referrals = <b>₹50 bonus!</b> 🎉"
    )
    await message.answer(text)
