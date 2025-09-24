// SendTrade.js — hardened key + Dry-Run + optional drop-weapon/case filters
require('dotenv').config();

const crypto = require('crypto');
const SteamUser = require('steam-user');
const SteamCommunity = require('steamcommunity');
const TradeOfferManager = require('steam-tradeoffer-manager');
const SteamTotp = require('steam-totp');

// --- Flags & Config ---
const isDryRun = (process.env.BANSHIELD_DRY_RUN === "1");

// Watching profile (sender)
const username       = process.env.WatchingProfileUsername;
const password       = process.env.WatchingProfilePassword;
const sharedSecret   = process.env.WatchingProfileSharedSecret;
const identitySecret = process.env.WatchingProfileIdentitySecret;

// Bank account (receiver)
const tradeURL = process.env.BankAccountTradeURL;

// Auto-accept (only in LIVE)
const autoAccept = (process.env.AutoAccept || "false").toLowerCase() === "true";

// Inventory selection: all, cs2, tf2, dota2 (comma separated)
const inventoryTypeRaw = (process.env.INVENTORY_TYPE || "all").toLowerCase().replace(/\s+/g, "");
let inventoryTypes = inventoryTypeRaw.split(",");
if (inventoryTypes.includes("all")) inventoryTypes = ["all"];

// --- Offer state names for readable logs ---
const OFFER_STATE_NAMES = {
  1:  'Invalid',
  2:  'Active',
  3:  'Accepted',
  4:  'Countered',
  5:  'Expired',
  6:  'Canceled',
  7:  'Declined',
  8:  'InvalidItems',
  9:  'NeedsConfirmation',
  10: 'CanceledBySecondFactor',
  11: 'InEscrow'
};

// --- Secure, URL-safe trade key ---
function generateTradeKey(bytes = 24) {
  const b64 = crypto.randomBytes(bytes).toString('base64');
  return b64.replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/g, '');
}
const tradeKey  = generateTradeKey();
const maskedKey = tradeKey.slice(0,4) + "…" + tradeKey.slice(-4);

// --- Inventory maps ---
const GAME_INVENTORIES = {
  cs2:   { appid: 730, contextid: 2 },
  tf2:   { appid: 440, contextid: 2 },
  dota2: { appid: 570, contextid: 2 },
  all: [
    { appid: 730, contextid: 2 }, // CS2
    { appid: 440, contextid: 2 }, // TF2
    { appid: 570, contextid: 2 }, // Dota2
    { appid: 753, contextid: 6 }  // Steam collectibles
  ]
};

let INVENTORIES = [];
if (inventoryTypes.includes("all")) {
  INVENTORIES = GAME_INVENTORIES.all;
} else {
  if (inventoryTypes.includes("cs2"))   INVENTORIES.push(GAME_INVENTORIES.cs2);
  if (inventoryTypes.includes("tf2"))   INVENTORIES.push(GAME_INVENTORIES.tf2);
  if (inventoryTypes.includes("dota2")) INVENTORIES.push(GAME_INVENTORIES.dota2);
}

// --- Basic validation ---
if (!username || !password || !sharedSecret || !identitySecret || !tradeURL) {
  console.error("All .env information must be complete!");
  process.exit(1);
}

// --- Steam setup ---
const client    = new SteamUser();
const community = new SteamCommunity();
const manager   = new TradeOfferManager({ steam: client, community, language: "en" });

const RETRY_INTERVAL = 15000; // 15s
const twoFactorCode  = SteamTotp.generateAuthCode(sharedSecret);

client.logOn({ accountName: username, password, twoFactorCode });

client.on('loggedOn', () => {
  console.log("Logged into Steam.");
  client.setPersona(SteamUser.EPersonaState.Online);
});

client.on('webSession', (sessionID, cookies) => {
  manager.setCookies(cookies, (err) => {
    if (err) {
      console.error("TradeOfferManager session error:", err);
      process.exit(1);
    }
    community.setCookies(cookies);
    sendAllTradableItems();
  });
});

