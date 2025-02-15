import json
import logging
import os
from cripto_bot_v1.sql.db_manager import connect_db

__base_dir = "C:/crypto_bot/cripto_bot_v1/binance_bot"
CRYPTO_ORDERS_FILE = os.path.join(__base_dir, "crypto_orders.json")


def get_crypto_orders():
    if os.path.exists(CRYPTO_ORDERS_FILE):
        try:
            with open(CRYPTO_ORDERS_FILE, "r", encoding="utf-8") as file:
                return json.load(file)
        except json.JSONDecodeError as e:
            logging.error(f"JSON Decode Error: {e}")
            return []
    else:
        logging.warning("Crypto orders file not found!")
        return []


def get_crypto_closes():
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT crypto_symbol, close
        FROM crypto_prices
        WHERE (crypto_symbol, timestamp) IN (
            SELECT crypto_symbol, MAX(timestamp)
            FROM crypto_prices
            GROUP BY crypto_symbol
        )
    ''')
    data = cursor.fetchall()
    print(data[0])

    # Close fiyatlarını ve sembolleri döndür
    prices = [
        {"symbol": row[0], "close": row[1]}
        for row in data
    ]

    conn.close()
    return prices


def get_crypto_close(symbol):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT crypto_symbol, close, timestamp
        FROM crypto_prices
        WHERE crypto_symbol = ?
        ORDER BY timestamp DESC
        LIMIT 1
    ''', (symbol,))
    row = cursor.fetchone()

    conn.close()

    # Sembol için bir veri bulunmazsa None döner
    if row is None:
        return None

    # Sembolün kapanış fiyatı ve timestamp bilgisi
    return {"symbol": row[0], "price": row[1], "timestamp": row[2]}


# Kripto paraları veritabanından yükle
def load_cryptos():
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, symbol, owned, enabled, score
        FROM cryptocurrencies
        ORDER BY symbol;
    ''')
    data = cursor.fetchall()

    cryptos = [
        {
            "id": row[0],
            "symbol": row[1],
            "owned": bool(row[2]),
            "enabled": bool(row[3]),
            "score": bool(row[4]),
        }
        for row in data
    ]

    conn.close()
    return cryptos


def update_crypto_field(symbol, field, value):
    """
    Belirtilen kripto paranın belirtilen alanını günceller.
    """
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(
        f"UPDATE cryptocurrencies SET {field} = ? WHERE symbol = ?",
        (value, symbol),
    )
    conn.commit()
    conn.close()


def toggle_crypto_field(symbol, field):
    """
    Belirtilen kripto paranın belirtilen alanını (owned veya enabled) tersine çevirir.
    """
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(f"SELECT {field} FROM cryptocurrencies WHERE symbol = ?", (symbol,))
    current_value = cursor.fetchone()

    conn.close()

    if current_value is not None:
        new_value = not current_value[0]
        update_crypto_field(symbol, field, new_value)
        print(f"dede{not current_value[0]}")

    return not current_value[0]


def toggle_crypto_owned(symbol):
    action = toggle_crypto_field(symbol, "owned")
    return action


def toggle_crypto_enabled(symbol):
    toggle_crypto_field(symbol, "enabled")
