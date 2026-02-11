"""
Stats service for admin dashboard.
"""
from database import Database


async def get_full_stats(db: Database) -> str:
    total = await db.get_total_users()
    today = await db.get_users_today()
    active = await db.get_active_users()
    payout = await db.get_total_payout()

    pending = await db.pool.fetchval("SELECT COUNT(*) FROM withdrawals WHERE status='pending'") or 0
    approved = await db.pool.fetchval("SELECT COUNT(*) FROM withdrawals WHERE status='approved'") or 0
    total_withdrawn = await db.pool.fetchval(
        "SELECT COALESCE(SUM(amount),0) FROM withdrawals WHERE status='approved'"
    )

    return (
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "📊 <b>FULL STATISTICS</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"👤 Total Users: <b>{total}</b>\n"
        f"📅 Joined Today: <b>{today}</b>\n"
        f"🟢 Active (7d): <b>{active}</b>\n\n"
        f"💰 Total Earned (all users): <b>₹{payout:,.2f}</b>\n"
        f"💸 Total Withdrawn: <b>₹{float(total_withdrawn):,.2f}</b>\n"
        f"⏳ Pending Withdrawals: <b>{pending}</b>\n"
        f"✅ Approved Withdrawals: <b>{approved}</b>\n"
    )
