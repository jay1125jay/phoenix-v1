import ccxt
import pandas as pd
import time
import random
import copy
import requests
from ta.trend import EMAIndicator
from ta.momentum import RSIIndicator

print("🔥 Phoenix v20 - Safety System ON")

exchange = ccxt.binance()

# ======================
# 텔레그램 (선택)
# ======================
BOT_TOKEN = "8949048008:AAFt-McN20S-urp3v8GpnggXYXI26rPI8H8"
CHAT_ID = "@phoenix_1125_bot"

def send_msg(text):
    if BOT_TOKEN == "8949048008:AAFt-McN20S-urp3v8GpnggXYXI26rPI8H8":
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": text})

# ======================
# run 함수 (이게 핵심)
# ======================
def run():

    balance = 1_000_000
    position = None
    entry_price = 0
    coin_amount = 0
    position_symbol = None

    consecutive_losses = 0
    total_loss = 0
    MAX_LOSS = -5
    MAX_CONSEC = 3

    symbols = ["BTC/USDT", "ETH/USDT", "SOL/USDT"]

    def kill_switch(reason):
        print("🛑 KILL SWITCH:", reason)
        send_msg(f"🛑 STOP\n{reason}")
        exit()

    while True:

        try:

            if total_loss <= MAX_LOSS:
                kill_switch("누적 손실")

            if consecutive_losses >= MAX_CONSEC:
                kill_switch("연속 손실")

            best_symbol = None
            best_score = -999
            best_df = None

            for symbol in symbols:

                ohlcv = exchange.fetch_ohlcv(symbol, '5m', 100)

                df = pd.DataFrame(
                    ohlcv,
                    columns=['time','open','high','low','close','volume']
                )

                df['ema9'] = EMAIndicator(df['close'], 9).ema_indicator()
                df['ema21'] = EMAIndicator(df['close'], 21).ema_indicator()
                df['rsi'] = RSIIndicator(df['close'], 14).rsi()

                last = df.iloc[-1]

                score = 0
                if last['ema9'] > last['ema21']:
                    score += 1
                if 45 < last['rsi'] < 65:
                    score += 1

                if score > best_score:
                    best_score = score
                    best_symbol = symbol
                    best_df = df

            last = best_df.iloc[-1]
            price = last['close']
            rsi = last['rsi']

            buy_signal = (
                last['ema9'] > last['ema21'] and
                45 < rsi < 65
            )

            sell_signal = (
                last['ema9'] < last['ema21'] or
                rsi > 70
            )

            print("-----")
            print("코인:", best_symbol)
            print("RSI:", round(rsi,2))
            print("손실:", total_loss)
            print("연속:", consecutive_losses)

            if position is None and buy_signal:

                position = best_symbol
                entry_price = price
                coin_amount = balance / price

                send_msg(f"🔥 BUY {best_symbol}")
                print("BUY")

            elif position is not None and sell_signal:

                profit = ((price - entry_price) / entry_price) * 100
                balance = coin_amount * price

                if profit < 0:
                    consecutive_losses += 1
                    total_loss += profit
                else:
                    consecutive_losses = 0

                send_msg(f"💰 SELL {position}\n{round(profit,2)}%")
                print("SELL", profit)

                position = None
                entry_price = 0

            time.sleep(60)

        except Exception as e:
            print("오류:", e)
            time.sleep(10)