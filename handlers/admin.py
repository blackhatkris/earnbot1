"""
Admin panel — Super Admin only (/black command).
Moderators get limited access via moderator.py.
"""
import io
import csv
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, BufferedInputFile
from config import SUPER_ADMINS
from database import Database
from keyboards.admin_menu import admin_menu_keyboard

router = Router()


def is_super_admin(user_id: int) -> bool:
    return user_id in SUPER_ADMINS


@router.message(Command("black"))
async def admin_panel(message: Message, db: Database):
    uid = message.from_user.id
    is_mod = await db.is_moderator(uid)

    if not is_super_admin(uid) and not is_mod:
        return  # Silent ignore

    await message.answer(
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔐 <b>ADMIN PANEL</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Select an option below:",
        reply_markup=admin_menu_keyboard(is_super_admin(uid)),
    )


# ─── SUPER ADMIN COMMANDS ────────────────────────────────────────

@router.message(F.text == "➕ Add Moderator")
async def add_mod_prompt(message: Message, db: Database):
    if not is_super_admin(message.from_user.id):
        return
    await message.answer(
        "Send in this format:\n<code>addmod USER_ID</code>\n\n"
        "Example: <code>addmod 123456789</code>"
    )


@router.message(F.text == "➖ Remove Moderator")
async def remove_mod_prompt(message: Message, db: Database):
    if not is_super_admin(message.from_user.id):
        return
    await message.answer(
        "Send in this format:\n<code>removemod USER_ID</code>\n\n"
        "Example: <code>removemod 123456789</code>"
    )


@router.message(F.text == "📢 Add Channel")
async def add_channel_prompt(message: Message):
    if not is_super_admin(message.from_user.id):
        return
    await message.answer(
        "Send channel info in this format:\n"
        "<code>CHANNEL_ID|Channel Name|https://t.me/invite_link</code>"
    )


@router.message(F.text == "🗑 Remove Channel")
async def remove_channel_prompt(message: Message):
    if not is_super_admin(message.from_user.id):
        return
    await message.answer(
        "Send in this format:\n<code>rmchannel CHANNEL_ID</code>\n\n"
        "Example: <code>rmchannel -1001234567890</code>"
    )


@router.message(F.text == "⚙️ Change Rewards")
async def change_rewards(message: Message, db: Database):
    if not is_super_admin(message.from_user.id):
        return
    ref = await db.get_setting("referral_reward")
    daily = await db.get_setting("daily_reward")
    bonus = await db.get_setting("milestone_bonus")
    min_wd = await db.get_setting("min_withdraw")
    text = (
        "Current settings:\n"
        f"• Referral: ₹{ref}\n"
        f"• Daily: ₹{daily}\n"
        f"• Milestone Bonus: ₹{bonus}\n"
        f"• Min Withdraw: ₹{min_wd}\n\n"
        "To change, send:\n"
        "<code>set referral_reward 20</code>\n"
        "<code>set daily_reward 15</code>\n"
        "<code>set milestone_bonus 100</code>\n"
        "<code>set min_withdraw 300</code>"
    )
    await message.answer(text)


@router.message(F.text.startswith("set "))
async def set_setting(message: Message, db: Database):
    if not is_super_admin(message.from_user.id):
        return
    parts = message.text.split(maxsplit=2)
    if len(parts) != 3:
        return await message.answer("Format: <code>set key value</code>")
    key, value = parts[1], parts[2]
    allowed = {"referral_reward", "l2_referral_reward", "daily_reward", "streak_bonus",
               "milestone_bonus", "min_withdraw", "withdraw_cooldown_days", "streak_days"}
    if key not in allowed:
        return await message.answer(f"❌ Unknown setting. Allowed: {', '.join(allowed)}")
    await db.set_setting(key, value)
    await message.answer(f"✅ <b>{key}</b> set to <b>{value}</b>")


@router.message(F.text == "🔨 Ban User")
async def ban_prompt(message: Message, db: Database):
    uid = message.from_user.id
    if not is_super_admin(uid) and not await db.is_moderator(uid):
        return
    await message.answer(
        "Send in this format:\n<code>ban USER_ID</code>\n\n"
        "Example: <code>ban 123456789</code>"
    )


@router.message(F.text == "🔓 Unban User")
async def unban_prompt(message: Message):
    if not is_super_admin(message.from_user.id):
        return
    await message.answer(
        "Send in this format:\n<code>unban USER_ID</code>\n\n"
        "Example: <code>unban 123456789</code>"
    )


