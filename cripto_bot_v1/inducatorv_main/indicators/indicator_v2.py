import random

import numpy as np


# ========================= STRATEJİLER ========================= #

def is_volatility_low(data):
    """Son 10 günün ortalama ATR değerine göre volatilitenin düşük olduğunu kontrol eder."""
    recent_volatility = data['atr'].iloc[-2:].mean()  # Son 2 değerin ortalaması
    average_volatility = data['atr'].iloc[-10:].mean()  # Son 10 değerin ortalaması
    return recent_volatility < average_volatility


def is_price_above_mean(data):
    """Fiyatın, kapanış fiyatlarının ortalamasından daha yüksek olup olmadığını kontrol eder."""
    return data['close'].iloc[-1] > data['close'].mean()


def calculate_ichimoku_cloud(data):
    """Ichimoku Bulutu hesaplar."""
    high_9 = data['high'].rolling(window=9).max()
    low_9 = data['low'].rolling(window=9).min()
    high_26 = data['high'].rolling(window=26).max()
    low_26 = data['low'].rolling(window=26).min()
    high_52 = data['high'].rolling(window=52).max()
    low_52 = data['low'].rolling(window=52).min()

    data['tenkan_sen'] = (high_9 + low_9) / 2
    data['kijun_sen'] = (high_26 + low_26) / 2
    data['senkou_span_a'] = ((data['tenkan_sen'] + data['kijun_sen']) / 2).shift(26)
    data['senkou_span_b'] = ((high_52 + low_52) / 2).shift(26)
    data['chikou_span'] = data['close'].shift(-26)
    return data


def is_ichimoku_bullish(data):
    """Ichimoku bulutuna göre yükseliş trendini kontrol eder."""
    return (
            data['close'].iloc[-1] > data['senkou_span_a'].iloc[-1] > data['senkou_span_b'].iloc[-1]
            and data['tenkan_sen'].iloc[-1] > data['kijun_sen'].iloc[-1]
    )


def is_ichimoku_bearish(data):
    """Ichimoku bulutuna göre düşüş trendini kontrol eder."""
    return (
            data['close'].iloc[-1] < data['senkou_span_a'].iloc[-1] < data['senkou_span_b'].iloc[-1]
            and data['tenkan_sen'].iloc[-1] < data['kijun_sen'].iloc[-1]
    )


def is_price_increasing(data, threshold=0.5):
    """Fiyatın belirli bir yüzdeden fazla artıp artmadığını kontrol eder."""
    price_change = data['close'].iloc[-1] - data['close'].iloc[-2]
    price_change_percentage = (price_change / data['close'].iloc[-2]) * 100
    # print(f"price_change_percentage {price_change_percentage}")
    return price_change_percentage > threshold


def is_price_decreasing(data, threshold=1.0):
    """Fiyatın belirli bir yüzdeden fazla düştüğünü kontrol eder."""
    price_change = data['close'].iloc[-1] - data['close'].iloc[-2]
    price_change_percentage = (price_change / data['close'].iloc[-2]) * 100
    return price_change_percentage < -threshold


def is_ema_uptrend(data):
    """EMA'lerin yukarı yönlü bir trendde olup olmadığını kontrol eder."""
    return data['ema_short'].iloc[-1] > data['ema_long'].iloc[-1] > data['ema_longer'].iloc[-1]


def is_ema_downtrend(data):
    """EMA'lerin aşağı yönlü bir trendde olup olmadığını kontrol eder."""
    return data['ema_short'].iloc[-1] < data['ema_long'].iloc[-1] < data['ema_longer'].iloc[-1]


def is_macd_bullish(data):
    """MACD histogramın pozitif olduğunu kontrol eder."""
    macd_histogram = data['macd'].iloc[-1] - data['macd_signal'].iloc[-1]
    return macd_histogram > 0


def is_macd_bearish(data):
    """MACD histogramın negatif olduğunu kontrol eder."""
    macd_histogram = data['macd'].iloc[-1] - data['macd_signal'].iloc[-1]
    return macd_histogram < 0


def is_rsi_rebound(data):
    """RSI'ın dipten dönme işareti verip vermediğini kontrol eder."""
    return data['rsi'].iloc[-1] > data['rsi'].iloc[-2] > data['rsi'].iloc[-3] and data['rsi'].iloc[-1] < 50


