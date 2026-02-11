"""
Moderator-specific actions: broadcast.
"""
import asyncio
import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from config import SUPER_ADMINS
from database import Database

router = Router()
logger = logging.getLogger(__name__)


class BroadcastForm(StatesGroup):
    message = State()


@router.message(F.text == "📣 Broadcast")
async def broadcast_start(message: Message, db: Database, state: FSMContext):
    uid = message.from_user.id
    if uid not in SUPER_ADMINS and not await db.is_moderator(uid):
        return
    await message.answer(
        "📣 <b>BROADCAST</b>\n\n"
        "Send the message to broadcast.\n"
        "Supports: text, photo+caption, text with buttons.\n\n"
        "Send /cancel to abort."
    )
    await state.set_state(BroadcastForm.message)


@router.message(BroadcastForm.message)
async def broadcast_send(message: Message, db: Database, state: FSMContext):
    await state.clear()

    user_ids = await db.get_all_user_ids()
    sent, failed = 0, 0

    await message.answer(f"📣 Broadcasting to <b>{len(user_ids)}</b> users...")

    for uid in user_ids:
        try:
            await message.copy_to(uid)
            sent += 1
        except Exception:
            failed += 1
        # Rate limit: 25 msg/sec Telegram limit
        if sent % 25 == 0:
            await asyncio.sleep(1)

    await message.answer(
        f"📣 <b>Broadcast Complete</b>\n\n"
        f"✅ Sent: {sent}\n❌ Failed: {failed}"
    )
    await db.add_log(message.from_user.id, "broadcast", f"sent={sent}, failed={failed}")
