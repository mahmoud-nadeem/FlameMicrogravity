/* Browser test of real behaviour (needs Playwright: `npm i -D playwright && npx playwright install chromium`).
   Run: node tests/browser.e2e.cjs   — it serves this folder on a free port by itself. */
const http = require("node:http"), fs = require("node:fs"), path = require("node:path"), assert = require("node:assert/strict");
const { chromium, devices } = require("playwright");
const root = path.join(__dirname, "..");
const types = { ".html": "text/html", ".js": "text/javascript", ".mjs": "text/javascript", ".css": "text/css", ".pdf": "application/pdf", ".png": "image/png", ".woff2": "font/woff2", ".json": "application/json" };
const server = http.createServer((req, res) => {
  const file = path.join(root, decodeURIComponent(req.url.split("?")[0]).replace(/^\/$/, "/index.html"));
  if (!file.startsWith(root) || !fs.existsSync(file)) { res.writeHead(404); res.end(); return; }
  res.writeHead(200, { "Content-Type": types[path.extname(file)] || "application/octet-stream" }); fs.createReadStream(file).pipe(res);
});
const GL = ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"];
const ok = (msg) => console.log("  ok -", msg);

server.listen(0, async () => {
  const base = `http://localhost:${server.address().port}/`;
  const browser = await chromium.launch({ args: GL });
  try {
    const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
    const errors = []; page.on("pageerror", (e) => errors.push(String(e)));
    const wait = (ms) => page.waitForTimeout(ms);

    await page.goto(base + "#/explore"); await wait(2500);
    assert.equal(await page.evaluate(() => FIF.universe.mode), "webgl"); ok("WebGL universe running");
    const node = page.locator('.map-node[data-index="2"]'), b = await node.boundingBox();
    await page.mouse.move(b.x + b.width / 2, b.y + b.height / 2); await wait(600);
    const p1 = await page.evaluate(() => FIF.universe.body("w-T3").pos.join()); await wait(600);
    assert.equal(p1, await page.evaluate(() => FIF.universe.body("w-T3").pos.join())); ok("hovered world holds still");
    assert.equal(await page.locator(".preview-name").textContent(), "AEROSOL"); ok("hover preview");
    await page.mouse.click(b.x + b.width / 2, b.y + b.height / 2);
    await page.waitForURL(/#\/profile\/nadeem/, { timeout: 6000 }); await wait(800); ok("click approaches and navigates");
    await page.goBack(); await wait(1500);
    assert.equal(await page.locator(".map-node.is-selected").getAttribute("data-index"), "2"); ok("back restores the selected world");
    assert.match(await page.locator("#map-comment").textContent(), /Welcome back/); ok("guide notices the return");
    for (let i = 0; i < 5; i++) { await page.evaluate(() => (location.hash = "#/explore")); await wait(150); await page.evaluate(() => (location.hash = "#/profile/gamal")); await wait(150); }
    assert.equal(await page.evaluate(() => FIF.universe._listeners()), 1); ok("no frame callbacks accumulate");

    await page.evaluate(() => (location.hash = "#/lab/PSI-101")); await wait(800);
    await page.locator("#lab-u").fill("6"); await page.locator("#lab-u").dispatchEvent("input");
    assert.match(await page.locator("#lab-reaction").textContent(), /6 cm\/s/); ok("scientist reacts to the actual airflow");
    await page.locator("#chat-launch").click();
    const crew = page.locator("#chat-crew button");
    await crew.nth(3).click(); await crew.nth(4).click(); await crew.nth(4).click();
    assert.equal(await page.locator("#chat-log .msg.bot.is-transmitting").count(), 1); ok("one character speaks at a time");
    await crew.nth(3).click();
    await page.locator("#chat-input").fill("Does smoke grow as it ages?"); await page.keyboard.press("Enter");
    await crew.nth(4).click();
    for (let i = 0; i < 10; i++) { await page.getByText("SHOW FULL MESSAGE").click(); await wait(120); }
    await wait(800);
    const order = await page.evaluate(() => [...document.querySelectorAll("#chat-log .msg")].map((m) => (m.classList.contains("user") ? "U" : m.dataset.speaker)).join(" "));
    assert.match(order, /U nadeem tamer$/); ok("answer keeps its recipient: " + order);
    await page.locator("#space-toggle").click(); await wait(300);
    assert.equal(await page.locator("#lab-u").inputValue(), "6"); assert.ok(await page.locator("#chat-log .msg").count() > 3); ok("mode switch keeps lab and conversation");
    await page.locator("#chat-launch").click(); await page.keyboard.press("Escape"); await wait(300);
    assert.ok(await page.locator("#chat").isHidden()); ok("Escape closes the crew panel");

    await page.evaluate(() => (location.hash = "#/shorts")); await wait(3500);
    assert.equal(await page.locator("#pdf-stage canvas").count(), 1); ok("PDF.js renders the original document locally");
    await page.locator("#viewport").focus(); for (let i = 0; i < 5; i++) await page.keyboard.press(i % 2 ? "ArrowLeft" : "ArrowRight");
    await wait(2500); assert.equal(await page.locator("#pdf-stage canvas").count(), 1); ok("rapid document changes settle on one page");
    assert.deepEqual(errors, []); ok("no page errors (desktop)");

    const phone = await browser.newContext({ ...devices["iPhone 13"] });
    const m = await phone.newPage(); await m.goto(base + "#/explore"); await m.waitForTimeout(2500);
    const sel = await m.locator(".map-node.is-selected").boundingBox();
    await m.touchscreen.tap(sel.x + sel.width / 2, sel.y + sel.height / 2); await m.waitForURL(/#\/profile\//, { timeout: 6000 }); ok("phone: tapping the focused world approaches it");
    await phone.close();

    const calm = await browser.newContext({ viewport: { width: 1280, height: 800 }, reducedMotion: "reduce" });
    const r = await calm.newPage(); await r.goto(base + "#/explore"); await r.waitForTimeout(1500);
    const s1 = await r.evaluate(() => FIF.universe.body("w-T1").spin); await r.waitForTimeout(800);
    assert.equal(s1, await r.evaluate(() => FIF.universe.body("w-T1").spin)); ok("reduced motion: worlds stay still");
    await calm.close();
    console.log("Browser test passed.");
  } catch (e) { console.error(e); process.exitCode = 1; }
  finally { await browser.close(); server.close(); }
});
