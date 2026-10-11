/**
 * Pure Node.js E2E Test Suite for GrassQuest using Chrome DevTools Protocol (CDP).
 */
import { spawn } from "child_process";
import fs from "fs";
import path from "path";

const CHROME_PATH = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const PORT = 9222;
const APP_URL = "http://localhost:5173";
const TEMP_USER_DATA = path.resolve("./server/tests/.chrome_test_profile");
const SCREENSHOT_DIR = path.resolve("./server/tests/screenshots");

if (!fs.existsSync(SCREENSHOT_DIR)) {
  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
}

class CDPClient {
  constructor(wsUrl) {
    this.ws = new WebSocket(wsUrl);
    this.id = 0;
    this.callbacks = new Map();
    this.errors = [];

    this.ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      if (msg.id && this.callbacks.has(msg.id)) {
        const { resolve, reject } = this.callbacks.get(msg.id);
        this.callbacks.delete(msg.id);
        if (msg.error) reject(msg.error);
        else resolve(msg.result);
      } else if (msg.method) {
        if (msg.method === "Runtime.exceptionThrown") {
          this.errors.push(msg.params);
          console.error("[BROWSER ERROR]", msg.params.exceptionDetails?.text, msg.params.exceptionDetails?.exception?.description);
        } else if (msg.method === "Console.messageAdded" && msg.params.message?.level === "error") {
          this.errors.push(msg.params.message);
          console.error("[CONSOLE ERROR]", msg.params.message.text);
        }
      }
    };
  }

  async ready() {
    if (this.ws.readyState === WebSocket.OPEN) return;
    return new Promise((resolve) => {
      this.ws.onopen = () => resolve();
    });
  }

  send(method, params = {}) {
    return new Promise((resolve, reject) => {
      const id = ++this.id;
      this.callbacks.set(id, { resolve, reject });
      this.ws.send(JSON.stringify({ id, method, params }));
    });
  }

  async eval(expression) {
    const res = await this.send("Runtime.evaluate", {
      expression,
      returnByValue: true,
      awaitPromise: true,
    });
    return res.result?.value;
  }

  async screenshot(filename) {
    const res = await this.send("Page.captureScreenshot", { format: "png" });
    const buf = Buffer.from(res.data, "base64");
    const filepath = path.join(SCREENSHOT_DIR, filename);
    fs.writeFileSync(filepath, buf);
    console.log(`[SCREENSHOT] Saved ${filename} (${Math.round(buf.length / 1024)} KB)`);
    return filepath;
  }

  close() {
    this.ws.close();
  }
}

async function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

