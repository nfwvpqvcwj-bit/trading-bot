from dataclasses import dataclass
from typing import List
import numpy as np

@dataclass
class Signal:
    direction: str
    confidence: int
    score: float
    reasons: List[str]
    votes_buy: int
    votes_sell: int
    volatility: float
    expire_seconds: int

def ema(x, period):
    x = np.asarray(x, dtype=float)
    out = np.zeros_like(x)
    k = 2 / (period + 1)
    out[0] = x[0]
    for i in range(1, len(x)):
        out[i] = x[i] * k + out[i-1] * (1-k)
    return out

def sma(x, p):
    x = np.asarray(x, dtype=float)
    if len(x) < p: return np.array([])
    return np.convolve(x, np.ones(p)/p, mode="valid")

def macd_hist(close, fast, slow, sig):
    if len(close) < slow + sig + 5: return 0.0
    m = ema(close, fast) - ema(close, slow)
    s = ema(m, sig)
    return float((m-s)[-1])

def ao(high, low, fast, slow):
    mid = (high + low) / 2
    if len(mid) < slow + 5: return 0.0
    f = sma(mid, fast); s = sma(mid, slow)
    if len(f) == 0 or len(s) == 0: return 0.0
    return float(f[-1] - s[-1])

def rsi(close, period=14):
    if len(close) < period + 2: return 50.0
    diff = np.diff(close)
    gain = np.where(diff > 0, diff, 0.0)
    loss = np.where(diff < 0, -diff, 0.0)
    avg_gain = np.mean(gain[-period:])
    avg_loss = np.mean(loss[-period:])
    if avg_loss == 0: return 100.0
    rs = avg_gain / avg_loss
    return float(100 - (100 / (1 + rs)))

def volatility(close, window=14):
    if len(close) < window + 1: return 0.0
    ret = np.diff(close[-window:]) / close[-window:-1]
    return float(np.std(ret))

def candle_body_filter(open_, high, low, close, multiplier=2.2):
    bodies = np.abs(close[-20:] - open_[-20:])
    avg = float(np.mean(bodies[:-1])) if len(bodies) > 2 else 0.0
    last = float(bodies[-1])
    rng = float(high[-1] - low[-1])
    return avg > 0 and (last > avg * multiplier), last, avg, rng

def sr_signal(close, high, low, lookback=60):
    if len(close) < lookback: return 0, "بعيد عن دعم/مقاومة"
    c = float(close[-1])
    hh = float(np.max(high[-lookback:-1])); ll = float(np.min(low[-lookback:-1]))
    span = hh - ll
    if span <= 0: return 0, "نطاق ضعيف"
    dist_low = abs(c - ll) / c
    dist_high = abs(hh - c) / c
    # قرب دعم = BUY، قرب مقاومة = SELL
    if dist_low < 0.00025: return 1, "قريب من دعم"
    if dist_high < 0.00025: return -1, "قريب من مقاومة"
    return 0, "بعيد عن دعم/مقاومة"

