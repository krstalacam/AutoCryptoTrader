import sqlite3
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output

import sys  # Import sys for exiting the script


DB_PATH = '../crypto_data.db'


def connect_db():
    return sqlite3.connect(DB_PATH)


def fetch_data_from_db(crypto_symbol, start_index=0, num_data_points=60):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM cryptocurrencies WHERE symbol = ?', (crypto_symbol,))
    result = cursor.fetchone()

    if result:
        crypto_id = result[0]
        query = "SELECT open, high, low, close, interval_type FROM crypto_prices WHERE crypto_id = ? ORDER BY interval_type LIMIT ? OFFSET ?"
        data = pd.read_sql_query(query, conn, params=(crypto_id, num_data_points, start_index))
    else:
        print(f"{crypto_symbol} bulunamadı.")
        data = pd.DataFrame()

    conn.close()
    return data


def calculate_atr(data, period=2):
    high = data['high']
    low = data['low']
    close = data['close']
    tr1 = high - low
    tr2 = np.abs(high - close.shift(1))
    tr3 = np.abs(low - close.shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    return atr


app = Dash(__name__)

# Global variables
trade_signals = []
initial_balance = 100
data = pd.DataFrame()  # Global DataFrame for price data
position = 0  # Global position variable (0 = not holding, 1 = holding)
position_size = 0  # Global variable to keep track of position size
last_buy_price = 0  # Global variable to keep track of last buy price
total_profit_loss = 0  # Total profit/loss
trade_profit_loss = 0  # Profit/Loss from the last trade
selected_points = []  # To hold selected points for percentage calculation

# Initialize global variables for last figure, timestamp, and simulation flag
last_timestamp = None
last_figure = None
simulation_ended = False
def plot_data(data):
    global total_profit_loss, trade_profit_loss

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=data['interval_type'],
        y=data['close'],
        mode='lines',
        name='Kapanış Fiyatı',
        line=dict(color='blue')
    ))

    fig.add_trace(go.Scatter(
        x=data['interval_type'],
        y=data['ht'],
        mode='lines',
        name='HalfTrend',
        line=dict(color='orange')
    ))

    for signal_type, date, price in trade_signals:
        if signal_type == "Alış":
            fig.add_trace(go.Scatter(
                x=[date],
                y=[price],
                mode='markers',
                name='Alım Sinyali',
                marker=dict(color='green', size=10, symbol='triangle-up'),
                customdata=[price],
                hoverinfo='text',
                text=[f'AL: {price}']
            ))
        elif signal_type == "Satış":
            fig.add_trace(go.Scatter(
                x=[date],
                y=[price],
                mode='markers',
                name='Satım Sinyali',
                marker=dict(color='red', size=10, symbol='triangle-down'),
                customdata=[price],
                hoverinfo='text',
                text=[f'SAT: {price}']
            ))

    fig.add_annotation(
        text=f"Toplam Kar/Zarar: ${total_profit_loss:.2f}",
        xref="paper", yref="paper",
        x=0.5, y=1.15,
        showarrow=False,
        font=dict(size=16, color="darkgreen" if total_profit_loss >= 0 else "red")
    )

    fig.add_annotation(
        text=f"Son İşlem Kar/Zarar: ${trade_profit_loss:.2f}",
        xref="paper", yref="paper",
        x=0.5, y=1.1,
        showarrow=False,
        font=dict(size=16, color="darkgreen" if trade_profit_loss >= 0 else "red")
    )

    fig.update_layout(
        title='HalfTrend Göstergesi',
        xaxis_title='Tarih',
        yaxis_title='Fiyat',
        legend=dict(x=0, y=1),
        template='plotly'
    )

    return fig


@app.callback(
    Output('graph', 'figure'),
    Output('closing-price-output', 'children'),
    Input('interval-component', 'n_intervals'),
    prevent_initial_call=True
)



# Flag to indicate if the simulation has ended

