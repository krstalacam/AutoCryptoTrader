import sqlite3
import time
from datetime import datetime, timedelta

import ccxt
import threading
from cripto_bot_v1.sql.crypto_operations import insert_price_data_all
from cripto_bot_v1.website_app.data_manager import load_cryptos
from cripto_bot_v1.inducatorv_main.database_manager import DatabaseManager

from cripto_bot_v1.sql.db_manager import connect_db

# CCXT Binance borsa nesnesini oluştur
exchange = ccxt.binance()

# Kilit oluştur
db_lock = threading.Lock()


# Binance'dan OHLCV verilerini çeken fonksiyon
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


# Fiyat verilerini belirli bir zaman aralığında toplayan fonksiyon
def fetch_data(cryptos_batch, result_list):
    data = []
    for crypto in cryptos_batch:
        symbol = crypto['symbol']
        try:
            # Güncel zaman aralığı
            end_date = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())
            start_date = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(time.time() - 3600 * 10))  # Son 10 saat

            ohlcv_data = fetch_binance_ohlcv(symbol + '/USDT', '1m', start_date, end_date)

            for ohlcv in ohlcv_data:
                timestamp, open_price, high_price, low_price, close_price, volume = ohlcv

                # Zaman damgasına 3 saat ekle
                adjusted_time = datetime.utcfromtimestamp(timestamp / 1000) + timedelta(hours=3)
                adjusted_timestamp = adjusted_time.strftime("%Y-%m-%d %H:%M:%S")

                data.append({
                    'symbol': symbol,
                    'open_price': open_price,
                    'high_price': high_price,
                    'low_price': low_price,
                    'close_price': close_price,
                    'volume': volume,  # Volume verisi eklendi
                    'timestamp': adjusted_timestamp
                })
                print(f"{symbol}: {close_price} USD at {adjusted_timestamp}, Volume: {volume}")

        except Exception as e:
            print(f"Hata: {e}")

    # Kilit ile koruma altına alarak sonucu topluca result_list'e ekle
    with threading.Lock():
        result_list.extend(data)


# İş parçacıklarını (threads) oluşturup çalıştıran fonksiyon
def create_threads(cryptos):
    batch_size = 60
    threads = []
    result_list = []

    # 60'lık gruplar halinde kripto paraları iş parçacıklarına bölün
    for i in range(0, len(cryptos), batch_size):
        cryptos_batch = cryptos[i:i + batch_size]
        thread = threading.Thread(target=fetch_data, args=(cryptos_batch, result_list))
        thread.start()
        threads.append(thread)

    # Tüm iş parçacıklarının tamamlanmasını bekleyin
    for thread in threads:
        thread.join()

    # İş parçacıkları tamamlandığında tüm sonuçları tek seferde veritabanına ekle
    if result_list:
        # Kilit ile veritabanı işlemine eşzamanlı erişimi engelle
        with db_lock:
            insert_price_data_all(result_list)


# Veritabanındaki kripto sembollerini al


# Ana veri çekme fonksiyonu
def fetch_and_save_data(selected_crypto=None, start_id=None, end_id=None):
    cryptos = load_cryptos()

    if not cryptos:
        print("Veritabanında hiç kripto para bulunmuyor. Lütfen önce kripto paraları ekleyin.")
        return

    # Seçilen kripto para ile filtreleme
    if selected_crypto and selected_crypto != "ALL":
        cryptos = [crypto for crypto in cryptos if crypto['symbol'] == selected_crypto]

    # Eğer bir aralık belirtilmişse, veritabanından aralıktaki kripto sembollerini al
    if start_id and end_id:
        limit = end_id - start_id + 1
        cryptos = databaseManager.get_crypto_symbols_in_range(start_id, limit)
        cryptos = [{'symbol': symbol} for symbol in cryptos]

    # enabled değeri False olanları filtrele

    if not cryptos:
        print(f"{selected_crypto} sembolüne sahip kripto para bulunamadı.")
        databaseManager.add_crypto_to_db(selected_crypto)  # Yeni sembolü ekle
        cryptos = [{'symbol': selected_crypto}]  # Devam etmek için listeye ekle

        cryptos = [crypto for crypto in cryptos if crypto['enabled']]


    create_threads(cryptos)  # Verileri çek ve kaydet
    print("--------------------")


databaseManager = DatabaseManager()


def main():
    start_time = time.time()  # Program başlangıcında zaman damgası al
    selected_crypto = input(
        "Kaç tane kripto gireceksiniz? Hangi kripto paranın verisini almak istersiniz? (Örnek: BTC, ETH veya 'all' veya 'range' yazın) ").strip().upper()
    if selected_crypto == "RANGE":
        start_id = int(input("Başlangıç ID'sini girin: "))
        end_id = int(input("Bitiş ID'sini girin: "))
        fetch_and_save_data(start_id=start_id, end_id=end_id)
    else:
        try:
            fetch_and_save_data(selected_crypto=selected_crypto)  # Bir defa veriyi çek
        except KeyboardInterrupt:
            print("Program sonlandırıldı.")
            quit()

    end_time = time.time()  # Program bitişinde zaman damgası al
    elapsed_time = end_time - start_time  # Geçen süreyi hesapla
    print(f"Program toplamda {elapsed_time:.2f} saniye sürdü.")  # Konsola yazdır


if __name__ == "__main__":
    main()
