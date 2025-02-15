import sqlite3
import pandas as pd
import requests
import ccxt  # Binance API library

from cripto_bot_v1.sql.db_manager import get_db_path


def get_all_possible_symbols():
    """Fetch a list of all possible cryptocurrency symbols paired with USDT from Binance."""
    url = "https://api.binance.com/api/v3/exchangeInfo"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        symbols = data.get("symbols", [])

        # Filter for symbols that are trading with USDT only
        usdt_symbols = [symbol['symbol'] for symbol in symbols if 'USDT' in symbol['symbol']]

        # Return the filtered symbols, removing the 'USDT' part to get only the base symbols (e.g., BTCUSDT -> BTC)
        return usdt_symbols
    else:
        print("Failed to fetch Binance data.")
        return []


class DatabaseManager:
    def __init__(self, db_path='C:\\crypto_bot\\cripto_bot_v1\\crypto_data.db'):
        self.db_path = db_path

    def connect_db(self):
        return sqlite3.connect(self.db_path)

    def execute_query(self, query, params=None):
        """
        Genel bir SQL sorgusu çalıştırır ve sonucu bir pandas DataFrame olarak döndürür.
        """
        conn = None  # Başlangıçta bağlantıyı None olarak başlatıyoruz
        try:
            conn = self.connect_db()  # Yeni bağlantı oluşturuluyor
            if params:
                df = pd.read_sql_query(query, conn, params=params)
            else:
                df = pd.read_sql_query(query, conn)
        except Exception as e:
            print(f"SQL sorgusu sırasında hata oluştu: {e}")
            df = pd.DataFrame()
        finally:
            if conn:
                conn.close()  # Bağlantıyı her zaman kapatıyoruz, sadece conn tanımlandıysa

        return df

    def add_crypto_to_db(self, symbol, owned=0, enabled=False, score=0, buy_price=0, sell_price=0):
        conn = self.connect_db()  # Yeni bağlantı oluşturuluyor
        cursor = conn.cursor()

        # Kripto para daha önce eklenmiş mi kontrol et
        cursor.execute("SELECT * FROM cryptocurrencies WHERE symbol = ?", (symbol,))
        if cursor.fetchone() is None:
            try:
                # Yeni kripto para ekle
                cursor.execute(''' 
                    INSERT INTO cryptocurrencies (symbol, owned, enabled, score, buy_price, sell_price) 
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (symbol, owned, enabled, score, buy_price, sell_price))
                print(f"{symbol} veritabanına eklendi.")
            except Exception as e:
                print(f"{symbol} eklenirken hata oluştu: {e}")

        conn.commit()  # Değişiklikleri kaydediyoruz
        conn.close()  # Bağlantıyı kapatıyoruz

    def get_crypto_symbols_in_range(self, start_id, limit):
        conn = self.connect_db()  # Yeni bağlantı oluşturuluyor
        cursor = conn.cursor()

        query = """
            SELECT symbol 
            FROM cryptocurrencies
            WHERE id >= ? 
            LIMIT ? 
        """
        cursor.execute(query, (start_id, limit))

        symbols = cursor.fetchall()

        conn.close()  # Bağlantıyı kapatıyoruz

        return [symbol[0] for symbol in symbols]

    def fetch_data(self, crypto_symbol, start_index=0, num_data_points=60):
        """
        Veritabanından belirli bir kripto sembolüne ait fiyat verilerini çeker.

        Args:
            crypto_symbol (str): Çekilecek kripto sembolü.
            start_index (int): Başlangıç indeks numarası.
            num_data_points (int): Çekilecek veri sayısı.

        Returns:
            pd.DataFrame: Çekilen verileri içeren DataFrame.
        """
        conn = None  # Bağlantıyı başta None olarak tanımlıyoruz
        try:
            conn = self.connect_db()  # Yeni bağlantı oluşturuluyor
            # Kripto sembolünü kontrol et
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM cryptocurrencies WHERE symbol = ?', (crypto_symbol,))
            result = cursor.fetchone()

            if result:
                # Sembol bulundu, veri sorgusunu yap
                query = """
                    SELECT open, high, low, close, volume, timestamp 
                    FROM crypto_prices 
                    WHERE crypto_symbol = ? 
                    ORDER BY timestamp 
                    LIMIT ? OFFSET ?
                """
                # params'ı liste olarak geçiyoruz
                data = pd.read_sql_query(query, conn, params=[crypto_symbol, num_data_points, start_index])
            else:
                # Sembol bulunamadı
                print(f"{crypto_symbol} bulunamadı.")
                data = pd.DataFrame()
        except Exception as e:
            print(f"Veri çekme sırasında hata oluştu: {e}")
            data = pd.DataFrame()
        finally:
            if conn:
                conn.close()  # Bağlantıyı güvenli bir şekilde kapatıyoruz

        return data

    def get_owned_crypto_symbols(self, enabled_active):
        """Fetch all cryptocurrency symbols that are marked as owned, optionally filtering by enabled."""
        conn = self.connect_db()  # Yeni bağlantı oluşturuluyor
        cursor = conn.cursor()

        # "owned" değeri True olan sembolleri seçiyoruz, enabled_active'e göre filtre uyguluyoruz
        if enabled_active:
            query = "SELECT symbol FROM cryptocurrencies WHERE owned = 1 AND enabled = 1"
        else:
            query = "SELECT symbol FROM cryptocurrencies WHERE owned = 1"

        cursor.execute(query)

        owned_symbols = cursor.fetchall()
        conn.close()  # Bağlantıyı kapatıyoruz

        # Sadece sembol isimlerini döndürüyoruz
        return [symbol[0] for symbol in owned_symbols]

    def get_all_crypto_symbols(self, enabled_active):
        """Fetch all unique cryptocurrency symbols from the database, optionally filtering by enabled and owned."""
        conn = self.connect_db()  # Yeni bağlantı oluşturuluyor
        cursor = conn.cursor()

        # enabled_active'e göre filtre uyguluyoruz
        if enabled_active:
            query = """
            SELECT DISTINCT symbol 
            FROM cryptocurrencies 
            WHERE enabled = 1 OR owned = 1
            """
        else:
            query = "SELECT DISTINCT symbol FROM cryptocurrencies"

        cursor.execute(query)

        symbols = cursor.fetchall()
        conn.close()  # Bağlantıyı kapatıyoruz

        return [symbol[0] for symbol in symbols]

    def add_crypto_symbols(self, symbols):
        """Add cryptocurrency symbols to the database."""
        conn = self.connect_db()  # Yeni bağlantı oluşturuluyor
        cursor = conn.cursor()

        for symbol in symbols:
            # Check if the symbol already exists to prevent duplicates
            cursor.execute("SELECT id FROM cryptocurrencies WHERE symbol = ?", (symbol,))
            result = cursor.fetchone()

            if result:
                print(f"{symbol} zaten veritabanında mevcut.")
            else:
                # Insert with a default name (you can adjust this logic to fetch actual names if available)
                cursor.execute("INSERT INTO cryptocurrencies (symbol) VALUES (?)",
                               (symbol, symbol))  # Using the symbol itself as the name

        conn.commit()  # Değişiklikleri kaydediyoruz
        conn.close()  # Bağlantıyı kapatıyoruz
        print(f"Added {len(symbols)} new symbols.")


def check_usdt_pairs(db_manager):
    # Binance borsasına bağlan
    exchange = ccxt.binance()

    # Veritabanı bağlantısını kur
    conn = db_manager.connect_db()
    cursor = conn.cursor()

    # Tüm USDT çiftleri için başlangıç fiyatlarını al
    markets = exchange.fetch_tickers()

    for symbol, market_data in markets.items():
        if symbol.endswith('/USDT'):  # Sadece USDT çiftlerini kontrol et
            current_price = market_data.get('last')
            volume = market_data.get('quoteVolume')  # Volume bilgisi

            if current_price is None:
                print(f"{symbol} için fiyat bilgisi mevcut değil, atlanıyor...")
                continue

            name = symbol.replace('/USDT', '')

            # Kripto para sembolünün cryptocurrencies tablosunda olup olmadığını kontrol et
            cursor.execute('SELECT id FROM cryptocurrencies WHERE symbol = ?', (name,))
            result = cursor.fetchone()

            if not result:
                # Sembol yoksa ekle
                cursor.execute('INSERT INTO cryptocurrencies (symbol,owned,enabled,score) VALUES (?,?,?,?)',
                               (name, False, True, 0))
                print(f"{name} veritabanına eklendi.")

            # Kripto para veritabanında varsa fiyat tablosunu güncelle
            cursor.execute(''' 
                INSERT INTO crypto_prices (crypto_symbol, open, high, low, close, volume, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (crypto_symbol, timestamp) DO UPDATE SET
                    open=excluded.open,
                    high=excluded.high,
                    low=excluded.low,
                    close=excluded.close,
                    volume=excluded.volume
            ''', (name,
                  market_data['open'],
                  market_data['high'],
                  market_data['low'],
                  current_price,
                  volume,
                  market_data['timestamp']))

    # Değişiklikleri kaydet ve bağlantıyı kapat
    conn.commit()
    conn.close()
    print("Veriler güncellendi.")


def main():
    db_manager = DatabaseManager(get_db_path())

    # Call the check_usdt_pairs function to update database with USDT pairs
    check_usdt_pairs(db_manager)

    # Fetch all crypto symbols and print them
    all_symbols = db_manager.get_all_crypto_symbols()
    count = 0
    if all_symbols:
        print("Tüm Kripto Sembolleri:")
        for symbol in all_symbols:
            count += 1
            print(f"{count} {symbol}")
    else:
        print("Veritabanında hiçbir kripto sembolü bulunamadı.")


if __name__ == "__main__":
    main()
