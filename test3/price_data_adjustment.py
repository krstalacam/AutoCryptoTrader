import ccxt
import pandas as pd
import plotly.graph_objects as go

# Binance borsasına bağlan
exchange = ccxt.binance()


# Belirli tarih aralığında veri çek
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
        #exchange.sleep(500)  # 0.5 saniye uyuma

    return all_ohlcv

# RSI hesaplama fonksiyonu
def calculate_rsi(data, window=14):
    delta = data['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


# Al ve sat sinyallerini bulma fonksiyonu
def generate_signals(data):
    data['buy_signal'] = (data['rsi'] < 30)  # RSI 30'un altına düştüğünde AL sinyali
    data['sell_signal'] = (data['rsi'] > 70)  # RSI 70'in üstüne çıktığında SAT sinyali
    return data


# Tarih aralığını belirle
#start_date = '2024-10-22 21:30:00' # 23 30 2 SAAT kayma var
#end_date = '2024-10-23 10:00:00'

#start_date = '2024-10-19 16:30:00'  #  3 SAAT kayma var utc+3 oldugumuz icin
#end_date = '2024-10-20 09:00:00'

start_date = '2024-10-22 00:00:00'  #  3 SAAT kayma var utc+3 oldugumuz icin
end_date = '2024-10-24 00:00:00'
symbol ='TURBO/USDT'
# 1 dakikalık veriyi çek
ohlcv = fetch_binance_ohlcv(symbol, '1m', start_date, end_date)

# Veriyi DataFrame'e çevir
df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
df['timestamp'] = df['timestamp'].dt.tz_localize('UTC').dt.tz_convert('Europe/Istanbul')  # Zaman dilimini Türkiye'ye göre ayarlıyoruz

# RSI hesapla
df['rsi'] = calculate_rsi(df)

# Al ve sat sinyalleri oluştur
df = generate_signals(df)

# Fiyat grafiği
fig = go.Figure()

# Fiyat grafiği çizimi
fig.add_trace(go.Scatter(x=df['timestamp'], y=df['close'], mode='lines', name='Fiyat'))

# AL sinyallerini işaretleme (yeşil üçgen)
fig.add_trace(go.Scatter(x=df[df['buy_signal']]['timestamp'],
                         y=df[df['buy_signal']]['close'],
                         mode='markers',
                         marker=dict(symbol='triangle-up', size=10, color='green'),
                         name='Al Sinyali'))

# SAT sinyallerini işaretleme (kırmızı üçgen)
fig.add_trace(go.Scatter(x=df[df['sell_signal']]['timestamp'],
                         y=df[df['sell_signal']]['close'],
                         mode='markers',
                         marker=dict(symbol='triangle-down', size=10, color='red'),
                         name='Sat Sinyali'))

# RSI grafiği çizimi (İkinci eksen)

# Grafiğin düzeni
fig.update_layout(
    title=f'{symbol} Fiyat ve RSI İndikatörleri ile Al-Sat Sinyalleri',
    xaxis_title='Tarih',
    yaxis_title='Fiyat',
    xaxis_rangeslider_visible=True,  # Sağ-sol kaydırma çubuğu
    yaxis2=dict(
        title="RSI",
        overlaying="y",  # Aynı grafikte RSI'yi de göster
        side="right",
        range=[0, 100]  # RSI için aralık 0-100
    )
)

# Grafiği göster
fig.show()

# Veri tablosu
print(df[['timestamp', 'close', 'rsi', 'buy_signal', 'sell_signal']].tail(20))  # Son 20 satırı göster
