import pandas as pd
import numpy as np
import ccxt
import plotly.graph_objects as go

# Binance'tan veri çekme fonksiyonu
exchange = ccxt.binance()

def fetch_binance_ohlcv(symbol, timeframe, start_date, end_date):
    all_ohlcv = []
    since = exchange.parse8601(start_date)
    end_timestamp = exchange.parse8601(end_date)

    total_minutes = (end_timestamp - since) // 60000

    while since < end_timestamp:
        if total_minutes <= 0:
            break

        current_limit = min(1000, total_minutes)

        ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, since=since, limit=current_limit)

        if not ohlcv:
            break

        all_ohlcv.extend(ohlcv)
        since = ohlcv[-1][0] + 1
        total_minutes = (end_timestamp - since) // 60000

        exchange.sleep(500)

    return all_ohlcv


# Veri çekme
symbol = 'SANTOS/USDT'
timeframe = '1m'
start_date = '2024-10-26 17:30:00'
end_date = '2024-10-28 15:32:00'

ohlcv = fetch_binance_ohlcv(symbol, timeframe, start_date, end_date)
data = pd.DataFrame(ohlcv, columns=['timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'])
data['timestamp'] = pd.to_datetime(data['timestamp'], unit='ms')
data.set_index('timestamp', inplace=True)

# HalfTrend İndikatörü Hesaplama
def halftrend_indicator(data, amplitude, channel_deviation):
    trend = np.zeros(len(data))
    max_low_price = np.zeros(len(data))
    min_high_price = np.zeros(len(data))
    up = np.zeros(len(data))
    down = np.zeros(len(data))

    atr2 = data['Close'].rolling(window=100).std() / 2  # Basit ATR hesaplama
    dev = channel_deviation * atr2

    for i in range(amplitude, len(data)):
        high_price = data['High'].iloc[i - amplitude:i].max()
        low_price = data['Low'].iloc[i - amplitude:i].min()

        if i == amplitude:
            max_low_price[i] = low_price
            min_high_price[i] = high_price
        else:
            max_low_price[i] = max(low_price, max_low_price[i - 1])
            min_high_price[i] = min(high_price, min_high_price[i - 1])

        if trend[i - 1] == 0 and data['Close'].iloc[i] < low_price:
            trend[i] = 1
            up[i] = high_price + dev.iloc[i]
        elif trend[i - 1] == 1 and data['Close'].iloc[i] > high_price:
            trend[i] = 0
            down[i] = low_price - dev.iloc[i]
        else:
            trend[i] = trend[i - 1]
            up[i] = up[i - 1] if trend[i] == 0 else high_price + dev.iloc[i]
            down[i] = down[i - 1] if trend[i] == 1 else low_price - dev.iloc[i]

    data['Trend'] = trend
    return data

data = halftrend_indicator(data, 2, 2)

# Alım ve satım sinyalleri
# Alım ve satım sinyalleri
data['Position'] = 0
initial_amount = 100
current_amount = initial_amount
in_position = False

for i in range(1, len(data)):
    # Alım koşulları
    if data['Close'].iloc[i] > data['Trend'].iloc[i] and not in_position:
        data.loc[data.index[i], 'Position'] = 1  # Use loc[] for assignment
        in_position = True
        buy_price = data['Close'].iloc[i]
        current_amount -= current_amount * 0.001  # Alım ücreti
    # Satım koşulları
    elif data['Close'].iloc[i] < data['Trend'].iloc[i] and in_position:
        data.loc[data.index[i], 'Position'] = -1  # Use loc[] for assignment
        in_position = False
        sell_price = data['Close'].iloc[i]
        profit = (sell_price - buy_price) * (current_amount / buy_price)
        current_amount += profit - current_amount * 0.001  # Satım ücreti

# Toplam kârı hesaplama
total_profit = current_amount - initial_amount

# Grafik oluşturma
fig = go.Figure()

# Fiyat grafiği (kapanış fiyatı üzerinden çizilecek)
fig.add_trace(go.Scatter(
    x=data.index,
    y=data['Close'],
    mode='lines',
    name='Fiyat',
    line=dict(color='blue')
))

# Alım sinyalleri
buy_signals = data[data['Position'] == 1]
sell_signals = data[data['Position'] == -1]

fig.add_trace(go.Scatter(
    x=buy_signals.index,
    y=buy_signals['Close'],
    mode='markers',
    name='Alım Sinyali',
    marker=dict(color='green', size=10, symbol='triangle-up')
))

fig.add_trace(go.Scatter(
    x=sell_signals.index,
    y=sell_signals['Close'],
    mode='markers',
    name='Satım Sinyali',
    marker=dict(color='red', size=10, symbol='triangle-down')
))

# Başlık ve düzenleme
fig.update_layout(title=f'Ticaret Grafiği - Toplam Kâr: ${total_profit:.2f}',
                  xaxis_title='Tarih',
                  yaxis_title='Fiyat (USDT)',
                  template='plotly_white')

fig.show()
