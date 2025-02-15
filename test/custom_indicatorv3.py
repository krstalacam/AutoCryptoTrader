import pandas as pd
import numpy as np

# ATR calculation (using Pandas)
def calculate_atr(data, period):
    high_low = data['High'] - data['Low']
    high_close = np.abs(data['High'] - data['Close'].shift())
    low_close = np.abs(data['Low'] - data['Close'].shift())

    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    return atr

# SMA calculation (using Pandas)
def sma(series, period):
    return series.rolling(window=period).mean()

# HalfTrend calculation function
def calculate_signals(data, amplitude, channel_deviation):
    atr2 = calculate_atr(data, 100) / 2
    dev = channel_deviation * atr2

    data['HighMA'] = sma(data['High'], amplitude)
    data['LowMA'] = sma(data['Low'], amplitude)

    data['MaxLowPrice'] = data['Low'].rolling(window=amplitude).min().shift(1)
    data['MinHighPrice'] = data['High'].rolling(window=amplitude).max().shift(1)

    trend = 0
    next_trend = 1
    trends = []

    for i in range(len(data)):
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

        trends.append(trend)

    data['Trend'] = trends
    return data

# Improved signal generation function
def generate_signals(data, momentum_period=5, volume_threshold=1.5):
    # Calculate momentum
    data['Momentum'] = data['Close'].diff(momentum_period).rolling(window=momentum_period).mean()

    # Calculate average volume over the same period
    data['AverageVolume'] = data['Volume'].rolling(window=momentum_period).mean()

    # Define volume threshold for buy/sell signals
    data['VolumeSignal'] = data['Volume'] / data['AverageVolume']

    # Track if a buy signal has occurred
    data['HasBuySignal'] = False

    # Generate buy signals
    data['BuySignal'] = (data['Momentum'] > 0) & (data['VolumeSignal'] > volume_threshold)

    # Update HasBuySignal
    for i in range(len(data)):
        if i > 0:
            data.at[data.index[i], 'HasBuySignal'] = data['BuySignal'].iloc[i] or data['HasBuySignal'].iloc[i-1]

    # Generate sell signals only if there has been a previous buy signal
    data['SellSignal'] = (data['Momentum'] < 0) & (data['VolumeSignal'] > volume_threshold) & data['HasBuySignal']

    return data

# Example usage:
# df = pd.DataFrame({
#     'Close': [...],  # Closing prices
#     'Volume': [...],  # Trading volume
# })

# Apply the HalfTrend calculation
# df = calculate_halftrend(df, amplitude=2, channel_deviation=2)

# Apply the signal generation
# df = generate_signals(df)

# Print the results
# print(df[['Close', 'Momentum', 'AverageVolume', 'BuySignal', 'SellSignal']])

fonk = "custom_indicatorv3"
