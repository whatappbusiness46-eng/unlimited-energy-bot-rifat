# Unlimited Energy Bot

Production-oriented Telegram earning bot built with `python-telegram-bot`, MongoDB and Flask health endpoints.

## What is included

- Home/profile/balance/rank/statistics/activity
- Daily bonus, energy, spin wheel, Lucky Box and Scratch Card
- Referral system with self-referral/duplicate protection
- Premium membership
- VIP levels 1-5 with admin purchase ON/OFF
- Admin panel, user management, rewards/tasks/wheel/Lucky Box/referral settings
- Withdrawal flow for bKash, Nagad and Bybit, including pending/approve/reject/history
- Withdrawal approval notification and transaction/stat synchronization
- Persistent MongoDB-backed shortlink configuration with admin add/enable/disable/delete
- Shortlink token generation, cooldown and reward protection
- Callback routing for referral, offers, shortlinks, VIP and admin actions
- Render health server

## Important external integrations

The source is complete for the internal bot logic, but real-money/provider integrations still require the operator's own credentials and provider APIs. In particular:

1. bKash/Nagad/Bybit withdrawals are **admin-reviewed payouts**, not automatic payment-gateway transfers.
2. Shortlink URLs are configured by Admin. The bot does not invent or scrape a shortlink provider API.
3. CPA conversion verification/postback requires a real CPA network account and its postback specification; no provider credentials are included in this repository.
4. Telegram Bot Token and MongoDB credentials must be supplied as environment variables.

Do not put secrets in GitHub.

## Required Render environment variables

- `BOT_TOKEN`
- `MONGO_URI`
- `DATABASE_NAME` (optional; default `UnlimitedEnergy`)
- `ADMIN_ID`
- `BKASH_NUMBER` (recommended for payout display)
- `NAGAD_NUMBER` (recommended for payout display)
- `BYBIT_UID` (recommended for payout display)

## Local syntax check

```bash
python -m py_compile bot.py
python -m py_compile callbacks.py
python -m py_compile database.py
python -m py_compile admin.py
```

## Render

The included `Procfile` uses:

```text
worker: python bot.py
```

The Flask health server listens on the Render-provided `PORT` environment variable.

## Admin shortlink format

Open **Admin → Shortlinks → Add Shortlink** and send:

```text
id|name|url|reward|cooldown
```

Example:

```text
sl1|Example|https://example.com/go|10|86400
```

The configured URL must be a valid gateway/provider URL that can accept the bot's `token` query parameter if verification is expected.
