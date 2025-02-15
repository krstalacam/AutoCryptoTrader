import sqlite3
from cripto_bot_v1.sql.db_manager import get_db_path

# Veritabanı bağlantısını aç
db_path = get_db_path()
conn = sqlite3.connect(db_path)  # Veritabanı dosyasını uygun şekilde değiştirin
cursor = conn.cursor()

# Verilen semboller listesi
given_symbols = [
    'ADA', 'ALGO', 'ANKR', 'ATOM', 'BAND', 'BAT', 'BNB', 'BTC', 'CELR', 'CHZ',
    'COS', 'CVC', 'DASH', 'DENT', 'DOGE', 'DUSK', 'ENJ', 'EOS', 'ETC', 'FET',
    'FTM', 'FUN', 'HOT', 'ICX', 'IOST', 'IOTA', 'KEY', 'LINK', 'LTC', 'MTL',
    'NEO', 'NULS', 'ONE', 'ONG', 'ONT', 'QTUM', 'TFUEL', 'TRX', 'USDC', 'VET',
    'WAN', 'WIN', 'XLM', 'XRP', 'ZEC', 'ZIL', 'ZRX'
]

# Veritabanındaki mevcut semboller
cursor.execute("SELECT DISTINCT crypto_symbol FROM crypto_prices")
db_symbols = [row[0] for row in cursor.fetchall()]

# Veritabanında bulunmayan semboller
missing_symbols = [symbol for symbol in given_symbols if symbol not in db_symbols]

# Given listesinde olup veritabanında bulunmayan semboller
extra_db_symbols = [symbol for symbol in db_symbols if symbol not in given_symbols]

# Eksik semboller ve fazla olanlar
if missing_symbols:
    print("Veritabanında bulunmayan semboller:")
    for symbol in missing_symbols:
        print(symbol)
else:
    print("Tüm semboller veritabanında mevcut.")

if extra_db_symbols:
    print("\nVeritabanında olup da verilen listede olmayan semboller:")
    for symbol in extra_db_symbols:
        print(symbol)
else:
    print("Veritabanında verilen listede olmayan semboller yok.")

# Bağlantıyı kapat
conn.close()
