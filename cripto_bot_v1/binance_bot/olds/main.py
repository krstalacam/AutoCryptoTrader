import time
from cripto_bot_v1.binance_bot.olds.CryptoRanker import CryptoRanker

def main_loop():
    operations = CryptoRanker()

    # Add initial data
    initial_data = [
        {"symbol": "BTC", "volume": 2500, "ma25_angle": 6},
        {"symbol": "ETH", "volume": 2500, "ma25_angle": 5},
        {"symbol": "ADA", "volume": 2500, "ma25_angle": 4},
        {"symbol": "DOGE", "volume": 2500, "ma25_angle": 33},
        {"symbol": "XRP", "volume": 2500, "ma25_angle": 2},
        {"symbol": "2", "volume": 2500, "ma25_angle": 15},
        {"symbol": "3", "volume": 2500, "ma25_angle": 14},
        {"symbol": "4", "volume": 2500, "ma25_angle": 13},
        {"symbol": "5", "volume": 2500, "ma25_angle": 12},
        {"symbol": "6", "volume": 2500, "ma25_angle": 11},
        {"symbol": "7", "volume": 2500, "ma25_angle": 10},
        {"symbol": "8", "volume": 2500, "ma25_angle": 9},
        {"symbol": "9", "volume": 2500, "ma25_angle": 8},
        {"symbol": "10", "volume": 2500, "ma25_angle": 7},
        {"symbol": "1", "volume": 2500, "ma25_angle": 16},
        {"symbol": "a", "volume": 2500, "ma25_angle": 1},
        {"symbol": "b", "volume": 2500, "ma25_angle": 50},
    ]

    # Add initial data to low priority queue
    for data in initial_data:
        operations.add_to_low_priority(data['volume'], data['ma25_angle'], data['symbol'])

    start_time = time.time()
    last_maintenance_time = 0

    while True:
        current_time = int(time.time() - start_time)

        # Perform periodic maintenance every 10 seconds
        if current_time - last_maintenance_time >= 10:
            print(f"\n=== Maintenance at {current_time} seconds ===")
            operations.periodic_maintenance()
            operations.print_queues()
            last_maintenance_time = current_time

        # Specific actions at defined times
        if current_time == 5:
            print("\n=== 5s: Adding SOL, removing BTC ===")
            operations.add_to_low_priority(2500, 35, "SOL")
            operations.remove_from_low_priority("BTC")

        if current_time == 15:
            print("\n=== 15s: Adding DOGE ===")
            operations.add_to_low_priority(2500, 40, "DOGE")
        if current_time == 25:
            print("\n=== 15s: Adding DOGE ===")
            operations.remove_from_low_priority("DOGE")
        if current_time == 35:
            print("\n=== 15s: Adding DOGE ===")
            operations.add_to_low_priority(2500, 40, "DOGE")

        if current_time == 70:
            print("\n=== Test complete. Stopping loop. ===")
            break

if __name__ == "__main__":
    main_loop()
