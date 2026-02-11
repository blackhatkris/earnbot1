"""
User-facing keyboards.
"""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from database import Database


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🚀 Start Earning"), KeyboardButton(text="👤 My Account")],
            [KeyboardButton(text="📅 Daily Reward"), KeyboardButton(text="🏆 Leaderboard")],
            [KeyboardButton(text="💸 Withdraw"), KeyboardButton(text="📋 Withdraw History")],
            [KeyboardButton(text="📖 How To Earn"), KeyboardButton(text="❓ Help")],
        ],
        resize_keyboard=True,
    )


async def force_join_keyboard(db: Database) -> InlineKeyboardMarkup:
    channels = await db.get_active_channels()
    buttons = []
    for ch in channels:
        buttons.append([
            InlineKeyboardButton(
                text=f"📢 Join {ch['channel_name']}",
                url=ch["invite_link"],
            )
        ])
    buttons.append([
        InlineKeyboardButton(text="✅ I Have Joined", callback_data="check_joined")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
