import requests

API = "https://api.telegram.org/bot{token}/{method}"

MAIN_KEYBOARD = {
    "keyboard": [
        [{"text": "📊 الحالة"}, {"text": "📈 الإحصائيات"}],
        [{"text": "🔍 فحص الآن"}, {"text": "⏸️ إيقاف مؤقت"}, {"text": "▶️ تشغيل"}],
        [{"text": "🧪 تشغيل التداول التجريبي"}, {"text": "🛑 إيقاف التداول"}],
        [{"text": "🔒 الحساب الحقيقي"}, {"text": "✅ تسجيل فوز"}, {"text": "❌ تسجيل خسارة"}],
        [{"text": "♻️ تصفير"}, {"text": "ℹ️ شرح"}],
    ],
    "resize_keyboard": True,
    "one_time_keyboard": False,
    "is_persistent": True
}

def send(cfg, text: str, keyboard: bool = True):
    if not cfg.TELEGRAM_TOKEN or not cfg.TELEGRAM_CHAT_ID:
        print("⚠️ TELEGRAM_TOKEN أو TELEGRAM_CHAT_ID غير مضاف")
        return False
    payload = {
        "chat_id": cfg.TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    }
    if keyboard:
        payload["reply_markup"] = MAIN_KEYBOARD
    try:
        r = requests.post(API.format(token=cfg.TELEGRAM_TOKEN, method="sendMessage"), json=payload, timeout=12)
        if not r.ok:
            print("❌ Telegram:", r.text)
            return False
        return True
    except Exception as e:
        print("❌ Telegram error:", e)
        return False

def get_updates(cfg, offset=None):
    if not cfg.TELEGRAM_TOKEN:
        return []
    params = {"timeout": 1, "allowed_updates": ["message"]}
    if offset is not None:
        params["offset"] = offset
    try:
        r = requests.get(API.format(token=cfg.TELEGRAM_TOKEN, method="getUpdates"), params=params, timeout=5)
        data = r.json()
        return data.get("result", []) if data.get("ok") else []
    except Exception:
        return []
