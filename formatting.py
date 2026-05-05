from datetime import datetime, timezone

def msg_signal(asset, signal, price, allowed, reason, cfg):
    now = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")
    emoji = {"BUY":"🟢", "SELL":"🔴", "WAIT":"🟡"}.get(signal.direction, "⚪")
    action = "أعلى / BUY" if signal.direction == "BUY" else "أدنى / SELL" if signal.direction == "SELL" else "انتظار"
    lines = [
        "━━━━━━━━━━━━━━━━━━━━",
        f"{emoji} إشارة الدقيقة القادمة",
        "━━━━━━━━━━━━━━━━━━━━",
        f"📌 الأصل: {asset}",
        f"⏱️ الفريم: {cfg.TIMEFRAME_MINUTES}m",
        f"🕐 وقت الإرسال: {now}",
        f"💲 آخر إغلاق: {price:.5f}" if price else "",
        "━━━━━━━━━━━━━━━━━━━━",
        f"📡 القرار: *{signal.direction}* — {action}",
        f"🎯 الثقة: {signal.confidence}%",
        f"🧮 السكور: {signal.score:.2f}",
        f"⏳ نافذة الدخول: أول {cfg.ENTRY_WINDOW_SECONDS} ثواني فقط من الشمعة",
        "━━━━━━━━━━━━━━━━━━━━",
        "📊 الأسباب:",
    ]
    lines += [f"• {x}" for x in signal.reasons[-8:]]
    if not allowed:
        lines += ["━━━━━━━━━━━━━━━━━━━━", f"⛔ ممنوع الدخول: {reason}"]
    else:
        lines += ["━━━━━━━━━━━━━━━━━━━━", "✅ إشارات فقط — لا يوجد دخول تلقائي"]
    return "\n".join([x for x in lines if x])
