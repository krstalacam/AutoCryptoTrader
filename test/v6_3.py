import sqlite3
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import time

# SQLite veritabanına bağlantı
DB_PATH = '../cripto_bot_v1/crypto_data.db'  # Veritabanı dosyanızın yolu

def connect_db():
    """Veritabanı bağlantısını döndürür."""
    return sqlite3.connect(DB_PATH)

def load_cryptos():
    """Veritabanından mevcut kripto para birimlerini yükle."""
    conn = connect_db()
    query = "SELECT symbol FROM cryptocurrencies"
    crypto_list = pd.read_sql_query(query, conn)['symbol'].tolist()
    conn.close()
    return crypto_list

def fetch_data_from_db(crypto_symbol, start_index=0, num_data_points=60):
    """Veritabanından belirli bir kripto paranın OHLCV verilerini çekme fonksiyonu."""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM cryptocurrencies WHERE symbol = ?', (crypto_symbol,))
    result = cursor.fetchone()

    if result:
        crypto_id = result[0]
        query = f"SELECT open, high, low, close, interval_type FROM crypto_prices WHERE crypto_id = ? ORDER BY interval_type LIMIT ? OFFSET ?"
        data = pd.read_sql_query(query, conn, params=(crypto_id, num_data_points, start_index))
    else:
        print(f"{crypto_symbol} bulunamadı. Lütfen geçerli bir sembol girin.")
        data = pd.DataFrame()  # Boş DataFrame döndür

    conn.close()
    return data

def calculate_atr(data, period=14):
    """ATR hesaplama fonksiyonu."""
    high = data['high']
    low = data['low']
    close = data['close']

    tr1 = high - low
    tr2 = np.abs(high - close.shift(1))
    tr3 = np.abs(low - close.shift(1))

    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    return atr

def halftrend_indicator(data, amplitude=2):
    """HalfTrend göstergesi hesaplama fonksiyonu."""
    data = data.copy()  # Dilimleme sorunlarından kaçınmak için kopya al
    data['atr'] = calculate_atr(data) / 2

    trend = np.zeros(len(data))
    up = np.zeros(len(data))
    down = np.zeros(len(data))
    max_low_price = np.full(len(data), np.nan)
    min_high_price = np.full(len(data), np.nan)

    max_low_price[0] = data['low'].iloc[0]
    min_high_price[0] = data['high'].iloc[0]

    for i in range(1, len(data)):
        high_price = data['high'][i - amplitude:i + 1].max()
        low_price = data['low'][i - amplitude:i + 1].min()

        if trend[i - 1] == 0:
            max_low_price[i] = max(low_price, max_low_price[i - 1])
            if data['close'].iloc[i] < data['low'].iloc[i - 1]:
                trend[i] = 1
                min_high_price[i] = high_price
            else:
                min_high_price[i] = min(high_price, min_high_price[i - 1])
        else:
            min_high_price[i] = min(high_price, min_high_price[i - 1])
            if data['close'].iloc[i] > data['high'].iloc[i - 1]:
                trend[i] = 0
                max_low_price[i] = low_price

        if trend[i] == 0:
            up[i] = max_low_price[i] if np.isnan(up[i - 1]) else max(max_low_price[i], up[i - 1])
        else:
            down[i] = min_high_price[i] if np.isnan(down[i - 1]) else min(min_high_price[i], down[i])

    data.loc[:, 'ht'] = np.where(trend == 0, up, down)
    data.loc[:, 'position'] = 0

    position = 0
    balance = 100
    position_size = 0

    for i in range(1, len(data)):
        if position == 0:
            if data['close'].iloc[i] > data['ht'].iloc[i]:
                position_size = balance / data['close'].iloc[i]
                data.loc[data.index[i], 'position'] = 1
                position = 1
                balance -= position_size * data['close'].iloc[i] * 0.999
                print(f"Alış: {data['close'].iloc[i]}")
        elif position == 1:
            if data['close'].iloc[i] < data['ht'].iloc[i]:
                balance += position_size * data['close'].iloc[i] * 0.999
                data.loc[data.index[i], 'position'] = -1
                position = 0
                position_size = 0
                print(f"Satış: {data['close'].iloc[i]}")

    if position == 1:
        balance += position_size * data['close'].iloc[-1] * 0.999

    data['finalbalance'] = balance
    return data

def plot_data(data):
    """Grafik oluşturma fonksiyonu."""
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

    fig.add_trace(go.Scatter(
        x=data[data['position'] == 1]['interval_type'],
        y=data[data['position'] == 1]['ht'],
        mode='markers',
        name='Alım Sinyali',
        marker=dict(color='green', size=10, symbol='triangle-up')
    ))

    fig.add_trace(go.Scatter(
        x=data[data['position'] == -1]['interval_type'],
        y=data[data['position'] == -1]['ht'],
        mode='markers',
        name='Satım Sinyali',
        marker=dict(color='red', size=10, symbol='triangle-down')
    ))

    final_balance = data['finalbalance'].iloc[-1]
    profit_loss = final_balance - 100
    profit_loss_text = f'Toplam Kar/Zarar: ${profit_loss:.2f}'

    fig.update_layout(
        title=f'HalfTrend Göstergesi - {profit_loss_text}',
        xaxis_title='Tarih',
        yaxis_title='Fiyat',
        legend=dict(x=0, y=1),
        template='plotly',
    )

    fig.show()

def continuously_update_data():
    """Verileri sürekli güncelleyen döngü."""
    crypto_symbol = "APE"
    data = pd.DataFrame()
    num_data_points = 120
    start_index = 0

    while True:
        new_data = fetch_data_from_db(crypto_symbol, start_index, num_data_points)

        if new_data.empty:
            print("Veri bulunamadı.")
            break

        print(new_data.head())

        if 'interval_type' in new_data.columns:
            data = pd.concat([data, new_data]).drop_duplicates(subset=['interval_type']).reset_index(drop=True)
        else:
            print("Warning: 'interval_type' column is missing in new_data.")
            continue

        current_data = data.tail(num_data_points).copy()  # copy() ile veri güncelleniyor

        current_data = halftrend_indicator(current_data)
        plot_data(current_data)

        start_index += 1  # Her yeni döngüde verileri bir dakika ileri kaydırır

if __name__ == "__main__":
    try:
        continuously_update_data()
    except KeyboardInterrupt:
        print("Program sonlandırıldı.")
