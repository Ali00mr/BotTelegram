import ccxt
import statistics

exchange = ccxt.binance()

# محاسبه RSI
def rsi(closes, period=14):
    if len(closes) < period + 1:
        return 50
    gains, losses = [], []
    for i in range(1, len(closes)):
        change = closes[i] - closes[i-1]
        gains.append(max(0, change))
        losses.append(abs(min(0, change)))
    avg_gain = statistics.mean(gains[-period:]) if any(gains) else 0.0001
    avg_loss = statistics.mean(losses[-period:]) if any(losses) else 0.0001
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

# EMA
def ema(values, period):
    if len(values) < period:
        return []
    alpha = 2 / (period + 1)
    ema_vals = [statistics.mean(values[:period])]
    for price in values[period:]:
        ema_vals.append((price - ema_vals[-1]) * alpha + ema_vals[-1])
    return ema_vals

# MACD
def macd(closes, short=12, long=26, signal=9):
    if len(closes) < long + signal:
        return 0, 0, 0
    ema_short = ema(closes, short)
    ema_long = ema(closes, long)
    macd_line = [s - l for s, l in zip(ema_short[-len(ema_long):], ema_long)]
    signal_line = ema(macd_line, signal)
    if not signal_line:
        return 0, 0, 0
    histogram = macd_line[-1] - signal_line[-1]
    return macd_line[-1], signal_line[-1], histogram

# Bollinger Bands
def bollinger_bands(closes, period=20, std_factor=2):
    if len(closes) < period:
        return None, None, None
    ma = statistics.mean(closes[-period:])
    std = statistics.pstdev(closes[-period:])
    upper = ma + std_factor * std
    lower = ma - std_factor * std
    return lower, ma, upper

# تولید سیگنال‌ها
async def generate_signals(top_n=100, new_listing_days=60):
    markets = exchange.load_markets()
    usdt_pairs = [s for s in markets if s.endswith('/USDT')]
    tickers = exchange.fetch_tickers(usdt_pairs)

    sorted_pairs = sorted(tickers.items(), key=lambda x: x[1].get('quoteVolume', 0), reverse=True)
    top_pairs = [s[0] for s in sorted_pairs[:top_n]]

    signals = []
    for symbol in top_pairs:
        try:
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe='1h', limit=100)
            closes = [c[4] for c in ohlcv]
            last = closes[-1]

            # اندیکاتورها
            rsi_val = rsi(closes)
            macd_line, signal_line, hist = macd(closes)
            lower, ma, upper = bollinger_bands(closes)
            ma20 = statistics.mean(closes[-20:]) if len(closes) >= 20 else last

            if None in [lower, ma, upper]:
                continue

            # شرایط خرید
            buy_condition = (
                last > ma20 and
                40 < rsi_val < 70 and
                macd_line > signal_line and
                last < upper
            )

            if buy_condition:
                confidence = 70
                if hist > 0: confidence += 10
                if rsi_val < 60: confidence += 5

                signals.append({
                    'symbol': symbol,
                    'price': last,
                    'buy_price': round(last*0.995, 4),
                    'sell_target': round(last*1.02, 4),
                    'stop_loss': round(last*0.985, 4),
                    'confidence': min(confidence, 95),
                    'note': f"RSI={round(rsi_val,1)}, MACD={round(macd_line,3)}"
                })
        except Exception:
            continue
    return signals