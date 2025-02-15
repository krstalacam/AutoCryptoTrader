import math


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


def select_buy_strategy_indicators(data):  # bence riske atmayalim ma99 artanlarda işlem yapalım riske atmayalım bence
    """Alış stratejisini seçmek için gerekli koşulları kontrol eder."""
    if len(data) < 100:
        return False

    conditions = []

    # Koşulları listeye ekliyoruz
    conditions.append(is_volatility_low(data) and is_price_increasing(data))

    result = any(conditions)

    return result




def select_sell_strategy_indicators(data):
    """Satış stratejisini seçmek için gerekli koşulları kontrol eder."""
    if len(data) < 100:
        return False

    conditions = []

    # Koşulları listeye ekliyoruz
    conditions.append(is_price_decreasing(data) and is_price_above_mean(data))
    conditions.append(not is_price_increasing(data) and is_volatility_low(data))

    # Yeni bir koşul ekleyelim: Fiyatın MA25'in üstünde olması
    conditions.append(data['close'].iloc[-1] > data['ema_long'].iloc[-1])

    # all Koşulların hepsi doğruysa sonuç True olur
    # any koşullardan en az biri doğruysa sonuç True olur
    # result = all(conditions)
    result = any(conditions)

    return result

# def select_sell_strategy_indicators(data):
#     """Satış stratejisini seçmek için gerekli koşulları kontrol eder."""
#     return (is_price_decreasing(data) and is_price_above_mean(data)) or not (is_price_increasing(data) and is_volatility_low(data))


def add_signal(data, signals, signal_type):
    """Sinyali listeye ekler."""
    signals.append({
        'type': signal_type,
        'price': data.iloc[-1]['close'],
        'time': data.iloc[-1]['timestamp']
    })


def calculate_score(data):
    """Skoru hesaplar ve en iyi alım/satım fırsatını bulur."""

    if len(data) < 5:
        return 0

    last_close = data['close'].iloc[-1]

    # Fiyat ve hareketli ortalamalar üzerinden skor
    price_momentum_score = (last_close - data['close'].iloc[-2]) * 10 / data['close'].mean()

    # Hareketli ortalamalar ve volatilite katkısı
    ma_convergence_score = (data['ema_long'].iloc[-1] - data['ema_short'].iloc[-1])
    ma_divergence_score = (data['ema_longer'].iloc[-1] - data['ema_long'].iloc[-1])

    volatility_score = 20 if data['atr'].iloc[-1] < data['atr'].mean() else -20

    # Genel skor
    score = price_momentum_score + ma_convergence_score - ma_divergence_score + volatility_score

    # Ekstra durumlar
    if data['rsi'].iloc[-1] < 30:
        score += 20  # RSI düşükse (aşırı satılmış)
    elif data['rsi'].iloc[-1] > 70:
        score -= 20  # RSI yüksekse (aşırı alınmış)

    # score değerini kontrol et
    if math.isnan(score):
        score = 0
    else:
        score = int(round(score))

    print(score)


# en iyi v3 şu an crypto_trading_results1.xlsx burasıda v3 e gore oluşturuldu
# sonra v1 orta ama v3 e bak ve bunu da degıstır daha iyi olmalı kendin ayarlamalısın yani gpt ile olacak gibi değil
# en kötü v2 sil yani o kadar kötü uhhhahhha

# bazen v3 iyi bazi yerlerde v1 daha iyi o yuzden birlestirip test etmen lazim yeni durumlar olusturman lazim
# kesin karşılaştırman gereken kriptolar: xrp,ada, range 3 3 ,