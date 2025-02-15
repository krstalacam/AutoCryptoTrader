import json
import os

from binance.client import Client
from binance.exceptions import BinanceAPIException
import time


def read_api_credentials(file_path):
    """Read the API credentials from the JSON file."""
    try:
        with open(file_path, "r") as f:
            config = json.load(f)

        # Filter out any items with a "comment" key
        filtered_config = [
            item for item in config
            if "api_key" in item and "api_secret" in item
        ]

        if not filtered_config:
            print("No valid API credentials found.")
            exit()

        # Return the first set of API credentials
        api_key = filtered_config[0]["api_key"]
        api_secret = filtered_config[0]["api_secret"]
        return api_key, api_secret

    except FileNotFoundError:
        print(f"{file_path} dosyası bulunamadı.")
        exit()
    except json.JSONDecodeError:
        print(f"{file_path} dosyasında geçersiz JSON formatı.")
        exit()


def get_action():
    """Get the user's action (buy/sell/exit)."""
    while True:
        action = input("\nİşlem yapmak istiyor musunuz? ('Al', 'Sat' veya 'Çık' yazın): ").strip().lower()
        if action == 'çık':
            print("Program sonlandırılıyor...")
            return 'çık'
        if action in ['al', 'sat']:
            return action
        print("Hatalı giriş yaptınız. Lütfen 'Al' veya 'Sat' yazınız.")


def get_symbol():
    """Get the user's symbol and validate its existence."""
    while True:
        symbol = input(
            "Lütfen işlem yapmak istediğiniz kripto sembolünü giriniz (örneğin BTC): ").strip().upper() + "USDT"
        return symbol


def get_budget():
    """Get the user's budget for buying assets."""
    while True:
        try:
            budget = float(input("Alım yapmak için bütçenizi (USD cinsinden) giriniz: "))
            if budget <= 0:
                print("Geçersiz bütçe. Pozitif bir değer giriniz.")
            else:
                return budget
        except ValueError:
            print("Geçersiz giriş. Lütfen sayısal bir değer giriniz.")


def get_percentage():
    """Get the user's percentage for selling assets."""
    while True:
        try:
            percentage = int(input("Satmak istediğiniz yüzdelik oranı giriniz (1 - 100): "))
            if percentage < 1 or percentage > 100:
                print("Geçersiz yüzde. 1 ile 100 arasında bir değer giriniz.")
            else:
                return percentage
        except ValueError:
            print("Geçersiz giriş. Lütfen sayısal bir değer giriniz.")


