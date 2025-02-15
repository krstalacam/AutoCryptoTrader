from cripto_bot_v1.inducatorv_main.database_manager import DatabaseManager

import pandas as pd
import mplfinance as mpf
import matplotlib.pyplot as plt


def calculate_sar(data, af=0.02, max_af=0.2):
    """
    Geliştirilmiş Parabolic SAR hesaplama fonksiyonu (fiyat değişimlerini daha erken algılar).

    :param data: DataFrame, 'high' ve 'low' sütunlarını içermelidir.
    :param af: Başlangıç hızlanma faktörü (default: 0.02).
    :param max_af: Maksimum hızlanma faktörü (default: 0.2).
    :return: SAR değerlerini içeren bir DataFrame.
    """
    # SAR değerlerini tutacak liste
    sar = []

    # Başlangıç değerleri
    ep = data['high'].iloc[0]  # Extreme Point başlangıçta yüksek değer
    initial_sar = data['low'].iloc[0]  # İlk SAR başlangıçta düşük değer
    sar.append(initial_sar)

    af_current = af  # Mevcut hızlanma faktörü
    trend_up = True  # Başlangıçta yükseliş trendi kabul edilir

    for i in range(1, len(data)):
        # Önceki SAR değeri
        previous_sar = sar[i-1]

        # Yeni SAR hesaplama
        new_sar = previous_sar + af_current * (ep - previous_sar)

        # Eğer trend yükseliyorsa, SAR'ı 'low' değerine kadar düşür
        if trend_up:
            new_sar = min(new_sar, data['low'].iloc[i - 1])
        else:  # Eğer trend düşüyorsa, SAR'ı 'high' değerine kadar yükselt
            new_sar = max(new_sar, data['high'].iloc[i - 1])

        # EP (Extreme Point) güncelleme: Yükselen trendde yeni bir yüksek değer, düşen trendde yeni bir düşük değer
        if trend_up:
            if data['high'].iloc[i] > ep:
                ep = data['high'].iloc[i]
                af_current = min(af_current + af, max_af)
        else:
            if data['low'].iloc[i] < ep:
                ep = data['low'].iloc[i]
                af_current = min(af_current + af, max_af)

        # SAR'ın trendle uyumsuz olması durumunda yön değiştirme
        if trend_up and data['low'].iloc[i] < new_sar:
            trend_up = False
            ep = data['low'].iloc[i]
            af_current = af
        elif not trend_up and data['high'].iloc[i] > new_sar:
            trend_up = True
            ep = data['high'].iloc[i]
            af_current = af

        sar.append(new_sar)

    data['SAR'] = sar
    return data


def plot_candlestick_with_sar_v2(data, result, threshold=0.05):
    """
    Candlestick grafiği ve SAR çizgisini gösterirken, düşüş trendinde SAR değeri fiyatla
    çok yakın olduğunda sarı renkte gösterecek şekilde güncellenmiş fonksiyon.

    :param data: DataFrame, fiyat bilgilerini içeriyor.
    :param result: DataFrame, hesaplanmış SAR değerlerini içeriyor.
    :param threshold: SAR'ın fiyat seviyesine yaklaşma eşiği (default: %5).
    """
    # Zaman damgasını datetime formatına çevir ve indeks olarak ayarlayın
    data['timestamp'] = pd.to_datetime(data['timestamp'])
    data.set_index('timestamp', inplace=True)

    # SAR değerlerini alıyoruz
    sar = result['SAR']

    # SAR noktalarını renklendirecek listeyi oluşturuyoruz
    sar_colors = []

    for i, (sar_val, close) in enumerate(zip(sar, data['close'])):
        # Düşüş trendi kontrolü: SAR değeri fiyatın üzerinde olmalı
        if sar_val > close:
            # SAR değeri, fiyata çok yakınsa sarı renkte göster
            if abs(sar_val - close) / close <= threshold:
                sar_colors.append('yellow')
            else:
                sar_colors.append('red')
        else:  # Yükseliş trendi
            sar_colors.append('green')

    # Candlestick grafiğini ve SAR'ı oluşturuyoruz
    sar_plot = mpf.make_addplot(sar, type='scatter', markersize=50, color=sar_colors)

    # Candlestick grafiğini SAR ile birlikte çiziyoruz
    mpf.plot(
        data,
        type='candle',
        style='charles',
        title='Candlestick Chart with SAR (Red, Green, Yellow)',
        ylabel='Price',
        volume=False,
        figratio=(10, 6),
        addplot=sar_plot,  # SAR noktasını grafiğe ekliyoruz
        show_nontrading=False
    )

    plt.show()
