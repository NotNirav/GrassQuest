import { spawn } from "child_process";
import fs from "fs";
import path from "path";

const CHROME_PATH = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const PORT = 9225;
const APP_URL = "http://localhost:5173/?reset";
const TEMP_USER_DATA = path.resolve("./server/tests/.chrome_reset_profile");
const SCREENSHOT_PATH = path.resolve("./server/tests/screenshots/reset_landing.png");

async function run() {
  console.log("Starting Chrome...");
  const chromeProc = spawn(CHROME_PATH, [
    `--remote-debugging-port=${PORT}`,
    `--user-data-dir=${TEMP_USER_DATA}`,
    "--headless=new",
    "--disable-gpu",
    "--no-first-run",
    "--no-default-browser-check"
  ]);

  await new Promise(r => setTimeout(r, 1500));

  try {
    const res = await fetch(`http://127.0.0.1:${PORT}/json`);
    const targets = await res.json();
    const pageTarget = targets.find(t => t.type === "page") || targets[0];
    
    const ws = new WebSocket(pageTarget.webSocketDebuggerUrl);
    let id = 1;
    const callbacks = new Map();

    ws.onmessage = (e) => {
      const msg = JSON.parse(e.data);
      if (msg.id && callbacks.has(msg.id)) {
        callbacks.get(msg.id)(msg.result);
        callbacks.delete(msg.id);
      }
    };

    await new Promise(r => ws.onopen = r);

    const send = (method, params = {}) => new Promise((resolve) => {
      const msgId = id++;
      callbacks.set(msgId, resolve);
      ws.send(JSON.stringify({ id: msgId, method, params }));
    });

    await send("Page.enable");
    await send("Runtime.enable");
    
    console.log("Navigating to", APP_URL);
    await send("Page.navigate", { url: APP_URL });
    await new Promise(r => setTimeout(r, 2000));

    const evalResult = await send("Runtime.evaluate", {
      expression: "JSON.stringify({ storageLen: window.localStorage.length, h1: document.querySelector('h1')?.innerText, bodyText: document.body.innerText.slice(0, 100) })"
    });

    const parsed = JSON.parse(evalResult.result.value);
    console.log("Page state:", parsed);

    const shot = await send("Page.captureScreenshot", { format: "png" });
    fs.writeFileSync(SCREENSHOT_PATH, Buffer.from(shot.data, "base64"));
    console.log("Saved clean landing screenshot to:", SCREENSHOT_PATH);

    ws.close();
  } catch (err) {
    console.error("Error during reset verification:", err);
  } finally {
    chromeProc.kill("SIGKILL");
  }
}

run();
