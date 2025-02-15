def is_price_increasing(data):
    """Fiyatın %0.2'den fazla arttığını kontrol eder."""
    price_change = data['close'].iloc[-1] - data['close'].iloc[-2]
    price_change_percentage = (price_change / data['close'].iloc[-2]) * 100
    return price_change_percentage > 0.2


def is_price_decreasing(data):
    """Fiyatın %1'den fazla düştüğünü kontrol eder."""
    price_change = data['close'].iloc[-1] - data['close'].iloc[-2]
    price_change_percentage = (price_change / data['close'].iloc[-2]) * 100
    return price_change_percentage < -1


def is_volatility_low(data):
    """Son 10 günün ortalama ATR değerine göre volatilitenin düşük olduğunu kontrol eder."""
    recent_volatility = data['atr'].iloc[-2:].mean()  # Son 2 değerin ortalaması
    average_volatility = data['atr'].iloc[-10:].mean()  # Son 10 değerin ortalaması
    return recent_volatility < average_volatility


def is_ma25_up(data):
    """MA25'in yukarı doğru hareket ettiğini kontrol eder."""
    return data['ema_long'].iloc[-1] > data['ema_long'].iloc[-2]


def is_ma25_down(data):
    """MA25'in aşağı doğru hareket ettiğini kontrol eder."""
    return data['ema_long'].iloc[-1] < data['ema_long'].iloc[-2]


def is_price_above_mean(data):
    """Fiyatın, kapanış fiyatlarının ortalamasından daha yüksek olup olmadığını kontrol eder."""
    return data['close'].iloc[-1] > data['close'].mean()


def add_signal(data, signals, signal_type):
    """Sinyali listeye ekler."""
    signals.append({
        'type': signal_type,
        'price': data.iloc[-1]['close'],
        'time': data.iloc[-1]['timestamp']
    })


def generate_signals(data, position, last_buy_price, position_active):
    """Al/Sat sinyallerini üretir."""
    stop_loss_price, take_profit_price = 0, 0
    signals = []

    # Hareketli ortalama ve fiyat değişimlerini analiz et
    price_change = data['close'].iloc[-1] - data['close'].iloc[-2]
    price_change_percentage = (price_change / data['close'].iloc[-2]) * 100  # Yüzde değişim hesaplanıyor
    print(f"price_change_percentage {price_change_percentage}")

    # Fiyat dalgalanma analizi (volatilite)
    recent_volatility = data['atr'].iloc[-2:].mean()  # ATR'in son 2 değeri üzerinden volatilite
    is_volatility_low = recent_volatility < data['atr'].iloc[-10:].mean()

    # Hareketli ortalamaların yönleri
    is_ma25_up = data['ema_long'].iloc[-1] > data['ema_long'].iloc[-2]
    is_ma25_down = data['ema_long'].iloc[-1] < data['ema_long'].iloc[-2]

    # print(position_active)
    if position_active:
        if position == 0 and select_buy_strategy_indicators(data):
            add_signal(data, signals, 'buy')
        elif position == 1 and select_sell_strategy_indicators(data):
            add_signal(data, signals, 'sell')
            stop_loss_price = last_buy_price - data['atr'].iloc[-1] * 1.5
            take_profit_price = last_buy_price + data['atr'].iloc[-1] * 3
    else:
        if select_buy_strategy_indicators(data):
            add_signal(data, signals, 'buy')
        elif select_sell_strategy_indicators(data):
            add_signal(data, signals, 'sell')

    return signals, stop_loss_price, take_profit_price


