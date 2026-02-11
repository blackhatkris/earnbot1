"""
Daily check-in / login reward handler.
"""
from datetime import datetime, timezone, timedelta
from aiogram import Router, F
from aiogram.types import Message
from database import Database

router = Router()


@router.message(F.text == "📅 Daily Reward")
async def daily_reward(message: Message, db: Database):
    uid = message.from_user.id
    user = await db.get_user(uid)
    if not user:
        return await message.answer("Please /start first.")

    now = datetime.now(timezone.utc)
    last = user["last_checkin"]
    streak = user["streak"]

    daily_amount = float(await db.get_setting("daily_reward") or 10)
    streak_bonus_amount = float(await db.get_setting("streak_bonus") or 50)
    streak_days = int(await db.get_setting("streak_days") or 7)

    if last:
        diff = now - last
        if diff < timedelta(hours=24):
            remaining = timedelta(hours=24) - diff
            h, m = divmod(int(remaining.total_seconds()) // 60, 60)
            return await message.answer(
                f"⏳ <b>Already claimed today!</b>\n\n"
                f"Come back in <b>{h}h {m}m</b> ⏰"
            )
        elif diff > timedelta(hours=48):
            streak = 0  # Missed — reset streak

    streak += 1
    total_reward = daily_amount
    streak_msg = ""

    if streak >= streak_days:
        total_reward += streak_bonus_amount
        streak_msg = f"\n🎉 <b>STREAK BONUS: ₹{streak_bonus_amount}!</b> ({streak_days}-day streak!)"
        streak = 0  # Reset after bonus

    await db.update_balance(uid, total_reward)
    await db.checkin(uid, streak)
    await db.add_log(uid, "daily_checkin", f"₹{total_reward}, streak={streak}")

    text = (
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "📅 <b>DAILY REWARD CLAIMED!</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"✅ <b>₹{daily_amount}</b> added to your balance!\n"
        f"🔥 Current Streak: <b>{streak} days</b>"
        f"{streak_msg}\n\n"
        "Come back tomorrow to keep your streak! 💪"
    )
    await message.answer(text)