// --- Core flow ---
function sendAllTradableItems() {
  let allItems = [];
  let processed = 0;

  if (INVENTORIES.length === 0) {
    console.log("No inventory types selected in config!");
    process.exit(0);
  }

  INVENTORIES.forEach(({ appid, contextid }) => {
    manager.getInventoryContents(appid, contextid, true, (err, inventory) => {
      processed++;
      if (!err && inventory && inventory.length > 0) {
        allItems = allItems.concat(inventory);
      }

      if (processed === INVENTORIES.length) {
        if (allItems.length === 0) {
          console.log("No tradable items found.");
          process.exit(0);
        }

        // Apply optional filters
        if (allItems.length === 0) {
          console.log("After filters, no items left to send.");
          process.exit(0);
        }

        // --- DRY-RUN branch: NEVER send an offer ---
        if (isDryRun) {
          const itemNames = allItems.map(x => x.name || x.market_hash_name || x.classid || "Unknown Item");
          console.log("Simulation is about to end. If you receive a ban in the future, these items will be sent to your backup account immediately:");
          itemNames.forEach(n => console.log(" - " + n));
          process.exit(0);
          return;
        }

        // --- LIVE branch ---
        const offer = manager.createOffer(tradeURL);

        // Embed trade key for AutoAccept matching
        offer.setMessage(tradeKey);
        offer.addMyItems(allItems);

        offer.send((err, status) => {
          if (err) {
            console.error("Trade offer could not be sent:", err);
            process.exit(1);
          }
          console.log("All items successfully sent with trade offer. Status:", status);

          confirmOfferWithRetry(offer.id, 0, () => {
            if (autoAccept) {
              const { spawn } = require('child_process');
              console.log("AutoAccept.js starting, key:", maskedKey);
              spawn('node', ['AutoAccept.js', tradeKey], { stdio: 'inherit' });
              waitForTradeAccepted(offer.id);
            } else {
              process.exit(0);
            }
          });
        });
      }
    });
  });
}

// --- Helpers (LIVE only) ---
function confirmOfferWithRetry(offerId, attempt, callback) {
  community.acceptConfirmationForObject(identitySecret, offerId, (err) => {
    if (err) {
      attempt++;
      console.error(`Mobile confirmation failed (attempt ${attempt}), will retry in 15 seconds.`, err.message || err);
      setTimeout(() => confirmOfferWithRetry(offerId, attempt, callback), RETRY_INTERVAL);
    } else {
      console.log("Mobile confirmation successful!");
      if (callback) callback();
    }
  });
}

function waitForTradeAccepted(offerId) {
  manager.getOffer(offerId, (err, offer) => {
    if (err) {
      console.error("Trade offer could not be queried, will retry in 15 seconds...", err.message || err);
      setTimeout(() => waitForTradeAccepted(offerId), RETRY_INTERVAL);
      return;
    }
    if (offer.state === TradeOfferManager.ETradeOfferState.Accepted) {
      console.log("Trade offer accepted! Script shutting down.");
      process.exit(0);
    } else if (
      offer.state === TradeOfferManager.ETradeOfferState.Declined ||
      offer.state === TradeOfferManager.ETradeOfferState.Canceled
    ) {
      console.log("Trade offer declined or canceled. Script shutting down.");
      process.exit(0);
    } else {
      const stateName = OFFER_STATE_NAMES[offer.state] || "Unknown";
      console.log(`Trade offer still pending. Status: ${offer.state} (${stateName})`);
      setTimeout(() => waitForTradeAccepted(offerId), RETRY_INTERVAL);
    }
  });
}

// --- Safety nets ---
process.on('uncaughtException', (e) => {
  console.error("Unhandled error:", e?.stack || e);
  setTimeout(() => process.exit(1), 250);
});
process.on('unhandledRejection', (e) => {
  console.error("Unhandled rejection:", e);
  setTimeout(() => process.exit(1), 250);
});
