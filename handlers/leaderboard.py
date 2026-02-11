"""
Leaderboard handler.
"""
from aiogram import Router, F
from aiogram.types import Message
from database import Database

router = Router()


@router.message(F.text == "🏆 Leaderboard")
async def leaderboard(message: Message, db: Database):
    rows = await db.get_leaderboard(10)
    if not rows:
        return await message.answer("🏆 No data yet. Be the first earner!")

    medals = ["🥇", "🥈", "🥉"] + ["🏅"] * 7
    lines = ["━━━━━━━━━━━━━━━━━━━━━━\n🏆 <b>TOP EARNERS</b>\n━━━━━━━━━━━━━━━━━━━━━━\n"]
    for i, r in enumerate(rows):
        lines.append(
            f"{medals[i]} <b>{r['full_name'] or 'User'}</b>\n"
            f"   💰 ₹{float(r['total_earned']):,.2f} | 👥 {r['referral_count']} refs"
        )
    lines.append("\n🚀 Keep earning to reach the top!")
    await message.answer("\n".join(lines))
