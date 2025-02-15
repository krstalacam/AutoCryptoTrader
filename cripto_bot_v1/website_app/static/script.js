let socket; // WebSocket bağlantısını temsil eden değişken.
let allCryptos = []; // Sunucudan alınan tüm kripto verilerini saklayacak dizi.
let currentCryptos = []; // Ekranda gösterilen kriptoları tutar.
let prices;
let orders;
const transactionFeeRate = 0.001; // 0.1% işlem ücreti
const balance = 100; // kac dolarla işlem yaptığımızı gösterir
let maxOwnedCount = 4;

// Sayfa yüklendiğinde yapılacak işlemler.
window.onload = function () {
    const ws = `ws://${window.location.host}/ws`;
    setupWebSocket(ws); // WebSocket bağlantısını kurar ve gerekli olay işleyicilerini tanımlar.
    //initializeFilterButton(); // Filtre durumu ve buton metnini başlatır.

};
function calculateOwnedCryptos() {
    let ownedCount = 0;

    allCryptos.forEach(crypto => {
        if (crypto.owned) {
            ownedCount++;
        }
    });

    if(ownedCount < maxOwnedCount) disableAllBuyButtons(false);
    else disableAllBuyButtons(true);

    const totalOwnedElement = document.getElementById('crypto-count-text');
    const cryptoStatusElement = document.getElementById('crypto-status');
    totalOwnedElement.textContent = `${ownedCount}/${maxOwnedCount}`;

    cryptoStatusElement.classList.add("normal");

}
function disableAllBuyButtons(active) {
    // Tüm "Al" butonlarını seç
    const buyButtons = document.querySelectorAll('.owned.buy');

    // Her bir butonun "disabled" özelliğini true yap
    buyButtons.forEach(button => {
        button.disabled = active;
    });
}
// Tüm kripto işlemleri için toplam kar hesaplama
function calculateAllTotalProfit() {
    let totalProfit = 0;

    orders.forEach(order => {
        order.orders.forEach(_order => {
            if (_order.buy && _order.sell) {
                // Al/Sat işlemi varsa, işlem ücretiyle birlikte kar hesapla
                const buyPriceWithFee = _order.buy.price * (1 + transactionFeeRate); // Alımda işlem ücreti ekle
                const sellPriceWithFee = _order.sell.price * (1 - transactionFeeRate); // Satımda işlem ücreti çıkar

                const diff = ((sellPriceWithFee - buyPriceWithFee) / buyPriceWithFee) * balance;
                totalProfit += diff;
            } else if (_order.buy && !_order.sell) {
                // Sadece alım varsa, mevcut fiyat ile kar hesapla
                const currentPrice = prices.find(price => price.symbol === order.symbol)?.close || 0;
                if (currentPrice) {
                    const buyPriceWithFee = _order.buy.price * (1 + transactionFeeRate); // Alımda işlem ücreti ekle
                    const diff = ((currentPrice - buyPriceWithFee) / buyPriceWithFee) * balance;
                    totalProfit += diff;
                }
            }
        });
    });

    const totalProfitElement = document.getElementById('total-profit-text');
    totalProfitElement.textContent = `Toplam Kar: ${totalProfit.toFixed(2)}%`;

    const totalProfitContainer = document.getElementById('total-profit-container');
    totalProfitContainer.classList.remove("negative", "positive", "normal");

    if (totalProfit < 0) {
        totalProfitContainer.classList.add("negative");
    } else if (totalProfit > 0) {
        totalProfitContainer.classList.add("positive");
    } else {
        totalProfitContainer.classList.add("normal");
    }
}