@router.message(F.text == "📊 Full Stats")
async def full_stats(message: Message, db: Database):
    uid = message.from_user.id
    if not is_super_admin(uid) and not await db.is_moderator(uid):
        return
    from services.stats import get_full_stats
    text = await get_full_stats(db)
    await message.answer(text)


@router.message(F.text == "📤 Export Users")
async def export_users(message: Message, db: Database):
    if not is_super_admin(message.from_user.id):
        return
    rows = await db.export_users()
    if not rows:
        return await message.answer("No users to export.")

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["user_id", "username", "full_name", "balance", "total_earned", "referral_count", "created_at"])
    for r in rows:
        writer.writerow([r["user_id"], r["username"], r["full_name"],
                         float(r["balance"]), float(r["total_earned"]), r["referral_count"],
                         r["created_at"].isoformat()])
    buf = output.getvalue().encode()
    doc = BufferedInputFile(buf, filename="users_export.csv")
    await message.answer_document(doc, caption="📤 Users export")


@router.message(F.text == "🚀 Boost Mode")
async def toggle_boost(message: Message, db: Database):
    if not is_super_admin(message.from_user.id):
        return
    current = await db.get_setting("boost_mode")
    new_val = "0" if current == "1" else "1"
    await db.set_setting("boost_mode", new_val)
    status = "ON 🚀" if new_val == "1" else "OFF"
    await message.answer(f"Boost mode: <b>{status}</b>")


@router.message(F.text == "🔧 Maintenance")
async def toggle_maintenance(message: Message, db: Database):
    if not is_super_admin(message.from_user.id):
        return
    current = await db.get_setting("maintenance_mode")
    new_val = "0" if current == "1" else "1"
    await db.set_setting("maintenance_mode", new_val)
    status = "ON 🔧" if new_val == "1" else "OFF"
    await message.answer(f"Maintenance mode: <b>{status}</b>")


@router.message(F.text == "💳 Pending Withdrawals")
async def pending_withdrawals(message: Message, db: Database):
    uid = message.from_user.id
    if not is_super_admin(uid) and not await db.is_moderator(uid):
        return
    rows = await db.get_pending_withdrawals()
    if not rows:
        return await message.answer("✅ No pending withdrawals.")

    for r in rows:
        text = (
            f"📋 <b>Withdrawal #{r['id']}</b>\n"
            f"👤 User: {r['user_id']}\n"
            f"💰 ₹{float(r['amount']):,.2f}\n"
            f"📲 UPI: {r['upi']}\n"
            f"👤 Name: {r['name']}\n"
            f"📱 Phone: {r['phone']}\n"
            f"📧 Email: {r['email']}\n\n"
            f"Reply: <code>approve {r['id']}</code> or <code>reject {r['id']}</code>"
        )
        await message.answer(text)


@router.message(F.text.startswith("approve "))
async def approve_wd(message: Message, db: Database):
    uid = message.from_user.id
    if not is_super_admin(uid) and not await db.is_moderator(uid):
        return
    try:
        wid = int(message.text.split()[1])
    except (IndexError, ValueError):
        return await message.answer("Format: <code>approve ID</code>")
    await db.update_withdrawal_status(wid, "approved")
    await db.add_log(uid, "approve_withdraw", f"WID={wid}")
    await message.answer(f"✅ Withdrawal #{wid} approved!")


@router.message(F.text.startswith("reject "))
async def reject_wd(message: Message, db: Database):
    uid = message.from_user.id
    if not is_super_admin(uid) and not await db.is_moderator(uid):
        return
    try:
        wid = int(message.text.split()[1])
    except (IndexError, ValueError):
        return await message.answer("Format: <code>reject ID</code>")
    await db.update_withdrawal_status(wid, "rejected")
    await db.add_log(uid, "reject_withdraw", f"WID={wid}")
    await message.answer(f"❌ Withdrawal #{wid} rejected.")


@router.message(F.text.startswith("ban "))
async def ban_user(message: Message, db: Database):
    uid = message.from_user.id
    if not is_super_admin(uid) and not await db.is_moderator(uid):
        return
    try:
        target = int(message.text.split()[1])
    except (IndexError, ValueError):
        return await message.answer("Format: <code>ban USER_ID</code>")
    await db.set_banned(target, True)
    await db.add_log(uid, "ban_user", str(target))
    await message.answer(f"🔨 User {target} banned.")


@router.message(F.text.startswith("unban "))
async def unban_user(message: Message, db: Database):
    if not is_super_admin(message.from_user.id):
        return
    try:
        target = int(message.text.split()[1])
    except (IndexError, ValueError):
        return await message.answer("Format: <code>unban USER_ID</code>")
    await db.set_banned(target, False)
    await message.answer(f"🔓 User {target} unbanned.")


