import pandas as pd
import numpy as np


# ATR calculation
def calculate_atr(data, period):
    high_low = data['High'] - data['Low']
    high_close = np.abs(data['High'] - data['Close'].shift())
    low_close = np.abs(data['Low'] - data['Close'].shift())
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = tr.rolling(period).mean()
    return atr


# SMA calculation
def sma(series, period):
    return series.rolling(window=period).mean()


# Calculate BBTrend-based signals
def calculate_signals(data, amplitude):
    short_length, long_length, std_dev_mult = 10, 70, 10.0
    short_middle = sma(data['Close'], short_length)
    long_middle = sma(data['Close'], long_length)

    # Short and Long Bollinger Bands
    short_upper = short_middle + std_dev_mult * data['Close'].rolling(short_length).std()
    short_lower = short_middle - std_dev_mult * data['Close'].rolling(short_length).std()
    long_upper = long_middle + std_dev_mult * data['Close'].rolling(long_length).std()
    long_lower = long_middle - std_dev_mult * data['Close'].rolling(long_length).std()

    # BBTrend Calculation
    data['BBTrend'] = (np.abs(short_lower - long_lower) - np.abs(short_upper - long_upper)) / short_middle * 100
    data['Trend'] = np.where(data['BBTrend'] > 0, 1, 0)
    return data


# Generate buy/sell signals based on trend changes
def generate_signals(data):
    data['BuySignal'] = (data['Trend'] == 1) & (data['Trend'].shift(1) == 0)
    data['SellSignal'] = (data['Trend'] == 0) & (data['Trend'].shift(1) == 1)
    return data


fonk = "custom_indicatorv4"
