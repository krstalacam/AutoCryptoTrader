import time

from cripto_bot_v1.binance_bot.CryptoTrading import CryptoTrading


def filter_scores_for_sell(score, sell):
    """
    Sell verileri ile score'u karşılaştırır ve satılması gerekenleri score'dan çıkarır.

    Args:
        score (list): Mevcut score listesi.
        sell (list): Satılması gereken verilerin listesi.

    Returns:
        list: Güncellenmiş score listesi.
    """
    sell_ids = {item['symbol'] for item in sell}
    updated_scores = [item for item in score if item['symbol'] not in sell_ids and item['score'] >= average_score]
    return updated_scores


# def find_top_scores_in_buy(score, buy):
#     """
#     Buy verileri ile score'u karşılaştırır ve en yüksek skora sahip 4 veriyi bulur.
#
#     Args:
#         score (list): Mevcut score listesi.
#         buy (list): Alım sinyali içeren liste.
#
#     Returns:
#         list: En yüksek skora sahip 4 verinin listesi.
#     """
#     buy_ids = {item['symbol'] for item in buy}
#     top_buy_scores = [item for item in score if item['symbol'] in buy_ids]
#     # Skorları sıralayıp en yüksek 4 tanesini seç
#     top_buy_scores = sorted(top_buy_scores, key=lambda x: x['score'], reverse=True)[:4]
#     return top_buy_scores
#

# Maksimum eleman sayısını belirten değişken

max_list_size = 4  # İstediğiniz maksimum değer burada tanımlanır
average_score = 65  # İstediğiniz maksimum değer burada tanımlanır


def process_final_score_list(score, sell, buy):
    """
    Son skoru oluşturur, çıkarılanları ve eklenenleri raporlar.

    Args:
        score (list): Mevcut score listesi.
        sell (list): Satılması gereken verilerin listesi.
        buy (list): Alım sinyali içeren liste.

    Returns:
        tuple: (nihai score listesi, çıkarılanlar, eklenenler)
    """
    # 1. Satılması gerekenleri çıkar
    sell_ids = {item['symbol'] for item in sell}
    removed_items = [
        {
            'symbol': item['symbol'],
            'score': item['score'],
            'price': item['price'],  # Eğer price yoksa 'N/A' kullan
            'time': item['time']  # Eğer time yoksa 'N/A' kullan
        }
        for item in score if
        item['symbol'] in sell_ids or item[
            'score'] < average_score]  # hem sell dekiler siliniyor hem de score 5 den kucuk olanlar

    filtered_scores = [
        item for item in score if item['symbol'] not in sell_ids and item['score'] >= average_score
    ]

    # 2. Mevcut score listesindeki id'leri belirle
    existing_ids = {item['symbol'] for item in filtered_scores}

    # 3. Buy listesinden mevcut olmayanları seç ve en yüksek skorlarına göre sırala
    new_candidates = [item for item in buy if item['symbol'] not in existing_ids]
    top_buy_scores = sorted(new_candidates, key=lambda x: x['score'], reverse=True)

    # 4. Maksimum `MAX_LIST_SIZE` eleman olacak şekilde tamamla
    space_available = max_list_size - len(filtered_scores)
    added_items = [
        {
            'symbol': item['symbol'],
            'score': item['score'],
            'price': item.get('price', 'N/A'),  # 'price' yoksa 'N/A' koy
            'time': item.get('time', 'N/A')  # 'date' yoksa 'N/A' koy
        }
        for item in top_buy_scores[:space_available]
    ]

    # 5. Nihai score listesini oluştur
    final_scores = filtered_scores + added_items

    return final_scores, removed_items, added_items