// Belirli bir sembol için toplam kârı hesaplayan fonksiyon
function calculateTotalProfit(symbol) {
    const cryptoData = orders.find(item => item.symbol === symbol);
    let totalProfit = 0;

    if (cryptoData && cryptoData.orders.length > 0) {
        const reversedOrders = [...cryptoData.orders].reverse(); // En sonuncu işlem üstte olacak

        reversedOrders.forEach(order => {
            if (order.buy && order.sell) {
                // Alım ve satım işlemi varsa, işlem ücretini de dahil ederek karı hesapla
                const buyPriceWithFee = order.buy.price * (1 + transactionFeeRate); // Alımda işlem ücreti ekle
                const sellPriceWithFee = order.sell.price * (1 - transactionFeeRate); // Satımda işlem ücreti çıkar

                const diff = ((sellPriceWithFee - buyPriceWithFee) / buyPriceWithFee) * balance;
                totalProfit += diff;
            } else if (order.buy && !order.sell) {
                // Sadece alım işlemi varsa, mevcut fiyatla kârı hesapla
                const currentPrice = prices.find(price => price.symbol === symbol)?.close || 0;
                if (currentPrice) {
                    const buyPriceWithFee = order.buy.price * (1 + transactionFeeRate); // Alımda işlem ücreti ekle
                    const diff = ((currentPrice - buyPriceWithFee) / buyPriceWithFee) * balance;
                    totalProfit += diff;
                }
            }
        });
    }

    return totalProfit;
}
// WebSocket kurulum ve olay işleyicileri.
function setupWebSocket(url) {
    socket = new WebSocket(url); // WebSocket sunucusuna bağlanır.

    socket.onopen = function () {
        console.log("WebSocket bağlantısı kuruldu.");
        // İlk bağlantıda sunucudan tüm kripto verilerini al
        socket.send(JSON.stringify({ action: "get_orders" }));

    };

      // WebSocket onMessage fonksiyonunun içinde aşağıdaki gibi emirlerle birlikte kripto verilerini alıp, kartları güncelleyin.
    socket.onmessage = function (event) {
        const data = JSON.parse(event.data);
        if (data.type === "update") {
            // Kripto verilerini güncelledik.
            allCryptos = data.cryptos;
            orders = data.orders;
            prices = data.prices;
            //console.log(orders);

            const ownedFilter = localStorage.getItem("ownedFilter") === "true";
            const query = document.getElementById("search-input").value.trim().toLowerCase();
            updateCryptoCards(filterCryptos(allCryptos, ownedFilter, query));

        }
    };

    //socket.send(JSON.stringify({ action: "get_orders" }));

    socket.onerror = function (error) {
        console.error("WebSocket hatası:", error);
    };
}
// Kripto kartlarını güncelleme.
function updateCryptoCards(cryptos) {
    // Kriptoları sıralamak için sortCryptos fonksiyonunu çağırıyoruz
    const sortedCryptos = sortCryptos(cryptos, sortState);

    currentCryptos = sortedCryptos; // Sıralanmış kriptoları güncelle

    const container = document.getElementById("crypto-container");
    container.innerHTML = ""; // Kartları temizle

    sortedCryptos.forEach((crypto) => {
        const card = createCryptoCard(crypto); // Kripto kartlarını oluştur
        container.appendChild(card); // Yeni kartları ekle
    });

    calculateOwnedCryptos(); // Kripto sahipliğini hesapla
    calculateAllTotalProfit(); // Tüm kazancı hesapla
}


// Kripto kartı oluşturma.
function createCryptoCard(crypto) {
    const card = document.createElement("div");
    card.className = "crypto-card";

    // Butonları kapsayacak bir alan ekleyelim
    const buttonContainer = document.createElement("div");
    buttonContainer.className = "button-container";

    // Eğer kriptoyu sahiplenmişse, 💚 işareti ekleyelim
    if (crypto.owned) {
        const ownedTick = document.createElement("span");
        ownedTick.className = "owned-tick";
        ownedTick.textContent = "💚";
        card.appendChild(ownedTick);
    }

    // Kripto ismi
    const title = document.createElement("h2");
    title.textContent = crypto.symbol;
    title.style.marginTop = "12px"; // Sağ tarafa boşluk ekler

    card.appendChild(title);

    // Kripto için toplam kârı hesapla
    const totalProfit = document.createElement("p");

    // Toplam kâr hesaplama işlemi
    const profit = calculateTotalProfit(crypto.symbol);
    totalProfit.textContent = `${profit.toFixed(2)}%`;
    totalProfit.className = "profit-box";

    // Kârın pozitif, negatif veya nötr olduğunu belirleyip stil ekle
    if (profit < 0) {
        totalProfit.classList.add("negative");
    } else if (profit > 0) {
        totalProfit.classList.add("positive");
    } else {
        totalProfit.classList.add("normal");
    }

    // Toplam kârı karta ekle
    card.appendChild(totalProfit);

    // Devre dışı bırakma veya etkinleştirme butonu
    const toggleEnabledButton = createButton(
        crypto.enabled ? "Aktif" : "Devre Dışı",
        `toggle ${crypto.enabled ? "active" : "disabled"}`,
        (event) => {
            event.stopPropagation(); // Butona tıklanırken kartın tıklanmasını engelle
            toggleEnabled(crypto.symbol);
        }
    );
    // Butona sağ ve sol kenar boşluğu ekle
    toggleEnabledButton.style.marginRight = "-5px"; // Sağ tarafa boşluk ekler

    buttonContainer.appendChild(toggleEnabledButton);

    // Al / Sat butonu
    const toggleOwnedButton = createButton(
        crypto.owned ? "Sat" : "Al",
        `owned ${crypto.owned ? "sell" : "buy"} ${!crypto.enabled ? "disabled" : ""}`,
        (event) => {
            event.stopPropagation(); // Butona tıklanırken kartın tıklanmasını engelle
            toggleOwned(crypto.symbol);
        }
    );
    // Butona sol kenar boşluğu ekle
    toggleOwnedButton.style.marginLeft = "10px"; // Sol tarafa boşluk ekler

    buttonContainer.appendChild(toggleOwnedButton);

    // Butonları kartın alt kısmına ekleyelim
    card.appendChild(buttonContainer);

    // Kartın kendisine tıklanması, alttaki butonlar hariç, emirleri gösterir
    card.onclick = (event) => {
        // Alttaki butonlar dışında bir yere tıklanmışsa, emirleri göster
        if (!buttonContainer.contains(event.target)) {
            showOrders(crypto.symbol);
        }
    };

    return card;
}

