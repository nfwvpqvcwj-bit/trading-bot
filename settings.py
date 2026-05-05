import os

def _bool(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).strip().lower() in ("1", "true", "yes", "on")

def _int(name: str, default: str) -> int:
    try:
        return int(os.getenv(name, default))
    except Exception:
        return int(default)

def _float(name: str, default: str) -> float:
    try:
        return float(os.getenv(name, default))
    except Exception:
        return float(default)

# مصدر البيانات والأصل
DATA_SOURCE = os.getenv("DATA_SOURCE", "iqoption").lower()   # iqoption | yahoo
ASSET = os.getenv("ASSET", "EUR/USD OTC")
TIMEFRAME_MINUTES = _int("TIMEFRAME_MINUTES", "1")
ACCOUNT_TYPE = os.getenv("IQ_ACCOUNT_TYPE", "PRACTICE").upper()  # PRACTICE | REAL
IQ_EMAIL = os.getenv("IQ_EMAIL", "")
IQ_PASSWORD = os.getenv("IQ_PASSWORD", "")
ALLOW_YAHOO_FALLBACK = _bool("ALLOW_YAHOO_FALLBACK", "false")

# تيليجرام
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
ENABLE_TELEGRAM_COMMANDS = _bool("ENABLE_TELEGRAM_COMMANDS", "true")

# توقيت الإشارة: للشمعة القادمة فقط
NEXT_CANDLE_MODE = _bool("NEXT_CANDLE_MODE", "true")
SIGNAL_DELAY_SECONDS = _int("SIGNAL_DELAY_SECONDS", "2")  # يرسل بعد بداية الشمعة بثانيتين تقريبًا
ENTRY_WINDOW_SECONDS = _int("ENTRY_WINDOW_SECONDS", "5")  # لا تدخل بعد هذه الثواني

# المؤشرات
EMA_FAST = _int("EMA_FAST", "8")
EMA_SLOW = _int("EMA_SLOW", "21")
EMA_TREND = _int("EMA_TREND", "50")
MACD_FAST = _int("MACD_FAST", "12")
MACD_SLOW = _int("MACD_SLOW", "26")
MACD_SIGNAL = _int("MACD_SIGNAL", "9")
AO_FAST = _int("AO_FAST", "5")
AO_SLOW = _int("AO_SLOW", "34")
RSI_PERIOD = _int("RSI_PERIOD", "14")
SR_LOOKBACK = _int("SR_LOOKBACK", "60")

# حماية وجودة الإشارة
MODE = os.getenv("MODE", "STRICT").upper()  # STRICT | NORMAL | FAST
MIN_CONFIDENCE = _int("MIN_CONFIDENCE", "82")
MIN_SCORE = _float("MIN_SCORE", "4.2")
MAX_SPREAD_PCT = _float("MAX_SPREAD_PCT", "0.015")
MAX_VOLATILITY = _float("MAX_VOLATILITY", "0.0022")
MIN_CANDLES = _int("MIN_CANDLES", "120")
REQUIRE_TREND_CONFIRM = _bool("REQUIRE_TREND_CONFIRM", "true")
BLOCK_AFTER_BIG_CANDLE = _bool("BLOCK_AFTER_BIG_CANDLE", "true")
BIG_CANDLE_MULTIPLIER = _float("BIG_CANDLE_MULTIPLIER", "2.2")

# إدارة الخسائر
MAX_CONSECUTIVE_LOSSES = _int("MAX_CONSECUTIVE_LOSSES", "1")
DAILY_MAX_LOSSES = _int("DAILY_MAX_LOSSES", "2")
COOLDOWN_AFTER_LOSS_MINUTES = _int("COOLDOWN_AFTER_LOSS_MINUTES", "15")
COOLDOWN_AFTER_SIGNAL_SECONDS = _int("COOLDOWN_AFTER_SIGNAL_SECONDS", "55")

# تشغيل
SCAN_SLEEP_SECONDS = _int("SCAN_SLEEP_SECONDS", "1")
# التداول التلقائي
# ملاحظة: التداول التلقائي الحقيقي غير مفعل للحماية. التجريبي فقط.
DRY_RUN = True  # الإشارات فقط افتراضيًا
AUTO_TRADE_DEMO_DEFAULT = _bool("AUTO_TRADE_DEMO", "false")
TRADE_AMOUNT = _float("TRADE_AMOUNT", "1")
TRADE_DURATION_MINUTES = _int("TRADE_DURATION_MINUTES", "1")
REAL_MODE_PASSWORD = os.getenv("REAL_MODE_PASSWORD", "57818181")
ALLOW_REAL_AUTO_TRADE = False  # لا يتم تنفيذ صفقات حقيقية تلقائيًا
STATE_FILE = os.getenv("STATE_FILE", "bot_state.json")
