"""
Admin panel keyboards.
"""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def admin_menu_keyboard(is_super: bool = False) -> ReplyKeyboardMarkup:
    """Moderators get fewer options."""
    rows = [
        [KeyboardButton(text="📊 Full Stats"), KeyboardButton(text="💳 Pending Withdrawals")],
        [KeyboardButton(text="📣 Broadcast"), KeyboardButton(text="🔨 Ban User")],
    ]
    if is_super:
        rows.extend([
            [KeyboardButton(text="➕ Add Moderator"), KeyboardButton(text="➖ Remove Moderator")],
            [KeyboardButton(text="📢 Add Channel"), KeyboardButton(text="🗑 Remove Channel")],
            [KeyboardButton(text="⚙️ Change Rewards"), KeyboardButton(text="📤 Export Users")],
            [KeyboardButton(text="🚀 Boost Mode"), KeyboardButton(text="🔧 Maintenance")],
            [KeyboardButton(text="🔓 Unban User")],
        ])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)
