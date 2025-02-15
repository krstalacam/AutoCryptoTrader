# init_db.py

import db_manager
from db_manager import create_main_table, create_price_table, connect_db


def initialize_db():
    # Ana tabloyu ve fiyat tablosunu oluştur
    create_main_table()
    create_price_table()

    # Örnek kripto verileri
    initial_cryptos = [
        {"symbol": "BTC", "name": "Bitcoin", "owned": False, "enabled": True},
        {"symbol": "ETH", "name": "Ethereum", "owned": False, "enabled": True},
        {"symbol": "APE", "name": "ApeCoin", "owned": False, "enabled": True},


    ]

    conn = connect_db()
    """
    cursor = conn.cursor()

    # Her kripto parayı `cryptocurrencies` tablosuna ekle
    for crypto in initial_cryptos:
        cursor.execute('''
        INSERT OR IGNORE INTO cryptocurrencies (symbol, name, owned, enabled)
        VALUES (?, ?, ?, ?)
        ''', (crypto["symbol"], crypto["name"], crypto["owned"], crypto["enabled"]))

    conn.commit()
    conn.close()
    print("Veritabanı başlatıldı ve örnek veriler eklendi.")
    """


if __name__ == "__main__":
    db_manager.create_main_table()  # cryptocurrencies tablosunu oluşturur
    db_manager.create_price_table()  # crypto_prices tablosunu oluşturur
    initialize_db()
