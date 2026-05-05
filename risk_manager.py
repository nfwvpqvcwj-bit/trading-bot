import json, os, time
from datetime import datetime, timezone

class RiskManager:
    def __init__(self, cfg):
        self.cfg = cfg
        self.path = cfg.STATE_FILE
        self.state = {
            "paused": False, "consecutive_losses": 0, "daily_losses": {}, "signals": [],
            "cooldown_until": 0, "last_signal_ts": 0, "last_update_id": None,
            "auto_demo": bool(getattr(cfg, "AUTO_TRADE_DEMO_DEFAULT", False)),
            "real_unlocked": False, "awaiting_real_password": False,
            "demo_trades": []
        }
        self.load()

    def load(self):
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    self.state.update(json.load(f))
            except Exception:
                pass

    def save(self):
        self.state["signals"] = self.state.get("signals", [])[-300:]
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.state, f, ensure_ascii=False, indent=2)

    def today_key(self):
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")

    def can_signal(self, direction, confidence):
        now = time.time()
        if self.state.get("paused"):
            return False, "البوت متوقف مؤقتًا /pause"
        if direction == "WAIT":
            return False, "WAIT"
        if now < self.state.get("cooldown_until", 0):
            remain = int((self.state["cooldown_until"] - now) / 60) + 1
            return False, f"كول داون بعد خسارة: باقي {remain} دقيقة"
        if now - self.state.get("last_signal_ts", 0) < self.cfg.COOLDOWN_AFTER_SIGNAL_SECONDS:
            return False, "تم إرسال إشارة قريبة قبل قليل"
        if self.state.get("consecutive_losses", 0) >= self.cfg.MAX_CONSECUTIVE_LOSSES:
            return False, f"إيقاف بعد {self.state.get('consecutive_losses')} خسارة متتالية"
        dl = self.state.get("daily_losses", {}).get(self.today_key(), 0)
        if dl >= self.cfg.DAILY_MAX_LOSSES:
            return False, f"وصل حد خسائر اليوم: {dl}"
        if confidence < self.cfg.MIN_CONFIDENCE:
            return False, f"الثقة أقل من {self.cfg.MIN_CONFIDENCE}%"
        return True, "مسموح"

    def log_signal(self, asset, direction, confidence, score):
        self.state["last_signal_ts"] = time.time()
        self.state.setdefault("signals", []).append({
            "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "asset": asset, "direction": direction, "confidence": confidence, "score": score, "outcome": None
        })
        self.save()

    def record(self, outcome):
        outcome = outcome.upper()
        for s in reversed(self.state.get("signals", [])):
            if s.get("outcome") is None:
                s["outcome"] = outcome
                break
        if outcome == "LOSS":
            self.state["consecutive_losses"] = self.state.get("consecutive_losses", 0) + 1
            d = self.state.setdefault("daily_losses", {})
            d[self.today_key()] = d.get(self.today_key(), 0) + 1
            self.state["cooldown_until"] = time.time() + self.cfg.COOLDOWN_AFTER_LOSS_MINUTES * 60
        elif outcome == "WIN":
            self.state["consecutive_losses"] = 0
        self.save()

    def pause(self, val=True):
        self.state["paused"] = bool(val); self.save()

    def set_auto_demo(self, val=True):
        self.state["auto_demo"] = bool(val); self.save()

    def set_awaiting_real_password(self, val=True):
        self.state["awaiting_real_password"] = bool(val); self.save()

    def unlock_real(self):
        self.state["real_unlocked"] = True
        self.state["awaiting_real_password"] = False
        # للأمان: لا نسمح بالتداول التلقائي عند فتح الحقيقي
        self.state["auto_demo"] = False
        self.save()

    def log_demo_trade(self, asset, direction, amount, trade_id):
        self.state.setdefault("demo_trades", []).append({
            "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "asset": asset, "direction": direction, "amount": amount, "trade_id": str(trade_id)
        })
        self.state["demo_trades"] = self.state.get("demo_trades", [])[-200:]
        self.save()

    def reset(self):
        self.state["consecutive_losses"] = 0; self.state["cooldown_until"] = 0; self.save()

    def stats_text(self):
        sigs = self.state.get("signals", [])
        closed = [s for s in sigs if s.get("outcome")]
        wins = sum(1 for s in closed if s.get("outcome") == "WIN")
        losses = sum(1 for s in closed if s.get("outcome") == "LOSS")
        wr = (wins/len(closed)*100) if closed else 0
        return (f"📊 الإحصائيات\n"
                f"الإشارات: {len(sigs)}\n"
                f"فوز: {wins} | خسارة: {losses} | نسبة: {wr:.1f}%\n"
                f"خسائر متتالية: {self.state.get('consecutive_losses',0)}\n"
                f"خسائر اليوم: {self.state.get('daily_losses',{}).get(self.today_key(),0)}\n"
                f"تداول تجريبي تلقائي: {'شغال' if self.state.get('auto_demo') else 'متوقف'}\n"
                f"صفقات ديمو: {len(self.state.get('demo_trades', []))}\n"
                f"الحالة: {'متوقف' if self.state.get('paused') else 'شغال'}")
