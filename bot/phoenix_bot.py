import ccxt
import pandas as pd
import time
from ta.trend import EMAIndicator
from ta.momentum import RSIIndicator
from telegram import Bot
import json
import os

print("🔥 Phoenix v11 학습형 시스템 시작")

TOKEN = "8949048008:AAFt-McN20S-urp3v8GpnggXYXI26rPI8H8"
CHAT_ID = "@phoenix_1125_bot"

bot = Bot(token=TOKEN)
exchange = ccxt.binance()

# =========================
# 학습 데이터 저장 파일
# =========================
DATA_FILE = "learning_data.json"

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump([], f)

def save_trade(data):
    with open(DATA_FILE, "r") as f:
        history = json.load(f)

    history.append(data)

    with open(DATA_FILE, "w") as f:
        json.dump(history, f)

def calculate_score():
    with open(DATA_FILE, "r") as f:
        history = json.load(f)

    if len(history) == 0:
        return 0, 0, 0

    wins = len([h for h in history if h["profit"] > 0])
    losses = len(history) - wins
    avg = sum([h["profit"] for h in history]) / len(history)

    winrate = wins / len(history) * 100

    score = (winrate * 0.6) + (avg * 40)

    return winrate, avg, score

position = None
entry_price = None

while True:

    try:
        ohlcv = exchange.fetch_ohlcv(
            'BTC/USDT',
            timeframe='5m',
            limit=100
        )

        df = pd.DataFrame(
            ohlcv,
            columns=['time','open','high','low','close','volume']
        )

        df['ema9'] = EMAIndicator(df['close'], 9).ema_indicator()
        df['ema21'] = EMAIndicator(df['close'], 21).ema_indicator()
        df['rsi'] = RSIIndicator(df['close'], 14).rsi()

        last = df.iloc[-1]

        price = last['close']
        ema9 = last['ema9']
        ema21 = last['ema21']
        rsi = last['rsi']

        buy_signal = (
            ema9 > ema21 and
            45 < rsi < 65
        )

        sell_signal = (
            ema9 < ema21 or
            rsi > 70
        )

        print("-----")
        print("가격:", price)
        print("RSI:", round(rsi,2))

        # =====================
        # 매수
        # =====================
        if position is None and buy_signal:

            position = "LONG"
            entry_price = price

            bot.send_message(
                chat_id=CHAT_ID,
                text=f"🔥 매수 진입\n가격: {price}"
            )

        # =====================
        # 매도 + 학습
        # =====================
        elif position == "LONG" and sell_signal:

            profit = ((price - entry_price) / entry_price) * 100

            save_trade({
                "entry": entry_price,
                "exit": price,
                "profit": profit
            })

            winrate, avg, score = calculate_score()

            bot.send_message(
                chat_id=CHAT_ID,
                text=
                f"💰 청산\n"
                f"수익: {round(profit,2)}%\n"
                f"승률: {round(winrate,2)}%\n"
                f"평균: {round(avg,2)}%\n"
                f"점수: {round(score,2)}"
            )

            position = None
            entry_price = None

        else:
            print("⏳ 대기")

        time.sleep(60)

    except Exception as e:
        print("오류:", e)
        time.sleep(10)