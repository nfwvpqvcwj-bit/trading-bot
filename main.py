import os, sys, time, math
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import settings as cfg
from core.data_fetcher import fetch_candles, place_demo_trade
from core.indicators import analyze
from core.risk_manager import RiskManager
from notifications.telegram import send, get_updates
from notifications.formatting import msg_signal


def next_candle_wait():
    tf = max(60, int(cfg.TIMEFRAME_MINUTES*60))
    now = int(time.time())
    next_open = ((now // tf) + 1) * tf
    target = next_open + cfg.SIGNAL_DELAY_SECONDS
    return max(1, target - now)

def run_once(risk, allow_auto_trade=False):
    try:
        data = fetch_candles(cfg.ASSET, cfg.TIMEFRAME_MINUTES, 220)
        signal = analyze(data, cfg)
        price = float(data["close"][-1])
        allowed, reason = risk.can_signal(signal.direction, signal.confidence)
        text = msg_signal(cfg.ASSET, signal, price, allowed, reason, cfg)
        print(text.replace("*", ""))
        send(cfg, text)
        if allowed and signal.direction != "WAIT":
            risk.log_signal(cfg.ASSET, signal.direction, signal.confidence, signal.score)
            # تنفيذ تجريبي فقط، ولا يتم في زر فحص الآن إلا من التشغيل التلقائي
            if allow_auto_trade and risk.state.get("auto_demo"):
                try:
                    trade_id = place_demo_trade(cfg.ASSET, signal.direction, cfg.TRADE_AMOUNT, cfg.TRADE_DURATION_MINUTES)
                    risk.log_demo_trade(cfg.ASSET, signal.direction, cfg.TRADE_AMOUNT, trade_id)
                    send(cfg, f"🧪 تم تنفيذ صفقة تجريبية فقط\nالأصل: `{cfg.ASSET}`\nالاتجاه: *{signal.direction}*\nالمبلغ: `{cfg.TRADE_AMOUNT}`\nالمدة: `{cfg.TRADE_DURATION_MINUTES}m`\nرقم الصفقة: `{trade_id}`")
                except Exception as te:
                    send(cfg, f"❌ فشل تنفيذ صفقة الديمو: {te}")
    except Exception as e:
        err = f"❌ خطأ البوت: {e}"
        print(err)
        send(cfg, err)

def menu_text():
    return (
        "✅ *تم تشغيل البوت*\n"
        "اختر من الأزرار تحت بدون كتابة أوامر:\n\n"
        "🔍 فحص الآن = يعطي إشارة مرة واحدة\n"
        "📊 الحالة = إعدادات البوت\n"
        "📈 الإحصائيات = الفوز/الخسارة\n"
        "✅ تسجيل فوز / ❌ تسجيل خسارة = لإدارة المخاطر\n"
        "🧪 تشغيل التداول التجريبي = يدخل صفقات ديمو فقط عند الإشارة\n"
        "🛑 إيقاف التداول = إيقاف الدخول التجريبي\n"
        "🔒 الحساب الحقيقي = إشارات فقط بعد كلمة مرور، بدون دخول تلقائي حقيقي\n"
        "⏸️ إيقاف مؤقت / ▶️ تشغيل = تحكم بالإشارات"
    )

def handle_command(text, risk):
    raw = (text or "").strip()
    t = raw.lower()

    if risk.state.get("awaiting_real_password"):
        if raw == str(cfg.REAL_MODE_PASSWORD):
            risk.unlock_real()
            return "🔓 تم قبول كلمة مرور الحقيقي.\n⚠️ الحقيقي في هذه النسخة إشارات فقط، ولا يوجد تداول تلقائي حقيقي للحماية.\nللتداول التجريبي التلقائي استخدم زر: 🧪 تشغيل التداول التجريبي"
        risk.set_awaiting_real_password(False)
        return "❌ كلمة مرور الحقيقي غير صحيحة. تم الإلغاء."

    if t in ("/start", "start", "ابدأ", "بدء"):
        return menu_text()

    if raw in ("📊 الحالة",) or t in ("/status", "status", "حالة"):
        return (
            f"✅ *الحالة*\n"
            f"الأصل: `{cfg.ASSET}`\n"
            f"الفريم: `{cfg.TIMEFRAME_MINUTES}m`\n"
            f"الوضع: `{cfg.MODE}`\n"
            f"الحساب: `{cfg.ACCOUNT_TYPE}`\n"
            f"التداول التجريبي التلقائي: `{'شغال' if risk.state.get('auto_demo') else 'متوقف'}`\n"
            f"الحقيقي مفتوح: `{'نعم - إشارات فقط' if risk.state.get('real_unlocked') else 'لا'}`\n"
            f"مبلغ الديمو: `{cfg.TRADE_AMOUNT}` | مدة الصفقة: `{cfg.TRADE_DURATION_MINUTES}m`\n"
            f"أقل ثقة: `{cfg.MIN_CONFIDENCE}%`\n"
            f"نافذة الدخول: أول `{cfg.ENTRY_WINDOW_SECONDS}` ثواني"
        )

    if raw in ("📈 الإحصائيات",) or t in ("/stats", "stats", "احصائيات", "الإحصائيات"):
        return risk.stats_text()

    if raw in ("⏸️ إيقاف مؤقت",) or t in ("/pause", "pause", "ايقاف", "إيقاف"):
        risk.pause(True)
        return "⏸️ تم إيقاف الإشارات مؤقتًا"

    if raw in ("▶️ تشغيل",) or t in ("/resume", "resume", "تشغيل"):
        risk.pause(False)
        return "▶️ تم تشغيل الإشارات"

    if raw in ("🧪 تشغيل التداول التجريبي",):
        risk.set_auto_demo(True)
        risk.pause(False)
        return ("🧪 تم تشغيل التداول التجريبي التلقائي فقط.\n"
                f"المبلغ: `{cfg.TRADE_AMOUNT}` | المدة: `{cfg.TRADE_DURATION_MINUTES}m`\n"
                "✅ يدخل على PRACTICE فقط عند BUY/SELL المسموحة.\n"
                "⚠️ راقب النتائج وسجل فوز/خسارة من الأزرار.")

    if raw in ("🛑 إيقاف التداول",):
        risk.set_auto_demo(False)
        return "🛑 تم إيقاف التداول التجريبي التلقائي. الإشارات تبقى شغالة."

    if raw in ("🔒 الحساب الحقيقي",):
        risk.set_awaiting_real_password(True)
        return "🔐 اكتب كلمة مرور الحقيقي الآن. تنبيه: الحقيقي إشارات فقط، بدون دخول تلقائي حقيقي."

    if raw in ("♻️ تصفير",) or t in ("/reset", "reset", "تصفير"):
        risk.reset()
        return "✅ تم تصفير الخسائر والكول داون"

    if raw in ("❌ تسجيل خسارة",) or t in ("/loss", "loss", "خسارة"):
        risk.record("LOSS")
        return "❌ تم تسجيل خسارة + تفعيل الحماية"

    if raw in ("✅ تسجيل فوز",) or t in ("/win", "win", "فوز"):
        risk.record("WIN")
        return "✅ تم تسجيل فوز"

    if raw in ("🔍 فحص الآن",) or t in ("/once", "once", "فحص"):
        run_once(risk, allow_auto_trade=False)
        return "✅ تم فحص مرة واحدة — بدون تنفيذ تلقائي"

    if raw in ("ℹ️ شرح",) or t in ("/help", "help", "شرح"):
        return menu_text()

    return None

def poll_telegram_commands(risk):
    if not cfg.ENABLE_TELEGRAM_COMMANDS or not cfg.TELEGRAM_TOKEN:
        return
    updates = get_updates(cfg, risk.state.get("last_update_id"))
    for u in updates:
        risk.state["last_update_id"] = u.get("update_id", 0) + 1
        msg = u.get("message") or {}
        chat = str(msg.get("chat", {}).get("id", ""))
        # نسمح فقط لصاحب CHAT_ID
        if cfg.TELEGRAM_CHAT_ID and chat != str(cfg.TELEGRAM_CHAT_ID):
            continue
        reply = handle_command(msg.get("text", ""), risk)
        if reply:
            send(cfg, reply)
    risk.save()

def main():
    risk = RiskManager(cfg)
    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()
        if cmd == "once": run_once(risk, allow_auto_trade=False); return
        if cmd == "stats": print(risk.stats_text()); return
        if cmd == "loss": risk.record("LOSS"); print("تم تسجيل خسارة"); return
        if cmd == "win": risk.record("WIN"); print("تم تسجيل فوز"); return
        if cmd == "reset": risk.reset(); print("تم التصفير"); return
    print("✅ تشغيل مستمر — إشارات فقط")
    print(f"Asset={cfg.ASSET} TF={cfg.TIMEFRAME_MINUTES}m Mode={cfg.MODE} Account={cfg.ACCOUNT_TYPE}")
    send(cfg, f"✅ بدأ البوت\n{cfg.ASSET} | {cfg.TIMEFRAME_MINUTES}m | {cfg.MODE}\nاضغط Start في البوت ثم استخدم الأزرار تحت 👇")
    while True:
        poll_telegram_commands(risk)
        if cfg.NEXT_CANDLE_MODE:
            wait = next_candle_wait()
            while wait > 0:
                poll_telegram_commands(risk)
                time.sleep(min(1, wait))
                wait -= 1
            run_once(risk, allow_auto_trade=True)
        else:
            run_once(risk, allow_auto_trade=True)
            time.sleep(cfg.SCAN_SLEEP_SECONDS)

if __name__ == "__main__":
    main()