// Genel bir buton oluşturma işlevi.
function createButton(text, className, onClickHandler) {
    const button = document.createElement("button");
    button.textContent = text; // Buton üzerindeki metni belirler.
    button.className = className; // CSS sınıfını ekler.
    button.onclick = onClickHandler; // Tıklama olayını tanımlar.
    return button; // Oluşturulan butonu döner.
}

// Kripto sahiplik durumunu değiştirir.
function toggleOwned(symbol) {
    socket.send(JSON.stringify({ action: "toggle_owned", symbol }));

    // Kriptoyu güncelle.
    const ownedFilter = localStorage.getItem("ownedFilter") === "true";
    const query = document.getElementById("search-input").value.trim().toLowerCase();

    const updatedCryptos = allCryptos.map(crypto => {
        if (crypto.symbol === symbol) {
            return { ...crypto, owned: !crypto.owned };
        }
        return crypto;
    });
    allCryptos = updatedCryptos;

    updateCryptoCards(filterCryptos(updatedCryptos, ownedFilter, query));
}

// Kripto aktiflik durumunu değiştirir.
function toggleEnabled(symbol) {
    socket.send(JSON.stringify({ action: "toggle_enabled", symbol }));

    // Kriptoyu güncelle.
    const ownedFilter = localStorage.getItem("ownedFilter") === "true";
    const query = document.getElementById("search-input").value.trim().toLowerCase();

    const updatedCryptos = allCryptos.map(crypto => {
        if (crypto.symbol === symbol) {
            return { ...crypto, enabled: !crypto.enabled };
        }
        return crypto;
    });
    allCryptos = updatedCryptos;

    updateCryptoCards(filterCryptos(updatedCryptos, ownedFilter, query));
}

// Filtre ve arama işlemleri için yardımcı fonksiyon.
function filterCryptos(cryptos, ownedFilter, query) {
    let relevantCryptos = ownedFilter ? cryptos.filter(crypto => crypto.owned) : cryptos;
    if (query) {
        relevantCryptos = relevantCryptos.filter(crypto => crypto.symbol.toLowerCase().includes(query));
    }
    return relevantCryptos;
}

// Kullanıcı bir kripto araması yapmak istediğinde çağrılır.
function searchCrypto() {
    const query = document.getElementById("search-input").value.trim().toLowerCase(); // Arama çubuğundaki değeri alır.
    const suggestionsContainer = document.getElementById("suggestions-container");

    const ownedFilter = localStorage.getItem("ownedFilter") === "true"; // Filtre durumunu kontrol et.

    let filteredCryptos = filterCryptos(allCryptos, ownedFilter, query);

    updateCryptoCards(filteredCryptos);

    updateSuggestions(filteredCryptos, query);
}

// Öneri listesini günceller.
function updateSuggestions(cryptos, query) {
    const suggestionsContainer = document.getElementById("suggestions-container");
    suggestionsContainer.innerHTML = ""; // Mevcut önerileri temizle.

    // Eğer arama kutusu boşsa, öneri kutusunu gizle.
    if (query === "") {
        suggestionsContainer.style.display = "none"; // Arama kutusu boşsa öneri kutusunu gizle.
        return;
    }

    // Eğer önerilerde tam eşleşme varsa, öneri kutusunu gizle.
    if (cryptos.length === 0 || cryptos.some(crypto => crypto.symbol.toLowerCase() === query)) {
        suggestionsContainer.style.display = "none"; // Eğer tam eşleşme varsa öneri kutusunu gizle.
        return;
    }

    suggestionsContainer.style.display = "block"; // Öneri kutusunu göster.

    cryptos.forEach(crypto => {
        const suggestionItem = document.createElement("div");
        suggestionItem.className = "suggestion-item"; // CSS sınıfı ekleyebilirsiniz.
        suggestionItem.textContent = crypto.symbol;
        suggestionItem.onclick = () => {
            document.getElementById("search-input").value = crypto.symbol;
            searchCrypto();
        };
        suggestionsContainer.appendChild(suggestionItem);
    });
}

