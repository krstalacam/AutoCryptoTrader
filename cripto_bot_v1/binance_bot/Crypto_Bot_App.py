import logging
import threading
import queue
import asyncio

from cripto_bot_v1.binance_bot.CryptoOrdersManager import process_cryptos
from cripto_bot_v1.binance_bot.binance_bot import crypto_trading_app
from cripto_bot_v1.binance_bot.trading_signal_processor import trading_signal_processor_app
from cripto_bot_v1.sql.data_collector import data_collector_app

from cripto_bot_v1.sql.crypto_operations import update_crypto_status_and_scores
from cripto_bot_v1.website_app import data_manager
from cripto_bot_v1.website_app.website_app import start_crypto_app, manager

# Bayraklar ve senkronizasyon için kullanılacak Queue ve Event objeleri
signal_data_collector_event = threading.Event()  # Fiyat verileri toplanıp tabloya eklendikten sonra sinyal verecek bayrak
signal_ready_event = threading.Event()  # Al/sat sinyalleri üretildiğinde sinyal verecek bayrak
signal_queue = queue.Queue()  # Al/Sat sinyallerini paylaşmak için Queue


# Veri toplama işlemi
def run_data_collector():
    """Her 60 saniyede bir çalışacak fonksiyon."""
    while True:
        data_collector_app()
        signal_data_collector_event.set()

    # start_time = time.time()  # Başlangıç zamanını al
    # while True:
    #     current_time = time.time()  # Her döngüde mevcut zamanı al
    #     elapsed_time = current_time - start_time  # Geçen süreyi hesapla
    #
    #     if elapsed_time >= waiting_time:  # Eğer 50 saniye veya daha fazla geçtiyse
    #         print(f"{waiting_time} saniye tamamlandı. İşlem yapılıyor...")
    #         data_collector_app()
    #         print("denemetest")
    #         data_ready_event.set()
    #
    #         start_time = current_time  # Başlangıç zamanını güncelle
    #
    #     time.sleep(0.1)


# Al/Sat sinyallerini işleme
def run_trading_signal_processor():
    while True:
        # Data hazır olduğunda çalış
        signal_data_collector_event.wait()
        print("Signal Processor: Al/Sat sinyalleri hesaplanıyor.")
        removed_cryptos, added_cryptos = trading_signal_processor_app(print_active=True)
        signal_queue.put((removed_cryptos, added_cryptos))
        print("Signal Processor: Sinyaller hesaplandı.")
        # print(removed_cryptos)
        # print(added_cryptos)

        # Tablodaki 'owned' durumlarını güncelle
        update_crypto_status_and_scores(removed_cryptos, added_cryptos)

        # İşlem tamamlandıktan sonra diğer işlemlere izin ver
        signal_ready_event.set()

        # işlemler bittikten sonra en son json a kaydetme
        process_cryptos(removed_cryptos, added_cryptos)

        # WebSocket üzerinden web sitesini güncelle
        asyncio.run(update_web_clients())

        # İşlemler tamamlandı, sinyali temizle
        signal_data_collector_event.clear()


# WebSocket istemcilerini güncellemek için async fonksiyon
async def update_web_clients():
    try:
        updated_cryptos = data_manager.load_cryptos()
        orders = data_manager.get_crypto_orders()
        prices = data_manager.get_crypto_closes()

        # Güncel verileri tüm istemcilere gönder
        await manager.broadcast({"type": "update", "cryptos": updated_cryptos, "orders": orders, "prices": prices})
        print("Web clients updated successfully.")
    except Exception as e:
        logging.error(f"Error updating web clients: {e}")


# Al/Sat işlemlerini gerçekleştirme
def run_crypto_trading_app():
    while True:
        # Kullanıcıdan işlem açılmasını bekle
        print("Trading App: İşlem açılmasını bekliyor...")
        trading_control_event.wait()  # 'Set' edilene kadar bekler

        print("Trading App: İşlem aktif. Sinyal bekleniyor...")
        signal_ready_event.wait()  # Sinyal hazır olana kadar bekler
        print("Trading App: Sinyal alındı, işlem başlıyor.")

        # Al/Sat işlemleri
        removed_cryptos, added_cryptos = signal_queue.get()
        crypto_trading_app(removed_cryptos, added_cryptos)
        print("Trading App: İşlemler tamamlandı.")

        # İşlem sonrası temizleme
        signal_ready_event.clear()


# Web sitesini başlatma (sürekli çalışabilir veya bağımsız bir iş parçacığında tutulabilir)
def run_start_crypto_app():
    print("Web App: Web sitesi başlatılıyor.")
    start_crypto_app()


trading_control_event = threading.Event()


def main():
    print("Crypto Bot Başlatılıyor...")

    # İş parçacıklarını başlatma
    data_thread = threading.Thread(target=run_data_collector, daemon=True)
    signal_thread = threading.Thread(target=run_trading_signal_processor, daemon=True)
    # ONEMLI sinyaller olusuyor tamam da sonra ona gore de satacak ama orada owned olanlari aliyor score da ve eger cikarilanlar tablodan
    # owned lari sifir olmazsa olmamasi gereken seyler oluyor ve yanlis seyler oluyor o yuzden cikarilanlari tablodan cikarmayi sonra
    # eklenenleri de ownedlarini tabloda 1 yapmayi unutma
    # sey yap al sat emirleri once gercekten satilmali ondan sonra da tabloda degismeli satarken zaten tabloya gore yapnadigi icin sikinti cikmaz
    # bunlar da yapildi sanirim

    # sadece json olabilir sahte sanki cidden almis da satmis gibi fiyatlari kaydetsin ve karimizi zararimizi almisiz gibi gorelim normalde de
    # kullaniriz zaten ama satin alma kapaliyken de gorebiliriz deneme icin iyi olur iyi bir indikator mu vs
    trading_thread = threading.Thread(target=run_crypto_trading_app, daemon=True)
    website_thread = threading.Thread(target=run_start_crypto_app, daemon=True)

    # İş parçacıklarını çalıştırma
    data_thread.start()
    signal_thread.start()
    trading_thread.start()
    website_thread.start()

    # Main thread sonsuza kadar çalışsın
    while True:  # şu an başlangıçta binance den satın alma açık olmuyor eğer böyle kalırsa biz buradan aç diyip açmamız gerekiyor
        user_input = input("Al/Sat sinyalleri aç/kapat (saç): ").strip().lower()
        if user_input == "saç":     # al sinyalini erkenden çalıştırma
            signal_data_collector_event.set()
            print("al sat sinyalleri hesaplaniyor.")

        elif user_input == "aç":
            trading_control_event.set()  # İşlem yapmayı etkinleştir
            print("Al/Sat işlemi aktif.")
        elif user_input == "kapat":
            trading_control_event.clear()  # İşlem yapmayı duraklat
            print("Al/Sat işlemi durduruldu.")
        else:
            print("Geçersiz giriş. 'aç' veya 'kapat' girin.")


if __name__ == "__main__":
    main()
# gpt yazdigi yeni kodu denedigimde tablo kilitli hatasi veriyordu o olmaz baska turlu yap her yerde
# signal_ready_event.set() bunu kullaniyordu galiba ondan olabilir
# sanirim cozuldu o hata duzelttik yine de uzun sure test edip bi bak

# indicator_v2