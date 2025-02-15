import os
import sqlite3

__base_dir = "C:/crypto_bot/cripto_bot_v1"
__db_path = os.path.join(__base_dir, "crypto_data.db")

def connect_db():
    return sqlite3.connect(__db_path)


def get_db_path():
    return __db_path


# Ana tabloyu oluşturur
def create_main_table():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS cryptocurrencies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol TEXT UNIQUE,
        owned BOOLEAN,
        enabled BOOLEAN,
        score INTEGER,
        buy_price INTEGER,
        sell_price INTEGER

    );
    ''')
    conn.commit()
    conn.close()
    print("Ana tablo başarıyla oluşturuldu.")


# Fiyat verileri tablosunu oluşturur
def create_price_table():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS crypto_prices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        crypto_symbol TEXT,
        open REAL,
        high REAL,
        low REAL,
        close REAL,
        volume INTEGER, 
        timestamp DATETIME,
        FOREIGN KEY (crypto_symbol) REFERENCES cryptocurrencies(symbol),
        UNIQUE (crypto_symbol, timestamp)  -- Benzersiz anahtar
    );
    ''')
    conn.commit()
    conn.close()
    print("Fiyat verileri tablosu başarıyla oluşturuldu.")
