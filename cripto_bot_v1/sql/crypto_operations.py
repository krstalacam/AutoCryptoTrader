from cripto_bot_v1.sql.db_manager import connect_db


# Yeni bir kripto para ekler
def add_crypto(symbol, owned, enabled, score):
    conn = connect_db()
    cursor = conn.cursor()

    # Kripto parayı ekle
    cursor.execute(''' 
    INSERT OR IGNORE INTO cryptocurrencies (symbol, owned, enabled, score)
    VALUES (?, ?, ?, ?)
    ''', (symbol, owned, enabled, score))

    conn.commit()
    conn.close()
    print(f"{symbol} başarıyla eklendi.")


# Fiyat verisini crypto_prices tablosuna ekler (aynı veri tekrar eklenmesin)
def insert_price_data(symbol, open_price, high_price, low_price, close_price, volume, timestamp):
    conn = connect_db()
    cursor = conn.cursor()

    try:
        # Fiyat verisini ekle (Veritabanı, aynı timestamp ve crypto_symbol kombinasyonunu engelleyecek)
        cursor.execute('''
        INSERT OR IGNORE INTO crypto_prices (crypto_symbol, open, high, low, close, volume, timestamp)
        VALUES (?, ?, ?, ?, ?, ?,  ?)
        ''', (symbol, open_price, high_price, low_price, close_price, volume, timestamp))

        conn.commit()
        print(f"{symbol} için fiyat verisi eklendi.")

    except Exception as e:
        print(f"Veritabanı işlemi sırasında hata: {e}")
        conn.rollback()

    finally:
        conn.close()


# Eski verileri temizler
def cleanup_old_data(conn, cursor, symbol, max_records=600):
    """
    Belirtilen kripto para (symbol) için en fazla `max_records` kadar veri saklar.
    En eski veriler `timestamp` sütununa göre temizlenir.
    """
    cursor.execute(''' 
    DELETE FROM crypto_prices
    WHERE crypto_symbol = ? 
    AND id NOT IN (
        SELECT id FROM crypto_prices
        WHERE crypto_symbol = ? 
        ORDER BY timestamp DESC LIMIT ?
    )
    ''', (symbol, symbol, max_records))

    # print(f"{symbol} için eski veriler temizlendi.")


# Birden fazla fiyat verisi ekler ve eski verileri temizler
def insert_price_data_all(data):
    """
    Gelen fiyat verilerini `crypto_prices` tablosuna ekler.
    `volume` bilgisi de dahil edilmiştir.
    """
    conn = connect_db()
    cursor = conn.cursor()

    try:
        for d in data:
            # Fiyat verisini ekle
            cursor.execute('''
            INSERT OR IGNORE INTO crypto_prices (crypto_symbol, open, high, low, close, volume, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                d['symbol'],
                d['open_price'],
                d['high_price'],
                d['low_price'],
                d['close_price'],
                d['volume'],  # Volume alanı eklendi
                d['timestamp']
            ))

            # Temizlik işlemi (max_records=6000)
            cleanup_old_data(conn, cursor, d['symbol'], max_records=600)

        conn.commit()
        print("Tüm fiyat verileri başarıyla eklendi.")
    except Exception as e:
        print(f"Veritabanı işlem hatası: {e}")
        conn.rollback()
    finally:
        conn.close()


def update_crypto_status_and_scores(removed_cryptos, added_cryptos):
    """
    Tablodaki owned ve score sütunlarını günceller.
    removed_cryptos için owned False ve score 0,
    added_cryptos için owned True ve belirtilen score atanır.
    """
    conn = connect_db()
    cursor = conn.cursor()

    # Removed cryptos için 'owned' alanını False yap ve 'score' alanını 0 yap
    for crypto in removed_cryptos:
        symbol = crypto['symbol']
        cursor.execute('''
        UPDATE cryptocurrencies
        SET owned = FALSE,
            score = 0
        WHERE symbol = ?;
        ''', (symbol,))
        print(f"Updated {symbol}: owned = False, score = 0 (removed).")

    # Added cryptos için 'owned' alanını True yap ve 'score' alanını güncelle
    for crypto in added_cryptos:
        symbol = crypto['symbol']
        score = crypto.get('score', 0)  # Score belirtilmemişse varsayılan olarak 0 kullan
        cursor.execute('''
        UPDATE cryptocurrencies
        SET owned = TRUE,
            score = ?
        WHERE symbol = ?;
        ''', (score, symbol))
        print(f"Updated {symbol}: owned = True, score = {score} (added).")

    conn.commit()
    conn.close()
    print("Owned ve score durumları başarıyla güncellendi.")
