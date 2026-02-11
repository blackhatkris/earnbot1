"""
/start handler — big FOMO motivational welcome + main menu.
"""
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message
from database import Database
from keyboards.user_menu import main_menu_keyboard

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, db: Database, db_user: dict | None = None):
    user = message.from_user
    args = message.text.split()
    referrer_id = None

    if len(args) > 1:
        try:
            referrer_id = int(args[1])
        except ValueError:
            pass

    # Register with referral if new user
    if not db_user:
        await db.add_user(user.id, user.username or "", user.full_name or "", referred_by=referrer_id)

    # Fetch live stats
    total_users = await db.get_total_users()
    users_today = await db.get_users_today()
    total_payout = await db.get_total_payout()
    active_users = await db.get_active_users()

    # Process referral for new users
    if not db_user and referrer_id and referrer_id != user.id:
        from services.rewards import process_referral
        await process_referral(db, referrer_id, user.id, user.full_name, message.bot)

    welcome = (
        f"🎉 <b>Welcome to EarnBot, {user.full_name}!</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "💰 <b>START EARNING RIGHT NOW!</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "🔥 <b>₹15</b> per referral\n"
        "📅 <b>₹10</b> daily login reward\n"
        "🎯 <b>₹50</b> bonus every 10 referrals\n"
        "👥 <b>₹1</b> Level 2 referral earning\n"
        "💸 Withdraw at <b>₹500</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "📊 <b>LIVE STATS</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"👤 Users Joined Today: <b>{users_today}</b>\n"
        f"👥 Total Users: <b>{total_users}</b>\n"
        f"💰 Total Payout: <b>₹{total_payout:,.2f}</b>\n"
        f"🟢 Active Users: <b>{active_users}</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🚀 <b>Earn ₹15,000–₹20,000/month!</b>\n"
        "Just share your referral link and\n"
        "watch your earnings grow! 💸\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
    )

    await message.answer(welcome, reply_markup=main_menu_keyboard())


@router.message(F.text == "👤 My Account")
async def my_account(message: Message, db: Database):
    user = await db.get_user(message.from_user.id)
    if not user:
        return await message.answer("Please /start first.")

    bot_info = await message.bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={user['user_id']}"

    text = (
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "👤 <b>MY ACCOUNT</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🆔 User ID: <code>{user['user_id']}</code>\n"
        f"👤 Name: {user['full_name']}\n"
        f"💰 Balance: <b>₹{float(user['balance']):,.2f}</b>\n"
        f"📈 Total Earned: <b>₹{float(user['total_earned']):,.2f}</b>\n"
        f"👥 Referrals: <b>{user['referral_count']}</b>\n"
        f"🔥 Streak: <b>{user['streak']} days</b>\n\n"
        f"🔗 <b>Your Referral Link:</b>\n<code>{ref_link}</code>\n\n"
        "Share this link and earn <b>₹15</b> per friend! 🚀"
    )
    await message.answer(text)


@router.message(F.text == "🚀 Start Earning")
async def start_earning(message: Message):
    bot_info = await message.bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={message.from_user.id}"

    text = (
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🚀 <b>HOW TO START EARNING</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "1️⃣ Share your referral link below\n"
        "2️⃣ Your friend joins the bot\n"
        "3️⃣ They join our channels\n"
        "4️⃣ You earn <b>₹15 instantly!</b>\n\n"
        f"🔗 <b>Your Link:</b>\n<code>{ref_link}</code>\n\n"
        "📱 Share on WhatsApp, Instagram,\n"
        "Facebook groups & Telegram!\n\n"
        "💡 <b>Pro Tip:</b> Active referrers earn\n"
        "₹15,000–₹20,000 per month! 🔥"
    )
    await message.answer(text)
