import ccxt
import pandas as pd
import plotly.graph_objects as go
from test2.custom_indicator import calculate_volatility, generate_volatility_signals  # Özel indikatör fonksiyonları

# Binance borsasına bağlan
exchange = ccxt.binance()


# Belirli tarih aralığında veri çekme fonksiyonu
def fetch_binance_ohlcv(symbol, timeframe, start_date, end_date):
    all_ohlcv = []
    since = exchange.parse8601(start_date)
    end_timestamp = exchange.parse8601(end_date)

    total_minutes = (end_timestamp - since) // 60000  # Dakika cinsinden süre

    while since < end_timestamp:
        # Eğer total_minutes sıfır veya negatifse döngüden çık
        if total_minutes <= 0:
            break

        # Kaç tane veri çekeceğimizi belirliyoruz, 1000'den fazla veri varsa
        # kalan dakikalara göre ya 1000 ya da daha az veri çekeceğiz
        current_limit = min(1000, total_minutes)

        ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, since=since, limit=current_limit)

        if not ohlcv:
            break

        all_ohlcv.extend(ohlcv)

        # Zamanı son çekilen veriden sonraki milisaniyeye güncelliyoruz
        since = ohlcv[-1][0] + 1

        # Kalan süreyi güncelliyoruz
        total_minutes = (end_timestamp - since) // 60000

        # API limitini aşmamak için uyku
        exchange.sleep(500)  # 0.5 saniye uyuma

    return all_ohlcv



# start_date = '2024-10-22 21:30:00' # 3 SAAT kayma var
# end_date = '2024-10-23 10:00:00'

#start_date = '2024-10-19 16:30:00'  #  3 SAAT kayma var utc+3 oldugumuz icin
#end_date = '2024-10-20 09:00:00'

start_date = '2024-10-22 00:00:00'  #  3 SAAT kayma var utc+3 oldugumuz icin
end_date = '2024-10-24 00:00:00'

# 1 dakikalık veriyi çek
symbol = 'TURBO/USDT'
ohlcv = fetch_binance_ohlcv(symbol, '1m', start_date, end_date)

# Veriyi DataFrame'e çevir
df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
# Zaman damgalarını UTC'den yerel zaman dilimine dönüştür
df['timestamp'] = df['timestamp'].dt.tz_localize('UTC').dt.tz_convert('Europe/Istanbul')  # Zaman dilimini Türkiye'ye göre ayarlıyoruz

# Özel volatilite indikatörünü hesapla
df = calculate_volatility(df)

# Al ve sat sinyalleri oluştur (Volatilite indikatörüne dayalı)
df = generate_volatility_signals(df)

# Fiyat ve sinyalleri göster
fig = go.Figure()

# Fiyat grafiği çizimi
fig.add_trace(go.Scatter(x=df['timestamp'], y=df['close'], mode='lines', name='Fiyat'))

# Al sinyalleri (Yeşil noktalar)
fig.add_trace(go.Scatter(x=df[df['buy_signal'] == 1]['timestamp'],
                         y=df[df['buy_signal'] == 1]['close'],
                         mode='markers',
                         marker=dict(color='green', size=10),
                         name='Al Sinyali'))

# Sat sinyalleri (Kırmızı noktalar)
fig.add_trace(go.Scatter(x=df[df['sell_signal'] == 1]['timestamp'],
                         y=df[df['sell_signal'] == 1]['close'],
                         mode='markers',
                         marker=dict(color='red', size=10),
                         name='Sat Sinyali'))

# Volatiliteyi de çiz (İkinci eksende)
fig.add_trace(go.Scatter(x=df['timestamp'], y=df['volatility'], mode='lines', name='Volatilite', yaxis='y2'))

# Grafiğin düzeni
fig.update_layout(
    title=f'{symbol} Fiyat ve Volatilite İndikatörü',
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

# Sinyalleri ve fiyat verilerini tablodan görebilirsiniz
print(df[['timestamp', 'close', 'volatility', 'buy_signal', 'sell_signal']].tail(20))