def plot_candlestick_with_sar(data, result):
    # Ensure datetime format and set as index for candlestick data
    data['timestamp'] = pd.to_datetime(data['timestamp'])
    data.set_index('timestamp', inplace=True)

    # Ensure datetime format and set as index for SAR data
    result.index = pd.to_datetime(result.index)  # Make sure SAR also has correct datetime index

    # Create a DataFrame for SAR values (matching the candlestick timestamps)
    sar = result['SAR']  # Assuming the SAR values are in the 'SAR' column of the result DataFrame

    # Create color list for SAR points
    sar_colors = ['green' if sar_val < close else 'red' for sar_val, close in zip(sar, data['close'])]

    # Create the candlestick plot and SAR plot
    sar_plot = mpf.make_addplot(sar, type='scatter', markersize=50, color=sar_colors)  # Use color list for markers

    # Create the candlestick plot with SAR overlaid
    mpf.plot(
        data,
        type='candle',
        style='charles',
        title='Candlestick Chart with SAR',
        ylabel='Price',
        volume=False,
        figratio=(10, 6),
        addplot=sar_plot,  # Add the SAR plot on top of the candlestick chart
        show_nontrading=False
    )

    plt.show()


# Örnek veri
database = DatabaseManager()
data = database.fetch_data("WRX", 320, 50)
# SAR hesapla
result = calculate_sar(data)
print(data)

def identify_potential_reversals(data, threshold=0.02):
    """
    SAR ve fiyat seviyesinin yakınlaştığı noktaları algılar ve bu noktaları sarı renkte işaretler.

    :param data: SAR ve fiyat verilerini içeren DataFrame.
    :param threshold: SAR ve fiyat arasındaki yakınlık eşiği (default: 0.02).
    :return: SAR renklerini içeren liste ('red', 'green', 'yellow').
    """
    sar_colors = []

    for i in range(len(data)):
        sar_val = data['SAR'].iloc[i]
        close_val = data['close'].iloc[i]

        if sar_val < close_val:  # Yükseliş trendi
            if (close_val - sar_val) / close_val <= threshold:  # Yakınlık kontrolü
                sar_colors.append('yellow')  # Olası dönüş noktası
            else:
                sar_colors.append('green')
        else:  # Düşüş trendi
            if (sar_val - close_val) / close_val <= threshold:  # Yakınlık kontrolü
                sar_colors.append('yellow')  # Olası dönüş noktası
            else:
                sar_colors.append('red')

    return sar_colors

def plot_candlestick_with_sar_and_reversals(data, result, threshold=0.02):
    """
    SAR ile candlestick grafiği oluşturur ve potansiyel dönüş noktalarını sarı ile işaretler.

    :param data: DataFrame, 'high', 'low', 'close', 'timestamp' sütunlarını içermeli.
    :param result: SAR değerlerini içeren DataFrame.
    :param threshold: SAR ve fiyat arasındaki yakınlık eşiği.
    """
    # Ensure datetime format and set as index for candlestick data
    data['timestamp'] = pd.to_datetime(data['timestamp'])
    data.set_index('timestamp', inplace=True)

    # Ensure datetime format and set as index for SAR data
    result.index = pd.to_datetime(result.index)  # Make sure SAR also has correct datetime index

    # Create a DataFrame for SAR values (matching the candlestick timestamps)
    sar = result['SAR']  # Assuming the SAR values are in the 'SAR' column of the result DataFrame

    # Identify potential reversal points with custom function
    sar_colors = identify_potential_reversals(data, threshold=threshold)

    # Create the candlestick plot and SAR plot
    sar_plot = mpf.make_addplot(sar, type='scatter', markersize=50, color=sar_colors)  # Use color list for markers

    # Create the candlestick plot with SAR overlaid
    mpf.plot(
        data,
        type='candle',
        style='charles',
        title='Candlestick Chart with SAR and Potential Reversals',
        ylabel='Price',
        volume=False,
        figratio=(10, 6),
        addplot=sar_plot,  # Add the SAR plot on top of the candlestick chart
        show_nontrading=False
    )

    plt.show()

# SAR hesaplama ve grafik çizim
plot_candlestick_with_sar(data, result)
# plot_candlestick_with_sar_v2(data, result)
# plot_candlestick_with_sar_and_reversals(data, result, threshold=0.01)