class CryptoBot:
    __base_dir = "C:/crypto_bot/cripto_bot_v1"
    __config_file_path = os.path.join(__base_dir, "config.json")

    def __init__(self, config_file_path=__config_file_path):
        """Initialize the CryptoBot with the Binance client."""
        self.__api_key, self.__api_secret = read_api_credentials(config_file_path)
        self.__client = self.__create_client()

    def __create_client(self):
        """Create and return the Binance client."""
        print("Bilgisayar ayarlarından saat verilerini eşitlemeyi unutmayın!")
        client = Client(self.__api_key, self.__api_secret)

        # Time sync
        try:
            client.ping()
            server_time = client.get_server_time()
            time_offset = server_time['serverTime'] - int(time.time() * 1000)
            client.TIME_OFFSET = time_offset
            print("Binance bağlantısı başarılı!")
        except BinanceAPIException as e:
            print(f"API Hatası: {e}")
            exit()

        return client

    def control_symbol(self, symbol):
        try:
            # Check symbol validity
            return self.__client.get_symbol_info(symbol)  # If symbol is valid, return it

        except BinanceAPIException as e:
            print(f"Sembol geçersiz: {symbol}. Lütfen geçerli bir sembol giriniz. Hata: {e}")

    def get_balance(self, symbol):
        """Get the balance for the given asset symbol."""
        try:
            account_info = self.__client.get_account()
            asset = symbol[:-4]  # Extract asset from symbol (e.g., BTCUSDT -> BTC)
            for balance in account_info['balances']:
                if balance['asset'] == asset:
                    free_balance = float(balance['free'])
                    return free_balance
            return 0  # Return 0 if asset not found
        except BinanceAPIException as e:
            print(f"Varlık sorgulama hatası: {e}")
            return 0

    def buy_asset(self, symbol, budget_usd):
        symbol = symbol.upper()

        if not self.control_symbol(symbol):
            print("Böyle bir symbol bulunamadı.")
            return

        """Buy an asset with the given budget in USD."""
        try:
            # Get the price of the symbol
            price = self.__client.get_symbol_ticker(symbol=symbol)
            current_price = float(price['price'])

            # Get the symbol's LOT_SIZE information
            exchange_info = self.__client.get_symbol_info(symbol)
            lot_size_filter = next(f for f in exchange_info['filters'] if f['filterType'] == 'LOT_SIZE')
            min_qty = float(lot_size_filter['minQty'])
            step_size = float(lot_size_filter['stepSize'])

            # Calculate the quantity to buy and adjust to the LOT_SIZE
            quantity = budget_usd / current_price
            quantity = max(min_qty, (quantity // step_size) * step_size)

            if quantity < min_qty:
                print(f"Alım yapılamıyor: Minimum işlem miktarı {min_qty} {symbol}.")
                return None

            print(f"{budget_usd} USD ile {quantity} {symbol} alınacak.")

            # Place the market buy order
            order = self.__client.order_market_buy(
                symbol=symbol,
                quantity=quantity  # Rounded quantity
            )

            print(f"{symbol} alım emri başarıyla verildi!")
            return order

        except BinanceAPIException as e:
            print(f"Alım hatası: {e}")
            return None

    def sell_asset(self, symbol, percentage):
        symbol = symbol.upper()
        if not self.control_symbol(symbol):
            print("Böyle bir symbol bulunamadı.")
            return
        """Sell an asset at the market price."""
        try:
            # Get the balance of the asset to sell
            balance = self.get_balance(symbol)
            if balance <= 0:
                print(f"{symbol} için yeterli bakiye yok. Satış işlemi iptal edildi.")
                return None

            # Get the symbol's LOT_SIZE information
            exchange_info = self.__client.get_symbol_info(symbol)
            lot_size_filter = next(f for f in exchange_info['filters'] if f['filterType'] == 'LOT_SIZE')
            min_qty = float(lot_size_filter['minQty'])
            step_size = float(lot_size_filter['stepSize'])

            # Calculate the quantity to sell and adjust to the LOT_SIZE
            quantity_to_sell = balance * (percentage / 100)
            quantity_to_sell = max(min_qty, (quantity_to_sell // step_size) * step_size)

            if quantity_to_sell < min_qty:
                print(f"Satış yapılamıyor: Minimum işlem miktarı {min_qty} {symbol}.")
                return None

            print(f"{symbol} bakiyeniz: {balance}. Satılacak miktar (%{percentage}): {quantity_to_sell}")
            # Place the market sell order
            order = self.__client.order_market_sell(
                symbol=symbol,
                quantity=quantity_to_sell  # Rounded quantity
            )

            print(f"{symbol} satış emri başarıyla verildi!")
            return order

        except BinanceAPIException as e:
            print(f"Satış hatası: {e}")
            return None

    def display_balances(self):
        """Display all asset balances."""
        try:
            account_info = self.__client.get_account()
            print("\nHesabınızda bulunan varlıklar:")
            for balance in account_info['balances']:
                free_balance = float(balance['free'])
                locked_balance = float(balance['locked'])
                if free_balance > 0 or locked_balance > 0:
                    print(f"- {balance['asset']}: {free_balance} (Serbest), {locked_balance} (Kilitleme)")
        except BinanceAPIException as e:
            print(f"Bakiye sorgulama hatası: {e}")

    def get_usdt_balance(self):  # çalışıyor mu emin değilim
        """Get the total USDT balance (free + locked) in the account."""
        try:
            account_info = self.__client.get_account()

            for balance in account_info['balances']:
                if balance['asset'] == "USDT":
                    free_balance = float(balance['free'])
                    locked_balance = float(balance['locked'])
                    total_usdt_balance = free_balance + locked_balance
                    return total_usdt_balance

            return 0  # USDT bulunmazsa 0 döndür
        except BinanceAPIException as e:
            print(f"USDT bakiyesi sorgulama hatası: {e}")
            return 0


def crypto_trading_app(removed_cryptos, added_cryptos, budget=100, percentage=100):
    """
    Kontrol fonksiyonu: Eklenen ve çıkarılan kripto paraları kontrol eder.
    Binance üzerindeki sembollerin geçerliliğini kontrol eder, bakiye sorgular ve işlem yapar.
    """
    bot = CryptoBot()  # Initialize the bot


    print("\nÇıkarılan kriptolar kontrol ediliyor...")
    for crypto in removed_cryptos:
        symbol = crypto['symbol'] + "USDT"
        score = crypto['score']
        print(f"Kontrol edilen sembol: {symbol}, Puan: {score}")

        # Binance üzerinde sembolün geçerliliğini kontrol et
        if bot.control_symbol(symbol):
            print(f"{symbol} geçerli. Binance üzerinde kontrol ediliyor...")
            balance = bot.get_balance(symbol)
            print(f"{symbol} bakiyeniz: {balance} {symbol[:-4]}")

            # Satım işlemi (örneğin, puan 5 ve altındaysa)
            if balance > 0 and score <= 5:
                bot.sell_asset(symbol, percentage)

        else:
            print(f"{symbol} Binance üzerinde bulunamadı.")

    print("\nEklenen kriptolar kontrol ediliyor...")
    for crypto in added_cryptos:
        symbol = crypto['symbol'] + "USDT"
        score = crypto['score']
        print(f"Kontrol edilen sembol: {symbol}, Puan: {score}")

        # Binance üzerinde sembolün geçerliliğini kontrol et
        if bot.control_symbol(symbol):
            print(f"{symbol} geçerli. Binance üzerinde kontrol ediliyor...")
            balance = bot.get_balance(symbol)
            print(f"{symbol} bakiyeniz: {balance} {symbol[:-4]}")

            # Alım işlemi (örneğin, puan 8 ve üzeriyse)
            if score >= 6:
                bot.buy_asset(symbol, budget)

        else:
            print(f"{symbol} Binance üzerinde bulunamadı.")


def handle_buy_action(bot):
    """Handle the buy action for the user."""
    symbol = get_symbol()
    budget = get_budget()
    buy_order = bot.buy_asset(symbol, budget)
    if buy_order:
        print(f"{symbol} alım işlemi tamamlandı!")
    else:
        print(f"{symbol} alım işlemi başarısız oldu.")


def handle_sell_action(bot):
    """Handle the sell action for the user."""
    symbol = get_symbol()
    percentage = get_percentage()
    sell_order = bot.sell_asset(symbol, percentage)
    if sell_order:
        print(f"{symbol} satış işlemi tamamlandı!")
    else:
        print(f"{symbol} satış işlemi başarısız oldu.")


def process_action(bot):
    """Process the user's action based on the choice."""
    action = get_action()
    if action == 'çık':
        return False  # Exit if chosen
    if action == 'al':
        handle_buy_action(bot)
    elif action == 'sat':
        handle_sell_action(bot)
    return True  # Continue if action is completed


def main():
    """Main method to run the bot."""
    bot = CryptoBot()  # Initialize the bot

    # Display balances
    bot.display_balances()

    while True:
        try:
            # Process the user's action
            if not process_action(bot):
                break
        except KeyboardInterrupt:
            print("\nProgram sonlandırıldı.")
            quit()
        except Exception as e:
            print(f"\nBeklenmedik bir hata oluştu: {e}")


if __name__ == '__main__':
    main()  # Start the main loop
