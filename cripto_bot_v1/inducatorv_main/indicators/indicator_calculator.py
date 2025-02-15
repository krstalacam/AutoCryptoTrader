import numpy as np
import pandas as pd

from cripto_bot_v1.inducatorv_main.indicators.indicator_v2 import generate_signals, calculate_score
# v4 de iyi mesela firo da ama iste bazilari bazen iyi oluyor bazen kotu oluyor napcaz bilemiyorum
# v2_2 eh işte ama diğerleri iyi değil kullanma v2 yi kullancaz şu an onu yapıyoruz

def calculate_halftrend(data):
    trend = 0
    ht_values = []

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

    return pd.Series(ht_values, index=data.index)


def calculate_tenkan_sen(data):
    """Tenkan Sen (Conversion Line) hesaplar."""
    return (data['high'].rolling(window=9).max() + data['low'].rolling(window=9).min()) / 2


def calculate_kijun_sen(data):
    """Kijun Sen (Base Line) hesaplar."""
    return (data['high'].rolling(window=26).max() + data['low'].rolling(window=26).min()) / 2


def calculate_stoch_rsi(data, rsi_period=14, stoch_period=10, k_period=5, d_period=3):
    """
    Stochastic RSI hesaplayan bir fonksiyon (14-14-3-3 parametreleri).

    :param data: DataFrame, fiyat verilerini içermelidir ve 'close' sütununa sahip olmalıdır.
    :param rsi_period: int, RSI hesaplamasında kullanılacak dönem uzunluğu. Varsayılan 14.
    :param stoch_period: int, Stoch RSI hesaplamasında kullanılacak dönem uzunluğu. Varsayılan 14.
    :param k_period: int, %K çizgisi için kullanılan hareketli ortalama uzunluğu. Varsayılan 3.
    :param d_period: int, %D çizgisi için kullanılan hareketli ortalama uzunluğu. Varsayılan 3.
    :return: DataFrame, stoch_rsi, %K ve %D sütunları eklenmiş olarak döner.
    """
    # Fiyat değişimlerini hesapla
    delta = data['close'].diff()
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)

    # Ortalama kazanç ve kaybı hesapla (RSI için)
    avg_gain = pd.Series(gain).rolling(window=rsi_period).mean()
    avg_loss = pd.Series(loss).rolling(window=rsi_period).mean()

    # RSI hesaplama
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    # Stochastic RSI hesaplama
    min_rsi = rsi.rolling(window=stoch_period).min()
    max_rsi = rsi.rolling(window=stoch_period).max()
    stoch_rsi = (rsi - min_rsi) / (max_rsi - min_rsi)

    # %K çizgisi hesaplama (3 periyotluk hareketli ortalama)
    k_line = stoch_rsi.rolling(window=k_period).mean()

    # %D çizgisi hesaplama (3 periyotluk hareketli ortalama)
    d_line = k_line.rolling(window=d_period).mean()

    return stoch_rsi, k_line, d_line


def avg_volume(data, period=20):
    """
    Belirli bir periyot için hacim ortalamasını hesaplar.
    data: DataFrame veya dictionary, hacim verilerini içerir.
    period: Hesaplama için kullanılan periyot (gün sayısı).
    """
    # Veriler pandas DataFrame formatında ise, hacmi hesapla
    avg_volume = data['volume'].rolling(window=period).mean()

    return avg_volume


def avg_atr(data, period=14):
    """
    ATR'yi hesaplar.
    data: DataFrame, fiyat ve gerekli veriler içerir.
    period: Hesaplama için kullanılan periyot (gün sayısı).
    """
    # Gerçek aralık hesaplama (True Range)
    data['high-low'] = data['high'] - data['low']  # Yüksek ve düşük arasındaki fark
    data['high-close'] = abs(data['high'] - data['close'].shift(1))  # Yüksek ve önceki kapanış arasındaki fark
    data['low-close'] = abs(data['low'] - data['close'].shift(1))  # Düşük ve önceki kapanış arasındaki fark

    # True Range hesaplama: Max değerleri al
    data['true_range'] = data[['high-low', 'high-close', 'low-close']].max(axis=1)

    # ATR hesaplama: Son 'period' günlük gerçek aralıkların ortalaması
    atr = data['true_range'].rolling(window=period).mean()

    # Son ATR değerini döndür
    return atr  # Son değeri döndür

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

    return sar

