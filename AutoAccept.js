// AutoAccept.js — secure matcher (message+no-give+expected partner) + masked logging
require('dotenv').config();

const SteamUser = require('steam-user');
const TradeOfferManager = require('steam-tradeoffer-manager');
const SteamTotp = require('steam-totp');

// --- ENV (Bank/Receiver account) ---
const username = process.env.BankAccountUsername;
const password = process.env.BankAccountPassword;
const sharedSecret = process.env.BankAccountSharedSecret;

// Opsiyonel ama önerilen: sadece bu hesaptan gelen teklifleri kabul et
const EXPECTED_SENDER_STEAMID = process.env.EXPECTED_SENDER_STEAMID || null;

if (!username || !password || !sharedSecret) {
  console.error("HATA: .env eksik. BankAccountUsername/Password/SharedSecret gerekli.");
  process.exit(1);
}

// --- CLI arg: trade key ---
const tradeKey = process.argv[2];
if (!tradeKey || tradeKey.length < 16) {
  console.error("HATA: Trade key eksik veya çok kısa (>=16 olmalı).");
  process.exit(1);
}
const maskedKey = tradeKey.slice(0, 4) + "…" + tradeKey.slice(-4);

// --- Steam setup ---
const client = new SteamUser();
const manager = new TradeOfferManager({ steam: client, language: "en" });

const RETRY_INTERVAL = 15_000; // 15s
const twoFactorCode = SteamTotp.generateAuthCode(sharedSecret);

client.logOn({
  accountName: username,
  password: password,
  twoFactorCode
});

client.on('loggedOn', () => {
  console.log("BankAccount giriş yaptı. AutoAccept dinlemede. Key:", maskedKey);
  client.setPersona(SteamUser.EPersonaState.Online);
});

client.on('webSession', (sessionID, cookies) => {
  manager.setCookies(cookies, (err) => {
    if (err) {
      console.error("TradeOfferManager cookie hatası:", err);
      process.exit(1);
    }
    tick();
  });
});

// --- Güvenlik kontrolleri ---
function isOfferSafeForUs(offer) {
  // Bizden item çıkmamalı
  const giving = offer.itemsToGive || [];
  const receiving = offer.itemsToReceive || [];
  if (giving.length !== 0) return false;
  if (receiving.length === 0) return false;

  // Beklenen partner ise kontrol et
  if (EXPECTED_SENDER_STEAMID) {
    try {
      const partner64 = offer.partner.getSteamID64();
      if (partner64 !== EXPECTED_SENDER_STEAMID) return false;
    } catch {
      return false;
    }
  }
  return true;
}

function tick() {
  manager.getOffers(TradeOfferManager.EOfferFilter.ActiveOnly, (err, sent, received) => {
    if (err) {
      console.error("Teklifler alınamadı, tekrar denenecek:", err.message || err);
      return setTimeout(tick, RETRY_INTERVAL);
    }

    const match = (received || []).find(offer =>
      offer.state === TradeOfferManager.ETradeOfferState.Active &&
      offer.message === tradeKey &&
      isOfferSafeForUs(offer)
    );

    if (!match) {
      console.log("Eşleşen GÜVENLİ teklif yok. 15 sn sonra tekrar bakılacak.");
      return setTimeout(tick, RETRY_INTERVAL);
    }

    console.log("Eşleşen ve güvenli teklif bulundu. Kabul ediliyor...");
    match.accept(false, (err) => {
      if (err) {
        console.error("Kabul hatası, tekrar denenecek:", err.message || err);
        return setTimeout(tick, RETRY_INTERVAL);
      }
      console.log("Teklif kabul edildi. AutoAccept kapanıyor.");
      process.exit(0);
    });
  });
}

// Process yaşamı: beklenmedik hata yakalama
process.on('uncaughtException', (e) => {
  console.error("Yakalanmamış hata:", e?.stack || e);
  setTimeout(() => process.exit(1), 250);
});
process.on('unhandledRejection', (e) => {
  console.error("Yakalanmamış promise reddi:", e);
  setTimeout(() => process.exit(1), 250);
});
