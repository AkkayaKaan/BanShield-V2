require('dotenv').config({ path: __dirname + '/.env' });

const SteamUser = require('steam-user');
const TradeOfferManager = require('steam-tradeoffer-manager');
const SteamTotp = require('steam-totp');
const os = require('os');
const path = require('path');
const { spawn } = require('child_process');

console.log("[WatchDog] Started.");

const USERNAME = process.env.BankAccountUsername;
const PASSWORD = process.env.BankAccountPassword;
const SHARED_SECRET = process.env.BankAccountSharedSecret;

const TIMEOUT = 5 * 60 * 1000; // 5 minutes
const CHECK_INTERVAL = 5000;   // 5 seconds

function fullscreenError(reason) {
    if (os.platform() === 'win32') {
        process.stdout.write('\x1b[2J');
        try { require('child_process').execSync('mode con: cols=120 lines=40'); } catch {}
    }
    process.stdout.write('\x1b[41m\x1b[97m');
    for (let i = 0; i < 12; ++i) console.log('');
    for (let i = 0; i < 4; ++i) console.log(' '.repeat(32) + 'ERROR DETECTED'.padStart(24).padEnd(48));
    for (let i = 0; i < 2; ++i) console.log('');
    if (reason) console.log(' '.repeat(24) + reason.toUpperCase());
    for (let i = 0; i < 8; ++i) console.log('');
    process.stdout.write('\x1b[0m');
    setTimeout(() => { process.exit(1); }, 30000);
}

process.on('uncaughtException', (err) => {
    console.log('[WatchDog] UNCAUGHT ERROR:', err);
    fullscreenError('Script error!');
});

const client = new SteamUser();
const manager = new TradeOfferManager({
    steam: client,
    language: "en"
});
const twoFactorCode = SteamTotp.generateAuthCode(SHARED_SECRET);

client.logOn({
    accountName: USERNAME,
    password: PASSWORD,
    twoFactorCode: twoFactorCode
});

let offerFound = false;
let offerID = null;
let offerTime = null;
let timeoutTrade;
let timeoutAccept;
let attemptCount = 0; // Track number of 5-min loops

client.on('loggedOn', () => {
    console.log("[WatchDog] Logged into Steam.");
    client.setPersona(SteamUser.EPersonaState.Online);
});

client.on('webSession', (sessionID, cookies) => {
    manager.setCookies(cookies, (err) => {
        if (err) {
            console.error("[WatchDog] TradeOfferManager session error:", err);
            fullscreenError("Session error");
            return;
        }
        console.log("[WatchDog] Session established, watching for incoming trade offers...");
        waitForTradeOffer();
    });
});

function waitForTradeOffer() {
    const start = Date.now();
    offerFound = false;
    offerID = null;
    offerTime = null;

    timeoutTrade = setInterval(() => {
        if (Date.now() - start > TIMEOUT && !offerFound) {
            clearInterval(timeoutTrade);

            attemptCount += 1;

            if (attemptCount === 1) {
                // First loop: start SendTrade.js
                console.log("[WatchDog] No trade received in first 5 minutes. Launching SendTrade.js and restarting offer watch...");
                launchScript('SendTrade.js');
            } else {
                // Next loops: start AutoAccept.js
                console.log("[WatchDog] No trade received. Launching AutoAccept.js and restarting offer watch...");
                launchScript('AutoAccept.js');
            }

            setTimeout(() => {
                waitForTradeOffer();
            }, 2000);
            return;
        }
        manager.getOffers(TradeOfferManager.EOfferFilter.ActiveOnly, (err, sent, received) => {
            if (err) {
                console.error("[WatchDog] getOffers error:", err.message || err);
                return;
            }
            const activeOffers = received.filter(offer => offer.state === TradeOfferManager.ETradeOfferState.Active);
            if (activeOffers.length > 0) {
                offerFound = true;
                offerID = activeOffers[0].id;
                offerTime = Date.now();
                clearInterval(timeoutTrade);
                console.log(`[WatchDog] Trade offer detected: ID ${offerID}. Now watching for acceptance...`);
                waitForAccept(offerID);
            } else {
                console.log("[WatchDog] Still waiting for a trade offer...");
            }
        });
    }, CHECK_INTERVAL);
}

function waitForAccept(offerId) {
    offerTime = Date.now();
    timeoutAccept = setInterval(() => {
        if (Date.now() - offerTime > TIMEOUT) {
            clearInterval(timeoutAccept);
            console.log("[WatchDog] Trade was not accepted within 5 minutes.");
            fullscreenError("Trade not accepted!");
        }
        manager.getOffer(offerId, (err, offer) => {
            if (err) {
                console.error("[WatchDog] getOffer error:", err.message || err);
                return;
            }
            if (offer.state === TradeOfferManager.ETradeOfferState.Accepted) {
                console.log("[WatchDog] Trade offer accepted! Exiting.");
                process.exit(0);
            }
            if (offer.state === TradeOfferManager.ETradeOfferState.Declined
                || offer.state === TradeOfferManager.ETradeOfferState.Canceled) {
                clearInterval(timeoutAccept);
                console.log("[WatchDog] Trade offer declined or canceled.");
                fullscreenError("Offer canceled or declined!");
            } else {
                console.log(`[WatchDog] Waiting for trade acceptance... Current state: ${offer.state}`);
            }
        });
    }, CHECK_INTERVAL);
}

function launchScript(filename) {
    try {
        console.log(`[WatchDog] Launching ${filename}...`);
        if (os.platform() === 'win32') {
            spawn('cmd.exe', ['/c', 'start', '', 'node', filename], {
                detached: true,
                stdio: 'ignore'
            }).unref();
        } else {
            spawn('node', [filename], {
                detached: true,
                stdio: 'ignore'
            }).unref();
        }
    } catch (e) {
        console.error(`[WatchDog] Failed to launch ${filename}:`, e);
    }
}
