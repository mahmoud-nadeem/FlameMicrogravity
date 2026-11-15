/* Retro dialogue box with typewriter text; the speaking character's mouth moves while it types. */
(function () {
  const FIF = window.FIF;

  // Types `text` into `el`; animates every sprite canvas in `spriteEls`. Returns a promise.
  FIF.typeText = function (el, text, spriteEls = [], characterId = "guide") {
    return new Promise((resolve) => {
      if (el._finishTyping) el._finishTyping();
      if (FIF.settings.reduceMotion) { el.textContent = text; resolve(); return; }
      let i = 0, frame = 0;
      el.textContent = "";
      // Only the character actually speaking animates: speaking -> done (a small nod) -> idle.
      spriteEls.forEach(cv => { cv.classList.add("is-speaking"); cv.dataset.state = "speaking"; });
      const finish = () => {
        clearInterval(el._typing); el._typing = null; el._finishTyping = null;
        el.textContent = text;
        spriteEls.forEach(cv => { cv.classList.remove("is-speaking"); cv.dataset.state = "done"; FIF.drawSprite(cv, characterId, false);
          clearTimeout(cv._doneTimer); cv._doneTimer = setTimeout(() => { if (cv.dataset.state === "done") cv.dataset.state = "idle"; }, 700); });
        resolve();
      };
      el._finishTyping = finish;
      el._typing = setInterval(() => {
        if (!el.isConnected || FIF.settings.reduceMotion) { finish(); return; }
        i += 2;
        el.textContent = text.slice(0, i);
        frame++;
        if (frame % 3 === 0) { spriteEls.forEach((cv) => FIF.drawSprite(cv, characterId, (frame / 3) % 2 === 1)); FIF.blip(); }
        if (i >= text.length) {
          finish();
        }
      }, 22);
    });
  };

  FIF.dialogHTML = (id, who) =>
    `<div class="dialog" id="${id}"><span class="who">${FIF.esc(who)}</span><span class="txt"></span><span class="more" aria-hidden="true">&#9660;</span></div>`;

  // Shows a sequence of lines in a dialogue box; click or Enter advances.
  FIF.runDialog = function (box, lines, characterId, spriteEls) {
    const txt = box.querySelector(".txt");
    let k = 0;
    const next = () => { if (k < lines.length) FIF.typeText(txt, lines[k++], spriteEls, characterId); };
    box.tabIndex = 0;
    box.setAttribute("role", "button");
    box.setAttribute("aria-label", "Next line");
    box.addEventListener("click", next);
    box.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); next(); } });
    next();
  };
})();
