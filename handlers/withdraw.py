"""
Withdrawal handler with FSM for collecting UPI details.
"""
from datetime import datetime, timezone, timedelta
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import Database

router = Router()


class WithdrawForm(StatesGroup):
    amount = State()
    upi = State()
    name = State()
    phone = State()
    email = State()
    confirm = State()


@router.message(F.text == "💸 Withdraw")
async def withdraw_start(message: Message, db: Database, state: FSMContext):
    uid = message.from_user.id
    user = await db.get_user(uid)
    if not user:
        return await message.answer("Please /start first.")

    min_withdraw = float(await db.get_setting("min_withdraw") or 500)
    cooldown_days = int(await db.get_setting("withdraw_cooldown_days") or 3)

    balance = float(user["balance"])
    if balance < min_withdraw:
        return await message.answer(
            f"❌ <b>Insufficient balance!</b>\n\n"
            f"💰 Your Balance: ₹{balance:,.2f}\n"
            f"📍 Minimum: ₹{min_withdraw:,.2f}\n\n"
            f"Keep earning to reach ₹{min_withdraw:,.0f}! 🚀"
        )

    # Cooldown check
    last_wd = await db.get_last_withdrawal(uid)
    if last_wd:
        diff = datetime.now(timezone.utc) - last_wd["created_at"]
        if diff < timedelta(days=cooldown_days):
            remaining = timedelta(days=cooldown_days) - diff
            return await message.answer(
                f"⏳ <b>Withdrawal cooldown!</b>\n\n"
                f"You can withdraw again in <b>{remaining.days}d {remaining.seconds//3600}h</b>."
            )

    await message.answer(
        f"💸 <b>WITHDRAW</b>\n\n"
        f"Balance: <b>₹{balance:,.2f}</b>\n"
        f"Minimum: ₹{min_withdraw:,.0f}\n\n"
        f"Enter the amount to withdraw:"
    )
    await state.set_state(WithdrawForm.amount)


@router.message(WithdrawForm.amount)
async def collect_amount(message: Message, db: Database, state: FSMContext):
    try:
        amount = float(message.text)
    except ValueError:
        return await message.answer("❌ Enter a valid number.")

    user = await db.get_user(message.from_user.id)
    min_wd = float(await db.get_setting("min_withdraw") or 500)

    if amount < min_wd:
        return await message.answer(f"❌ Minimum withdrawal is ₹{min_wd:,.0f}")
    if amount > float(user["balance"]):
        return await message.answer("❌ Amount exceeds your balance.")

    await state.update_data(amount=amount)
    await message.answer("📲 Enter your <b>UPI ID</b> (e.g. name@paytm):")
    await state.set_state(WithdrawForm.upi)


@router.message(WithdrawForm.upi)
async def collect_upi(message: Message, state: FSMContext):
    await state.update_data(upi=message.text.strip())
    await message.answer("👤 Enter your <b>Full Name</b>:")
    await state.set_state(WithdrawForm.name)


@router.message(WithdrawForm.name)
async def collect_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await message.answer("📱 Enter your <b>Phone Number</b>:")
    await state.set_state(WithdrawForm.phone)


@router.message(WithdrawForm.phone)
async def collect_phone(message: Message, state: FSMContext):
    await state.update_data(phone=message.text.strip())
    await message.answer("📧 Enter your <b>Email</b>:")
    await state.set_state(WithdrawForm.email)


@router.message(WithdrawForm.email)
async def collect_email(message: Message, db: Database, state: FSMContext):
    await state.update_data(email=message.text.strip())
    data = await state.get_data()

    text = (
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "💸 <b>CONFIRM WITHDRAWAL</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"💰 Amount: <b>₹{data['amount']:,.2f}</b>\n"
        f"📲 UPI: <b>{data['upi']}</b>\n"
        f"👤 Name: <b>{data['name']}</b>\n"
        f"📱 Phone: <b>{data['phone']}</b>\n"
        f"📧 Email: <b>{data['email']}</b>\n\n"
        "Type <b>YES</b> to confirm or <b>NO</b> to cancel."
    )
    await message.answer(text)
    await state.set_state(WithdrawForm.confirm)


@router.message(WithdrawForm.confirm)
async def confirm_withdraw(message: Message, db: Database, state: FSMContext):
    if message.text.strip().upper() != "YES":
        await state.clear()
        return await message.answer("❌ Withdrawal cancelled.")

    data = await state.get_data()
    uid = message.from_user.id

    # Double-check balance
    user = await db.get_user(uid)
    if float(user["balance"]) < data["amount"]:
        await state.clear()
        return await message.answer("❌ Insufficient balance.")

    await db.deduct_balance(uid, data["amount"])
    wid = await db.create_withdrawal(uid, data["amount"], data["upi"], data["name"], data["phone"], data["email"])
    await db.add_log(uid, "withdraw_request", f"₹{data['amount']}, WID={wid}")
    await state.clear()

    await message.answer(
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "✅ <b>WITHDRAWAL SUBMITTED!</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📋 Request ID: <b>#{wid}</b>\n"
        f"💰 Amount: <b>₹{data['amount']:,.2f}</b>\n"
        f"📲 UPI: {data['upi']}\n\n"
        "Your withdrawal is being reviewed.\n"
        "You'll be notified once approved! 🎉"
    )


@router.message(F.text == "📋 Withdraw History")
async def withdraw_history(message: Message, db: Database):
    rows = await db.get_user_withdrawals(message.from_user.id)
    if not rows:
        return await message.answer("📋 No withdrawal history yet.")

    lines = ["━━━━━━━━━━━━━━━━━━━━━━\n📋 <b>WITHDRAWAL HISTORY</b>\n━━━━━━━━━━━━━━━━━━━━━━\n"]
    status_emoji = {"pending": "⏳", "approved": "✅", "rejected": "❌"}
    for r in rows:
        emoji = status_emoji.get(r["status"], "❓")
        lines.append(
            f"{emoji} #{r['id']} — ₹{float(r['amount']):,.2f} — {r['status'].upper()}\n"
            f"   📅 {r['created_at'].strftime('%d %b %Y')}"
        )
    await message.answer("\n".join(lines))
