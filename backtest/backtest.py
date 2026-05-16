import ccxt
import pandas as pd
from ta.trend import EMAIndicator
from ta.momentum import RSIIndicator

exchange = ccxt.binance()

print("🔥 Phoenix v9 모멘텀 전략")

ohlcv = exchange.fetch_ohlcv(
    'BTC/USDT',
    timeframe='5m',
    limit=1000
)

df = pd.DataFrame(
    ohlcv,
    columns=[
        'time',
        'open',
        'high',
        'low',
        'close',
        'volume'
    ]
)

df['ema9'] = EMAIndicator(
    df['close'],
    window=9
).ema_indicator()

df['ema21'] = EMAIndicator(
    df['close'],
    window=21
).ema_indicator()

df['rsi'] = RSIIndicator(
    df['close'],
    window=14
).rsi()

wins = 0
losses = 0
trades = []

for i in range(30, len(df)-5):

    candle_move = (
        (df['close'].iloc[i] -
         df['open'].iloc[i])
         /
         df['open'].iloc[i]
    ) * 100

    buy_signal = (

        df['ema9'].iloc[i]
        >
        df['ema21'].iloc[i]

        and

        df['rsi'].iloc[i]
        > 50

        and

        df['volume'].iloc[i]
        >
        df['volume'].iloc[i-1]

        and

        candle_move > 0.25
    )

    if buy_signal:

        entry = df['close'].iloc[i]
        exit_price = df['close'].iloc[i+5]

        profit = (
            (exit_price-entry)
            /entry
        )*100

        trades.append(profit)

        if profit > 0:
            wins += 1
        else:
            losses += 1

print("-----")
print("총 거래:", len(trades))
print("승:", wins)
print("패:", losses)

if len(trades) > 0:

    winrate = (wins/len(trades))*100
    avg = sum(trades)/len(trades)

    print("승률:", round(winrate,2), "%")
    print("평균 수익:", round(avg,2), "%")

else:
    print("거래 없음")