import ccxt
import pandas as pd
import numpy as np
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


    return all_ohlcv


def calculate_atr(data, period=100):
    """ ATR hesaplama fonksiyonu """
    high = data['High']
    low = data['Low']
    close = data['Close']

    tr1 = high - low
    tr2 = np.abs(high - close.shift(1))
    tr3 = np.abs(low - close.shift(1))

    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    return atr


def enhanced_halftrend_indicator(data, amplitude=2, atr_period=100, momentum_period=10):
    """ İyileştirilmiş HalfTrend göstergesi hesaplama fonksiyonu """

    data['ATR'] = calculate_atr(data, period=atr_period) / 2
    atr = data['ATR'].to_numpy()
    trend = np.zeros(len(data))
    up = np.zeros(len(data))
    down = np.zeros(len(data))
    max_low_price = np.full(len(data), np.nan)
    min_high_price = np.full(len(data), np.nan)

    # Başlangıç değerleri
    max_low_price[0] = data['Low'].iloc[0]
    min_high_price[0] = data['High'].iloc[0]

    # Momentum ve hareketli ortalama ekleyelim
    data['Momentum'] = data['Close'].diff(momentum_period)
    data['Short_MA'] = data['Close'].rolling(window=10).mean()

    for i in range(1, len(data)):
        high_price = data['High'][i - amplitude:i + 1].max()
        low_price = data['Low'][i - amplitude:i + 1].min()

        # Trendin yönü ve HalfTrend çizgisi
        if trend[i - 1] == 0:
            max_low_price[i] = max(low_price, max_low_price[i - 1])
            if data['Close'].iloc[i] < data['Low'].iloc[i - 1] and data['High'].rolling(window=amplitude).mean().iloc[
                i] < max_low_price[i]:
                trend[i] = 1
                min_high_price[i] = high_price
            else:
                min_high_price[i] = min(high_price, min_high_price[i - 1])
        else:
            min_high_price[i] = min(high_price, min_high_price[i - 1])
            if data['Close'].iloc[i] > data['High'].iloc[i - 1] and data['Low'].rolling(window=amplitude).mean().iloc[
                i] > min_high_price[i]:
                trend[i] = 0
                max_low_price[i] = low_price

        if trend[i] == 0:
            up[i] = max_low_price[i] if np.isnan(up[i - 1]) else max(max_low_price[i], up[i - 1])
        else:
            down[i] = min_high_price[i] if np.isnan(down[i - 1]) else min(min_high_price[i], down[i - 1])

    data['HT'] = np.where(trend == 0, up, down)

    # Alım ve Satım sinyalleri
    data['Position'] = 0  # 0: Bekle, 1: Al, -1: Sat
    position = 0  # Kullanıcının mevcut pozisyonunu tutar
    balance = 100  # Başlangıç bakiyesi
    position_size = 0  # Pozisyondaki miktar

    for i in range(1, len(data)):
        if position == 0:  # Eğer pozisyon yoksa
            # Momentum pozitif, fiyat trendin altından yukarı çıkmaya başlamış ve hacim destekliyorsa alım sinyali üret
            if data['Momentum'].iloc[i] > 0 and data['Close'].iloc[i] > data['HT'].iloc[i] and data['Volume'].iloc[i] > \
                    data['Volume'].rolling(5).mean().iloc[i]:
                position_size = balance / data['Close'].iloc[i]  # Alım miktarını hesapla
                data.loc[data.index[i], 'Position'] = 1
                position = 1  # Pozisyon açıldı
                balance -= position_size * data['Close'].iloc[i] * 0.999  # İşlem ücreti ekle
                print(f"alış {data['Close'].iloc[i]}")

        elif position == 1:  # Pozisyon varsa
            # Fiyat HalfTrend çizgisinin altına düşüyorsa veya momentum zayıflıyorsa sat sinyali üret
            if data['Close'].iloc[i] < data['HT'].iloc[i] or data['Momentum'].iloc[i] < 0:
                balance += position_size * data['Close'].iloc[i] * 0.999  # İşlem ücreti çıkart
                data.loc[data.index[i], 'Position'] = -1
                position = 0
                position_size = 0
                print(f"satış {data['Close'].iloc[i]}")
    if position == 1:  balance += position_size * data['Close'].iloc[len(data)-1] * 0.999
    data['FinalBalance'] = balance  # Son bakiyeyi kaydet

    return data


# Veri çekme
# Veri çekme
symbol = 'METIS/USDT'
timeframe = '1m'
start_date = '2024-10-27 12:12:50'
end_date = '2024-10-28 16:57:05'

symbol = 'TROY/USDT'
timeframe = '1m'
start_date = '2024-10-28 04:00:00'
end_date = '2024-10-28 05:00:00'



ohlcv = fetch_binance_ohlcv(symbol, timeframe, start_date, end_date)

# OHLCV verisini DataFrame'e çevirme
data = pd.DataFrame(ohlcv, columns=['timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'])
data['timestamp'] = pd.to_datetime(data['timestamp'], unit='ms')
data.set_index('timestamp', inplace=True)

# HalfTrend Göstergesini Hesaplama
data = enhanced_halftrend_indicator(data)

# Grafik oluşturma
fig = go.Figure()

# Fiyat grafiği (kapanış fiyatı üzerinden çizilecek)
fig.add_trace(go.Scatter(
    x=data.index,
    y=data['Close'],
    mode='lines',
    name='Kapanış Fiyatı',
    line=dict(color='blue')
))

# HalfTrend göstergesi
fig.add_trace(go.Scatter(
    x=data.index,
    y=data['HT'],
    mode='lines',
    name='HalfTrend',
    line=dict(color='orange')
))

# Alım sinyalleri
fig.add_trace(go.Scatter(
    x=data[data['Position'] == 1].index,
    y=data['HT'][data['Position'] == 1],
    mode='markers',
    name='Alım Sinyali',
    marker=dict(color='green', size=10, symbol='triangle-up')
))

# Satım sinyalleri
fig.add_trace(go.Scatter(
    x=data[data['Position'] == -1].index,
    y=data['HT'][data['Position'] == -1],
    mode='markers',
    name='Satım Sinyali',
    marker=dict(color='red', size=10, symbol='triangle-down')
))

# Toplam karı gösterme
final_balance = data['FinalBalance'].iloc[-1]
profit_loss = final_balance - 100  # Başlangıç bakiyesi 100 dolar
profit_loss_text = f'Toplam Kar/Zarar: ${profit_loss:.2f}'

# Grafik ayarları
fig.update_layout(
    title=f'{symbol} HalfTrend Göstergesi - {profit_loss_text}',
    xaxis_title='Tarih',
    yaxis_title='Fiyat',
    legend=dict(x=0, y=1),
    template='plotly',
)

fig.show()
