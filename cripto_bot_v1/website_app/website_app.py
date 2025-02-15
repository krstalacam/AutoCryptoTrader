import webbrowser

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import logging
import uvicorn
from cripto_bot_v1.website_app import data_manager
import socket

from cripto_bot_v1.website_app.manual_trade import manual_trade
from pathlib import Path

# FastAPI uygulamasını oluştur
app = FastAPI()

# Şablonlar ve statik dosyalar için yapılandırma
templates_dir = r"C:\crypto_bot\cripto_bot_v1\website_app\templates"
templates = Jinja2Templates(directory=templates_dir)

# Get the project root directory
project_root = Path(__file__).resolve().parent.parent.parent

# Create the full path to the static directory
static_dir = project_root / "cripto_bot_v1" / "website_app" / "static"
# print(static_dir)
# Mount the static files
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


# Aktif WebSocket bağlantılarını yönetmek için bir sınıf
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logging.error(f"Error sending message: {e}")


manager = ConnectionManager()


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """
    Ana sayfa
    """
    cryptos = data_manager.load_cryptos()
    orders = data_manager.get_crypto_orders()
    prices = data_manager.get_crypto_closes()
    return templates.TemplateResponse("index.html",
                                      {"request": request, "cryptos": cryptos, "orders": orders, "prices": prices})


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket bağlantısı için endpoint
    """
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            action = data.get("action")
            symbol = data.get("symbol")

            # toggle_owned a basinca al ve sat islemine gidecek onu ekler misin ve json da al sat emiri de
            # olusturacak sekilde yap eger satin alma aktif degilse satin almasin normal app de oldugu gibi
            if action == "toggle_owned":
                order_type = data_manager.toggle_crypto_owned(symbol)
                #print(f"Order type: {order_type}")  # Burada order_type'in doğru bir değer olduğunu doğrulayın.

                manual_trade(symbol, order_type, trade_active=False)
                #print("test1")

            elif action == "toggle_enabled":
                data_manager.toggle_crypto_enabled(symbol)

            elif action == "get_orders":  # Yeni bir action ekledik # burasi sey ordaki fonksiyon aclisrisa falan burasi da calisiyor gibi buraya gerek var mi bilemedim
                orders = data_manager.get_crypto_orders()
                prices = data_manager.get_crypto_closes()
                # print(prices)
                await websocket.send_json({"type": "orders", "symbol": symbol, "orders": orders,
                                           "prices": prices})  # burada send json var altta broadcast farklari ne öğren

            print("Test")
            # Güncellenmiş kripto verilerini istemcilere gönder
            updated_cryptos = data_manager.load_cryptos()
            orders = data_manager.get_crypto_orders()
            prices = data_manager.get_crypto_closes()

            await manager.broadcast({"type": "update", "cryptos": updated_cryptos, "orders": orders, "prices": prices})

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logging.error(f"WebSocket error: {e}")


def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(0)
    try:
        s.connect(('8.8.8.8', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip


# FastAPI uygulamasını çalıştırma fonksiyonu
def start_crypto_app():
    local_ip = get_local_ip()
    web_url = f"http://{local_ip}:4500"
    print(f"Your app is running at: {web_url}")
    # webbrowser.open(web_url)
    uvicorn.run(app, host=local_ip, port=4500, log_level="error")
    # uvicorn.run(app, host=local_ip, port=4500, log_level="error")


if __name__ == "__main__":
    start_crypto_app()
