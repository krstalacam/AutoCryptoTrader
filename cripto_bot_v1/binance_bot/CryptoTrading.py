import time

import matplotlib.pyplot as plt
import pandas as pd

from cripto_bot_v1.inducatorv_main.database_manager import DatabaseManager
from cripto_bot_v1.inducatorv_main.indicators.indicator_calculator import IndicatorCalculator
from cripto_bot_v1.sql.db_manager import get_db_path

import matplotlib


class CryptoTrading:

    def __init__(self):
        self.db_path = get_db_path()
        self.db_manager = DatabaseManager(self.db_path)  # DatabaseManager sınıfı tanımlı
        self.indicator_calculator = IndicatorCalculator()  # IndicatorCalculator'ı başlat
        self.previous_signals = []  # Önceki sinyalleri saklar

    def fetch_all_data(self, symbol):
        """
        Verilen sembol için işlem verilerini alır.
        """
        data = self.db_manager.fetch_data(symbol, start_index=0, num_data_points=600)
        if data.empty:
            return pd.DataFrame()  # Boş DataFrame döndür
        return data

    def fetch_price_data(self, symbol):
        conn = self.db_manager.connect_db()
        try:
            query = """
            SELECT timestamp, open, high, low, close
            FROM crypto_prices
            WHERE crypto_symbol = ?
            """
            # Change tuple to list for the params
            df = pd.read_sql_query(query, conn, params=[symbol])
        except Exception as e:
            print(f"Price data fetch error: {e}")
            df = pd.DataFrame()
        finally:
            conn.close()

        return df

    def process_and_trade_data(self, symbol):
        """
        Verilen sembol için işlem sinyalleri oluşturur.
        """
        data = self.fetch_all_data(symbol)
        if data.empty:
            return None

        # İşlem sinyalleri oluştur
        initial_balance = 100
        trade_signal = self.indicator_calculator.execute_trade(data, initial_balance, False, symbol)
        return trade_signal

    def only_score_process_and_trade_data(self, symbol):
        """
        Verilen sembol için işlem sinyalleri oluşturur.
        """
        data = self.fetch_all_data(symbol)
        if data.empty:
            return None

        # İşlem sinyalleri oluştur
        trade_signal = self.indicator_calculator.only_score_execute_trade(data, symbol)
        return trade_signal

    def create_signals(self, enabled_active=False, graph_active=False, matplotlib_use=False):
        symbols = self.db_manager.get_all_crypto_symbols(enabled_active)  # Tüm sembolleri al
        buy_signals = []
        sell_signals = []
        signals_with_symbols = []

        for symbol in symbols:
            signal = self.process_and_trade_data(symbol)
            if signal:
                crypto_symbol, generated_signal, score = signal
                if generated_signal:
                    if generated_signal['type'] == 'buy':
                        buy_signals.append({
                            'symbol': crypto_symbol,
                            'price': generated_signal['price'],
                            'time': generated_signal['time'],
                            'score': score
                        })
                    elif generated_signal['type'] == 'sell':
                        sell_signals.append({
                            'symbol': crypto_symbol,
                            'price': generated_signal['price'],
                            'time': generated_signal['time'],
                            'score': score
                        })

                    # Grafik için sinyalleri sakla
                    signals_with_symbols.append(
                        (symbol, generated_signal))  # şu an al ve sat sinyalleri oluşmayabiliyor
                    # yani normalde de her zaman oluşmayacak sonuçta o yüzden de al sat sinyali oluşmazsa grafik de
                    # oluşmuyor bilgin olsun

        # Grafikleri çiz
        if graph_active and signals_with_symbols:
            self.plot_graphs(signals_with_symbols, matplotlib_use)

        return buy_signals, sell_signals

    def create_only_score(self, enabled_active=False):
        score = []

        # Sahip olunan semboller listesini al
        owned_symbols = self.db_manager.get_owned_crypto_symbols(
            enabled_active)  # Bu fonksiyon veritabanındaki 'owned' sembollerini döndürmeli.

        for symbol in owned_symbols:
            # Sinyal üret ve işleme al
            signal = self.only_score_process_and_trade_data(symbol)

            if signal:
                crypto_symbol, _score, price, time = signal
                score.append({
                    'symbol': crypto_symbol,
                    'score': _score,
                    'price': price,
                    'time': time,
                })

        return score

    def plot_graphs(self, signals_with_symbols, matplotlib_use):
        """
        Fiyat ve işlem sinyalleriyle bir grafik oluşturur.
        4'er 4'er grafikleri bir sayfada gösterir.
        """

        count = 0
        if matplotlib_use:
            matplotlib.use('TkAgg')  # Alternatif olarak 'Qt5Agg' kullanılabilir.

        print(len(signals_with_symbols))
        num_signals = len(signals_with_symbols)
        batch_size = 4  # Her sayfada 4 grafik olacak
        for start_idx in range(0, num_signals, batch_size):
            end_idx = min(start_idx + batch_size, num_signals)
            current_batch = signals_with_symbols[start_idx:end_idx]

            # Alt grafik yerleşimi
            fig, axes = plt.subplots(2, 2, figsize=(15, 10))  # 2x2 düzen
            axes = axes.flatten()  # Düzleştir, kolay erişim için

            for i, (symbol, signal) in enumerate(current_batch):
                price_data = self.fetch_price_data(symbol)

                if price_data.empty:
                    print(f"No price data found for symbol: {symbol}")
                    continue

                # Fiyat verilerini sıralama
                price_data.sort_values(by='timestamp', inplace=True)  # Zaman damgasına göre sırala

                # Zaman ve fiyat verilerini ayır
                times = price_data['timestamp']  # Zaman damgaları
                closes = price_data['close']  # Kapanış fiyatları

                # Grafik oluşturma
                ax = axes[i]  # Şu anki subplot
                ax.plot(times, closes, label='Close Price', color='blue', linewidth=2)

                # Sinyali işaretle
                signal_time = signal['time']
                signal_price = signal['price']
                signal_label = "Buy Signal" if signal['type'] == 'buy' else "Sell Signal"
                signal_color = 'green' if signal['type'] == 'buy' else 'red'
                signal_marker = '^' if signal['type'] == 'buy' else 'v'

                ax.scatter(signal_time, signal_price, color=signal_color, label=signal_label, marker=signal_marker,
                           s=100)

                # Grafik başlık ve etiketler
                ax.set_title(f'Trading Signal for {symbol}')
                ax.set_xlabel('Time')
                ax.set_ylabel('Price')
                ax.legend()

                # X ekseninde sadece üç tarih yazdırma (timestamp olarak)
                time_labels = [times.iloc[0], times.iloc[len(times) // 2], times.iloc[-1]]  # İlk, ortada ve son tarih
                ax.set_xticks(time_labels)
                ax.set_xticklabels(time_labels, rotation=45)

                ax.grid(True)
                count += 1
                print(str(count) + "- " + symbol)
            # Kalan boş grafik alanlarını gizle
            for j in range(len(current_batch), len(axes)):
                fig.delaxes(axes[j])

            plt.tight_layout()
            plt.show()


# Kullanım
if __name__ == "__main__":
    # Veritabanı yolu
    crypto_trading = CryptoTrading()

    # Yeni sinyalleri kontrol et ve görselleştir
    crypto_trading.create_signals(graph_active=True, matplotlib_use=True)
    # matplotlib_use grafiklerin windows pencere olarak gorunmesini saglar
