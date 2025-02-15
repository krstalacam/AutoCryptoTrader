import ccxt
import sqlite3

from cripto_bot_v1.sql.db_manager import connect_db

# Binance borsasına bağlan
exchange = ccxt.binance()

# Yüzde değişim eşiği
count = 0


def check_usdt_pairs():
    global count  # count değişkenini global olarak kullanıyoruz
    # Veritabanı bağlantısını kur
    conn = connect_db()
    cursor = conn.cursor()

    # Tüm USDT çiftleri için başlangıç fiyatlarını al
    markets = exchange.fetch_tickers()

    # `None` fiyat dönen semboller için silme listesi
    symbols_to_remove = []

    for symbol, market_data in markets.items():
        if symbol.endswith('/USDT'):  # Sadece USDT çiftlerini kontrol et
            current_price = market_data['last']

            if current_price is None:
                print(f"{symbol} için fiyat bilgisi mevcut değil, siliniyor...")
                symbols_to_remove.append(symbol.replace('/USDT', ''))
                continue

            name = symbol.replace('/USDT', '')
            found = False

            # Eğer kripto para veritabanında varsa, güncellemeyi atla
            cursor.execute('SELECT * FROM cryptocurrencies WHERE symbol = ?', (name,))
            result = cursor.fetchone()

            if not result:
                # Eğer veritabanında yoksa, yeni bir kripto para ekle
                cursor.execute('''
                    INSERT INTO cryptocurrencies (symbol, owned, enabled, score)
                    VALUES (?, ?, ?, ?)
                ''', (name, name, False, True))
                print(f"{symbol}: Eklendi.")

            count += 1

    # `None` fiyatı dönen sembolleri veritabanından kaldır
    for symbol in symbols_to_remove:
        cursor.execute('DELETE FROM cryptocurrencies WHERE symbol = ?', (symbol,))

    # Değişiklikleri kaydet ve bağlantıyı kapat
    conn.commit()
    conn.close()
    print(f"Toplam işlem yapılan kripto sayısı: {count}")


print("Start")
if __name__ == "__main__":
    check_usdt_pairs()
