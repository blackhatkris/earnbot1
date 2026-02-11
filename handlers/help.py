"""
Help and How To Earn handler.
"""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

router = Router()


@router.message(Command("help"))
@router.message(F.text == "❓ Help")
async def help_cmd(message: Message):
    text = (
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "❓ <b>HELP & COMMANDS</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "/start — Start the bot\n"
        "/help — Show this help\n"
        "/black — Admin panel\n\n"
        "<b>Menu Options:</b>\n"
        "🚀 Start Earning — Get your referral link\n"
        "👤 My Account — View balance & stats\n"
        "📅 Daily Reward — Claim daily ₹10\n"
        "🏆 Leaderboard — Top earners\n"
        "💸 Withdraw — Cash out your earnings\n"
        "📋 Withdraw History — Past withdrawals\n"
        "📖 How To Earn — Earning guide\n"
        "❓ Help — This message\n"
    )
    await message.answer(text)


@router.message(F.text == "📖 How To Earn")
async def how_to_earn(message: Message):
    text = (
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "📖 <b>HOW TO EARN</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "💰 <b>1. Refer Friends — ₹15 each</b>\n"
        "Share your link. When a friend joins\n"
        "the bot AND our channels, you earn ₹15!\n\n"
        "👥 <b>2. Level 2 Referrals — ₹1 each</b>\n"
        "When your friend refers someone,\n"
        "you earn ₹1 automatically!\n\n"
        "📅 <b>3. Daily Login — ₹10/day</b>\n"
        "Claim daily reward every 24 hours.\n"
        "7-day streak = ₹50 bonus!\n\n"
        "🎯 <b>4. Milestone Bonus — ₹50</b>\n"
        "Get ₹50 bonus every 10 referrals!\n\n"
        "💸 <b>5. Withdraw</b>\n"
        "Minimum ₹500, paid via UPI.\n\n"
        "🚀 <b>Earning Potential:</b>\n"
        "₹15,000–₹20,000 per month!\n"
    )
    await message.answer(text)
