import json
import os


class CryptoOrdersManager:
    __base_dir = "C:/crypto_bot/cripto_bot_v1/binance_bot"
    __crypto_orders_file = os.path.join(__base_dir, "crypto_orders.json")

    def __init__(self, file_path=__crypto_orders_file):
        self.file_path = file_path
        self.data = []

    def load_json(self):
        """Load JSON data from file into the class's data variable."""
        try:
            with open(self.file_path, "r") as file:
                self.data = json.load(file)
                print("Data successfully loaded.")
                print(self.data)
        except FileNotFoundError:
            print("File not found, starting with a new dataset.")
            self.data = []

    def save_json(self):
        """Save the class's data variable to a file in JSON format."""
        with open(self.file_path, "w") as file:
            json.dump(self.data, file, indent=4)
            print("Data successfully saved.")

    def update_orders(self, symbol, buy_data=None, sell_data=None, score=None):
        """
        Update the orders for the specified crypto symbol.
        """
        # Find the record for the symbol
        record = next((item for item in self.data if item["symbol"] == symbol), None)

        if not record:
            print(f"No record found for {symbol}, creating new entry.")
            record = {"symbol": symbol, "orders": []}
            self.data.append(record)

        orders = record["orders"]

        if buy_data:
            # Check if there are unmatched buy orders
            for order in orders:
                if "buy" in order and "sell" not in order:
                    print(f"An unmatched buy order already exists for {symbol}, not adding another buy.")
                    return

            # If no unmatched buy exists, add a new buy order
            order = {"buy": {**buy_data, "score": score}}
            orders.append(order)
            print(f"Added new buy order for {symbol}: {order}")

        elif sell_data:
            # Check if there are unmatched sell orders
            for order in orders:
                if "sell" in order and "buy" not in order:
                    print(f"An unmatched sell order already exists for {symbol}, not adding another sell.")
                    return

            # Find the last unmatched buy and add the sell to it
            for order in orders:
                if "buy" in order and "sell" not in order:
                    order["sell"] = {**sell_data, "score": score}
                    print(f"Matched sell data to existing buy for {symbol}: {sell_data}")
                    return

            # If no unmatched buy is found, check for completed pairs
            completed = all("sell" in emir for emir in orders if "buy" in emir)
            if completed:
                print(f"All orders for {symbol} are complete. No additional sell will be added.")
                return

            # If no unmatched buy is found, add the sell as a separate order
            orders.append({"sell": {**sell_data, "score": score}})
            print(f"No unmatched buy found. Added sell data for {symbol}: {sell_data}")


def process_cryptos(removed_cryptos, added_cryptos):
    """
    Kaldırılan ve eklenen kriptoları işler ve JSON dosyasını günceller.

    Parameters:
    - removed_cryptos (list): List of dictionaries representing removed cryptos.
    - added_cryptos (list): List of dictionaries representing added cryptos.
    """

    def process_orders(cryptos, is_buy):
        for crypto in cryptos:
            symbol = crypto["symbol"]
            order_data = {"price": crypto["price"], "time": crypto["time"]}
            score = crypto.get("score")
            if is_buy:
                print(f"Processing added crypto: {symbol}")
                manager.update_orders(symbol, buy_data=order_data, score=score)
            else:
                print(f"Processing removed crypto: {symbol}")
                manager.update_orders(symbol, sell_data=order_data, score=score)

    manager = CryptoOrdersManager()
    manager.load_json()

    # Process added (buy) and removed (sell) cryptos
    process_orders(added_cryptos, is_buy=True)
    process_orders(removed_cryptos, is_buy=False)

    # Save updates to the JSON file
    manager.save_json()

# Example usage function
def example_usage():
    # Example removed and added cryptos
    removed_cryptos = [
        {"symbol": "ALGO", "price": 0.011, "time": "2024-12-02 23:21:00", "score": 70}
    ]

    added_cryptos = [
        {"symbol": "ALGO", "price": 0.0533, "time": "2024-12-02 23:22:00", "score": 90}
    ]

    # Process cryptos
    process_cryptos(removed_cryptos, added_cryptos)


# Run example
if __name__ == "__main__":
    example_usage()