def analyze(data, cfg) -> Signal:
    o, h, l, c = data["open"], data["high"], data["low"], data["close"]
    reasons = []
    vol = volatility(c)
    if vol > cfg.MAX_VOLATILITY:
        return Signal("WAIT", 0, 0, [f"تذبذب عالي جدًا {vol:.6f}"], 0, 0, vol, cfg.ENTRY_WINDOW_SECONDS)

    big, last_body, avg_body, rng = candle_body_filter(o, h, l, c, cfg.BIG_CANDLE_MULTIPLIER)
    if cfg.BLOCK_AFTER_BIG_CANDLE and big:
        return Signal("WAIT", 0, 0, [f"آخر شمعة قوية جدًا، غالبًا تصحيح: body={last_body:.6f} avg={avg_body:.6f}"], 0, 0, vol, cfg.ENTRY_WINDOW_SECONDS)

    ef = ema(c, cfg.EMA_FAST); es = ema(c, cfg.EMA_SLOW); et = ema(c, cfg.EMA_TREND)
    fast, slow, trend = float(ef[-1]), float(es[-1]), float(et[-1])
    fast_slope = float(ef[-1] - ef[-4])
    price = float(c[-1])

    ma = 0
    if fast > slow and fast_slope > 0: ma = 1
    elif fast < slow and fast_slope < 0: ma = -1
    reasons.append(f"MA={'BUY' if ma==1 else 'SELL' if ma==-1 else 'محايد'} fast={fast:.5f} slow={slow:.5f}")

    trend_sig = 0
    if price > trend and slow >= trend: trend_sig = 1
    elif price < trend and slow <= trend: trend_sig = -1
    reasons.append(f"Trend={'BUY' if trend_sig==1 else 'SELL' if trend_sig==-1 else 'محايد'} EMA{cfg.EMA_TREND}={trend:.5f}")

    mh = macd_hist(c, cfg.MACD_FAST, cfg.MACD_SLOW, cfg.MACD_SIGNAL)
    macd = 1 if mh > 0 else -1 if mh < 0 else 0
    reasons.append(f"MACD={'BUY' if macd==1 else 'SELL' if macd==-1 else 'محايد'} hist={mh:.6f}")

    av = ao(h, l, cfg.AO_FAST, cfg.AO_SLOW)
    aos = 1 if av > 0 else -1 if av < 0 else 0
    reasons.append(f"AO={'BUY' if aos==1 else 'SELL' if aos==-1 else 'محايد'} {av:.6f}")

    rv = rsi(c, cfg.RSI_PERIOD)
    # RSI متطرف يمنع ملاحقة القمم/القيعان
    rsi_sig = 0
    if rv < 38: rsi_sig = 1
    elif rv > 62: rsi_sig = -1
    reasons.append(f"RSI={rv:.1f} {'دعم BUY' if rsi_sig==1 else 'دعم SELL' if rsi_sig==-1 else 'محايد'}")

    sr, sr_reason = sr_signal(c, h, l, cfg.SR_LOOKBACK)
    reasons.append(f"SR={sr_reason}")

    momentum = 1 if c[-1] > c[-4] and c[-2] >= c[-5] else -1 if c[-1] < c[-4] and c[-2] <= c[-5] else 0
    reasons.append(f"Momentum={'BUY' if momentum==1 else 'SELL' if momentum==-1 else 'محايد'}")

    weights = {"ma": 2.0, "trend": 1.8, "macd": 1.4, "ao": 1.2, "rsi": 0.9, "sr": 0.8, "mom": 1.0}
    score = ma*weights['ma'] + trend_sig*weights['trend'] + macd*weights['macd'] + aos*weights['ao'] + rsi_sig*weights['rsi'] + sr*weights['sr'] + momentum*weights['mom']
    signals = [ma, trend_sig, macd, aos, rsi_sig, sr, momentum]
    buy_votes = sum(1 for x in signals if x == 1)
    sell_votes = sum(1 for x in signals if x == -1)

    # في الوضع الصارم لا نخالف الترند العام
    if cfg.REQUIRE_TREND_CONFIRM:
        if score > 0 and trend_sig == -1:
            reasons.append("الترند العام عكس BUY — WAIT")
            return Signal("WAIT", 0, score, reasons, buy_votes, sell_votes, vol, cfg.ENTRY_WINDOW_SECONDS)
        if score < 0 and trend_sig == 1:
            reasons.append("الترند العام عكس SELL — WAIT")
            return Signal("WAIT", 0, score, reasons, buy_votes, sell_votes, vol, cfg.ENTRY_WINDOW_SECONDS)

    direction = "WAIT"
    if score >= cfg.MIN_SCORE and buy_votes >= 4 and buy_votes > sell_votes:
        direction = "BUY"
    elif score <= -cfg.MIN_SCORE and sell_votes >= 4 and sell_votes > buy_votes:
        direction = "SELL"
    else:
        reasons.append("التصويت/السكور غير كافي — WAIT")

    confidence = 0
    if direction != "WAIT":
        confidence = int(min(94, 58 + abs(score)*5 + max(buy_votes, sell_votes)*3))
        if confidence < cfg.MIN_CONFIDENCE:
            reasons.append(f"الثقة {confidence}% أقل من الحد {cfg.MIN_CONFIDENCE}% — WAIT")
            direction = "WAIT"
            confidence = 0

    reasons.append(f"VOTES BUY={buy_votes} SELL={sell_votes} SCORE={score:.2f} VOL={vol:.6f}")
    return Signal(direction, confidence, score, reasons, buy_votes, sell_votes, vol, cfg.ENTRY_WINDOW_SECONDS)
