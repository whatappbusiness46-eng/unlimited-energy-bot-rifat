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


## Provider-backed earning integration (v2.1)

The previous manual `Claim Reward` flow has been removed. Users can no longer
credit themselves by pressing a Telegram button. Live offer rewards are
credited only after a verified server-to-server provider postback.

### Supported provider adapters

- **AdvertsReward**: live offer fetch + verified postback endpoint.
- **CPAGrip**: live offer fetch + verified postback endpoint.
- **ShrtFly / ShrinkMe**: API credentials are reserved for monetized-link
  generation once the provider's current API endpoint/contract is supplied.
  Do not use a shortener in an incentivized-click flow if its terms prohibit
  that traffic model.

### Postback endpoint

Set your Render public URL and configure the provider dashboard to call:

```text
https://YOUR-RENDER-SERVICE.onrender.com/postback/advertsreward
https://YOUR-RENDER-SERVICE.onrender.com/postback/cpagrip
```

The endpoint accepts GET, form POST, or JSON POST. It requires a documented
shared secret or HMAC signature. Event IDs are stored in MongoDB to prevent
duplicate credits.

### Important

Do not guess provider API URLs, signature formulas, or callback macros.
Provider accounts can have account-specific values. Put the exact API/feed URL,
postback secret/signature format, and macro names from the provider dashboard
into Render Environment Variables.

### VIP fix

VIP purchase ON/OFF is stored in MongoDB and checked both when opening a VIP
purchase flow and immediately before charging the user. Existing VIP
memberships are not revoked when purchasing is turned OFF.