# ========================= GÖSTERGELER ========================= #
def calculate_indicators(data):
    """Veriye tüm göstergeleri ekler."""
    # Mevcut göstergeler
    data['sar'] = calculate_sar(data)

    data['rsi'] = calculate_rsi(data, 14)
    data['stoch_rsi'], data['%K'], data['%D'] = calculate_stoch_rsi(data)

    data['ema_short'] = calculate_ema(data, 9)
    data['ema_long'] = calculate_ema(data, 26)
    data['ema_longer'] = calculate_ema(data, 90)
    data['ema_50'] = calculate_ema(data, 50)

    data['bb_middle'], data['bb_upper'], data['bb_lower'] = calculate_bollinger_bands(data)
    data['atr'] = calculate_atr(data)
    data['adx'] = calculate_adx(data)
    data['macd'], data['macd_signal'], data['macd_histogram'] = calculate_macd(data)

    data['stochastic_k'], data['stochastic_d'] = calculate_stochastic_oscillator(data)
    data['supertrend'] = calculate_supertrend(data)
    data['vwap'] = calculate_vwap(data)
    data['fibonacci_levels'] = calculate_fibonacci_levels(data)

    # Ichimoku göstergeleri
    data['tenkan_sen'] = calculate_tenkan_sen(data)
    data['kijun_sen'] = calculate_kijun_sen(data)


    data['avg_volume'] = avg_volume(data)
    data['avg_atr'] = avg_atr(data)

    return data