// Filtreleme işlemi.
function toggleFilter() {
    const ownedFilter = localStorage.getItem("ownedFilter") === "true" ? false : true; // Sahiplik filtresini değiştirir.
    localStorage.setItem("ownedFilter", ownedFilter); // Yeni durumu kaydeder.

    const filterContainer = document.getElementById("filter-container");
    const filterText = document.getElementById("filter-text");
    filterText.textContent = ownedFilter ? "İşlemde Olan Kriptolar" : "Tüm Kriptolar"; // Metni günceller. Sahip Olduğum Kriptolar

    // Filtre durumu değiştiğinde kartları tekrar oluştur.
    const query = document.getElementById("search-input").value.trim().toLowerCase();
    const filteredCryptos = filterCryptos(allCryptos, ownedFilter, query);

    updateCryptoCards(filteredCryptos);

}

// Filtreyi başlatan işlev
let sortState = false; // Varsayılan olarak alfabetik sıralama

// Filtreyi başlatan işlev
function initializeFilterContainer() {
    // Owned filter başlangıç durumu
    const ownedFilter = localStorage.getItem("ownedFilter") === "true";
    const filterContainer = document.getElementById("filter-container");
    const filterText = document.getElementById("filter-text");
    filterText.textContent = ownedFilter ? "Sahip Olduğum Kriptolar" : "Tüm Kriptolar"; // Başlangıç metni.
    filterContainer.onclick = toggleFilter; // Div üzerine tıklama işlevi ekler.

    // SortState başlangıç durumu
    sortState = localStorage.getItem("sortState") === "true";

    const popTextElement = document.getElementById('pop-text');
    popTextElement.textContent = sortState ? "Popüler" : " Alfabetik"; // Başlangıç metni

    calculateOwnedCryptos();
}



// Sıralama durumu değiştirme işlevi
function togglePop() {
    sortState = !sortState; // Durumu tersine çevir

    localStorage.setItem("sortState", sortState.toString()); // Yeni durumu kaydeder

    const popTextElement = document.getElementById('pop-text');
    popTextElement.textContent = sortState ? "Popüler" : " Alfabetik"; // Başlangıç metni

    if (!currentCryptos || currentCryptos.length === 0) {
        console.log("Gösterilecek kripto yok.");
        return;
    }

    updateCryptoCards(currentCryptos); // Kartları sıralanmış şekilde güncelle
}
// Kriptoları sıralama işlevi
function sortCryptos(cryptos, sortState) {
    let sortedCryptos = [...cryptos]; // Mevcut kriptoların bir kopyasını al

    if (sortState) {
        // En çok emire sahip olanları, sonra en son tarihli emirlere göre sıralama
        sortedCryptos.sort((a, b) => {
            const ordersA = orders.find(o => o.symbol === a.symbol)?.orders || [];
            const ordersB = orders.find(o => o.symbol === b.symbol)?.orders || [];

            // Emir sayısına göre azalan sırada sıralama
            if (ordersB.length !== ordersA.length) {
                return ordersB.length - ordersA.length;
            }

            // Eğer emir sayısı aynıysa, en son tarihe göre sıralama
            const latestOrderA = ordersA.reduce((latest, order) => {
                const orderDate = new Date(order.buy.time); // Alış zamanını kullanıyoruz
                return (!latest || orderDate > new Date(latest.buy.time)) ? order : latest;
            }, null);

            const latestOrderB = ordersB.reduce((latest, order) => {
                const orderDate = new Date(order.buy.time); // Alış zamanını kullanıyoruz
                return (!latest || orderDate > new Date(latest.buy.time)) ? order : latest;
            }, null);

            const dateA = latestOrderA ? new Date(latestOrderA.buy.time) : new Date(0); // Varsayılan en eski tarih
            const dateB = latestOrderB ? new Date(latestOrderB.buy.time) : new Date(0); // Varsayılan en eski tarih

            return dateB - dateA; // Tarihe göre azalan sıralama
        });
    } else {
        // Alfabetik sıralama
        sortedCryptos.sort((a, b) => a.symbol.localeCompare(b.symbol));
    }

    return sortedCryptos;
}

// Sayfa yüklendiğinde filtreyi başlat
document.addEventListener("DOMContentLoaded", function() {
    initializeFilterContainer();
});