@router.message(F.text.startswith("addmod "))
async def add_mod(message: Message, db: Database):
    if not is_super_admin(message.from_user.id):
        return
    try:
        target = int(message.text.split()[1])
    except (IndexError, ValueError):
        return await message.answer("Format: <code>addmod USER_ID</code>")
    await db.add_moderator(target, message.from_user.id)
    await message.answer(f"✅ User {target} is now a moderator.")


@router.message(F.text.startswith("removemod "))
async def remove_mod(message: Message, db: Database):
    if not is_super_admin(message.from_user.id):
        return
    try:
        target = int(message.text.split()[1])
    except (IndexError, ValueError):
        return await message.answer("Format: <code>removemod USER_ID</code>")
    await db.remove_moderator(target)
    await message.answer(f"✅ User {target} removed from moderators.")


@router.message(F.text.regexp(r"^-?\d+\|.+\|https?://.+"))
async def add_channel(message: Message, db: Database):
    if not is_super_admin(message.from_user.id):
        return
    parts = message.text.split("|", 2)
    if len(parts) != 3:
        return await message.answer("Format: <code>CHANNEL_ID|Name|Link</code>")
    await db.add_channel(parts[0].strip(), parts[1].strip(), parts[2].strip())
    await message.answer(f"✅ Channel <b>{parts[1].strip()}</b> added.")


@router.message(F.text.startswith("rmchannel "))
async def remove_channel(message: Message, db: Database):
    if not is_super_admin(message.from_user.id):
        return
    ch_id = message.text.split(maxsplit=1)[1].strip()
    await db.remove_channel(ch_id)
    await message.answer(f"✅ Channel {ch_id} removed.")


@router.message(Command("backfill"))
async def backfill_referrals(message: Message, db: Database):
    """One-time command to credit missed referral rewards for existing users."""
    if not is_super_admin(message.from_user.id):
        return

    await message.answer("⏳ Backfilling missed referral rewards... please wait.")

    reward = float(await db.get_setting("referral_reward") or 15)
    l2_reward = float(await db.get_setting("l2_referral_reward") or 1)
    milestone_bonus = float(await db.get_setting("milestone_bonus") or 50)

    # Find users who have referred_by set but no referral record exists
    rows = await db.pool.fetch("""
        SELECT u.user_id, u.full_name, u.referred_by
        FROM users u
        WHERE u.referred_by IS NOT NULL
          AND NOT EXISTS (
              SELECT 1 FROM referrals r
              WHERE r.referrer_id = u.referred_by AND r.referred_id = u.user_id
          )
    """)

    credited = 0
    for row in rows:
        referred_id = row["user_id"]
        referrer_id = row["referred_by"]
        referred_name = row["full_name"] or "User"

        # Skip self-referral
        if referrer_id == referred_id:
            continue

        # Check referrer exists
        referrer = await db.get_user(referrer_id)
        if not referrer:
            continue

        # L1 reward
        existing = await db.get_referral(referrer_id, referred_id)
        if not existing:
            await db.add_referral(referrer_id, referred_id, level=1, reward=reward)
            await db.update_balance(referrer_id, reward)
            await db.increment_referral_count(referrer_id)
            await db.add_log(referrer_id, "backfill_l1", f"referred={referred_id}, reward=₹{reward}")
            credited += 1

            # Milestone check
            ref_count = await db.get_referral_count(referrer_id)
            if ref_count > 0 and ref_count % 10 == 0:
                await db.update_balance(referrer_id, milestone_bonus)
                await db.add_log(referrer_id, "backfill_milestone", f"₹{milestone_bonus} at {ref_count} refs")

            # L2 reward
            l2_referrer_id = await db.get_referrer(referrer_id)
            if l2_referrer_id and l2_referrer_id != referred_id:
                existing_l2 = await db.get_referral(l2_referrer_id, referred_id)
                if not existing_l2:
                    await db.add_referral(l2_referrer_id, referred_id, level=2, reward=l2_reward)
                    await db.update_balance(l2_referrer_id, l2_reward)
                    await db.add_log(l2_referrer_id, "backfill_l2", f"referred={referred_id}, reward=₹{l2_reward}")

    await message.answer(
        f"✅ <b>Backfill complete!</b>\n\n"
        f"📊 <b>{credited}</b> missed referrals credited.\n"
        f"💰 ₹{reward} per referral given."
    )
