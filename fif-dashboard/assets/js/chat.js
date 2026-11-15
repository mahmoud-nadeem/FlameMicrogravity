/* "Ask the crew": offline expert system (TF-IDF matching over saved questions, findings and FAQ),
   with an optional online answer service. Every offline answer cites the finding it comes from. */
(function () {
  const FIF = window.FIF, D = FIF.data;
  const cfg = Object.assign({ api_url: "", timeout_ms: 8000, min_score: 0.18 }, D.chat || {});
  const STOP = new Set("a an the of to in on for and or is are was were be been it its this that these those what which who how why when where do does did can could would should will i you we they me my your our about with from by as at than then there here into out up down not no yes any some more most much many very just also only so if but".split(" "));
  const stem = (w) => w.length > 4 ? w.replace(/(ing|ed|es|s)$/, "") : w;
  // everyday words -> the words used in the findings (applied to questions and to the knowledge base)
  const SYN = {};
  [["size", "big", "bigger", "biggest", "large", "larger", "largest", "small", "smaller", "smallest", "tiny", "diameter", "grow", "grew", "growth", "nm", "um"],
   ["age", "aging", "ageing", "aged", "time", "later", "old", "older", "minute", "wait"],
   ["flow", "air", "airflow", "ventilation", "fan", "breeze", "wind", "velocity"],
   ["detector", "detection", "detect", "alarm", "sensor", "sense", "warning"],
   ["material", "plastic", "fabric", "teflon", "kapton", "silicone", "lampwick", "pyrell", "cotton", "foam"],
   ["smoke", "aerosol", "particle", "particulate", "soot"],
   ["heat", "heater", "hot", "hotter", "temperature", "warm", "overheat"],
   ["counter", "ptrak", "dustrak", "dusttrak", "instrument", "device"],
   ["moon", "lunar", "habitat", "mars", "oxygen", "pressure", "psi"]]
    .forEach((g) => g.forEach((w) => (SYN[stem(w)] = g[0])));
  const tokens = (s) => String(s || "").toLowerCase().replace(/f-t\d+-\d+/g, " ").replace(/([a-z])-([a-z])/g, "$1$2")
    .split(/[^a-z0-9]+/).filter((w) => w && !STOP.has(w)).map(stem).map((w) => SYN[w] || w);

  // ---- knowledge items -------------------------------------------------------------
  function buildItems() {
    const items = [];
    (D.faq.items || []).forEach((f) => items.push({ owner: "guide", q: f.q, text: [f.q, f.q, (f.keywords || []).join(" "), (f.keywords || []).join(" "), f.a], a: f.a, source: f.source, refs: [] }));
    D.tracks.forEach((t) => {
      const ch = FIF.characterForTrack(t.id);
      if (!ch) return;
      const recs = t.records.map((r) => D.records[r]).filter(Boolean);
      const words = recs.map((r) => `${r.acronym || r.id} ${r.title}`).join(" ");
      items.push({ owner: "guide", route: ch.id, q: `Who covers ${recs.map((r) => r.acronym || r.id).join(", ")}?`,
        text: ["who studied covers responsible expert crew member", words, ch.name, ch.role, ch.role], a: `That is ${ch.name}'s area: ${ch.role}. Pick ${ch.name.split(" ")[0]} in the crew bar above to ask about it.`, refs: [] });
      items.push({ owner: ch.id, q: "What is your part about?", text: ["what is your part about track topic study experiment explain", t.paragraph || ch.role],
        a: t.paragraph || (D.findings.some((f) => f.track === t.id)
          ? `${ch.role}. I have ${D.findings.filter((f) => f.track === t.id).length} findings from ${[...new Set(D.findings.filter((f) => f.track === t.id).map((f) => f.record))].join(", ")}; ask me about one of them, or open the evidence table.`
          : `${ch.role}. My findings are not in yet.`), refs: D.findings.filter((f) => f.track === t.id).slice(0, 2).map((f) => f.id) });
      if (t.limitations) items.push({ owner: ch.id, q: "What are the limits of your data?", text: ["limit limitation weakness caveat trust uncertain", t.limitations], a: t.limitations, refs: [] });
      // an experiment whose card is still empty gives no answer here: its crew notes (RAG) answer instead
      recs.filter((r) => r.objectives || r.approach).forEach((r) => items.push({ owner: ch.id, q: `What did ${r.acronym || r.id} do?`, text: [r.acronym || r.id, r.acronym || r.id, r.acronym || r.id, r.title, r.objectives, r.approach, "tell me about what did experiment do goal objective approach method"],
        a: (r.objectives ? r.objectives + " " : "") + (r.approach || "") || `${r.title}. Details are on its NASA PSI page.`, refs: [], link: `#/record/${r.id}` }));
    });
    D.questions.forEach((q) => { const ch = FIF.characterForTrack(q.track); if (ch) items.push({ owner: ch.id, q: q.q, text: [q.q, q.q, q.a], a: q.a, refs: q.findings || [] }); });
    D.tracks.forEach((t) => {
      const ch = FIF.characterForTrack(t.id); if (!ch) return;
      (t.snippets || []).forEach((s) => { const f = FIF.finding(s.id); items.push({ owner: ch.id, q: s.snippet, w: 1.1, text: [s.snippet, s.snippet, f ? f.statement : ""], a: s.snippet, refs: [s.id] }); });
    });
    D.findings.forEach((f) => { const ch = FIF.characterForTrack(f.track); if (ch) items.push({ owner: ch.id, q: null, w: 0.85, text: [f.statement, f.caveat], a: `${f.statement} Caveat: ${f.caveat}`, refs: [f.id] }); });
    // tf-idf vectors
    const docs = items.map((it) => tokens(it.text.join(" ")));
    const df = {}; docs.forEach((d) => new Set(d).forEach((w) => (df[w] = (df[w] || 0) + 1)));
    const N = docs.length, idf = (w) => Math.log((N + 1) / ((df[w] || 0) + 1)) + 1;
    const vec = (toks) => { const v = {}; toks.forEach((w) => (v[w] = (v[w] || 0) + 1)); let n = 0;
      for (const w in v) { v[w] *= idf(w); n += v[w] * v[w]; } n = Math.sqrt(n) || 1; for (const w in v) v[w] /= n; return v; };
    items.forEach((it, i) => (it.v = vec(docs[i])));
    return { items, vec };
  }
  let KB = null;
  const cos = (a, b) => { let s = 0; for (const w in a) if (b[w]) s += a[w] * b[w]; return s; };

  // "what did SAME-R do?" / "tell me about DAFT": answer with the experiment itself, not a single finding
  function recordIntent(question) {
    if (!/^\s*(what (did|does|is|was)|tell me (about|more)|explain|describe)\b/i.test(question)) return null;
    const q = " " + question.toLowerCase().replace(/[^a-z0-9-]+/g, " ") + " ";
    const hit = Object.values(D.records).filter((r) => r.acronym).map((r) => ({ r, keys: r.acronym.toLowerCase().split(/\s*\/\s*|\s+/).filter((k) => k.length > 2) }))
      .filter(({ keys }) => keys.some((k) => q.includes(" " + k + " ")))
      .sort((a, b) => Math.max(...b.keys.map((k) => k.length)) - Math.max(...a.keys.map((k) => k.length)))[0];
    return hit ? hit.r : null;
  }

  function answerOffline(question, who) {
    KB = KB || buildItems();
    const rec = recordIntent(question);
    if (rec) {
      const it = KB.items.find((x) => x.link === `#/record/${rec.id}`);
      const owner = FIF.characterForTrack(rec.track);
      if (it && (who === "guide" || owner.id === who)) {
        return { text: who === "guide" ? `${rec.acronym} is ${owner.name}'s experiment. ${it.a}` : it.a, refs: rec.findings.slice(0, 3), link: it.link, score: 1 };
      }
    }
    const qv = KB.vec(tokens(question));
    const pool = KB.items.filter((it) => who === "guide" ? true : it.owner === who || (it.owner === "guide" && !it.route));
    const ranked = pool.map((it) => ({ it, s: cos(qv, it.v) * (it.owner === who ? 1.15 : 1) * (it.w || 1) })).sort((a, b) => b.s - a.s);
    const best = ranked[0];
    if (!best || best.s < cfg.min_score) {
      return { text: "I can't answer that from our NASA data. Try one of the questions below, or ask the crew member who covers that experiment.", refs: [], miss: true };
    }
    const it = best.it, owner = FIF.character(it.owner);
    let text = it.a;
    if (who === "guide" && it.owner !== "guide") text = `${owner.name} found this: ${it.a}`;
    return { text, refs: it.refs, source: it.source, link: it.link, route: it.route, score: best.s };
  }

  async function answerOnline(question, who) {
    if (!cfg.api_url || !navigator.onLine) return null;
    const ch = FIF.character(who);
    KB = KB || buildItems();
    const qv = KB.vec(tokens(question));
    const context = KB.items.filter((it) => who === "guide" || it.owner === who).map((it) => ({ it, s: cos(qv, it.v) }))
      .sort((a, b) => b.s - a.s).slice(0, 6).map(({ it }) => ({ text: it.a, findings: it.refs }));
    const ctl = new AbortController(); const timer = setTimeout(() => ctl.abort(), cfg.timeout_ms);
    try {
      const r = await fetch(cfg.api_url, { method: "POST", headers: { "Content-Type": "application/json" }, signal: ctl.signal,
        body: JSON.stringify({ question, character: ch.name, track: ch.track, context }) });
      if (!r.ok) return null;
      const j = await r.json();
      return j && j.answer ? { text: j.answer, refs: [...new Set(context.flatMap((c) => c.findings))].slice(0, 4), online: true } : null;
    } catch (e) { return null; } finally { clearTimeout(timer); }
  }

  // Answer from the character's own RAG folders (rag/<PSI-ID>_<NAME>/). rag.js picks the passages and, when
  // api_url is set, lets the model write the answer from them (offline: the best sentences). Returns null when
  // nothing relevant is found or RAG is not loaded, so the saved answers below still run. chat.json: "rag": false turns it off.
  // What each crew member was just asked about, so "summary" / "what about its results?" continue the same topic.
  const mem = {};
  const memOf = (who) => mem[who] || (mem[who] = { topic: "", turns: [] });
  const wantsAll = (q) => /\b(all|everything|whole|overall|entire)\b/i.test(q);
  const DEFINITION_RE = /^\s*(what\s*(is|are|s|does)|whats|define|meaning of|explain)\b/i;
  const isDefinition = (q) => DEFINITION_RE.test(q) && !(window.FIF_RAG && window.FIF_RAG.topicMention && window.FIF_RAG.topicMention("*", q));

  async function answerRag(question, who, M) {
    if (!window.FIF_RAG || cfg.rag === false) return null;
    try {
      const r = await window.FIF_RAG.ask(who, question, { timeout: cfg.timeout_ms, lastTopic: M && M.topic, history: M ? M.turns : [] });
      if (!r || !r.answer) return null;
      return { text: r.answer, refs: [...new Set(r.answer.match(/F-T\d+-\d+/g) || [])], online: r.mode === "online", rag: true, topic: r.topic || "",
        rsources: (r.sources || []).slice(0, 3), caution: r.caution || "" };
    } catch (e) { return null; }
  }

  // Not in the texts, but a simple general question ("what is a spacecraft?"): the model answers it and the bubble says so.
  async function answerGeneral(question, who, M) {
    if (!window.FIF_RAG || !window.FIF_RAG.general || !cfg.api_url || !navigator.onLine) return null;
    const r = await window.FIF_RAG.general(who, question, { timeout: cfg.timeout_ms, history: M ? M.turns : [] });
    return r ? { text: r.answer, refs: [], online: true, general: true } : null;
  }

  // Small talk ("hi", "thanks", "who are you"): answered in the speaker's voice, no search and no model call.
  // Only a message that is entirely small talk matches, so "hi, how did the smoke grow?" still goes to the texts.
  const NAMES = new Set(FIF.characters.flatMap((c) => c.name.toLowerCase().split(/\s+/)).concat(["crew", "everyone", "guys", "there", "team"]));
  // first name, or the full name when two crew members share it (two "Mohamed"s)
  const shortName = (c) => (FIF.characters.filter((x) => x.name.split(" ")[0] === c.name.split(" ")[0]).length > 1 ? c.name : c.name.split(" ")[0]);
  const TALK = [
    ["greet", /^(hi|hello|hey|hiya|howdy|yo|hola|salam|ahlan|marhaba|greetings|good (morning|afternoon|evening)|assalamu alaykum|as salamu alaykum|مرحبا|اهلا|أهلا|سلام|السلام عليكم)$/u],
    ["how", /^(how are you|how are you doing|how r u|how do you do|what s up|whats up|sup)$/u],
    ["thanks", /^((ok |okay |great |cool )?(thanks|thank you|thank you so much|thx|ty)|شكرا|شكرا جزيلا)( a lot)?$/u],
    ["bye", /^(bye|goodbye|see you|see ya|good night|later|cya|مع السلامة)$/u],
    ["who", /^(who are you|what are you|what is your name|what s your name|your name|introduce yourself)$/u],
    ["help", /^(help|what can you do|what can i ask|what can i ask you|what do you know|how does this work|how do i use this)$/u],
    ["ok", /^(ok|okay|cool|nice|great|awesome|got it|i see|alright)$/u],
  ];
  function smallTalk(question, who) {
    let t = question.toLowerCase().replace(/[^\p{L}\p{N}\s']/gu, " ").replace(/'/g, " ").replace(/\s+/g, " ").trim();
    const stripped = t.split(" ").filter((w) => !NAMES.has(w)).join(" ").trim();
    if (stripped) t = stripped;
    const hit = TALK.find(([, re]) => re.test(t));
    if (!hit) return null;
    const ch = FIF.character(who), first = shortName(ch);
    const topic = who === "guide" ? "this site, microgravity fire and which crew member to ask" : ch.role;
    const text = {
      greet: who === "guide" ? `Hello! I'm the Guide. Ask me about ${topic}, or tap one of the questions below.` : `Hello! I'm ${first}. I cover ${topic}. Ask me about it, or tap one of the questions below.`,
      how: `All systems normal up here, thanks for asking. What would you like to know about ${topic}?`,
      thanks: "You're welcome! Ask me anything else whenever you like.",
      bye: "Goodbye! Come back any time with more questions.",
      who: who === "guide" ? "I'm the Guide of this mission: I explain the site and point you to the right crew member." : `I'm ${ch.name}. My area: ${ch.role}. Every answer I give comes from the NASA data our team read.`,
      help: `Ask me a question in your own words about ${topic}. I answer from our NASA data and show where it came from. The buttons below are some examples.`,
      ok: "Great! Ask me anything else about " + topic + ".",
    }[hit[0]];
    return { text, refs: [], smalltalk: true };
  }

  // ---- questions about the chat itself: "what do you answer", "recommend me questions", "give me a summary" ----------
  const norm = (q) => q.toLowerCase().replace(/\brec+om+e?nd\w*\b/g, "recommend").replace(/\bsugest\w*\b/g, "suggest")
    .replace(/[^\p{L}\p{N}\s']/gu, " ").replace(/'/g, " ").replace(/\s+/g, " ").trim();
  const SUMMARY_RE = /\b(summary|summarize|summarise|overview|recap|tldr|tl dr)\b/;
  const FILL = new Set("tell give show me us a an the of all everything anything you your know knows can could would please short quick brief full complete summary summarize summarise overview recap tldr about it that this data texts info information whatever what do i to have said say from our my yourself and also just got".split(" "));
  const SUGGEST_RE = [
    /^(please )?(recommend|suggest|give|show|list|propose|offer)( me| us)?( some| a few| few| any| more| other)?( good| example| sample| nice| interesting)? (questions?|topics?|examples?|ideas?|prompts?)( to ask( you| me)?| i can ask( you)?| for me)?$/,
    /^(what|which)( questions?| topics?)? (should|can|could|do|would) (i|we) ask( you| about| first)?$/,
    /^(help me ask|any questions|any ideas|example questions|sample questions|ask me something|i (do not|dont|don t) know what to ask|help|what can you do|how does this work|how do i use this|how to use this)$/,
  ];
  const SCOPE_RE = [
    /^what( \w+){0,3} (do|can|could|would|will) you (answer|cover|handle|discuss|do|talk about|know about|help me with|help with|tell me|tell me about|explain|teach)( exactly)?$/,
    /^(what|which) (are|is)( your| you)( \w+)? (about|area|topics?|subjects?|specialty|expertise|field|focus|job|role)( exactly)?$/,
  ];
  // "what is SPICE and what answers I can ask in it" = a question plus a request for example questions
  const ASK_CLAUSE = /\b(?:what|which)(?:\s+\w+){0,2}?\s+(?:(?:i|we)\s+(?:can|could|should|would)|(?:can|could|should|do|would)\s+(?:i|we))\s+ask(?:\s+(?:you|him|her|them|it|in|about|on|this|that|there|here|of))*/i;
  function splitAsk(q) {
    const m = ASK_CLAUSE.exec(q);
    if (!m) return { rest: q, wantQs: false };
    const rest = (q.slice(0, m.index) + " " + q.slice(m.index + m[0].length)).replace(/[\s,;.?!]+$/, "").replace(/\b(and|also|then|plus)$/i, "").replace(/^[\s,;.]+|[\s,;.?!]+$/g, "");
    const real = norm(rest).split(" ").filter((w) => w && !NAMES.has(w));
    return { rest: real.length ? rest : "", wantQs: true };
  }
  function intentOf(q) {
    const words = norm(q).split(" ").filter((w) => !NAMES.has(w)), t = words.join(" ");
    if (!t) return null;
    const summaryish = SUMMARY_RE.test(t) || (/\b(all|everything)\b/.test(t) && /\b(know|tell|say|have|got)\b/.test(t)) || t === "what do you know";
    if (summaryish && !words.filter((w) => !FILL.has(w)).length) return "summary";   // "summary of the air flow" is a normal question
    if (SUGGEST_RE.some((re) => re.test(t))) return "suggest";
    if (SCOPE_RE.some((re) => re.test(t))) return "scope";
    return null;
  }

  // example questions built from this character's own texts (section headings, and one overview question per experiment)
  function exampleQuestions(who, n, only) {
    const R = window.FIF_RAG;
    if (!R || cfg.rag === false) return [];
    const topics = (only ? [only] : R.topicsFor(who)).filter((t) => (R.data.topics[t] || []).length), titled = [], generic = [];
    topics.forEach((t) => {
      generic.push(`What did ${R.labelOf(t)} find?`);
      const seen = new Set();
      R.data.topics[t].forEach((ch) => {
        if (ch.kind === "record" || ch.kind === "policy") return;
        const stem = ch.source.replace(/\.[^.]+$/, "").replace(/_/g, " ").toLowerCase(), ti = String(ch.title || "").trim().replace(/[?.!:]+$/, "");
        if (!ti || ti.toLowerCase() === stem || seen.has(ti.toLowerCase()) || ti.split(" ").length > 12) return;
        seen.add(ti.toLowerCase()); titled.push(`What does the data say about ${ti}?`);
      });
    });
    const pick = (arr, k) => (arr.length <= k ? arr : Array.from({ length: k }, (_, i) => arr[Math.floor(i * arr.length / k)]));
    const g = Math.min(generic.length, Math.ceil(n / 2));
    return [...pick(titled, n - g), ...pick(generic, g)].slice(0, n);
  }
  const crewAreas = () => FIF.characters.filter((c) => c.id !== "guide").map((c) => `${shortName(c)}: ${c.role}`).join("; ");

  function scopeAnswer(who) {
    const R = window.FIF_RAG, ch = FIF.character(who), qs = exampleQuestions(who, 4);
    if (who === "guide") return { text: `I explain this site and point you to the right crew member, and I can look across all the crew's texts. The crew covers: ${crewAreas()}. Try one of these:`, refs: [], questions: qs };
    const topics = R && cfg.rag !== false ? R.topicsFor(who).filter((t) => (R.data.topics[t] || []).length).map((t) => t.replace("_", " · ")) : [];
    return topics.length
      ? { text: `I answer questions about ${ch.role}, using our team's NASA data: ${topics.join(", ")}. If something is not in my texts I will say so or point you to the crew member who covers it. Try one of these:`, refs: [], questions: qs }
      : { text: `I answer questions about ${ch.role}. My texts are not loaded yet, so I can only give saved answers for now.`, refs: [] };
  }
  function suggestAnswer(who) {
    const qs = exampleQuestions(who, 5);
    return qs.length ? { text: "Here are some questions you could ask me. Tap one, or type your own:", refs: [], questions: qs }
      : { text: `Ask me about ${who === "guide" ? "this site and which crew member to ask" : FIF.character(who).role} in your own words.`, refs: [] };
  }
  async function summaryAnswer(who, q, M) {
    const R0 = window.FIF_RAG, topics = R0 && M && M.topic && !wantsAll(q) && R0.data.topics[M.topic] ? [M.topic] : undefined;   // "summary" after a question about SPICE = summary of SPICE
    if (who === "guide" && !topics) return { text: `This site explains NASA's microgravity fire experiments. Our crew covers: ${crewAreas()}. Pick a crew member to go through their texts, or ask me anything and I will point you to the right one.`, refs: [], questions: exampleQuestions(who, 3) };
    if (window.FIF_RAG && cfg.rag !== false) {
      const r = await window.FIF_RAG.summarize(who, { question: q, timeout: cfg.timeout_ms, topics });
      if (r) return { text: r.answer, refs: [...new Set(r.answer.match(/F-T\d+-\d+/g) || [])], online: r.mode === "online", rag: true, topic: r.topic || "",
        rsources: (r.sources || []).slice(0, 3), questions: exampleQuestions(who, 3, topics && topics[0]) };
    }
    return null;   // no texts yet: the saved answers take over
  }

  // buttons under a message: "ASK <crew member>" and clickable example questions
  function addExtras(bubble, a, speaker) {
    if (a.route && FIF.character(a.route)) {
      const b = document.createElement("button"); b.className = "chip"; b.type = "button";
      b.textContent = `ASK ${shortName(FIF.character(a.route)).toUpperCase()}`; b.onclick = () => select(a.route); bubble.appendChild(b);
    }
    if (a.questions && a.questions.length) {
      const row = document.createElement("div"); row.className = "chat-suggest";
      a.questions.forEach((qq) => {
        const b = document.createElement("button"); b.className = "chip"; b.type = "button"; b.textContent = String(qq);
        b.onclick = () => { if (speaker && speaker !== current) select(speaker); ask(String(qq)); }; row.appendChild(b);
      });
      bubble.appendChild(row);
    }
  }

  // Nothing found in this character's texts: point to the crew member whose texts hold it, or say what we cover.
  function recommendation(q, who, redirectOnly) {
    const first = shortName;
    const r = window.FIF_RAG && cfg.rag !== false ? window.FIF_RAG.recommend(who, q) : null;
    if (r) {
      const owners = r.owners.map((id) => FIF.character(id)).filter(Boolean);
      if (owners.length) {
        const names = owners.map(first).join(" or "), label = r.topic.replace("_", " · ");
        return { text: who === "guide" ? `That is covered by ${names} (${label}). Tap the button to ask ${first(owners[0])}.`
          : `That is outside my area, but ${names} covers it (${label}) and may know. Tap the button to ask ${first(owners[0])}.`, refs: [], route: owners[0].id };
      }
    }
    if (redirectOnly) return null;
    if (who !== "guide") return { text: "I could not find that in my data. Try other words, or ask the Guide, who can look across all the crew's texts.", refs: [], route: "guide" };
    const areas = FIF.characters.filter((c) => c.id !== "guide").map((c) => `${first(c)}: ${c.role}`).join("; ");
    return { text: `I could not find that in our texts. Try other words. Our crew covers: ${areas}.`, refs: [] };
  }

  // Chat history is kept in this browser, so old messages come back after a reload or when the panel is reopened.
  const HKEY = "fif.chat.v1", HMAX = 80;
  let hist = [];
  try { hist = (JSON.parse(localStorage.getItem(HKEY) || "{}").items || []).filter((m) => m && (m.t === "u" || m.t === "b")); } catch (e) { hist = []; }
  function remember(item) {
    hist.push(item); if (hist.length > HMAX) hist = hist.slice(-HMAX);
    try { localStorage.setItem(HKEY, JSON.stringify({ items: hist })); } catch (e) { /* storage full or blocked: history just will not persist */ }
  }
  function restoreHistory() {
    if (!hist.length) return;
    const box = log();
    let lastQ = "";   // rebuild what each crew member was last asked about
    hist.forEach((m) => {
      if (m.t === "u") { lastQ = String(m.text || ""); return; }
      if (!m.who) return;
      const M = memOf(m.who);
      if (m.a && m.a.topic) M.topic = m.a.topic;
      if (lastQ) { M.turns.push({ q: lastQ, a: String(m.text || "").slice(0, 300) }); M.turns = M.turns.slice(-3); }
    });
    hist.forEach((m) => {
      if (m.t === "u") { const u = document.createElement("div"); u.className = "msg user"; u.textContent = String(m.text || ""); box.appendChild(u); return; }
      const ch = FIF.character(m.who); if (!ch) return;
      const el = document.createElement("div"); el.className = "msg bot"; el.dataset.speaker = ch.id; el.dataset.restored = "1";
      el.innerHTML = `${FIF.spriteHTML(ch.id)}<div class="bubble"><span class="who">${FIF.esc(ch.name.toUpperCase())}</span><span class="t"></span></div>`;
      el.querySelector(".t").textContent = String(m.text || "");
      const a = Object.assign({}, m.a || {}); if (a.link && !/^#\//.test(a.link)) a.link = "";
      const bubble = el.querySelector(".bubble"), h = refsHTML(a);
      if (h) bubble.insertAdjacentHTML("beforeend", h);
      addExtras(bubble, a, m.who);
      box.appendChild(el);
    });
    FIF.paintSprites(box);
    box.scrollTop = box.scrollHeight;
  }

  // ---- UI -------------------------------------------------------------------------
  let current = "guide";
  const log = () => FIF.$("#chat-log");

  function refsHTML(a) {
    const parts = [];
    if (a.refs && a.refs.length) parts.push("Evidence: " + a.refs.map((id) => `<a href="#/research?q=${encodeURIComponent(id)}">${FIF.esc(id)}</a>`).join(", "));
    if (a.rsources && a.rsources.length) parts.push("From: " + a.rsources.map((s) => {
      const label = (s.psi && D.records[s.psi] && D.records[s.psi].acronym) || String(s.topic || "").replace(/^PSI-\d+_/, "").replace(/[-_]/g, " ");
      const where = s.psi && D.records[s.psi] ? `<a href="#/record/${encodeURIComponent(s.psi)}">${FIF.esc(s.psi)} ${FIF.esc(label)}</a>` : FIF.esc(s.topic || "");
      return `${where} &middot; ${FIF.esc(s.id || "")}${s.evidence ? ` (${FIF.esc(s.evidence.replace(/_/g, " "))})` : ""}`;
    }).join("; "));
    if (a.caution) parts.push(FIF.esc(a.caution));
    if (a.source) parts.push("Source: " + FIF.esc(a.source));
    if (a.link) parts.push(`<a href="${a.link}">Open the experiment</a>`);
    if (a.general) parts.push("General knowledge, not taken from our NASA texts.");
    else if (a.online) parts.push(a.rag ? "Written by an AI from our NASA texts: check important facts." : "Online AI answer: check the cited findings.");
    return parts.length ? `<div class="refs">${parts.join(" &middot; ")}</div>` : "";
  }

  // A message slot is created the moment a greeting or question is requested, so the log
  // keeps request order even while earlier crew members are still talking.
  function slot(speaker, note) {
    const ch = FIF.character(speaker);
    const el = document.createElement("div");
    el.className = "msg bot is-queued";
    el.innerHTML = `${FIF.spriteHTML(ch.id)}<div class="bubble"><span class="who">${FIF.esc(ch.name.toUpperCase())}</span><span class="t"><span class="wait-dots" aria-hidden="true">&#9646;&#9646;&#9646;</span> ${FIF.esc(note)}</span></div>`;
    el.dataset.speaker = ch.id;
    log().appendChild(el);
    const cv = el.querySelector("canvas"); if (cv) { cv.dataset.state = "waiting"; FIF.drawSprite(cv, ch.id); }
    log().scrollTop = log().scrollHeight;
    return el;
  }

  async function botSay(text, a = {}, speaker = current, el = null) {
    const ch = FIF.character(speaker);
    if (!el) el = slot(speaker, "");
    const bubble = el.querySelector(".bubble"), t = el.querySelector(".t"), cv = el.querySelector("canvas");
    el.classList.remove("is-queued", "is-waiting");
    el.classList.add("is-transmitting");
    t.textContent = "";
    if (refsHTML(a)) bubble.insertAdjacentHTML("beforeend", refsHTML(a));
    const typing = FIF.typeText(t, text, cv ? [cv] : [], ch.id);
    activeText = t;
    if (FIF.attachChatVisual) FIF.attachChatVisual(bubble, a, text);
    log().scrollTop = log().scrollHeight;
    addExtras(bubble, a, speaker);
    await typing;
    if (!a.noSave) remember({ t: "b", who: speaker, text, a: { refs: a.refs || [], source: a.source || "", topic: a.topic || "", general: !!a.general, link: a.link || "", online: !!a.online, rag: !!a.rag, route: a.route || "", questions: a.questions || [],
      rsources: a.rsources || [], caution: a.caution || "" } });
    el.classList.remove("is-transmitting");
    activeText = null;
    log().scrollTop = log().scrollHeight;
  }

  let activeText = null;
  const queue = FIF.createConversationQueue((pending, running) => {
    const status = FIF.$("#chat-queue-status");
    if (status) status.textContent = running ? (pending ? `${pending} waiting · one crew member at a time` : "Crew transmission in progress") : "Ready for your next question";
  });
  FIF.voiceQueue = queue;   // shared with the planet guide: one character speaks at a time across the site
  const enqueue = job => queue.add(job).catch(() => {
    const status = FIF.$("#chat-queue-status");
    if (status) status.textContent = "That transmission failed. You can try again.";
  });

  function suggestions() {
    KB = KB || buildItems();
    const qs = [...new Set([...exampleQuestions(current, 4), ...KB.items.filter((it) => it.owner === current && it.q && /\?$/.test(it.q)).map((it) => it.q)])];
    const box = FIF.$("#chat-suggest");
    box.innerHTML = "";
    qs.slice(0, 4).forEach((q) => { const b = document.createElement("button"); b.type = "button"; b.textContent = q.length > 70 ? q.slice(0, 68) + "..." : q;
      b.onclick = () => ask(q); box.appendChild(b); });
  }

  const greeted = new Set();
  function select(id) {
    if (id === current && log().children.length) return; // repeated clicks never repeat a greeting
    current = id;
    FIF.$$("#chat-crew button").forEach((b) => b.setAttribute("aria-selected", String(b.dataset.id === id)));
    const ch = FIF.character(id);
    const line = greeted.has(id) ? `${ch.name.split(" ")[0]} here again. What would you like to know?` : ch.greeting;
    greeted.add(id);
    const el = slot(id, "waiting to speak…");
    enqueue(() => botSay(line, { noSave: true }, id, el));
    suggestions();
  }

  function ask(q) {
    q = q.trim(); if (!q) return;
    const speaker = current; // Capture the recipient before any asynchronous work.
    const u = document.createElement("div"); u.className = "msg user"; u.textContent = q; log().appendChild(u); remember({ t: "u", text: q });
    const el = slot(speaker, "question received, waiting in line…");
    enqueue(async () => {
      const crewButton = FIF.$$("#chat-crew button").find(button => button.dataset.id === speaker);
      crewButton?.classList.add("is-waiting");
      el.classList.add("is-waiting");
      const t = el.querySelector(".t"); if (t) t.innerHTML = '<span class="wait-dots" aria-hidden="true">&#9646;&#9646;&#9646;</span> thinking…';
      try {
        const ragOn = !!window.FIF_RAG && cfg.rag !== false;
        const sp = splitAsk(q), Q = sp.rest || q;   // Q: the question itself, without "what can I ask"
        const kind = sp.wantQs && !sp.rest ? "suggest" : intentOf(Q);
        const M = memOf(speaker);
        let a = kind === "scope" ? scopeAnswer(speaker) : kind === "suggest" ? suggestAnswer(speaker) : kind === "summary" ? await summaryAnswer(speaker, Q, M) : null;
        if (!a) a = smallTalk(Q, speaker);
        // the crew member's own curated answer to (nearly) this question comes before a passage search
        if (!a && ragOn) { const own = answerOffline(Q, speaker); if (!own.miss && own.score >= 0.5) a = own; }
        if (!a && ragOn) a = await answerRag(Q, speaker, M);
        if (!a && !ragOn) a = await answerOnline(Q, speaker);
        let triedGeneral = false;
        // "what is a cargo?": a plain definition is answered from general knowledge instead of sending the visitor elsewhere
        if (!a && ragOn && cfg.api_url && isDefinition(Q)) { triedGeneral = true; a = await answerGeneral(Q, speaker, M); }
        // another crew member's texts hold it: recommend them before falling back to the generic saved answers
        if (!a && ragOn && !(speaker === "guide" && cfg.api_url)) a = recommendation(Q, speaker, true);
        if (!a && ragOn && cfg.api_url && !triedGeneral) a = await answerGeneral(Q, speaker, M);
        if (!a) {
          const saved = answerOffline(Q, speaker);
          a = !ragOn || (!saved.miss && saved.score >= Math.max(cfg.min_score || 0, 0.2)) ? saved : recommendation(Q, speaker);
        }
        if (sp.wantQs && sp.rest && a && !a.route && !a.questions) {   // add example questions for the experiment asked about
          const men = window.FIF_RAG && window.FIF_RAG.topicMention ? window.FIF_RAG.topicMention(speaker, sp.rest) : null;
          const qs = exampleQuestions(speaker, 4, men && men.t);
          if (qs.length) a = Object.assign({}, a, { questions: qs, text: a.text + " You can ask me things like:" });
        }
        if (!a.smalltalk && !a.miss) {   // remember the topic and the last turns for the next question
          if (a.topic) M.topic = a.topic;
          M.turns.push({ q: Q, a: String(a.text).slice(0, 300) }); M.turns = M.turns.slice(-3);
        }
        await botSay(a.text, a, speaker, el);
      } catch (error) {
        el.classList.remove("is-waiting", "is-queued"); el.classList.add("is-failed");
        if (t) t.textContent = "Transmission failed. Please ask again.";
        throw error;
      } finally {
        crewButton?.classList.remove("is-waiting");
        const cv = el.querySelector("canvas"); if (cv && cv.dataset.state === "waiting") cv.dataset.state = "idle";
      }
    });
  }

  FIF.openChat = function (id) {
    const panel = FIF.$("#chat"), launch = FIF.$("#chat-launch");
    panel.hidden = false; launch.hidden = true; launch.setAttribute("aria-expanded", "true");
    if (!log().children.length) restoreHistory();
    if (id && id !== current) select(id);
    else if (!log().children.length) select(current);
    FIF.$("#chat-input").focus();
  };

  FIF.initChat = function () {
    const status = document.createElement("p"); status.id = "chat-queue-status";
    status.className = "chat-mode"; status.setAttribute("role", "status");
    status.textContent = "Ready for your next question";
    const finish = document.createElement("button"); finish.className = "chip";
    finish.textContent = "SHOW FULL MESSAGE"; finish.type = "button";
    finish.onclick = () => activeText?._finishTyping?.();
    FIF.$("#chat").insertBefore(status, FIF.$("#chat-form"));
    FIF.$("#chat-suggest").after(finish);
    const clear = document.createElement("button"); clear.className = "chip"; clear.type = "button"; clear.textContent = "CLEAR HISTORY";
    clear.onclick = () => { hist = []; Object.keys(mem).forEach((k) => delete mem[k]); try { localStorage.removeItem(HKEY); } catch (e) {} log().innerHTML = ""; greeted.clear(); select(current); };
    finish.after(clear);
    const crew = FIF.$("#chat-crew");
    crew.innerHTML = FIF.characters.map((c) => `<button type="button" role="tab" data-id="${FIF.esc(c.id)}" title="${FIF.esc(c.name)}: ${FIF.esc(c.role)}" aria-selected="false">${FIF.spriteHTML(c.id, "", c.name)}</button>`).join("");
    FIF.paintSprites(crew);
    crew.addEventListener("click", (e) => { const b = e.target.closest("button[data-id]"); if (b) select(b.dataset.id); });
    FIF.$("#chat-launch").addEventListener("click", () => FIF.openChat());
    FIF.$("#chat-close").addEventListener("click", () => { if (FIF.closeChat) { FIF.closeChat(true); return; } FIF.$("#chat").hidden = true; const l = FIF.$("#chat-launch"); l.hidden = false; l.setAttribute("aria-expanded", "false"); l.focus(); });
    FIF.$("#chat-form").addEventListener("submit", (e) => { e.preventDefault(); const i = FIF.$("#chat-input"); ask(i.value); i.value = ""; });
    FIF.$("#chat-mode").textContent = window.FIF_RAG && cfg.rag !== false ? (cfg.api_url ? "Answers from each crew member's own texts, written by an AI when connected." : "Answers from each crew member's own texts (works offline).") : cfg.api_url ? "Online answers when connected; saved answers otherwise." : "Saved answers (works offline). Every answer cites its finding.";
  };
  FIF._answerOffline = answerOffline; // used by the self-test
})();
