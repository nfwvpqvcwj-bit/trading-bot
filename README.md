# Trading Bot Pro Telegram Menu — Demo Auto Trade

نسخة أزرار تيليجرام مع تداول تجريبي تلقائي فقط.

## المهم
- زر **🧪 تشغيل التداول التجريبي** ينفذ صفقات على PRACTICE فقط.
- زر **🔒 الحساب الحقيقي** محمي بكلمة مرور، لكنه إشارات فقط بدون تداول تلقائي حقيقي للحماية.
- لا يوجد ضمان ربح أو 0 خسارة. استخدم ديمو أولًا.

## التشغيل
```cmd
py -3.12 -m pip install -r requirements.txt
set "TELEGRAM_TOKEN=ضع_توكنك"
set "TELEGRAM_CHAT_ID=7996102376"
set "IQ_EMAIL=ضع_ايميلك"
set "IQ_PASSWORD=ضع_كلمة_مرورك"
set "IQ_ACCOUNT_TYPE=PRACTICE"
set "ASSET=EUR/USD OTC"
set "TIMEFRAME_MINUTES=1"
set "MODE=NORMAL"
set "TRADE_AMOUNT=1"
set "TRADE_DURATION_MINUTES=1"
set "REAL_MODE_PASSWORD=57818181"
py -3.12 main.py
```

## الأزرار
- 📊 الحالة
- 📈 الإحصائيات
- 🔍 فحص الآن
- 🧪 تشغيل التداول التجريبي
- 🛑 إيقاف التداول
- 🔒 الحساب الحقيقي
- ✅ تسجيل فوز
- ❌ تسجيل خسارة
- ♻️ تصفير