def is_rsi_peak(data):
    """RSI'ın zirveden dönme işareti verip vermediğini kontrol eder."""
    return data['rsi'].iloc[-1] < data['rsi'].iloc[-2] < data['rsi'].iloc[-3] and data['rsi'].iloc[-1] > 50


def is_price_bouncing_from_ema(data):
    """Fiyatın EMA'ların üzerinden sıçrama yapıp yapmadığını kontrol eder."""
    return data['close'].iloc[-1] > data['ema_short'].iloc[-1] and data['close'].iloc[-2] < data['ema_short'].iloc[-2]


def is_price_rejected_by_ema(data):
    """Fiyatın EMA'ların altında reddedildiğini kontrol eder."""
    return data['close'].iloc[-1] < data['ema_short'].iloc[-1] and data['close'].iloc[-2] > data['ema_short'].iloc[-2]


def is_volume_breakout(data):
    """Hacimde ani bir artış olup olmadığını kontrol eder."""
    return data['volume'].iloc[-1] > data['volume'].mean() * 2


def is_volume_dropping(data):
    """Hacmin önemli ölçüde azaldığını kontrol eder."""
    return data['volume'].iloc[-1] < data['volume'].mean() * 0.5


##########

def calculate_derivative(data, column, window=5):
    """Hesaplanan bir sütunun türevini hesaplar."""
    return data[column].diff().rolling(window=window).mean()


def calculate_random_weight():
    """0.5 ile 1 arasında rastgele bir ağırlık oluşturur."""
    return np.random.uniform(0.5, 1.0)


def is_price_accelerating(data):
    """Fiyatın ivme kazandığını kontrol eder."""
    derivative = calculate_derivative(data, 'close')
    return derivative.iloc[-1] > 0 and derivative.iloc[-2] > 0


def is_price_decelerating(data):
    """Fiyatın ivme kaybettiğini kontrol eder."""
    derivative = calculate_derivative(data, 'close')
    return derivative.iloc[-1] < 0 and derivative.iloc[-2] < 0


def is_rsi_bullish(data):
    """RSI'nin yukarı yönlü sinyal verdiğini kontrol eder."""
    return data['rsi'].iloc[-1] < 30 or (data['rsi'].iloc[-1] > data['rsi'].iloc[-2] and data['rsi'].iloc[-1] < 50)


def is_rsi_bearish(data):
    """RSI'nin aşağı yönlü sinyal verdiğini kontrol eder."""
    return data['rsi'].iloc[-1] > 70 or (data['rsi'].iloc[-1] < data['rsi'].iloc[-2] and data['rsi'].iloc[-1] > 50)


def is_volume_spiking(data):
    """Hacimde ani bir artış olup olmadığını kontrol eder."""
    avg_volume = data['volume'].rolling(window=20).mean().iloc[-1]
    return data['volume'].iloc[-1] > avg_volume * 1.5


def is_bollinger_breakout(data):
    """Fiyatın Bollinger üst bandını aştığını kontrol eder."""
    return data['close'].iloc[-1] > data['bb_upper'].iloc[-1]


def is_bollinger_support(data):
    """Fiyatın Bollinger alt bandına yakın olduğunu kontrol eder."""
    return data['close'].iloc[-1] < data['bb_lower'].iloc[-1]


def is_price_near_high(data, window=10):
    """Fiyatın son X günün en yüksek fiyatına yakın olup olmadığını kontrol eder."""
    recent_high = data['close'].rolling(window=window).max().iloc[-1]
    return data['close'].iloc[-1] >= recent_high * 0.98


def is_price_near_low(data, window=10):
    """Fiyatın son X günün en düşük fiyatına yakın olup olmadığını kontrol eder."""
    recent_low = data['close'].rolling(window=window).min().iloc[-1]
    return data['close'].iloc[-1] <= recent_low * 1.02


def calculate_bollinger_bands(data, window=20):
    """Bollinger Bantlarını hesaplar ve veriye ekler."""
    data['bb_middle'] = data['close'].rolling(window=window).mean()
    data['bb_upper'] = data['bb_middle'] + (data['close'].rolling(window=window).std() * 2)
    data['bb_lower'] = data['bb_middle'] - (data['close'].rolling(window=window).std() * 2)
    return data


