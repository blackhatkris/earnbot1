# 🤖 EarnBot — Telegram Earning Bot

Production-ready Telegram earning bot built with **aiogram 3.x** + **asyncpg** + **PostgreSQL**.  
Optimized for **Railway Free Plan** (single instance, polling mode, low memory).

---

## 📁 Project Structure

```
bot/
├── main.py                    # Entry point — polling
├── config.py                  # Environment variables
├── database.py                # asyncpg database layer
├── requirements.txt           # Python dependencies
├── Procfile                   # Railway worker process
├── runtime.txt                # Python version
├── middlewares/
│   └── auth.py                # Auth + ForceJoin middlewares
├── handlers/
│   ├── user.py                # /start, My Account, Start Earning
│   ├── referral.py            # My Referrals info
│   ├── daily.py               # Daily check-in reward
│   ├── withdraw.py            # Withdrawal FSM flow
│   ├── leaderboard.py         # Top earners
│   ├── help.py                # /help + How To Earn
│   ├── forcejoin.py           # Channel join verification
│   ├── admin.py               # Super Admin panel (/black)
│   └── moderator.py           # Broadcast system
├── services/
│   ├── rewards.py             # Referral L1/L2 + milestones
│   ├── fraud.py               # Anti-fraud (leave detection)
│   ├── stats.py               # Full stats for admin
│   ├── notifications.py       # Safe message sender
│   └── boost.py               # Boost mode helper
└── keyboards/
    ├── user_menu.py            # Main menu + force join
    └── admin_menu.py           # Admin panel keyboard
```

---

## 🚀 Features

| Feature | Details |
|---------|---------|
| **Referral System** | ₹15/referral, ₹1 Level-2, ₹50 every 10 refs |
| **Daily Login** | ₹10/day, 7-day streak → ₹50 bonus |
| **Force Join** | Multi-channel, inline buttons, re-check |
| **Withdraw** | Min ₹500, UPI, 3-day cooldown, manual approval |
| **Admin Panel** | `/black` — full control panel |
| **Moderators** | Broadcast, stats, approve, ban |
| **Anti-Fraud** | Self-ref block, leave detection, rate limits |
| **Boost Mode** | 2x referral rewards toggle |
| **Broadcast** | Text/photo, rate-limited, error-safe |
| **FOMO Welcome** | Live stats, earning potential, motivation |

---

## 🛤️ Railway Deployment (Step by Step)

### 1. Create GitHub Repository

```bash
# In terminal, navigate to the bot/ folder
cd bot

# Initialize git
git init
git add .
git commit -m "Initial commit - EarnBot"

# Create repo on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/earnbot.git
git branch -M main
git push -u origin main
```

### 2. Set Up Railway

1. Go to [railway.app](https://railway.app) and sign in with GitHub
2. Click **"New Project"** → **"Deploy from GitHub Repo"**
3. Select your `earnbot` repository
4. Railway will auto-detect the `Procfile`

### 3. Add PostgreSQL

1. In your Railway project, click **"+ New"** → **"Database"** → **"PostgreSQL"**
2. The `DATABASE_URL` variable is auto-injected ✅

### 4. Add Environment Variables

In Railway → your service → **Variables** tab, add:

| Variable | Value |
|----------|-------|
| `BOT_TOKEN` | Your Telegram bot token from [@BotFather](https://t.me/BotFather) |
| `SUPER_ADMINS` | Your Telegram user ID (comma-separated for multiple) |

> `DATABASE_URL` is auto-set by the PostgreSQL plugin.

### 5. Important Settings

- **Replicas**: Set to `1` (avoid TelegramConflictError)
- Railway auto-uses `Procfile` → runs `worker: python main.py`
- The bot deletes webhook on startup to prevent conflicts
- Uses polling mode (no need for a public URL)

### 6. Get Your Telegram User ID

Message [@userinfobot](https://t.me/userinfobot) on Telegram to get your numeric user ID.

---

## 🔧 Local Development

```bash
cd bot
pip install -r requirements.txt

# Set environment variables
export BOT_TOKEN="your-bot-token"
export DATABASE_URL="postgresql://user:pass@localhost:5432/earnbot"
export SUPER_ADMINS="your-telegram-user-id"

python main.py
```

---

## 📤 How to Upload Files to GitHub

### Option A: Using Terminal (Recommended)

```bash
# 1. Copy all files from bot/ folder to a new directory
mkdir earnbot && cp -r bot/* earnbot/

# 2. Initialize and push
cd earnbot
git init
git add .
git commit -m "🤖 EarnBot - Telegram Earning Bot"
git remote add origin https://github.com/YOUR_USERNAME/earnbot.git
git branch -M main
git push -u origin main
```

### Option B: GitHub Web Upload

1. Go to [github.com/new](https://github.com/new) → Create new repo named `earnbot`
2. Click **"uploading an existing file"**
3. Drag & drop ALL files from the `bot/` folder maintaining the structure
4. **Important**: Create folders first by uploading files with paths:
   - Upload `main.py`, `config.py`, `database.py`, `requirements.txt`, `Procfile`, `runtime.txt` to root
   - Create `handlers/` folder and upload all handler files
   - Create `services/` folder and upload all service files
   - Create `keyboards/` folder and upload keyboard files
   - Create `middlewares/` folder and upload middleware files
5. Don't forget the `__init__.py` files in each subfolder!

### Option C: GitHub Desktop

1. Create repo on GitHub
2. Clone it locally with GitHub Desktop
3. Copy all bot/ files into the cloned folder
4. Commit & Push

---

## ⚠️ Avoiding Common Issues

| Issue | Solution |
|-------|----------|
| `TelegramConflictError` | Ensure only 1 instance runs. Set Railway replicas = 1 |
| Bot not responding | Check `BOT_TOKEN` is correct. Check Railway logs |
| DB connection error | Verify `DATABASE_URL` from PostgreSQL plugin |
| Webhook conflict | Bot auto-deletes webhook on startup |
| Rate limiting | Broadcast uses `sleep(1)` every 25 messages |

---

## 📋 Admin Commands Quick Reference

| Command | Access | Action |
|---------|--------|--------|
| `/black` | Admin/Mod | Open admin panel |
| `set referral_reward 20` | Admin | Change referral reward |
| `set daily_reward 15` | Admin | Change daily reward |
| `approve 123` | Admin/Mod | Approve withdrawal #123 |
| `reject 123` | Admin/Mod | Reject withdrawal #123 |
| `ban 12345` | Admin/Mod | Ban user |
| `unban 12345` | Admin | Unban user |
| `addmod 12345` | Admin | Add moderator |
| `removemod 12345` | Admin | Remove moderator |
| `CHANNEL_ID\|Name\|Link` | Admin | Add force-join channel |
| `rmchannel CHANNEL_ID` | Admin | Remove channel |

---

Built for virality 🚀 — FOMO messaging, referral motivation, and streak mechanics included.
