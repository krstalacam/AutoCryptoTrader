from cripto_bot_v1.binance_bot.CryptoOrdersManager import process_cryptos
from cripto_bot_v1.binance_bot.binance_bot import CryptoBot
from cripto_bot_v1.website_app.data_manager import get_crypto_close


def set_orders(symbol, order_type):
    crypto_info = get_crypto_close(symbol)
    added_crypto = []
    removed_crypto = []

    # Eğer price ve time eksikse, 'N/A' değerini kullan
    price = crypto_info.get("price", 'N/A')
    timestamp = crypto_info.get("timestamp", 'N/A')

    # Verilen formata uygun şekilde buy_data ve sell_data oluştur
    order_data = {
        'symbol': symbol,
        'price': price,
        'time': timestamp
    }

    if order_type:
        # Process added cryptos
        added_crypto.append(order_data)
        print(f"test Processing added crypto: {symbol}   {order_data}")
    else:
        # Process removed cryptos
        removed_crypto.append(order_data)
        print(f"test Processing removed crypto: {symbol}  {order_data}")

    process_cryptos(removed_crypto, added_crypto)


def run_crypto_trading(symbol, order_type):
    # Kullanıcıdan işlem açılmasını bekle
    print("Trading App: İşlem açılmasını bekliyor...")

    # Al/Sat işlemleri
    bot = CryptoBot()  # Initialize the bot

    if order_type:
        bot.sell_asset(symbol, 100)  # %100 ünü yani tamamini sat
    else:
        bot.buy_asset(symbol, 100)  # 100 dolarlik satin al
    print("Trading App: İşlemler tamamlandı.")


def manual_trade(symbol, order_type, trade_active=True):
    print("test")
    if order_type is not None:
        set_orders(symbol, order_type)

        if trade_active:
            run_crypto_trading(symbol, order_type)
        print("İşlem başarılı")
    else:
        print("hata oluştu")