def print_summary(final_scores, removed_items, added_items):
    """
    Çıkarılanları, eklenenleri ve nihai listeyi yazdırır.
    """
    # Çıkarılanlar kısmı
    print("\nÇıkarılanlar:")
    if not removed_items:
        print("Hiçbir şey çıkarılmadı.")
    else:
        for item in removed_items:
            print(
                f"Symbol: {item['symbol']}, Score: {item['score']}, Price: {item.get('price', 'N/A')}, Time: {item.get('time', 'N/A')}")

    # Eklenenler kısmı
    print("\nEklenenler:")
    if not added_items:
        print("Hiçbir şey eklenmedi.")
    else:
        for item in added_items:
            print(
                f"Symbol: {item['symbol']}, Score: {item['score']}, Price: {item.get('price', 'N/A')}, Time: {item.get('time', 'N/A')}")

    # Nihai Skor Listesi kısmı
    print("\nNihai Skor Listesi:")
    for item in final_scores:
        print(
            f"Symbol: {item['symbol']}, Score: {item['score']}, Price: {item.get('price', 'N/A')}, Time: {item.get('time', 'N/A')}")


def trading_signal_processor_app(print_active=False):
    # Veritabanı bağlantısı oluştur

    signal_processor = CryptoTrading()

    # Skorları yazdır
    score = signal_processor.create_only_score(
        enabled_active=False)  # enabled_active false olsun yoksa, eger sahip oldugumuz bir kriptoyu devredışı yaparsak algilayamaz
    # ve sikinti olur ama false yaparsak algilar hatta düşerse satar yani score 5 altına düşerse ama en onemlısı elımızde varken devre dısı bırakınca satılana kadar
    # durması ve hata olusmaması dıye dusunuyorum test etmedım ama oyle olmalı

    # Alış ve satış sinyallerini yazdır
    buy, sell = signal_processor.create_signals(enabled_active=True, matplotlib_use=False)
    # matplotlib_use grafiklerin windows pencere olarak gorunmesini saglar

    # print(buy)
    # print(sell)

    # test etme ornek veriler
    # score = [
    #     {'symbol': 'BTC', 'score': 4},
    #     {'symbol': 'ETH', 'score': 6},
    #     {'symbol': 'DOGE', 'score': 7}
    # ]
    # sell = [
    #     {'symbol': 'BTC', 'price': 50000, 'time': '2024-11-28', 'score': 4},
    #     {'symbol': 'DOGE', 'price': 0.1, 'time': '2024-11-28', 'score': 7}
    # ]
    # buy = [
    #     {'symbol': 'BTC', 'price': 50000, 'time': '2024-11-28', 'score': 8},
    #     {'symbol': 'ADA', 'price': 1.2, 'time': '2024-11-28', 'score': 9},
    #     {'symbol': 'ETH', 'price': 1800, 'time': '2024-11-28', 'score': 5},
    #     {'symbol': 'XRP', 'price': 0.5, 'time': '2024-11-28', 'score': 10}
    # ]

    # print(score)

    # Sonuçları işle
    final_scores, removed_items, added_items = process_final_score_list(score, sell, buy)

    # print(removed_items)
    # print(added_items)
    # print(final_scores)

    if print_active:
        # Emirleri yazdır
        print_data("Scores", score)
        print_data("Buy Signals", buy)
        print_data("Sell Signals", sell)

        # Özeti yazdır
        print_summary(final_scores, removed_items, added_items)

    return removed_items, added_items


def print_data(title, data):
    """
    Gelen veriyi analiz ederek okunabilir bir şekilde yazdırır.

    Args:
    title (str): Verinin başlığı.
    data (list): Yazdırılacak veri. İçerik genelde sözlüklerden oluşur.
    """
    print(f"\n{title}:")
    if not data:
        print("Veri bulunamadı.")
        return

    # Dinamik başlıklar için ilk elemandaki anahtarları alıyoruz
    headers = list(data[0].keys())
    header_line = " | ".join(headers)
    print(header_line)
    print("-" * len(header_line))

    # Her bir veriyi satır halinde yazdırıyoruz
    for item in data:
        row = " | ".join(str(item.get(header, "-")) for header in headers)
        print(row)


if __name__ == "__main__":
    while True:
        try:
            print("Yeni analiz turu başlatılıyor...")
            trading_signal_processor_app(True)
            time.sleep(10)
        except KeyboardInterrupt:
            print("Program durduruldu.")
            break
        except Exception as e:
            print(f"Hata oluştu: {e}")
            time.sleep(10)  # Hata durumunda kısa bir bekleme