def update_graph(n_intervals):
    global data, position, position_size, last_timestamp, last_figure, simulation_ended  # Declare global variables
    crypto_symbol = "LUMIA"
    num_data_points = 60
    start_index = n_intervals  # Use n_intervals to fetch updated data
    #if simulation_ended: app.
    try:
        # Initialize data only once at the start
        if n_intervals == 0:
            data = fetch_data_from_db(crypto_symbol, start_index, num_data_points)
            # Set last_timestamp to the second-to-last timestamp, if available
            last_timestamp = data['interval_type'].iloc[-2] if len(data) > 1 else data['interval_type'].iloc[-1]
        else:
            # Fetch new data from the database
            new_data = fetch_data_from_db(crypto_symbol, start_index, num_data_points)

            # Check if the simulation should end based on the second-to-last timestamp
            if not new_data.empty:
                new_last_timestamp = new_data['interval_type'].iloc[-2] if len(new_data) > 1 else new_data['interval_type'].iloc[-1]
                if new_last_timestamp == last_timestamp:
                    #print("Simülasyon Bitti.")  # Display end message
                    simulation_ended = True  # Set the flag to indicate simulation has ended

                    final_figure = plot_data(data.tail(num_data_points))
                    last_figure = final_figure  # Update last_figure with the final plot
                else:
                    last_timestamp = new_last_timestamp  # Update the last known timestamp

            if new_data.empty:
                print("Veri bulunamadı.")
                final_figure = plot_data(data.tail(num_data_points))
                last_figure = final_figure  # Keep the last valid figure
                return final_figure, "Veri bulunamadı."

            # Update the main data variable
            if 'interval_type' in new_data.columns:
                data = pd.concat([data, new_data]).drop_duplicates(subset=['interval_type']).reset_index(drop=True)
            else:
                print("Warning: 'interval_type' column is missing in new_data.")
                return last_figure if last_figure else go.Figure(), "Veri formatı hatası."  # Return last valid figure

        current_data = data.tail(num_data_points).copy()

        # Define the maximum number of trade signals to keep
        max_signals = 10  # Adjust this value as needed

        # Remove signals that are older than the last few data points
        trade_signals[:] = trade_signals[-max_signals:]

        balance, position, position_size, current_value, profit_loss = halftrend_indicator_single(
            current_data, initial_balance, position, position_size)

        figure = plot_data(current_data)
        last_figure = figure  # Store the last valid figure

        return figure, "Simülasyon Devam Ediyor..."

    except Exception as e:
        # Check if the simulation has already ended
        if simulation_ended:
            print("Simülasyon Bitti.v2")  # Print the end message
            return last_figure if last_figure else go.Figure(), "Simülasyon Bitti."  # Return last valid figure on error
        else:
            print(f"Error occurred: {e}")
            return last_figure if last_figure else go.Figure(), "Hata oluştu." # Return last valid figure on error
def halftrend_indicator_single(data, balance, position, position_size):
    global last_buy_price, total_profit_loss, trade_profit_loss
    last_data = data.iloc[-1]
    data['atr'] = calculate_atr(data) / 2
    trend = 0
    ht_values = []

    # Calculate HalfTrend values
    for i in range(len(data)):
        if i < 1:
            ht_values.append(np.nan)
            continue

        high_price = data['high'].iloc[i - 1]
        low_price = data['low'].iloc[i - 1]
        close_price = data['close'].iloc[i]

        if trend == 0:
            if close_price < low_price:
                trend = 1
                ht_values.append(high_price)
            else:
                ht_values.append(low_price)
        else:
            if close_price > high_price:
                trend = 0
                ht_values.append(low_price)
            else:
                ht_values.append(high_price)

    data['ht'] = ht_values

    # Trading logic with trend confirmation
    profit_loss = 0
    current_value = balance

    recent_trend = data['close'].iloc[-3:].mean() > data['ht'].iloc[-3:].mean()  # Trend confirmation

    if position == 0 and recent_trend and last_data['close'] > data['ht'].iloc[-1]:
        # Buy signal: Confirm trend and ensure recent closes are above HalfTrend
        position_size = balance / last_data['close']
        position = 1
        last_buy_price = last_data['close']
        balance -= position_size * last_data['close'] * 0.999  # Account for transaction cost
        trade_signals.append(("Alış", last_data['interval_type'], last_data['close']))
        print(f"Alım yapıldı.{last_data['close']}")

    elif position == 1 and (last_data['close'] < data['ht'].iloc[-1] or last_data['close'] > last_buy_price * 1.02):
        # Sell signal: price drops below HalfTrend or achieves profit threshold (e.g., 2% above buy price)
        profit_loss = (last_data['close'] - last_buy_price) * position_size  # Profit/Loss from trade
        balance += position_size * last_data['close'] * 0.999  # Update balance with sale
        position = 0
        position_size = 0
        last_buy_price = 0
        total_profit_loss += profit_loss
        trade_profit_loss = profit_loss
        trade_signals.append(("Satış", last_data['interval_type'], last_data['close']))
        print(f"Satım yapıldı. {last_data['close']}")

    # Update trade profit/loss for open positions
    if position == 1:
        trade_profit_loss = (last_data['close'] - last_buy_price) * position_size

    data['finalbalance'] = balance if position == 0 else current_value
    return balance, position, position_size, current_value, profit_loss


app.layout = html.Div([
    html.Div(id='profit-loss-output', style={'font-size': '30px', 'font-weight': 'bold', 'text-align': 'center', 'margin-bottom': '10px'}),
    html.Div(id='trade-profit-loss-output', style={'font-size': '16px', 'text-align': 'center', 'margin-bottom': '20px'}),
    dcc.Graph(id='graph', style={'width': '100%', 'height': '80vh', 'margin': 'auto'}),  # Full-width graph
    dcc.Interval(
        id='interval-component',
        interval=1 * 100,  # 100 milliseconds
        n_intervals=0
    ),
    html.Div(id='closing-price-output', style={'position': 'absolute', 'bottom': '10px', 'left': '10px', 'backgroundColor': 'white', 'padding': '10px'})  # Bottom left corner
])

if __name__ == '__main__':
    app.run_server(debug=True, port=8051)  # Change port if needed
