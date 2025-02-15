import sqlite3
import sys
import time
from concurrent.futures import as_completed

import ccxt
import threading
from datetime import datetime, timedelta
from queue import Queue
from concurrent.futures import ThreadPoolExecutor
from cripto_bot_v1.sql.crypto_operations import insert_price_data, cleanup_old_data
from cripto_bot_v1.website_app.data_manager import load_cryptos


def wait_for_next_minute():
    """Bir sonraki dakikaya kadar bekler."""
    now = datetime.now()
    next_minute = (now + timedelta(minutes=1)).replace(second=0, microsecond=0)
    wait_time = (next_minute - now).total_seconds()
    wait_extra = 2  # her ihtimale karsi 2 saniye ekstra bekleme yeni muma gectiginden emin olmak icin
    wait_time = wait_time + wait_extra

    print(f"Waiting {wait_time:.2f} seconds for the next minute...")

    time.sleep(wait_time)


class CryptoDataCollector:
    def __init__(self, num_workers=15):
        self.exchange = ccxt.binance()
        self.db_queue = Queue()
        self.lock = threading.Lock()
        self.count = 0
        self.running = True
        self.num_workers = num_workers
        self.executor = ThreadPoolExecutor(max_workers=self.num_workers)  # Sabit thread havuzu
        self.db_threads = []
    def increment_count(self):
        with self.lock:
            self.count += 1

    def reset_count(self):
        with self.lock:
            self.count = 0

    def fetch_data(self, crypto):
        symbol = crypto['symbol']
        data = []
        try:
            # Fetch 1-minute candlestick data
            ohlcv = self.exchange.fetch_ohlcv(symbol + '/USDT', '1m', limit=2)

            if ohlcv:
                last_candle = ohlcv[-2]
                open_price = last_candle[1]
                high_price = last_candle[2]
                low_price = last_candle[3]
                close_price = last_candle[4]
                usdt_volume = last_candle[5]

                timestamp = (datetime.utcfromtimestamp(last_candle[0] / 1000) + timedelta(hours=3)).replace(second=0,
                                                                                                            microsecond=0).strftime(
                    "%Y-%m-%d %H:%M:%S")

                data.append({
                    'symbol': symbol,
                    'open_price': open_price,
                    'high_price': high_price,
                    'low_price': low_price,
                    'close_price': close_price,
                    'volume': usdt_volume,
                    'timestamp': timestamp
                })

                print(f"{symbol}: {close_price} USD at {timestamp}, Volume: {usdt_volume} USDT")

                self.increment_count()

        except Exception as e:
            print(f"Error: {e}")

        if data:
            self.db_queue.put(data)

    def db_worker(self):
        while True:
            data = self.db_queue.get()
            if data is None:  # Kuyruğa "None" gelirse çıkış yap
                break
            try:
                for record in data:
                    insert_price_data(record['symbol'], record['open_price'], record['high_price'],
                                      record['low_price'], record['close_price'], record['volume'], record['timestamp'])
                    # Optionally, clean up old data
                    conn = sqlite3.connect('../crypto_data.db')
                    cursor = conn.cursor()
                    cleanup_old_data(conn, cursor, record['symbol'], max_records=600)
                    conn.commit()
                    conn.close()
            except sqlite3.OperationalError as e:
                print(f"Database error: {e}")
                time.sleep(1)
                self.db_queue.put(data)
            finally:
                self.db_queue.task_done()
    def fetch_and_save_data(self, cryptos):
        self.running = True
        futures = []

        # Görevleri thread pool içinde dağıt ve future objelerini sakla
        for crypto in cryptos:
            future = self.executor.submit(self.fetch_data, crypto)
            futures.append(future)

        # Tüm future'ların tamamlanmasını bekle
        for future in as_completed(futures):
            try:
                future.result()  # Eğer bir hata oluşursa burada yakalanabilir
            except Exception as e:
                print(f"Thread error: {e}")

        print("All threads have completed their tasks.")

    def start_data_collection(self):
        print("Starting data collection...")

        # Veritabanı işlemleri için sabit sayıda thread başlat
        self.db_threads = [threading.Thread(target=self.db_worker, daemon=True) for _ in range(5)]
        for db_thread in self.db_threads:
            db_thread.start()

        try:
            cryptos = load_cryptos()
            if not cryptos:
                print("No cryptos found. Please add them first.")
                return  # Eğer kripto listesi yoksa işlem başlatmadan dön
            self.fetch_and_save_data(cryptos)  # İşlerin tamamlanmasını bekliyor
            print("Data collection cycle completed.")
            # Worker thread'leri durdur
            # self.running = False
            # for _ in range(len(self.db_threads)):
            #     self.db_queue.put(None)  # Worker'lara çıkma sinyali gönder
            # self.db_queue.join()  # Queue'daki tüm işlerin tamamlanmasını bekle
            #
            # # ThreadPool'u kapat
            # self.executor.shutdown(wait=True)
            # quit(0)

        except KeyboardInterrupt:
            print("Program terminated by user.")
        finally:

            print("All resources have been cleaned up.")


def data_collector_app():
    collector = CryptoDataCollector(num_workers=15)  # Maksimum 15 işçi thread'i
    collector.start_data_collection()


# Example usage
if __name__ == "__main__":
    data_collector_app()