def calculate_probabilities(data):
    """Fiyatın yukarı veya aşağı hareket etme olasılığını tahmin eder."""
    up_factors = 0
    down_factors = 0

    # Yükseliş faktörleri
    if is_ema_uptrend(data):
        up_factors += 2
    if is_bollinger_support(data):
        up_factors += 1.5
    if data['rsi'].iloc[-1] < 30:
        up_factors += 1.5

    # Düşüş faktörleri
    if is_ema_downtrend(data):
        down_factors += 2
    if is_bollinger_breakout(data):
        down_factors += 1.5
    if data['rsi'].iloc[-1] > 70:
        down_factors += 1.5

    total_factors = up_factors + down_factors
    if total_factors == 0:
        return 50, 50  # Olasılıklar eşit

    up_probability = (up_factors / total_factors) * 100
    down_probability = (down_factors / total_factors) * 100
    return up_probability, down_probability


###############
def stoch_rsi_risen(data, threshold=0.90):  # 90 dan buyukse true olacak yani satma zamani
    """
    Check if both %K and %D columns in the given data are above 90.
    Parameters:
        data (DataFrame): The input data with '%K' and '%D' columns.
    Returns:
        bool: True if both '%K' and '%D' are above 90, False otherwise.
        :param data:
        :param threshold:
    """
    return data['%K'].iloc[-1] > threshold < data['%D'].iloc[-1]


def stoch_rsi_fallen(data, threshold=0.30):  # 30 dan kucukse true olacak yani alma zamani
    """
    Check if both %K and %D columns in the given data are below 30.
    Parameters:
        data (DataFrame): The input data with '%K' and '%D' columns.
    Returns:
        bool: True if both '%K' and '%D' are below 30, False otherwise.
        :param data:
        :param threshold:
    """
    return data['%K'].iloc[-1] < threshold > data['%D'].iloc[-1]


def sar_greater_price(data):  # burada satilir, alınmaz
    return data['sar'].iloc[-1] > data['close'].iloc[-2:-1].mean()


def sar_less_price(data):  # burada alinir
    return data['sar'].iloc[-1] < data['close'].iloc[-2:-1].mean()


def ema_is_higher(data, ema_type):
    """
    Belirtilen EMA tipine göre yüksek değer kontrolü yapar.
    - 'ema_short' : Kısa vadeli EMA
    - 'ema_long' : Orta vadeli EMA
    - 'ema_longer' : Uzun vadeli EMA
    """
    return data[ema_type].iloc[-5:-3].mean() > data[ema_type].iloc[-8:-6].mean()


def ema_is_lower(data, ema_type):
    """
    Belirtilen EMA tipine göre düşük değer kontrolü yapar.
    - 'ema_short' : Kısa vadeli EMA
    - 'ema_long' : Orta vadeli EMA
    - 'ema_longer' : Uzun vadeli EMA
    """
    return data[ema_type].iloc[-2:-1].mean() < data[ema_type].iloc[-4:-3].mean()


def check_price_rise(data, percent=1):
    # Yüzde değişimi hesapla
    price_change_percentage = ((data['close'].iloc[-1] - data['open'].iloc[-1]) / data['open'].iloc[-1]) * 100

    # Eğer değişim yüzde 1'den büyükse True döndür
    return price_change_percentage > percent


def check_price_drop(data, percent=1):
    # Yüzde değişimi hesapla
    price_change_percentage = ((data['close'].iloc[-1] - data['open'].iloc[-1]) / data['open'].iloc[-1]) * 100

    # Eğer değişim yüzde 1'den büyükse True döndür
    return price_change_percentage < -percent


def is_ema_50_dropping(data, threshold=1):
    """
    Check if EMA 50 is dropping significantly over the last few data points.

    Parameters:
    - data (list or array): A list of EMA 50 values.
    - threshold (float): The threshold value to determine if the drop is significant.

    Returns:
    - bool: True if the EMA is dropping faster than the threshold, False otherwise.
    """
    # Ensure there are enough data points to calculate the drop
    if len(data) < 10:
        return 0

    # Calculate the average rate of change
    total_change = 0
    for i in range(1, 5):
        total_change += data['ema_50'].iloc[-i] - data['ema_50'].iloc[-i - 1]

    average_change = total_change / (5 - 1)
    print(average_change)
    # Compare the average change with the negative threshold
    return average_change < -threshold