# RSI Hesaplama
def calculate_rsi(data, period=14):
    delta = data['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


# EMA Hesaplama
def calculate_ema(data, period):
    return data['close'].ewm(span=period, adjust=False).mean()


# Bollinger Bantları
def calculate_bollinger_bands(data, period=20, std_dev=2):
    mid = data['close'].rolling(window=period).mean()
    std = data['close'].rolling(window=period).std()
    upper = mid + (std_dev * std)
    lower = mid - (std_dev * std)
    return mid, upper, lower


# ATR Hesaplama
def calculate_atr(data, period=14):
    high_low = data['high'] - data['low']
    high_close = np.abs(data['high'] - data['close'].shift())
    low_close = np.abs(data['low'] - data['close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = ranges.max(axis=1)
    return true_range.rolling(window=period).mean()


# ADX Hesaplama
def calculate_adx(data, period=14):
    plus_dm = data['high'].diff().where(data['high'].diff() > data['low'].diff(), 0).clip(lower=0)
    minus_dm = data['low'].diff().where(data['low'].diff() > data['high'].diff(), 0).clip(lower=0)
    atr = calculate_atr(data, period)
    plus_di = (100 * (plus_dm.rolling(window=period).sum() / atr)).fillna(0)
    minus_di = (100 * (minus_dm.rolling(window=period).sum() / atr)).fillna(0)
    dx = (abs(plus_di - minus_di) / (plus_di + minus_di)) * 100
    return dx.rolling(window=period).mean()


# MACD Hesaplama
def calculate_macd(data, short=7, long=30, signal=20):
    ema_short = calculate_ema(data, short)
    ema_long = calculate_ema(data, long)
    macd = ema_short - ema_long
    signal_line = macd.ewm(span=signal, adjust=False).mean()

    macd_histogram = macd - signal_line

    return macd, signal_line, macd_histogram


# Stochastic Oscillator
def calculate_stochastic_oscillator(data, k_period=14, d_period=3):
    low_min = data['low'].rolling(window=k_period).min()
    high_max = data['high'].rolling(window=k_period).max()
    stochastic_k = 100 * ((data['close'] - low_min) / (high_max - low_min))
    stochastic_d = stochastic_k.rolling(window=d_period).mean()
    return stochastic_k, stochastic_d


# Supertrend Hesaplama
def calculate_supertrend(data, multiplier=3, period=10):
    # Calculate ATR and hl2
    atr = calculate_atr(data, period)  # Ensure you have a valid calculate_atr function
    hl2 = (data['high'] + data['low']) / 2

    # Initialize basic bands
    basic_upper = hl2 + (multiplier * atr)
    basic_lower = hl2 - (multiplier * atr)

    # Initialize upper and lower bands
    upper_band = basic_upper.copy()
    lower_band = basic_lower.copy()

    for i in range(1, len(data)):
        if basic_upper.iloc[i] < upper_band.iloc[i - 1] or data['close'].iloc[i - 1] > upper_band.iloc[i - 1]:
            upper_band.iloc[i] = basic_upper.iloc[i]
        else:
            upper_band.iloc[i] = upper_band.iloc[i - 1]

        if basic_lower.iloc[i] > lower_band.iloc[i - 1] or data['close'].iloc[i - 1] < lower_band.iloc[i - 1]:
            lower_band.iloc[i] = basic_lower.iloc[i]
        else:
            lower_band.iloc[i] = lower_band.iloc[i - 1]

    # Calculate the Supertrend
    supertrend = np.where(data['close'] > upper_band, lower_band, upper_band)

    return pd.Series(supertrend, index=data.index)


# VWAP Hesaplama
def calculate_vwap(data):
    cumulative_volume = data['volume'].cumsum()
    cumulative_price_volume = (data['close'] * data['volume']).cumsum()
    return cumulative_price_volume / cumulative_volume


# Fibonacci Seviyeleri
def calculate_fibonacci_levels(data):
    recent_high = data['high'].rolling(window=20).max()
    recent_low = data['low'].rolling(window=20).min()
    diff = recent_high - recent_low
    levels = {
        'level_0.236': recent_high - diff * 0.236,
        'level_0.382': recent_high - diff * 0.382,
        'level_0.5': recent_high - diff * 0.5,
        'level_0.618': recent_high - diff * 0.618
    }
    return levels


def generate_signals_main(data, position, last_buy_price, position_active=True):  # position_active normalde true cunku
    # dashboard app de kullandigimiz durumda icin ama bot calisirken false oluyor zaten ellemeye gerek yok
    """Al/Sat sinyallerini üretir."""

    signals, stop_loss_price, take_profit_price = generate_signals(data, position, last_buy_price, position_active)

    return signals, stop_loss_price, take_profit_price


def calculate_score_main(data):
    """Skoru hesaplar."""
    # Boş bırakılan bir skor hesaplama fonksiyonu

    score = calculate_score(data)
    return score


class IndicatorCalculator:
    def __init__(self):
        self.trade_signals = []
        self.total_profit_loss = 0
        self.trade_profit_loss = 0
        self.last_buy_price = 0
        self.position = 0
        self.position_size = 0
        self.initial_balance = 100
        self.last_trade_time = None
        self.minimum_trade_interval = 3
        self.stop_loss_price = None
        self.take_profit_price = None
        self.score = 0

    def execute_trade(self, data, balance, position_on=True, crypto_symbol="unknown"):
        """Ana işlem fonksiyonu."""
        # Göstergeleri hesapla
        data = calculate_indicators(data)

        # Minimum işlem aralığını kontrol et
        current_index = len(data) - 1
        if self.last_trade_time and (current_index - self.last_trade_time < self.minimum_trade_interval):
            return balance if position_on else None

        # Verinin yeterli olup olmadığını kontrol et
        if len(data) < 2:
            print("Not enough data, skipping trade.")
            return balance if position_on else None

        # Al/Sat sinyallerini üret
        signals, stop_loss_price, take_profit_price = generate_signals_main(
            data, self.position, self.last_buy_price, position_active=True)  # position_active false olursa beklemez
        # ve surekli sat veya al sinyali gozukur true olursa al dan sonra sat 1 tane gelir sonra sat gelmesini bekler
        # eger trading signal processor test ediyorsan false olmali, normalde ne olmali bilmiyorum ama galiba false

        last_data = data.iloc[-1]

        profit_loss = (last_data['close'] - self.last_buy_price) * self.position_size
        self.trade_profit_loss = profit_loss
        # İşlem yap
        if signals:
            if position_on:
                self.trade_signals.append(
                    {'type': signals[0]['type'], 'price': last_data['close'], 'time': current_index})
                if signals[0]['type'] == 'buy':
                    last_data = data.iloc[-1]
                    self.position_size = balance / last_data['close']
                    self.position = 1
                    self.last_buy_price = last_data['close']
                    balance -= self.position_size * last_data['close'] * 0.999
                    self.stop_loss_price = stop_loss_price
                    self.take_profit_price = take_profit_price
                    self.last_trade_time = current_index
                    print(f"Bought {crypto_symbol} at {last_data['close']}")

                elif signals[0]['type'] == 'sell':
                    last_data = data.iloc[-1]
                    balance += self.position_size * last_data['close'] * 0.999
                    self.position = 0
                    self.position_size = 0
                    self.last_buy_price = 0
                    self.total_profit_loss += profit_loss

                    self.stop_loss_price = None
                    self.take_profit_price = None
                    self.last_trade_time = current_index
                    print(f"Sold {crypto_symbol} at {last_data['close']}, P/L: {profit_loss}")
            else:
                # Skor hesaplama ve sonuç döndürme
                score = calculate_score_main(data)
                return crypto_symbol, (signals[0] if signals else None), score

    def only_score_execute_trade(self, data, crypto_symbol="unknown"):
        """Sadece sembol ve skor döndüren fonksiyon."""
        # Göstergeleri hesapla
        data = calculate_indicators(data)
        last_data = data.iloc[-1]

        # Verinin yeterli olup olmadığını kontrol et
        if len(data) < 2:
            print("Not enough data, skipping score calculation.")
            return crypto_symbol, None  # Verinin yetersiz olması durumunda None döndürülür

        # Skor hesapla
        score = calculate_score_main(data)

        return crypto_symbol, score, last_data['close'], last_data['timestamp']
