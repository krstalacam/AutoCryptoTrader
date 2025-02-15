import ccxt
import pandas as pd
import time

# Binance borsa nesnesini oluştur
exchange = ccxt.binance()

# Belirli bir kripto para çiftinin (örneğin BTC/USDT) mum verilerini çek
symbol = 'APE/USDT'
timeframe = '1s'  # 1 dakika
limit = 5  # Çekilecek mum sayısı

while True:
    # Mum verilerini çek
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)

    # Verileri pandas DataFrame'e dönüştür
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])

    # Zaman damgasını okunabilir formata çevir
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

    # Sonuçları yazdır
    print(df)

    # 1 saniye bekle (veya istediğiniz süre)
    time.sleep(2)
