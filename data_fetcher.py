import time
from typing import Optional, Tuple
import numpy as np

try:
    import yfinance as yf
except Exception:
    yf = None

try:
    from iqoptionapi.stable_api import IQ_Option
except Exception:
    IQ_Option = None

from config import settings as cfg

_IQ = None

ASSET_MAP = {
    "EUR/USD": "EURUSD=X", "GBP/USD": "GBPUSD=X", "USD/JPY": "JPY=X", "USD/CHF": "CHF=X",
    "AUD/USD": "AUDUSD=X", "USD/CAD": "CAD=X", "NZD/USD": "NZDUSD=X", "EUR/GBP": "EURGBP=X",
    "EUR/JPY": "EURJPY=X", "GBP/JPY": "GBPJPY=X", "BTC/USD": "BTC-USD", "ETH/USD": "ETH-USD",
}
TIMEFRAME_MAP = {1: ("1m", "1d"), 5: ("5m", "5d"), 15: ("15m", "5d"), 30: ("30m", "1mo"), 60: ("60m", "3mo")}

def normalize_iq_asset(asset: str) -> str:
    a = asset.strip().upper().replace(" ", "").replace("/", "")
    if a.endswith("OTC") and not a.endswith("-OTC"):
        a = a[:-3] + "-OTC"
    return a

def _iq_connect():
    global _IQ
    if IQ_Option is None:
        raise RuntimeError("iqoptionapi غير مثبتة. ثبّت: py -3.12 -m pip install git+https://github.com/iqoptionapi/iqoptionapi.git")
    if not cfg.IQ_EMAIL or not cfg.IQ_PASSWORD:
        raise RuntimeError("ضع IQ_EMAIL و IQ_PASSWORD في Environment Variables")
    if _IQ is not None:
        try:
            if _IQ.check_connect():
                return _IQ
        except Exception:
            pass
    print("🔌 اتصال IQ Option لجلب الشموع فقط...")
    _IQ = IQ_Option(cfg.IQ_EMAIL, cfg.IQ_PASSWORD)
    ok, reason = _IQ.connect()
    if not ok:
        _IQ = None
        raise RuntimeError(f"فشل دخول IQ Option: {reason}")
    try:
        _IQ.change_balance(cfg.ACCOUNT_TYPE)
    except Exception:
        pass
    print("✅ متصل بـ IQ Option")
    return _IQ

def fetch_iq_candles(asset: str, timeframe_minutes: int, n_candles: int = 200):
    iq = _iq_connect()
    active = normalize_iq_asset(asset)
    interval = int(timeframe_minutes * 60)
    now = int(time.time())
    candles = iq.get_candles(active, interval, n_candles + 3, now)
    if not candles:
        raise RuntimeError(f"لا توجد شموع للأصل: {active}")
    candles = sorted(candles, key=lambda c: c.get("from", 0))
    # نستخدم الشموع المغلقة فقط حتى تكون الإشارة للشمعة القادمة
    closed = [c for c in candles if int(c.get("from", 0)) + interval <= now]
    if len(closed) < cfg.MIN_CANDLES:
        raise RuntimeError(f"شموع غير كافية: {len(closed)}")
    closed = closed[-n_candles:]
    opens = np.array([float(c.get("open", 0)) for c in closed], dtype=float)
    highs = np.array([float(c.get("max", c.get("high", 0))) for c in closed], dtype=float)
    lows = np.array([float(c.get("min", c.get("low", 0))) for c in closed], dtype=float)
    closes = np.array([float(c.get("close", 0)) for c in closed], dtype=float)
    vols = np.array([float(c.get("volume", 0)) for c in closed], dtype=float)
    last_close_ts = int(closed[-1].get("from", 0)) + interval
    return {"open": opens, "high": highs, "low": lows, "close": closes, "volume": vols, "last_close_ts": last_close_ts, "active": active}

def fetch_yahoo_candles(asset: str, timeframe_minutes: int, n_candles: int = 200):
    if yf is None:
        raise RuntimeError("yfinance غير مثبتة")
    clean = asset.replace(" OTC", "").replace("-OTC", "").strip()
    symbol = ASSET_MAP.get(clean, clean)
    interval, period = TIMEFRAME_MAP.get(timeframe_minutes, ("1m", "1d"))
    df = yf.download(symbol, interval=interval, period=period, progress=False, auto_adjust=True)
    if df is None or df.empty:
        raise RuntimeError(f"لا توجد بيانات Yahoo لـ {symbol}")
    if hasattr(df.columns, "levels"):
        df.columns = df.columns.get_level_values(0)
    df = df.dropna().tail(n_candles)
    return {
        "open": df["Open"].values.astype(float), "high": df["High"].values.astype(float),
        "low": df["Low"].values.astype(float), "close": df["Close"].values.astype(float),
        "volume": df.get("Volume", df["Close"]*0).values.astype(float), "last_close_ts": int(time.time()), "active": symbol,
    }

def fetch_candles(asset: str = None, timeframe_minutes: int = None, n_candles: int = 200):
    asset = asset or cfg.ASSET
    timeframe_minutes = timeframe_minutes or cfg.TIMEFRAME_MINUTES
    if cfg.DATA_SOURCE == "iqoption":
        try:
            return fetch_iq_candles(asset, timeframe_minutes, n_candles)
        except Exception as e:
            if cfg.ALLOW_YAHOO_FALLBACK:
                print(f"⚠️ فشل IQ، استخدام Yahoo كبديل غير OTC: {e}")
                return fetch_yahoo_candles(asset, timeframe_minutes, n_candles)
            raise
    return fetch_yahoo_candles(asset, timeframe_minutes, n_candles)


def place_demo_trade(asset: str, direction: str, amount: float, duration_minutes: int):
    """ينفذ صفقة تجريبية فقط على IQ Option. لا يستخدم REAL نهائيًا."""
    iq = _iq_connect()
    active = normalize_iq_asset(asset)
    try:
        iq.change_balance("PRACTICE")
    except Exception:
        pass
    d = direction.upper().strip()
    if d == "BUY":
        side = "call"
    elif d == "SELL":
        side = "put"
    else:
        raise RuntimeError("لا يمكن تنفيذ WAIT")
    ok, trade_id = iq.buy(float(amount), active, side, int(duration_minutes))
    if not ok:
        raise RuntimeError(f"فشل تنفيذ الصفقة التجريبية: {trade_id}")
    return trade_id
