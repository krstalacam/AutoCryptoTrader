import sqlite3
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px  # Eklenen kütüphane
import time

DB_PATH = '../cripto_bot_v1/crypto_data.db'

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

def calculate_atr(data, period=14):
    high = data['high']
    low = data['low']
    close = data['close']
    tr1 = high - low
    tr2 = np.abs(high - close.shift(1))
    tr3 = np.abs(low - close.shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    return atr

# Global değişkenler
trade_signals = []
initial_balance = 100
selected_points = []  # Kullanıcının seçtiği noktaları saklamak için

def plot_data(data):
    global selected_points  # Global değişken olarak kullan

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
                marker=dict(color='green', size=10, symbol='triangle-up')
            ))
        elif signal_type == "Satış":
            fig.add_trace(go.Scatter(
                x=[date],
                y=[price],
                mode='markers',
                name='Satım Sinyali',
                marker=dict(color='red', size=10, symbol='triangle-down')
            ))

    # Yüzde farkı hesaplama
    if len(selected_points) == 2:
        price1 = data[data['interval_type'] == selected_points[0]]['close'].values[0]
        price2 = data[data['interval_type'] == selected_points[1]]['close'].values[0]
        percentage_diff = ((price2 - price1) / price1) * 100
        fig.add_annotation(
            text=f"Yüzde Fark: {percentage_diff:.2f}%",
            xref="paper", yref="paper",
            x=0.5, y=1.1,
            showarrow=True,
            arrowhead=2,
            ax=0,
            ay=-40,
            font=dict(size=16, color="black"),
            bgcolor="lightyellow"
        )

    final_balance = data['finalbalance'].iloc[-1]
    profit_loss = final_balance - initial_balance
    profit_loss_text = f'Toplam Kar/Zarar: ${profit_loss:.2f}'

    fig.update_layout(
        title=f'HalfTrend Göstergesi - {profit_loss_text}',
        xaxis_title='Tarih',
        yaxis_title='Fiyat',
        legend=dict(x=0, y=1),
        template='plotly',
        clickmode='event+select'  # Tıklama modunu etkinleştir
    )

    # Tıklama olayını dinleme
    fig.data[0].on_click(lambda trace, points, state: handle_click(points, data))
    fig.show()

def handle_click(points, data):
    global selected_points

    if points.point_inds:  # Eğer bir nokta tıklanmışsa
        index = points.point_inds[0]
        selected_points.append(data['interval_type'].iloc[index])

        if len(selected_points) > 2:
            selected_points.pop(0)  # İki noktadan fazlasını saklama

        print(f"Seçilen Noktalar: {selected_points}")

def halftrend_indicator_single(data, balance=100, position=0, position_size=0):
    last_data = data.iloc[-1]
    data['atr'] = calculate_atr(data) / 2
    trend = 0
    ht_values = []

    for i in range(len(data)):
        if i < 1:
            ht_values.append(np.nan)
            continue

        high_price = data['high'].iloc[i-1]
        low_price = data['low'].iloc[i-1]
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

    if position == 0 and last_data['close'] > data['ht'].iloc[-1]:
        position_size = balance / last_data['close']
        position = 1
        balance -= position_size * last_data['close'] * 0.999
        trade_signals.append(("Alış", last_data['interval_type'], last_data['close']))
    elif position == 1 and last_data['close'] < data['ht'].iloc[-1]:
        balance += position_size * last_data['close'] * 0.999
        position = 0
        trade_signals.append(("Satış", last_data['interval_type'], last_data['close']))

    current_value = balance
    if position == 1:
        current_value += position_size * last_data['close']

    data['finalbalance'] = current_value
    return balance, position, position_size

def continuously_update_data():
    crypto_symbol = "LUMIA"
    data = pd.DataFrame()
    num_data_points = 60
    start_index = 0
    balance = initial_balance
    position = 0
    position_size = 0

    while True:
        new_data = fetch_data_from_db(crypto_symbol, start_index, num_data_points)

        if new_data.empty:
            print("Veri bulunamadı.")
            break

        if 'interval_type' in new_data.columns:
            data = pd.concat([data, new_data]).drop_duplicates(subset=['interval_type']).reset_index(drop=True)
        else:
            print("Warning: 'interval_type' column is missing in new_data.")
            continue

        current_data = data.tail(num_data_points).copy()

        balance, position, position_size = halftrend_indicator_single(current_data, balance, position, position_size)

        plot_data(current_data)

        start_index += 1

if __name__ == "__main__":
    try:
        continuously_update_data()
    except KeyboardInterrupt:
        print("Program sonlandırıldı.")
