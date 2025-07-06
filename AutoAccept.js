require('dotenv').config();

const SteamUser = require('steam-user');
const TradeOfferManager = require('steam-tradeoffer-manager');
const SteamTotp = require('steam-totp');

const username = process.env.BankAccountUsername;
const password = process.env.BankAccountPassword;
const sharedSecret = process.env.BankAccountSharedSecret;

if (!username || !password || !sharedSecret) {
    console.error("Tüm .env bilgileri eksiksiz olmalı!");
    process.exit(1);
}

const tradeKey = process.argv[2];
if (!tradeKey || tradeKey.length < 10) {
    console.error("Trade key parametresi eksik veya kısa!");
    process.exit(1);
}

const client = new SteamUser();
const manager = new TradeOfferManager({
    steam: client,
    language: "en"
});
const RETRY_INTERVAL = 15000; // 15 saniye

const twoFactorCode = SteamTotp.generateAuthCode(sharedSecret);

client.logOn({
    accountName: username,
    password: password,
    twoFactorCode: twoFactorCode
});

client.on('loggedOn', () => {
    console.log("BankAccount Steam'e giriş yaptı, bekleniyor...");
    client.setPersona(SteamUser.EPersonaState.Online);
});

client.on('webSession', (sessionID, cookies) => {
    manager.setCookies(cookies, (err) => {
        if (err) {
            console.error("TradeOfferManager oturum hatası:", err);
            process.exit(1);
        }
        checkForMatchingTrade();
    });
});

// --- DÜZELTİLEN FONKSİYON ---
function checkForMatchingTrade() {
    // Eski: manager.getOffers(TradeOfferManager.EOfferFilter.Pending, ...)
    manager.getOffers(TradeOfferManager.EOfferFilter.ActiveOnly, (err, sent, received) => {
        if (err) {
            console.error("Trade teklifleri alınamadı, 15 saniye sonra tekrar denenecek...", err.message || err);
            setTimeout(checkForMatchingTrade, RETRY_INTERVAL);
            return;
        }
        const match = received.find(offer => offer.message === tradeKey && offer.state === TradeOfferManager.ETradeOfferState.Active);
        if (match) {
            console.log("Eşleşen takas teklifi bulundu! Teklif kabul ediliyor...");
            match.accept(false, (err) => {
                if (err) {
                    console.error("Takas teklifi kabul edilemedi, 15 saniye sonra tekrar denenecek...", err.message || err);
                    setTimeout(checkForMatchingTrade, RETRY_INTERVAL);
                } else {
                    console.log("Takas teklifi başarıyla kabul edildi! AutoAccept.js kapanıyor.");
                    process.exit(0);
                }
            });
        } else {
            console.log("Henüz eşleşen takas yok. 15 saniye sonra tekrar denenecek...");
            setTimeout(checkForMatchingTrade, RETRY_INTERVAL);
        }
    });
}
