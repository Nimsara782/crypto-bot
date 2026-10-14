import time
import requests
import pandas as pd
from ta.trend import EMAIndicator, MACD
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange, BollingerBands

# --- Telegram තොරතුරු ---
TELEGRAM_BOT_TOKEN = "8995241511:AAHrPEVF3Qea1VFooMXsx2u81-eFykipDqE"
TELEGRAM_CHAT_ID = "8414347027"

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"දෝෂයක් මතු විය: {e}")

def get_binance_data(symbol, interval):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit=100"
    res = requests.get(url).json()
    df = pd.DataFrame(res, columns=['time', 'open', 'high', 'low', 'close', 'vol', 'close_time', 'q1', 'q2', 'q3', 'q4', 'q5'])
    df['close'] = df['close'].astype(float)
    df['high'] = df['high'].astype(float)
    df['low'] = df['low'].astype(float)
    df['vol'] = df['vol'].astype(float)
    return df

def run_bot():
    symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
    timeframes = ["15m", "1h", "4h"]
    
    print("උසස් විශ්ලේෂණ (EMA, RSI, ATR, MACD, Bollinger Bands, Volume) සහිත ස්කෑනරය ක්‍රියාත්මක විය...")
    
    while True:
        for sym in symbols:
            for tf in timeframes:
                try:
                    df = get_binance_data(sym, tf)
                    close = df['close']
                    volume = df['vol']
                    
                    # --- Indicators ගණනය කිරීම ---
                    ema20 = EMAIndicator(close, 20).ema_indicator()
                    ema50 = EMAIndicator(close, 50).ema_indicator()
                    rsi = RSIIndicator(close, 14).rsi()
                    atr = AverageTrueRange(df['high'], df['low'], close, 14).average_true_range()
                    
                    # MACD
                    macd_ind = MACD(close)
                    macd = macd_ind.macd()
                    macd_signal = macd_ind.macd_signal()
                    
                    # Bollinger Bands
                    bb = BollingerBands(close, window=20, window_dev=2)
                    bb_low = bb.bollinger_lband()
                    bb_high = bb.bollinger_hband()
                    
                    # Volume Average (ගනුදෙනු පරිමාව සාමාන්‍යයට වඩා වැඩිදැයි බැලීමට)
                    vol_sma = volume.rolling(window=20).mean()
                    
                    p = close.iloc[-1]
                    atr_val = atr.iloc[-1]
                    current_vol = volume.iloc[-1]
                    avg_vol = vol_sma.iloc[-1]
                    
                    # ප්‍රබල තහවුරු කිරීමක් සඳහා Volume එක සාමාන්‍යයට වඩා වැඩි විය යුතුය
                    volume_ok = current_vol > avg_vol

                    # --- 🟢 BUY Signal (මිලදී ගැනීමේ කොන්දේසි) ---
                    # 1. EMA 20 පහළ සිට ඉහළට EMA 50 හරහා යාම (Crossover)
                    # 2. RSI > 48 (Bullish zone)
                    # 3. MACD Line > MACD Signal Line
                    # 4. Volume එක සාමාන්‍යයට වඩා වැඩි වීම
                    if (ema20.iloc[-2] < ema50.iloc[-2]) and (ema20.iloc[-1] > ema50.iloc[-1]) and \
                       (rsi.iloc[-1] > 48) and (macd.iloc[-1] > macd_signal.iloc[-1]) and volume_ok:
                        
                        sl = p - (atr_val * 1.5)
                        tp = p + ((p - sl) * 2.0)
                        msg = f"🚀 *උසස් මිලදී ගැනීමේ සංඥාව (BUY SIGNAL)*\n\n🔹 *මුදල් යුගලය:* {sym}\n🔹 *කාලරාමුව:* {tf}\n🔹 *මිළ:* {p}\n🎯 *TP:* {tp:.2f}\n🛑 *SL:* {sl:.2f}\n📊 *විශ්ලේෂණය:* EMA Crossover + MACD Bullish + High Volume"
                        send_telegram(msg)
                    
                    # --- 🔴 SELL Signal (විකිණීමේ කොන්දේසි) ---
                    # 1. EMA 20 ඉහළ සිට පහළට EMA 50 හරහා යාම
                    # 2. RSI < 52 (Bearish zone)
                    # 3. MACD Line < MACD Signal Line
                    # 4. Volume එක සාමාන්‍යයට වඩා වැඩි වීම
                    elif (ema20.iloc[-2] > ema50.iloc[-2]) and (ema20.iloc[-1] < ema50.iloc[-1]) and \
                         (rsi.iloc[-1] < 52) and (macd.iloc[-1] < macd_signal.iloc[-1]) and volume_ok:
                        
                        sl = p + (atr_val * 1.5)
                        tp = p - ((sl - p) * 2.0)
                        msg = f"🔻 *උසස් විකිණීමේ සංඥාව (SELL SIGNAL)*\n\n🔹 *මුදල් යුගලය:* {sym}\n🔹 *කාලරාමුව:* {tf}\n🔹 *මිළ:* {p}\n🎯 *TP:* {tp:.2f}\n🛑 *SL:* {sl:.2f}\n📊 *විශ්ලේෂණය:* EMA Crossover + MACD Bearish + High Volume"
                        send_telegram(msg)
                        
                except Exception as e:
                    print(f"{sym} ({tf}) පරීක්ෂා කිරීමේදී දෝෂයක් මතු විය: {e}")
                    
        time.sleep(300) # සෑම විනාඩි 5කට වරක්ම ස්කෑන් කරයි

if __name__ == "__main__":
    run_bot()
