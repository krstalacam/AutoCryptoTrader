import pandas as pd
import numpy as np

# ATR hesaplama (Pandas ile)
def calculate_atr(data, period):
    high_low = data['High'] - data['Low']
    high_close = np.abs(data['High'] - data['Close'].shift())
    low_close = np.abs(data['Low'] - data['Close'].shift())

    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = tr.rolling(period).mean()
    return atr

# SMA hesaplama (Pandas ile)
def sma(series, period):
    return series.rolling(window=period).mean()

# HalfTrend indikatörü hesaplama fonksiyonu
def calculate_signals(data, amplitude):

    data['HighMA'] = sma(data['High'], amplitude)
    data['LowMA'] = sma(data['Low'], amplitude)

    data['MaxLowPrice'] = data['Low'].rolling(window=amplitude).min()
    data['MinHighPrice'] = data['High'].rolling(window=amplitude).max()

    trend = 0
    next_trend = 1
    data['Trend'] = 0

    for i in range(1, len(data)):
        if next_trend == 1:
            data.at[data.index[i], 'MaxLowPrice'] = max(data['Low'].iloc[i], data['MaxLowPrice'].iloc[i-1])

            if data['HighMA'].iloc[i] < data['MaxLowPrice'].iloc[i] and data['Close'].iloc[i] < data['Low'].iloc[i-1]:
                trend = 1
                next_trend = 0
                data.at[data.index[i], 'MinHighPrice'] = data['High'].iloc[i]
        else:
            data.at[data.index[i], 'MinHighPrice'] = min(data['High'].iloc[i], data['MinHighPrice'].iloc[i-1])

            if data['LowMA'].iloc[i] > data['MinHighPrice'].iloc[i] and data['Close'].iloc[i] > data['High'].iloc[i-1]:
                trend = 0
                next_trend = 1
                data.at[data.index[i], 'MaxLowPrice'] = data['Low'].iloc[i]

        data.at[data.index[i], 'Trend'] = trend

    return data

# Al/Sat sinyalleri oluşturma fonksiyonu
def generate_signals(data):
    data['BuySignal'] = (data['Trend'] == 0) & (data['Trend'].shift(1) == 1)
    data['SellSignal'] = (data['Trend'] == 1) & (data['Trend'].shift(1) == 0)
    return data

fonk = "custom_indicatorv2"
