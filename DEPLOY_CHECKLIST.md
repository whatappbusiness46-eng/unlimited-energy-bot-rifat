# Deployment checklist

- [ ] Set BOT_TOKEN in Render Environment Variables.
- [ ] Set MONGO_URI.
- [ ] Set ADMIN_ID.
- [ ] Set payout details if withdrawals are enabled.
- [ ] Deploy from the intended GitHub branch.
- [ ] Confirm `Running 'python bot.py'` in Render logs.
- [ ] Confirm `/start` works.
- [ ] Confirm Home callbacks work.
- [ ] Confirm Admin panel and VIP ON/OFF work.
- [ ] Test one withdrawal submission.
- [ ] Test Admin approval and user notification.
- [ ] Test Admin rejection and refund.
- [ ] Test referral link/stat callbacks.
- [ ] Configure at least one shortlink before expecting Shortlinks to show an offer.
- [ ] Only enable real CPA/payment integrations after adding the provider-specific API/postback code and credentials.