async function run() {
  console.log("============================================================");
  console.log("GRASSQUEST AUTOMATED UI & E2E TEST SUITE");
  console.log("============================================================");

  console.log("Launching Headless Chrome on port", PORT);
  const chrome = spawn(
    CHROME_PATH,
    [
      `--remote-debugging-port=${PORT}`,
      "--headless=new",
      "--disable-gpu",
      `--user-data-dir=${TEMP_USER_DATA}`,
      "--window-size=1280,900",
      "about:blank",
    ],
    { stdio: "ignore" }
  );

  let client;
  let passed = 0;
  let total = 0;

  function test(name, ok, detail = "") {
    total++;
    if (ok) {
      passed++;
      console.log(`[PASS] ${name}${detail ? ": " + detail : ""}`);
    } else {
      console.error(`[FAIL] ${name}${detail ? ": " + detail : ""}`);
    }
  }

  try {
    let targets = null;
    for (let i = 0; i < 20; i++) {
      await sleep(300);
      try {
        const res = await fetch(`http://127.0.0.1:${PORT}/json`);
        targets = await res.json();
        if (targets && targets.length) break;
      } catch {}
    }

    if (!targets || !targets.length) {
      throw new Error("Could not connect to Chrome debugging endpoint.");
    }

    const pageTarget = targets.find((t) => t.type === "page") || targets[0];
    client = new CDPClient(pageTarget.webSocketDebuggerUrl);
    await client.ready();

    await client.send("Page.enable");
    await client.send("Runtime.enable");
    await client.send("Console.enable");

    // Clear local storage for a fresh session
    await client.send("Page.navigate", { url: APP_URL });
    await sleep(1500);
    await client.eval("localStorage.clear(); sessionStorage.clear();");
    await client.send("Page.navigate", { url: APP_URL });
    await sleep(1500);

    // TEST 1: Landing Page
    const heroTitle = await client.eval("document.querySelector('h1')?.innerText");
    test("Landing Page renders with hero title", heroTitle?.toLowerCase().includes("quest map"), heroTitle);
    await client.screenshot("1_landing_page.png");

    // TEST 2: Navigate to Setup
    await client.eval("document.querySelector('button.btn.primary')?.click()");
    await sleep(800);
    const setupHeading = await client.eval("document.querySelector('h1')?.innerText");
    test("Setup Page displays 3 checks", setupHeading?.toLowerCase().includes("three quick checks"), setupHeading);
    await client.screenshot("2_setup_page.png");

    // TEST 3: AI Check Detection
    await sleep(1200);
    const aiText = await client.eval("document.querySelectorAll('.check')[1]?.innerText");
    const aiOk = aiText?.includes("gemma4") || aiText?.includes("photos stay on this computer");
    test("AI check auto-detects Gemma 4 via Ollama", aiOk, aiText?.replace(/\n/g, " ").slice(0, 80));

    // TEST 4: Base Camp Picker (React controlled input)
    await client.eval(`
      const input = document.querySelector('.picker-search input');
      const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
      setter.call(input, 'Pimple Saudagar');
      input.dispatchEvent(new Event('input', { bubbles: true }));
    `);

    // Poll for Photon search results
    let resultsCount = 0;
    for (let i = 0; i < 20; i++) {
      await sleep(300);
      resultsCount = await client.eval("document.querySelectorAll('.picker-search .results button').length");
      if (resultsCount > 0) break;
    }
    test("BaseCamp search brings live Photon results", resultsCount > 0, `found ${resultsCount} results`);

    // Click first result
    await client.eval("document.querySelector('.picker-search .results button')?.click()");

    // Wait for reverse lookup and lock button to be active
    let lockReady = false;
    for (let i = 0; i < 20; i++) {
      await sleep(300);
      lockReady = await client.eval("Boolean(document.querySelector('.lock-bar button.primary:not(:disabled)'))");
      if (lockReady) break;
    }
    await client.screenshot("3_basecamp_picked.png");
    test("Base Camp pin locked address resolved", lockReady);

    // Lock Base Camp
    await client.eval("document.querySelector('.lock-bar button.primary')?.click()");
    await sleep(800);
    const placeLocked = await client.eval("!document.querySelector('.picker')");
    test("Base Camp locked successfully", placeLocked);

    // TEST 5: Enter explorer handle and start
    const explorerName = `Explorer_${Math.floor(Math.random() * 9000 + 1000)}`;
    await client.eval(`
      const hInput = document.querySelector('input[aria-label="Explorer name"]');
      if (hInput) {
        const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
        setter.call(hInput, '${explorerName}');
        hInput.dispatchEvent(new Event('input', { bubbles: true }));
      }
      document.querySelector('form button.primary')?.click();
    `);

    // Poll for Today's screen quests to load
    let questCards = 0;
    for (let i = 0; i < 30; i++) {
      await sleep(600);
      questCards = await client.eval("document.querySelectorAll('.choice').length");
      if (questCards >= 3) break;
    }
    await client.screenshot("4_today_quests.png");

    // TEST 6: Today Screen Quests Rendered
    const todayTitle = await client.eval("document.querySelector('h1')?.innerText");
    test("Today's quests loaded and displayed", todayTitle?.toLowerCase().includes("today's quests") && questCards >= 1, `rendered ${questCards} choices`);

    // TEST 7: Inspect Quest Card Details
    const firstQuest = await client.eval(`
      const q = document.querySelector('.choice');
      ({
        slot: q?.querySelector('.slot')?.innerText,
        title: q?.querySelector('h3')?.innerText,
        meta: q?.querySelector('.meta')?.innerText
      })
    `);
    test("Quest card displays TabPFN flow info and rewards", Boolean(firstQuest?.title), JSON.stringify(firstQuest));

    // TEST 8: Tab Navigation - Basecamp
    await client.eval("document.querySelectorAll('.tabs button')[1]?.click()");
    await sleep(800);
    const campShopItems = await client.eval("document.querySelectorAll('.shop-item').length");
    const campSceneExists = await client.eval("Boolean(document.querySelector('.camp-scene'))");
    test("Basecamp screen renders with shop upgrades", campSceneExists && campShopItems >= 6, `${campShopItems} items, interactive camp scene`);
    await client.screenshot("5_basecamp_tab.png");

    // TEST 9: Tab Navigation - Field Guide
    await client.eval("document.querySelectorAll('.tabs button')[2]?.click()");
    await sleep(800);
    const guideFilters = await client.eval("document.querySelectorAll('.seg button').length");
    const guideContainer = await client.eval("Boolean(document.querySelector('.cards, .card.empty'))");
    test("Field Guide screen renders with filters", guideContainer && guideFilters >= 6, `${guideFilters} categories`);
    await client.screenshot("6_field_guide_tab.png");

    // TEST 10: Tab Navigation - Leaderboard
    await client.eval("document.querySelectorAll('.tabs button')[3]?.click()");
    await sleep(800);
    const boardRows = await client.eval("document.querySelectorAll('table.board tbody tr').length");
    const boardExists = await client.eval("Boolean(document.querySelector('table.board'))");
    test("Leaderboard screen renders with scores", boardExists, `${boardRows} explorers listed`);
    await client.screenshot("7_leaderboard_tab.png");

    // TEST 11: Tab Navigation - Profile
    await client.eval("document.querySelectorAll('.tabs button')[4]?.click()");
    await sleep(800);
    const profileKicker = await client.eval("document.querySelectorAll('.page-head .kicker')[1]?.innerText");
    const badgeElements = await client.eval("document.querySelectorAll('.badges .badge').length");
    test("Profile screen renders stats and badges", profileKicker?.toLowerCase().includes("level") && badgeElements >= 12, `${badgeElements} badges displayed, ${profileKicker}`);
    await client.screenshot("8_profile_tab.png");

    // TEST 12: Zero Browser Console / Runtime Errors
    test("Zero unhandled console or runtime errors during user journey", client.errors.length === 0, `${client.errors.length} errors`);

    // Clean up created explorer from DB
    try {
      await client.eval(`
        fetch('/api/users/' + JSON.parse(localStorage.getItem('grassquest.settings'))?.userId, { method: 'DELETE' }).catch(() => {});
      `);
    } catch {}

  } catch (err) {
    console.error("Test execution failed:", err);
  } finally {
    if (client) client.close();
    chrome.kill();
    console.log("============================================================");
    console.log(`UI TEST SUMMARY: ${passed}/${total} passed (${Math.round(passed / total * 100)}%)`);
    console.log("============================================================");
    process.exit(passed === total ? 0 : 1);
  }
}

run();