def select_buy_strategy_indicators(data):
    """Gelişmiş alış stratejisi."""

    conditions = []
    conditions.append(False)

    conditions.append(


    )
    return bool(any(conditions))  # Ensures it returns a boolean (True or False)


def select_sell_strategy_indicators(data):
    """Gelişmiş satış stratejisi."""
    conditions = []

    conditions.append(False)
    conditions.append(
        stoch_rsi_risen(
            data) or  # threshold degerlerinden emin degilim cunku bazen 90 ustune cikamiyor ve 85 gorup sonra
        # düşebiliyor bu durumda sıkıntı olabilir yani bunun için en yüksek stoch_rsi ortalamarına bakıp eğer onların
        # üstünde ise yapabiliriz ama bu da ne kadar iyi olur bilmiyorum ama yapılabilir
        sar_greater_price(data) or
        check_price_drop(data)

    )

    return bool(any(conditions))  # Ensures it returns a boolean (True or False)


def generate_signals(data, position, last_buy_price, position_active):
    """Al/Sat sinyallerini üretir."""
    signals = []
    stop_loss_price, take_profit_price = 0, 0
    if position_active:
        if position == 0 and select_buy_strategy_indicators(data):
            signals.append({'type': 'buy', 'price': data['close'].iloc[-1], 'time': data['timestamp'].iloc[-1]})
        elif position == 1 and select_sell_strategy_indicators(data):
            signals.append({'type': 'sell', 'price': data['close'].iloc[-1], 'time': data['timestamp'].iloc[-1]})
            stop_loss_price = last_buy_price - data['atr'].iloc[-1] * 1.5
            take_profit_price = last_buy_price + data['atr'].iloc[-1] * 3

        # elif position == 1:
        #     if is_price_increasing(data, threshold=.01):
        #         # Fiyat artıyorsa bekle
        #         pass
        #
        #     elif select_sell_strategy_indicators(data):
        #         # Satış sinyali
        #         signals.append({'type': 'sell', 'price': data['close'].iloc[-1], 'time': data['timestamp'].iloc[-1]})
        #         stop_loss_price = last_buy_price - data['atr'].iloc[-1] * 1.5
        #         take_profit_price = last_buy_price + data['atr'].iloc[-1] * 3
    else:
        if select_buy_strategy_indicators(data):
            signals.append({'type': 'buy', 'price': data['close'].iloc[-1], 'time': data['timestamp'].iloc[-1]})
        elif select_sell_strategy_indicators(data):
            signals.append({'type': 'sell', 'price': data['close'].iloc[-1], 'time': data['timestamp'].iloc[-1]})

    return signals, stop_loss_price, take_profit_price


def calculate_score(data):
    """
    Yükselme ihtimali olan kriptolar için skor hesaplar.
    """
    score = 0
    if len(data) < 5:
        return 0

    # Bollinger alt bandı desteği (3 puan)
    if is_bollinger_support(data):
        score += 3

    # RSI düşük ve artıyor (2 puan)
    if data['rsi'].iloc[-1] < 40 and data['rsi'].iloc[-1] > data['rsi'].iloc[-2]:
        score += 2

    # MACD histogram pozitif (3 puan)
    macd_histogram = data['macd'].iloc[-1] - data['macd_signal'].iloc[-1]
    if macd_histogram > 0:
        score += 3

    # Hacim artışı (2 puan)
    if data['volume'].iloc[-1] > data['volume'].iloc[-2]:
        score += 2

    # ATR düşük (2 puan)
    if data['atr'].iloc[-1] < data['atr'].mean():
        score += 2

    return score


def add_signal(data, signals, signal_type):
    """Sinyali listeye ekler."""
    signals.append({
        'type': signal_type,
        'price': data.iloc[-1]['close'],
        'time': data.iloc[-1]['timestamp']
    })
