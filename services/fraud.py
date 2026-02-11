"""
Anti-fraud service — channel leave detection, referral invalidation.
Call check_channel_membership periodically or on certain triggers.
"""
import logging
from aiogram import Bot
from database import Database

logger = logging.getLogger(__name__)


async def check_and_revoke_if_left(db: Database, bot: Bot, user_id: int):
    """
    Check if a referred user has left any required channel.
    If so, invalidate their referral and deduct the reward from the referrer.
    """
    channels = await db.get_active_channels()
    if not channels:
        return

    for ch in channels:
        try:
            member = await bot.get_chat_member(int(ch["channel_id"]), user_id)
            if member.status in ("left", "kicked"):
                # User left — find referrer and deduct
                referrer_id = await db.get_referrer(user_id)
                if referrer_id:
                    ref = await db.get_referral(referrer_id, user_id)
                    if ref and ref["is_valid"]:
                        reward = float(ref["reward"])
                        await db.invalidate_referral(referrer_id, user_id)
                        await db.deduct_balance(referrer_id, reward)
                        await db.add_log(referrer_id, "referral_revoked",
                                         f"user {user_id} left channel {ch['channel_id']}, -₹{reward}")
                        try:
                            await bot.send_message(
                                referrer_id,
                                f"⚠️ <b>Credit Deducted!</b>\n\n"
                                f"Your referral (ID: {user_id}) left a required channel.\n"
                                f"💸 <b>₹{reward:.0f}</b> has been deducted from your balance.\n\n"
                                f"Referred users must stay in all channels!"
                            )
                        except Exception:
                            pass

                        # Also notify the user who left
                        try:
                            await bot.send_message(
                                user_id,
                                f"⚠️ <b>Warning!</b>\n\n"
                                f"You left a required channel.\n"
                                f"Your referrer's credit of ₹{reward:.0f} was deducted.\n"
                                f"Please rejoin to continue using the bot!"
                            )
                        except Exception:
                            pass
                return  # One violation is enough
        except Exception:
            pass


async def is_rapid_referral(db: Database, referrer_id: int, window_seconds: int = 60, max_refs: int = 5) -> bool:
    """Check if referrer has too many referrals in a short window (farming detection)."""
    count = await db.pool.fetchval(
        "SELECT COUNT(*) FROM referrals WHERE referrer_id=$1 AND created_at > NOW() - INTERVAL '1 second' * $2",
        referrer_id, window_seconds,
    )
    return (count or 0) >= max_refs
