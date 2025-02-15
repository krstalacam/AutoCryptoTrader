import numpy as np  # numpy kütüphanesini ekleyin

# Volatilite hesaplama fonksiyonu (standart sapmaya dayalı)
def calculate_volatility(df, window=20):
    df['log_return'] = (df['close'] / df['close'].shift(1)).apply(lambda x: np.log(x))  # Logaritmik getiri
    df['volatility'] = df['log_return'].rolling(window=window).std() * np.sqrt(window)  # Standart sapma
    return df

# Volatiliteye dayalı al-sat sinyalleri
def generate_volatility_signals(df, volatility_threshold=0.02):
    df['buy_signal'] = 0
    df['sell_signal'] = 0

    # Al sinyali: Volatilite belirli bir eşiğin altındaysa
    df.loc[df['volatility'] < volatility_threshold, 'buy_signal'] = 1

    # Sat sinyali: Volatilite belirli bir eşiğin üstündeyse
    df.loc[df['volatility'] > volatility_threshold, 'sell_signal'] = 1

    return df


###################################################################

