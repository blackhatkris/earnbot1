"""
Boost mode service — doubles referral rewards when enabled.
Boost status is stored in settings table (boost_mode = "1" or "0").
Reward multiplication is handled in services/rewards.py.
"""
from database import Database


async def is_boost_active(db: Database) -> bool:
    val = await db.get_setting("boost_mode")
    return val == "1"
