CPAGrip integration files for Unlimited Energy Bot

Files:
- cpagrip.py
- cpagrip_postback.py
- earn.py.cpa.patch.txt

Important:
1. Add cpagrip.py and cpagrip_postback.py to the repo root.
2. Apply the exact three changes in earn.py.cpa.patch.txt.
3. Your current bot.py already imports/registers cpagrip_bp.
4. Render environment variables:
   CPAGRIP_SMARTLINK=https://playabledownload.com/1911566
   CPA_REWARD_POINTS=10
   CPA_DAILY_LIMIT=5
   CPAGRIP_POSTBACK_PASSWORD=<same password configured in CPAGrip>
5. CPAGrip Global Postback URL:
   https://unlimited-energy-bot-v2-06pl.onrender.com/cpagrip/postback

The current GitHub earn.py is 851 lines. A shortened "replacement"
would risk deleting existing earning features, so the patch intentionally
changes only the CPA-related parts.
