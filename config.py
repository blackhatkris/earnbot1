"""
Configuration — all env vars loaded here.
"""
import os

BOT_TOKEN: str = os.environ["BOT_TOKEN"]
DATABASE_URL: str = os.environ["DATABASE_URL"]

# Super admin Telegram user IDs (comma-separated)
SUPER_ADMINS: list[int] = [
    int(x.strip()) for x in os.getenv("SUPER_ADMINS", "").split(",") if x.strip()
]

# Defaults (overridable via DB settings table)
DEFAULT_REFERRAL_REWARD = 15      # ₹15 per referral
DEFAULT_L2_REFERRAL_REWARD = 1    # ₹1 level-2
DEFAULT_DAILY_REWARD = 10         # ₹10 per day
DEFAULT_STREAK_BONUS = 50         # ₹50 for 7-day streak
DEFAULT_MILESTONE_BONUS = 50      # ₹50 every 10 referrals
DEFAULT_MIN_WITHDRAW = 500        # ₹500
WITHDRAW_COOLDOWN_DAYS = 3
STREAK_DAYS = 7
