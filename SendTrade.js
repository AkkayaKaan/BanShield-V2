require('dotenv').config();

const SteamUser = require('steam-user');
const SteamCommunity = require('steamcommunity');
const TradeOfferManager = require('steam-tradeoffer-manager');
const SteamTotp = require('steam-totp');

// Table mapping status names
const OFFER_STATE_NAMES = {
    1: 'Invalid',
    2: 'Active',
    3: 'Accepted',
    4: 'Countered',
    5: 'Expired',
    6: 'Canceled',
    7: 'Declined',
    8: 'InvalidItems',
    9: 'NeedsConfirmation',
    10: 'CanceledBySecondFactor',
    11: 'InEscrow'
};

function generateRandomKey(length) {
    const chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
    let key = "";
    for (let i = 0; i < length; i++) {
        key += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return key;
}

const tradeKey = generateRandomKey(14);
const username = process.env.WatchingProfileUsername;
const password = process.env.WatchingProfilePassword;
const sharedSecret = process.env.WatchingProfileSharedSecret;
const identitySecret = process.env.WatchingProfileIdentitySecret;
const tradeURL = process.env.BankAccountTradeURL;
const autoAccept = (process.env.AutoAccept || "false").toLowerCase() === "true";

if (!username || !password || !sharedSecret || !identitySecret || !tradeURL) {
    console.error("All .env information must be complete!");
    process.exit(1);
}

const client = new SteamUser();
const community = new SteamCommunity();
const manager = new TradeOfferManager({
    steam: client,
    community: community,
    language: "en"
});

const INVENTORIES = [
    { appid: 730, contextid: 2 },   // CS:GO
    { appid: 440, contextid: 2 },   // TF2
    { appid: 570, contextid: 2 },   // Dota2
    { appid: 753, contextid: 6 },   // Steam collectible cards and gifts
];

const RETRY_INTERVAL = 15000; // 15 seconds

const twoFactorCode = SteamTotp.generateAuthCode(sharedSecret);

client.logOn({
    accountName: username,
    password: password,
    twoFactorCode: twoFactorCode
});

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

function sendAllTradableItems() {
    let allItems = [];
    let processed = 0;

    INVENTORIES.forEach(({appid, contextid}) => {
        manager.getInventoryContents(appid, contextid, true, (err, inventory) => {
            processed++;
            if (!err && inventory.length > 0) {
                allItems = allItems.concat(inventory);
            }
            if (processed === INVENTORIES.length) {
                if (allItems.length === 0) {
                    console.log("No tradable items found.");
                    process.exit(0);
                }
                const offer = manager.createOffer(tradeURL);

                offer.setMessage(tradeKey); // Critical line: trade offer description key!
                offer.addMyItems(allItems);

                offer.send((err, status) => {
                    if (err) {
                        console.error("Trade offer could not be sent:", err);
                        process.exit(1);
                    }
                    console.log("All items successfully sent with trade offer. Status:", status);
                    // Retry mobile confirmation
                    confirmOfferWithRetry(offer.id, 0, () => {
                        if (autoAccept) {
                            // Start AutoAccept.js
                            const { spawn } = require('child_process');
                            console.log("AutoAccept.js starting, key:", tradeKey);
                            const child = spawn('node', ['AutoAccept.js', tradeKey], { stdio: 'inherit' });
                            // (Remove process.exit(0) to wait, trade accepted will be monitored)
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

// Function to retry mobile confirmation
function confirmOfferWithRetry(offerId, attempt, callback) {
    community.acceptConfirmationForObject(identitySecret, offerId, (err) => {
        if (err) {
            attempt++;
            console.error(`Mobile confirmation failed (attempt ${attempt}), will retry in 15 seconds...`, err.message || err);
            setTimeout(() => {
                confirmOfferWithRetry(offerId, attempt, callback);
            }, RETRY_INTERVAL);
        } else {
            console.log("Mobile confirmation successful!");
            if (callback) callback();
        }
    });
}

// Function to wait for trade accepted
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
        } else if (offer.state === TradeOfferManager.ETradeOfferState.Declined
                   || offer.state === TradeOfferManager.ETradeOfferState.Canceled) {
            console.log("Trade offer declined or canceled. Script shutting down.");
            process.exit(0);
        } else {
            console.log("Trade offer still pending. Status: " + offer.state + " (" + (OFFER_STATE_NAMES[offer.state] || "Unknown") + ")");
            setTimeout(() => waitForTradeAccepted(offerId), RETRY_INTERVAL);
        }
    });
}