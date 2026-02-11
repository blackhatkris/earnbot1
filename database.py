"""
Async PostgreSQL database layer using asyncpg.
Handles connection pool, table creation, and all queries.
"""
import asyncio
import asyncpg
import logging
import os
import ssl
from urllib.parse import parse_qs, urlparse

from config import (
    DATABASE_URL, DEFAULT_REFERRAL_REWARD, DEFAULT_L2_REFERRAL_REWARD,
    DEFAULT_DAILY_REWARD, DEFAULT_STREAK_BONUS, DEFAULT_MILESTONE_BONUS,
    DEFAULT_MIN_WITHDRAW, WITHDRAW_COOLDOWN_DAYS, STREAK_DAYS,
)

logger = logging.getLogger(__name__)


class Database:
    def __init__(self):
        self.pool: asyncpg.Pool | None = None

    @staticmethod
    def _should_use_ssl(dsn: str) -> bool:
        """Enable SSL when DB URL explicitly asks for it, or via env override.

        Railway/managed DBs often use ?sslmode=require in DATABASE_URL.
        """
        try:
            q = parse_qs(urlparse(dsn).query)
            sslmode = (q.get("sslmode") or [None])[0]
            if sslmode and str(sslmode).lower() in ("require", "verify-ca", "verify-full"):
                return True
        except Exception:
            pass

        return os.getenv("DATABASE_SSL", "").lower() in ("1", "true", "yes")

    async def connect(self, retries: int = 6):
        use_ssl = self._should_use_ssl(DATABASE_URL)
        ssl_ctx = ssl.create_default_context() if use_ssl else None

        last_err: Exception | None = None
        for attempt in range(1, retries + 1):
            try:
                self.pool = await asyncpg.create_pool(
                    DATABASE_URL,
                    min_size=1,
                    max_size=5,
                    command_timeout=30,
                    max_inactive_connection_lifetime=60,
                    ssl=ssl_ctx,
                )
                logger.info("Database pool created")
                return
            except Exception as e:
                last_err = e

                # Fail fast on auth/config errors (retry won't help)
                msg = str(e).lower()
                if "password authentication failed" in msg or "invalid authorization" in msg:
                    raise

                wait_s = min(2 ** attempt, 20)
                logger.warning(
                    "DB connect failed (attempt %s/%s): %r — retrying in %ss",
                    attempt,
                    retries,
                    e,
                    wait_s,
                )
                await asyncio.sleep(wait_s)

        logger.error("DB connect failed after %s attempts: %r", retries, last_err)
        raise last_err  # type: ignore[misc]

    async def ensure_pool(self):
        """Reconnect if pool is dead."""
        if self.pool is None or self.pool._closed:
            logger.warning("Pool lost, reconnecting...")
            await self.connect()

    async def close(self):
        if self.pool:
            await self.pool.close()

    # ─── TABLE CREATION ────────────────────────────────────────────

    async def create_tables(self):
        async with self.pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id BIGINT PRIMARY KEY,
                    username TEXT,
                    full_name TEXT,
                    balance NUMERIC(12,2) DEFAULT 0,
                    total_earned NUMERIC(12,2) DEFAULT 0,
                    referral_count INT DEFAULT 0,
                    referred_by BIGINT REFERENCES users(user_id),
                    is_banned BOOLEAN DEFAULT FALSE,
                    joined_channels BOOLEAN DEFAULT FALSE,
                    last_checkin TIMESTAMPTZ,
                    streak INT DEFAULT 0,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );

                CREATE TABLE IF NOT EXISTS referrals (
                    id SERIAL PRIMARY KEY,
                    referrer_id BIGINT NOT NULL REFERENCES users(user_id),
                    referred_id BIGINT NOT NULL REFERENCES users(user_id),
                    level INT DEFAULT 1,
                    reward NUMERIC(12,2) DEFAULT 0,
                    is_valid BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    UNIQUE(referrer_id, referred_id)
                );
                CREATE INDEX IF NOT EXISTS idx_referrals_referrer ON referrals(referrer_id);
                CREATE INDEX IF NOT EXISTS idx_referrals_referred ON referrals(referred_id);

                CREATE TABLE IF NOT EXISTS withdrawals (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL REFERENCES users(user_id),
                    amount NUMERIC(12,2) NOT NULL,
                    upi TEXT,
                    name TEXT,
                    phone TEXT,
                    email TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    reviewed_at TIMESTAMPTZ
                );
                CREATE INDEX IF NOT EXISTS idx_withdrawals_user ON withdrawals(user_id);
                CREATE INDEX IF NOT EXISTS idx_withdrawals_status ON withdrawals(status);

                CREATE TABLE IF NOT EXISTS channels (
                    id SERIAL PRIMARY KEY,
                    channel_id TEXT UNIQUE NOT NULL,
                    channel_name TEXT,
                    invite_link TEXT,
                    is_active BOOLEAN DEFAULT TRUE
                );

                CREATE TABLE IF NOT EXISTS moderators (
                    user_id BIGINT PRIMARY KEY,
                    added_by BIGINT,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );

                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS logs (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT,
                    action TEXT,
                    detail TEXT,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );
                CREATE INDEX IF NOT EXISTS idx_logs_user ON logs(user_id);
            """)
        logger.info("Tables ensured ✅")

    async def seed_settings(self):
        defaults = {
            "referral_reward": str(DEFAULT_REFERRAL_REWARD),
            "l2_referral_reward": str(DEFAULT_L2_REFERRAL_REWARD),
            "daily_reward": str(DEFAULT_DAILY_REWARD),
            "streak_bonus": str(DEFAULT_STREAK_BONUS),
            "milestone_bonus": str(DEFAULT_MILESTONE_BONUS),
            "min_withdraw": str(DEFAULT_MIN_WITHDRAW),
            "withdraw_cooldown_days": str(WITHDRAW_COOLDOWN_DAYS),
            "streak_days": str(STREAK_DAYS),
            "boost_mode": "0",
            "maintenance_mode": "0",
        }
        async with self.pool.acquire() as conn:
            for k, v in defaults.items():
                await conn.execute(
                    "INSERT INTO settings(key,value) VALUES($1,$2) ON CONFLICT(key) DO NOTHING",
                    k, v,
                )

    # ─── SETTINGS ──────────────────────────────────────────────────

    async def get_setting(self, key: str) -> str | None:
        return await self.pool.fetchval("SELECT value FROM settings WHERE key=$1", key)

    async def set_setting(self, key: str, value: str):
        await self.pool.execute(
            "INSERT INTO settings(key,value) VALUES($1,$2) ON CONFLICT(key) DO UPDATE SET value=$2",
            key, value,
        )

    # ─── USERS ─────────────────────────────────────────────────────

    async def get_user(self, user_id: int):
        return await self.pool.fetchrow("SELECT * FROM users WHERE user_id=$1", user_id)

    async def add_user(self, user_id: int, username: str, full_name: str, referred_by: int | None = None):
        await self.pool.execute(
            """INSERT INTO users(user_id, username, full_name, referred_by)
               VALUES($1,$2,$3,$4) ON CONFLICT(user_id) DO NOTHING""",
            user_id, username, full_name, referred_by,
        )

    async def update_balance(self, user_id: int, amount: float):
        await self.pool.execute(
            "UPDATE users SET balance=balance+$2, total_earned=total_earned+$2 WHERE user_id=$1",
            user_id, amount,
        )

    async def deduct_balance(self, user_id: int, amount: float):
        await self.pool.execute(
            "UPDATE users SET balance=balance-$2 WHERE user_id=$1",
            user_id, amount,
        )

    async def set_banned(self, user_id: int, banned: bool):
        await self.pool.execute("UPDATE users SET is_banned=$2 WHERE user_id=$1", user_id, banned)

    async def set_joined_channels(self, user_id: int, joined: bool):
        await self.pool.execute("UPDATE users SET joined_channels=$2 WHERE user_id=$1", user_id, joined)

    async def get_total_users(self) -> int:
        return await self.pool.fetchval("SELECT COUNT(*) FROM users") or 0

    async def get_users_today(self) -> int:
        return await self.pool.fetchval(
            "SELECT COUNT(*) FROM users WHERE created_at >= CURRENT_DATE"
        ) or 0

    async def get_total_payout(self) -> float:
        val = await self.pool.fetchval("SELECT COALESCE(SUM(total_earned),0) FROM users")
        return float(val)

    async def get_active_users(self) -> int:
        return await self.pool.fetchval(
            "SELECT COUNT(*) FROM users WHERE last_checkin >= NOW() - INTERVAL '7 days'"
        ) or 0

    async def get_all_user_ids(self) -> list[int]:
        rows = await self.pool.fetch("SELECT user_id FROM users WHERE is_banned=FALSE")
        return [r["user_id"] for r in rows]

    async def export_users(self):
        return await self.pool.fetch(
            "SELECT user_id, username, full_name, balance, total_earned, referral_count, created_at FROM users ORDER BY total_earned DESC"
        )

    # ─── REFERRALS ─────────────────────────────────────────────────

    async def add_referral(self, referrer_id: int, referred_id: int, level: int, reward: float):
        await self.pool.execute(
            """INSERT INTO referrals(referrer_id, referred_id, level, reward)
               VALUES($1,$2,$3,$4) ON CONFLICT DO NOTHING""",
            referrer_id, referred_id, level, reward,
        )

    async def get_referral(self, referrer_id: int, referred_id: int):
        return await self.pool.fetchrow(
            "SELECT * FROM referrals WHERE referrer_id=$1 AND referred_id=$2", referrer_id, referred_id,
        )

    async def increment_referral_count(self, user_id: int):
        await self.pool.execute("UPDATE users SET referral_count=referral_count+1 WHERE user_id=$1", user_id)

    async def get_referral_count(self, user_id: int) -> int:
        return await self.pool.fetchval("SELECT referral_count FROM users WHERE user_id=$1", user_id) or 0

    async def invalidate_referral(self, referrer_id: int, referred_id: int):
        await self.pool.execute(
            "UPDATE referrals SET is_valid=FALSE WHERE referrer_id=$1 AND referred_id=$2",
            referrer_id, referred_id,
        )

    async def get_referrer(self, user_id: int) -> int | None:
        return await self.pool.fetchval("SELECT referred_by FROM users WHERE user_id=$1", user_id)

    # ─── DAILY CHECK-IN ───────────────────────────────────────────

    async def checkin(self, user_id: int, streak: int):
        await self.pool.execute(
            "UPDATE users SET last_checkin=NOW(), streak=$2 WHERE user_id=$1",
            user_id, streak,
        )

    # ─── WITHDRAWALS ──────────────────────────────────────────────

    async def create_withdrawal(self, user_id: int, amount: float, upi: str, name: str, phone: str, email: str):
        return await self.pool.fetchval(
            """INSERT INTO withdrawals(user_id, amount, upi, name, phone, email)
               VALUES($1,$2,$3,$4,$5,$6) RETURNING id""",
            user_id, amount, upi, name, phone, email,
        )

    async def get_last_withdrawal(self, user_id: int):
        return await self.pool.fetchrow(
            "SELECT * FROM withdrawals WHERE user_id=$1 ORDER BY created_at DESC LIMIT 1", user_id,
        )

    async def get_pending_withdrawals(self):
        return await self.pool.fetch(
            "SELECT * FROM withdrawals WHERE status='pending' ORDER BY created_at ASC"
        )

    async def update_withdrawal_status(self, wid: int, status: str):
        await self.pool.execute(
            "UPDATE withdrawals SET status=$2, reviewed_at=NOW() WHERE id=$1", wid, status,
        )

    async def get_user_withdrawals(self, user_id: int):
        return await self.pool.fetch(
            "SELECT * FROM withdrawals WHERE user_id=$1 ORDER BY created_at DESC LIMIT 10", user_id,
        )

    # ─── CHANNELS ─────────────────────────────────────────────────

    async def get_active_channels(self):
        return await self.pool.fetch("SELECT * FROM channels WHERE is_active=TRUE")

    async def add_channel(self, channel_id: str, channel_name: str, invite_link: str):
        await self.pool.execute(
            """INSERT INTO channels(channel_id, channel_name, invite_link)
               VALUES($1,$2,$3) ON CONFLICT(channel_id) DO UPDATE SET channel_name=$2, invite_link=$3, is_active=TRUE""",
            channel_id, channel_name, invite_link,
        )

    async def remove_channel(self, channel_id: str):
        await self.pool.execute("UPDATE channels SET is_active=FALSE WHERE channel_id=$1", channel_id)

    # ─── MODERATORS ───────────────────────────────────────────────

    async def is_moderator(self, user_id: int) -> bool:
        return await self.pool.fetchval(
            "SELECT EXISTS(SELECT 1 FROM moderators WHERE user_id=$1)", user_id,
        )

    async def add_moderator(self, user_id: int, added_by: int):
        await self.pool.execute(
            "INSERT INTO moderators(user_id, added_by) VALUES($1,$2) ON CONFLICT DO NOTHING",
            user_id, added_by,
        )

    async def remove_moderator(self, user_id: int):
        await self.pool.execute("DELETE FROM moderators WHERE user_id=$1", user_id)

    # ─── LEADERBOARD ──────────────────────────────────────────────

    async def get_leaderboard(self, limit: int = 10):
        return await self.pool.fetch(
            "SELECT user_id, full_name, total_earned, referral_count FROM users ORDER BY total_earned DESC LIMIT $1",
            limit,
        )

    # ─── LOGS ─────────────────────────────────────────────────────

    async def add_log(self, user_id: int, action: str, detail: str = ""):
        await self.pool.execute(
            "INSERT INTO logs(user_id, action, detail) VALUES($1,$2,$3)",
            user_id, action, detail,
        )
