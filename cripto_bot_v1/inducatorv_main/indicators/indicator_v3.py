import pandas as pd


def generate_signals(data, position, last_buy_price, position_active):
    """Al/Sat sinyallerini üretir."""
    if len(data) < 3:
        return [], None, None  # Return empty signals and no stop-loss or take-profit prices if not enough data

    last_data = data.iloc[-1]
    signals = []

    # Hareketli ortalama yönlerini kontrol et
    is_ma25_up = data['ema_long'].iloc[-1] > data['ema_long'].iloc[-2]
    is_ma25_down = data['ema_long'].iloc[-1] < data['ema_long'].iloc[-2]
    is_ma99_up = data['ema_longer'].iloc[-1] > data['ema_longer'].iloc[-2]
    is_ma99_down = data['ema_longer'].iloc[-1] < data['ema_longer'].iloc[-2]

    # Fiyat hareketlerini kontrol et
    price_change = last_data['close'] - data['close'].iloc[-2]
    previous_price_change = data['close'].iloc[-2] - data['close'].iloc[-3]

    # Dalgalanma analizi (volatility)
    recent_volatility = data['atr'].iloc[-1]
    average_volatility = data['atr'].mean()
    low_volatility = recent_volatility < average_volatility

    # Hareketli ortalamalar
    ma_7_trend_up = data['ema_short'].iloc[-1] > data['ema_short'].iloc[-2] > data['ema_short'].iloc[-3]
    ma_7_trend_down = data['ema_short'].iloc[-1] < data['ema_short'].iloc[-2] < data['ema_short'].iloc[-3]

    # Stop loss ve take profit seviyeleri
    atr = data['atr'].iloc[-1]
    stop_loss_price = last_buy_price - atr * 1.5 if position == 1 else None
    take_profit_price = last_buy_price + atr * 3 if position == 1 else None

    # 1. Durum: Düşüş ardından yükseliş
    if previous_price_change < 0 and price_change > 0:
        signals.append({'type': 'buy', 'price': last_data['close'], 'time': last_data['timestamp']})

    # 2. Durum: Düşük dalgalanma ardından yükseliş
    elif low_volatility and price_change > 0 and ma_7_trend_up:
        signals.append({'type': 'buy', 'price': last_data['close'], 'time': last_data['timestamp']})

    # 3. Durum: Yüksekteyken ani düşüş
    elif position == 1 and price_change < 0 and previous_price_change > 0:
        signals.append({'type': 'sell', 'price': last_data['close'], 'time': last_data['timestamp']})

    # 4. Durum: Yükseliş ardından dalgalanma azalarak fiyat sabitlenmesi
    elif position == 1 and low_volatility and not ma_7_trend_up:
        signals.append({'type': 'sell', 'price': last_data['close'], 'time': last_data['timestamp']})

    return signals, stop_loss_price, take_profit_price


def calculate_score(data):
    """Skoru hesaplar ve en iyi alım/satım fırsatını bulur."""
    last_close = data['close'].iloc[-1]
    previous_close = data['close'].iloc[-2]
    price_change = last_close - previous_close

    # Temel göstergelere dayalı skor hesaplama
    rsi_score = max(0, 100 - abs(50 - data['rsi'].iloc[-1] if pd.notna(data['rsi'].iloc[-1]) else 50))
    macd_trend_score = 10 if pd.notna(data['macd'].iloc[-1]) and data['macd'].iloc[-1] > data['macd_signal'].iloc[-1] else -10
    adx_trend_score = (data['adx'].iloc[-1] * 0.5 if pd.notna(data['adx'].iloc[-1]) else 0)
    volatility_score = 10 if pd.notna(data['atr'].iloc[-1]) and data['atr'].iloc[-1] < data['atr'].mean() else -10
    ma_direction_score = 20 if pd.notna(data['ema_long'].iloc[-1]) and data['ema_long'].iloc[-1] > data['ema_longer'].iloc[-1] else -20

    # Ek fiyat analizi skorları
    price_trend_score = 20 if price_change > 0 else -20
    momentum_score = 10 if price_change > 0 and data['ema_short'].iloc[-1] > data['ema_long'].iloc[-1] else -10

    # Tahmine dayalı skor
    early_prediction_score = 15 if data['close'].iloc[-1] > data['ema_longer'].iloc[-1] and price_change > 0 else -15

    # Toplam skor
    score = (rsi_score + macd_trend_score + adx_trend_score + volatility_score +
             ma_direction_score + price_trend_score + momentum_score + early_prediction_score)

    return int(round(score))

# Kod bu şekilde genişletilerek daha fazla durumu kapsayacak hale getirildi.

# en iyi v3 şu an crypto_trading_results1.xlsx burasıda v3 e gore oluşturuldu
# sonra v1 orta ama v3 e bak ve bunu da degıstır daha iyi olmalı kendin ayarlamalısın yani gpt ile olacak gibi değil
# en kötü v2 sil yani o kadar kötü uhhhahhha

# bazen v3 iyi bazi yerlerde v1 daha iyi o yuzden birlestirip test etmen lazim yeni durumlar olusturman lazim
# gerkeksiz yere çok sık al sat yapmasın
# kesin karşılaştırman gereken kriptolar: xrp,ada, range 3 3 ,

# bence v3 de çok iyi değil çünkü alıyo artmaya devam etsede hemen satıyor bu da sürekli işlem ücreti ödemeye sebep olur
# fiyat düşünce hemen satmaktansa biraz bir kac fiyata bakarak analiz etsin ani karar vermesin