def select_sell_strategy_indicators(data):
    """
    Alım stratejisi: MA25 yükseliyorsa ve fiyat yükselme eğilimindeyse AL sinyali oluşturur.
    """
    if len(data) < 100:
        return 0

    # Gerekli sütunları kontrol et
    required_columns = ['close', 'ema_long', 'rsi', 'macd', 'macd_signal']
    for col in required_columns:
        if col not in data or len(data[col]) < 5:
            return False

    conditions = []

    # 1. MA25 yükseliyor olmalı
    if len(data['ema_long']) >= 5:
        conditions.append(data['ema_long'].iloc[-1] > data['ema_long'].iloc[-2])

    # 2. Fiyat yükselişte olmalı
    if len(data['close']) >= 3:
        conditions.append(data['close'].iloc[-1] > data['close'].iloc[-2] > data['close'].iloc[-3])

    # 3. RSI uygun bölgede olmalı (aşırı alımda olmamalı)
    if len(data['rsi']) >= 5:
        conditions.append(30 < data['rsi'].iloc[-1] < 70)

    # 4. MACD histogram pozitife dönmüş olmalı
    if len(data['macd']) >= 5 and len(data['macd_signal']) >= 5:
        macd_histogram = data['macd'].iloc[-1] - data['macd_signal'].iloc[-1]
        conditions.append(macd_histogram > 0)

    # Tüm koşulları değerlendir ve AL sinyali üret
    result = all(conditions)
    print(f"Buy Strategy Result: {result}")
    return result

def select_buy_strategy_indicators(data):
    """
    Satış stratejisi: Fiyat aniden düşerse satış yapar, yoksa bekler.
    """
    if len(data) < 100:
        return 0

    # Gerekli sütunları kontrol et
    required_columns = ['close', 'ema_long', 'atr', 'macd', 'macd_signal']
    for col in required_columns:
        if col not in data or len(data[col]) < 5:
            return False

    conditions = []

    # 1. Fiyat aniden düşerse satış
    if len(data['close']) >= 3:
        sudden_drop = data['close'].iloc[-1] < data['close'].iloc[-2] * 0.97
        conditions.append(sudden_drop)

    # 2. ATR yükselmişse volatilite artışına göre tepki ver
    if len(data['atr']) >= 5:
        atr_spike = data['atr'].iloc[-1] > data['atr'].mean() * 1.5
        conditions.append(atr_spike)

    # 3. MACD histogram negatife dönmüşse (momentum kaybı)
    if len(data['macd']) >= 5 and len(data['macd_signal']) >= 5:
        macd_histogram = data['macd'].iloc[-1] - data['macd_signal'].iloc[-1]
        conditions.append(macd_histogram < 0)

    # En az bir koşul sağlanıyorsa SAT sinyali üret, yoksa bekle
    result = any(conditions)
    print(f"Sell Strategy Result: {result}")
    return result

def calculate_score(data):
    """
    Yükselme ihtimali olan kriptolar için skor hesaplar.
    """
    score = 0
    if len(data) < 5:
        return 0

    # 1. Fiyat MA99'a yakın (potansiyel taban fiyat) - 3 puan
    if data['close'].iloc[-1] > data['ema_longer'].iloc[-1] * 0.98 and \
       data['close'].iloc[-1] < data['ema_longer'].iloc[-1] * 1.02:
        score += 3

    # 2. MA7'nin MA25'i yeni yukarı kesmiş olması (yükseliş başlangıcı) - 5 puan
    if data['ema_short'].iloc[-1] > data['ema_long'].iloc[-1] and \
       data['ema_short'].iloc[-2] <= data['ema_long'].iloc[-2]:
        score += 5

    # 3. RSI 30-50 arasında ve yükseliyor (aşırı alımda değil, potansiyel var) - 4 puan
    if 30 < data['rsi'].iloc[-1] < 50:
        score += 4
    if data['rsi'].iloc[-1] > data['rsi'].iloc[-2]:  # RSI yükseliyor
        score += 2

    # 4. MACD histogram pozitif ama aşırı genişlememiş - 3 puan
    macd_histogram = data['macd'].iloc[-1] - data['macd_signal'].iloc[-1]
    if macd_histogram > 0 and macd_histogram < data['close'].std() * 0.5:
        score += 3

    # 5. ATR düşük (volatilite artışı beklenebilir) ve hacim artıyor - 2 puan
    if data['atr'].iloc[-1] < data['atr'].mean():
        score += 2
    if data['volume'].iloc[-1] > data['volume'].iloc[-2]:
        score += 2

    # 6. Fiyat önceki zirveye çok yakın değil (aşırı yükseliş riski yok) - 3 puan
    recent_high = data['high'].rolling(window=20).max().iloc[-1]
    if data['close'].iloc[-1] < recent_high * 0.95:
        score += 3

    return score

# score deniyoruz burada yeni score fonksiyonlari
