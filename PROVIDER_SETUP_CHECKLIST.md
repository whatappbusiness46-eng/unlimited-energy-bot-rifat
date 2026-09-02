# REAL PROVIDER SETUP CHECKLIST

This project intentionally contains no secrets.

## Required before enabling live offers

### AdvertsReward
From your publisher dashboard, provide/enter in Render:
- API key/token (if the dashboard uses one)
- Site/website/offerwall ID or key
- Exact REST API offers endpoint
- Exact request parameters for user ID / placement
- Exact postback URL macro list
- Postback secret and/or HMAC signing rule
- Which field is the unique conversion/event ID
- Whether `reward`/`payout` is USD or another currency
- Approved/held/reversed status values

### CPAGrip
- API/offer-feed key
- Exact JSON/RSS/offer-feed URL
- Exact tracking URL/user-sub ID format
- Exact postback URL macros
- Postback secret/signature method
- Unique conversion ID field
- Payout currency

### ShrtFly
- API token from the publisher dashboard
- Current API endpoint and response format from their current developer docs
- IMPORTANT: ShrtFly's current Terms prohibit incentivizing clicks with gifts/points/cash. Therefore it must not be wired as a rewarded-click task unless ShrtFly gives you written approval.

### ShrinkMe
- API key from Developers API
- Current API endpoint + response format
- Any callback/verification specification if you intend to reward a user for a completed action
- Traffic/incentive policy confirmation

## Render
- PUBLIC_BASE_URL = your HTTPS Render service URL
- All provider secrets should be added as Render Environment Variables.
- Never commit secrets to GitHub.

## Payments (only if you want automatic user withdrawals)
Current bot withdrawals are admin-reviewed. For automatic payouts you would additionally need the official merchant/API credentials and webhook docs for:
- bKash
- Nagad
- Bybit

Do NOT put passwords, OTPs, seed phrases, private keys, recovery codes, or personal identity documents into the bot repository.
