import ccxt
import pandas as pd
import plotly.graph_objects as go
from custom_indicatorv2 import calculate_signals, generate_signals, fonk

# Binance borsasına bağlanmak için ccxt kullanıyoruz
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

"""# Veri çekme
symbol = 'APE/USDT'
timeframe = '1m' #1s yapinca indikatorler dogru calismiyor sanirim ve 1 dakika iyi 1 anlik veriyi birden cok duserse diye kulllanilabilir belki ama o baska bir kod
start_date = '2024-10-19 16:30:00'  #  3 SAAT kayma var utc+3 oldugumuz icin
end_date = '2024-10-20 09:00:00'"""


symbol = 'TROY/USDT'
timeframe = '1m'
start_date = '2024-10-26 17:30:00'
end_date = '2024-10-28 15:32:00'

symbol = 'TROY/USDT'
timeframe = '1m'
start_date = '2024-10-28 04:30:00'
end_date = '2024-10-28 04:32:00'

#start_date = '2024-10-26 21:20:00'  #  3 SAAT kayma var utc+3 oldugumuz icin
#end_date = '2024-10-27 01:05:00'  #45 dk geriye bakmak yeterli sanirim

ohlcv = fetch_binance_ohlcv(symbol, timeframe, start_date, end_date)

# OHLCV verisini DataFrame'e çevirme
data = pd.DataFrame(ohlcv, columns=['timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'])
data['timestamp'] = pd.to_datetime(data['timestamp'], unit='ms')
data.set_index('timestamp', inplace=True)

# HalfTrend hesaplaması
amplitude = 2

data = calculate_signals(data, amplitude)

# Al/Sat sinyalleri oluşturma
data = generate_signals(data)




# Fiyat ve sinyalleri görselleştir
fig = go.Figure()

# Fiyat grafiği (kapanış fiyatı üzerinden çizilecek)
fig.add_trace(go.Scatter(
    x=data.index,
    y=data['Close'],
    mode='lines',
    name='Fiyat',
    line=dict(color='blue')
))

# Al sinyalleri (Yeşil noktalar)
fig.add_trace(go.Scatter(
    x=data[data['BuySignal'] == True].index,
    y=data[data['BuySignal'] == True]['Close'],
    mode='markers',
    marker=dict(color='green', size=10),
    name='Al Sinyali'
))

# Sat sinyalleri (Kırmızı noktalar)
fig.add_trace(go.Scatter(
    x=data[data['SellSignal'] == True].index,
    y=data[data['SellSignal'] == True]['Close'],
    mode='markers',
    marker=dict(color='red', size=10),
    name='Sat Sinyali'
))

fig.update_layout(
    title=f'{symbol} Fiyat ve Volatilite İndikatörü {fonk}',
    xaxis_title='Tarih',
    yaxis_title='Fiyat',
    yaxis2=dict(
        title="Volatilite",
        overlaying="y",  # Aynı grafikte göster
        side="right"
    ),
    xaxis_rangeslider_visible=True
)
# Grafiği göster
fig.show()

# Al/Sat sinyallerini gösterme
print(data[['Close', 'BuySignal', 'SellSignal']][data['BuySignal'] | data['SellSignal']])

