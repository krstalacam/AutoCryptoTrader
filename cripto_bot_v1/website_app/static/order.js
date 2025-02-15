async function showOrders(symbol) {
    const modal = document.getElementById("order-modal");
    const ordersContainer = document.getElementById("orders-container");

    // Modal içeriğini temizle
    ordersContainer.innerHTML = "";

    // Sembol için orders içinden veriyi bul
    const cryptoData = orders.find(item => item.symbol === symbol);

    let totalProfit = 0;

    // İşlem ücreti oranı (binde 1, yani %0.1)
    const transactionFeeRate = 0.001; // 0.1%

    // 100 dolarlık bir işlem varsayalım
    const balance = 100;

    if (cryptoData && cryptoData.orders.length > 0) {
        // Orders array'ini ters çevir (en sonuncu en üstte olacak)
        const reversedOrders = [...cryptoData.orders].reverse();

        reversedOrders.forEach(order => {
            // Alım ve satım fiyatları ile ilgili bilgi grubu
            const orderGroup = document.createElement("div");
            orderGroup.className = "order-group";

            if (order.buy && order.sell) {
                // Alım ve satım fiyatlarını işlem ücretiyle hesapla
                const buyPriceWithFee = order.buy.price * (1 + transactionFeeRate);
                const sellPriceWithFee = order.sell.price * (1 - transactionFeeRate);

                // Alım ve satım bilgilerini oluştur (gereksiz sıfırları kaldır)
                const buyDiv = document.createElement("div");
                buyDiv.className = "buy-info";
                buyDiv.textContent = `Alındı: ${Number(order.buy.price.toFixed(8))} (${order.buy.time})`;

                const sellDiv = document.createElement("div");
                sellDiv.className = "sell-info";
                sellDiv.textContent = `Satıldı: ${Number(order.sell.price.toFixed(8))} (${order.sell.time})`;

                // Kârı hesapla
                const diff = ((sellPriceWithFee - buyPriceWithFee) / buyPriceWithFee) * balance;

                // diff değerini 2 ondalıklı basamağa yuvarla ama float olarak tut
                const roundedDiff = Math.round(diff * 100) / 100;

                const percentageDiv = document.createElement("div");
                percentageDiv.className = "percentage-diff";

                // Yuvarlanmış diff'i yüzde olarak göster
                percentageDiv.textContent = `${roundedDiff.toFixed(2)}%`;

                console.log(roundedDiff); // Konsolda da yuvarlanmış değeri göster

                // Kârın pozitif, negatif veya nötr olduğunu belirle
                percentageDiv.classList.add(roundedDiff > 0 ? "percentage-positive" : (roundedDiff < 0 ? "percentage-negative" : "percentage-normal"));

                // Toplam kârı güncelle
                totalProfit += diff;

                // Alım ve satım bilgilerini gruba ekle
                orderGroup.appendChild(buyDiv);
                orderGroup.appendChild(sellDiv);
                orderGroup.appendChild(percentageDiv);
            }
            else if (order.buy && !order.sell) {
                // Eğer sadece "Al" varsa, son fiyatı kullan
                const buyPrice = order.buy.price;

                // Son fiyatı sembole göre al
                const currentPrice = prices.find(price => price.symbol === symbol)?.close || 0;

                if (currentPrice) {
                    // Satış fiyatını işlem ücretiyle hesapla
                    const sellPriceWithFee = currentPrice * (1 - transactionFeeRate);

                    // Kârı hesapla (alım ve satım fiyatı arasındaki fark)
                    const diff = ((sellPriceWithFee - buyPrice) / buyPrice) * balance;

                    // Yüzdelik farkı hesapla ve göster
                    const percentageDiv = document.createElement("div");
                    percentageDiv.className = "percentage-diff";
                    percentageDiv.textContent = `${diff.toFixed(2)}%`;

                    // Kârın pozitif veya negatif olduğunu belirle
                    percentageDiv.classList.add(diff > 0 ? "percentage-positive" : (diff < 0 ? "percentage-negative" : "percentage-normal"));

                    // Toplam kârı güncelle
                    totalProfit += diff;

                    // Alım bilgilerini ve yüzdelik farkı gruba ekle
                    const buyDiv = document.createElement("div");
                    buyDiv.className = "buy-info";
                    buyDiv.textContent = `Alındı: ${Number(buyPrice.toFixed(8))} (${order.buy.time})`;
                    orderGroup.appendChild(buyDiv);
                    orderGroup.appendChild(percentageDiv);
                } else {
                    // Son fiyat yoksa bilgi mesajı
                    const incompleteDiv = document.createElement("div");
                    incompleteDiv.textContent = "Son fiyat bilgisi mevcut değil.";
                    orderGroup.appendChild(incompleteDiv);
                }
            }
            else {
                // Eğer emir eksikse bilgi mesajı göster
                const incompleteDiv = document.createElement("div");
                incompleteDiv.textContent = "Eksik emir bilgisi.";
                orderGroup.appendChild(incompleteDiv);
            }

            // Grubu emirlere ekle
            ordersContainer.appendChild(orderGroup);
        });
    } else {
        // Eğer emir yoksa bilgi mesajı göster
        const noOrdersDiv = document.createElement("div");
        noOrdersDiv.textContent = "Bu kripto için herhangi bir emir bulunmamaktadır.";
        ordersContainer.appendChild(noOrdersDiv);
    }

    // Modalı göster
    modal.style.display = "block";

    // Kripto sembolünü ve toplam kârı göster
    const cryptoSymbolElement = document.getElementById("crypto-symbol");
    const totalProfitElement = document.querySelector(".total-profit");

    // Sembolle toplam kârı ayarla
    cryptoSymbolElement.textContent = symbol;
    totalProfitElement.textContent = `Toplam Kâr: ${totalProfit.toFixed(2)}%`;

    // Eski sınıfları temizle ve uygun sınıf ekle
    totalProfitElement.classList.remove("negative", "positive", "normal");

    if (totalProfit < 0) {
        totalProfitElement.classList.add("negative");
    } else if (totalProfit > 0) {
        totalProfitElement.classList.add("positive");
    } else {
        totalProfitElement.classList.add("normal");
    }
}
// Modalı kapatmak için fonksiyon
function closeModal() {
    const modal = document.getElementById("order-modal");
    modal.style.display = "none";
}
