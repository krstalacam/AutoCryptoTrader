import ccxt
import pandas as pd
import json
import plotly.graph_objects as go
from custom_indicatorv4 import calculate_signals, generate_signals

# Binance exchange setup
exchange = ccxt.binance()

# Load symbols from `crypto_data.json`
def load_symbols_from_json(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    symbols = [item['symbol'] + '/USDT' for item in data if item['enabled']]
    return symbols

# Fetch OHLCV data for a symbol
def fetch_binance_ohlcv(symbol, timeframe, start_date, end_date):
    all_ohlcv = []
    since = exchange.parse8601(start_date)
    end_timestamp = exchange.parse8601(end_date)

    total_minutes = (end_timestamp - since) // 60000

    while since < end_timestamp:
        if total_minutes <= 0:
            break

        current_limit = min(1000, total_minutes)

        ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, since=since, limit=current_limit)

        if not ohlcv:
            break

        all_ohlcv.extend(ohlcv)
        since = ohlcv[-1][0] + 1
        total_minutes = (end_timestamp - since) // 60000

        exchange.sleep(500)

    return all_ohlcv

# Calculate net profit for each symbol
def analyze_symbols(symbols, start_date, end_date, budget=100):
    symbol_profits = {}
    trade_amount = 1  # Fixed amount per trade
    total_trades = 0  # Total number of trades made

    for symbol in symbols:
        try:
            # Fetch data
            ohlcv = fetch_binance_ohlcv(symbol, '1m', start_date, end_date)
            data = pd.DataFrame(ohlcv, columns=['timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'])
            data['timestamp'] = pd.to_datetime(data['timestamp'], unit='ms')
            data.set_index('timestamp', inplace=True)

            # Calculate indicators and signals
            amplitude = 2
            channel_deviation = 2
            data = calculate_signals(data, amplitude, channel_deviation)
            data = generate_signals(data)

            # Extract buy and sell prices
            buy_prices = data[data['BuySignal'] == True]['Close'].values
            sell_prices = data[data['SellSignal'] == True]['Close'].values
            paired_trades = min(len(buy_prices), len(sell_prices))

            # Calculate total gross profit and fees
            total_gross_profit = 0
            for i in range(paired_trades):
                buy_price = buy_prices[i]
                sell_price = sell_prices[i]

                # Calculate profit for this trade
                profit = (sell_price - buy_price) * trade_amount
                total_gross_profit += profit
                total_trades += 1  # Count this trade

            # Calculate total fees (0.1% per trade)
            total_fee = total_trades * trade_amount * 0.001  # 0.1% of the total trades

            # Calculate net profit
            net_profit = (total_gross_profit - total_fee) * (budget / trade_amount)
            symbol_profits[symbol] = net_profit

        except Exception as e:
            print(f"Error processing {symbol}: {e}")

    # Sort by profit and get top 10
    top_symbols = sorted(symbol_profits.items(), key=lambda x: x[1], reverse=True)[:10]
    return top_symbols

# Visualization for a single symbol with buy/sell signals and profit
def visualize_symbol(symbol, profit, start_date, end_date):
    ohlcv = fetch_binance_ohlcv(symbol, '1m', start_date, end_date)
    data = pd.DataFrame(ohlcv, columns=['timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'])
    data['timestamp'] = pd.to_datetime(data['timestamp'], unit='ms')
    data.set_index('timestamp', inplace=True)

    # Calculate signals for display
    data = calculate_signals(data, 2, 2)
    data = generate_signals(data)

    # Create figure
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(x=data.index, y=data['Close'], mode='lines', name=f'{symbol} (Profit: ${profit:.2f})')
    )
    fig.add_trace(go.Scatter(x=data[data['BuySignal'] == True].index, y=data[data['BuySignal'] == True]['Close'],
                             mode='markers', marker=dict(color='green', size=10), name=f'{symbol} Buy'))
    fig.add_trace(go.Scatter(x=data[data['SellSignal'] == True].index, y=data[data['SellSignal'] == True]['Close'],
                             mode='markers', marker=dict(color='red', size=10), name=f'{symbol} Sell'))

    fig.update_layout(title=f"{symbol} - Net Profit: ${profit:.2f}", xaxis_title='Date', yaxis_title='Price')
    fig.show()

# Main workflow
start_date = '2024-10-19 18:30:00'  # Adjust as needed for your timezone
end_date = '2024-10-20 01:00:00'
json_file = '../cripto_bot_v1/crypto_data.json'
symbols = load_symbols_from_json(json_file)

top_symbols = analyze_symbols(symbols, start_date, end_date, budget=100)
print("Top 10 Cryptocurrencies by Net Profit:")
for symbol, profit in top_symbols:
    print(f"{symbol}: ${profit:.2f}")

# Visualize each of the top 10 results individually
for symbol, profit in top_symbols:
    visualize_symbol(symbol, profit, start_date, end_date)
