"""
Referral reward processing — handles Level 1 + Level 2 + milestone bonuses.
"""
import logging
from aiogram import Bot
from database import Database

logger = logging.getLogger(__name__)


async def process_referral(db: Database, referrer_id: int, referred_id: int, referred_name: str, bot: Bot):
    """Called when a new user starts the bot with a referral link."""

    # Prevent self-referral
    if referrer_id == referred_id:
        return

    # Check if referrer exists
    referrer = await db.get_user(referrer_id)
    if not referrer:
        return

    # Prevent duplicate
    existing = await db.get_referral(referrer_id, referred_id)
    if existing:
        return

    # ─── LEVEL 1 REWARD ───────────────────────────────────────────
    reward = float(await db.get_setting("referral_reward") or 15)
    boost = await db.get_setting("boost_mode")
    if boost == "1":
        reward *= 2  # Double during boost

    await db.add_referral(referrer_id, referred_id, level=1, reward=reward)
    await db.update_balance(referrer_id, reward)
    await db.increment_referral_count(referrer_id)
    await db.add_log(referrer_id, "referral_l1", f"referred={referred_id}, reward=₹{reward}")

    # Notify referrer
    try:
        await bot.send_message(
            referrer_id,
            f"🎉 <b>Referral Successful!</b>\n\n"
            f"You just referred <b>{referred_name}</b>.\n"
            f"💰 <b>₹{reward:.0f}</b> added to your balance!\n\n"
            f"Keep inviting and earn <b>₹15,000–₹20,000</b> per month! 🚀"
        )
    except Exception:
        pass

    # ─── MILESTONE BONUS ──────────────────────────────────────────
    ref_count = await db.get_referral_count(referrer_id)
    if ref_count > 0 and ref_count % 10 == 0:
        milestone_bonus = float(await db.get_setting("milestone_bonus") or 50)
        await db.update_balance(referrer_id, milestone_bonus)
        await db.add_log(referrer_id, "milestone_bonus", f"₹{milestone_bonus} at {ref_count} refs")
        try:
            await bot.send_message(
                referrer_id,
                f"🎯 <b>MILESTONE BONUS!</b>\n\n"
                f"You reached <b>{ref_count} referrals</b>!\n"
                f"💰 <b>₹{milestone_bonus:.0f}</b> bonus added! 🎉"
            )
        except Exception:
            pass

    # ─── LEVEL 2 REWARD ───────────────────────────────────────────
    l2_referrer_id = await db.get_referrer(referrer_id)
    if l2_referrer_id and l2_referrer_id != referred_id:
        l2_reward = float(await db.get_setting("l2_referral_reward") or 1)
        existing_l2 = await db.get_referral(l2_referrer_id, referred_id)
        if not existing_l2:
            await db.add_referral(l2_referrer_id, referred_id, level=2, reward=l2_reward)
            await db.update_balance(l2_referrer_id, l2_reward)
            await db.add_log(l2_referrer_id, "referral_l2", f"referred={referred_id}, reward=₹{l2_reward}")
            try:
                await bot.send_message(
                    l2_referrer_id,
                    f"👥 <b>Level 2 Earning!</b>\n\n"
                    f"Your referral's friend joined!\n"
                    f"💰 <b>₹{l2_reward:.0f}</b> added to your balance! 🎉"
                )
            except Exception:
                pass
