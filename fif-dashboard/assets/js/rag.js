/* rag.js - per-character retrieval for the crew chat. Works offline (file://).
 *
 *   const r = await FIF_RAG.ask("tamer", "How big were the flames?");
 *   // -> { answer, sources:[{topic,source,title,psi,url}], mode:"offline"|"online" }  or null if nothing relevant
 *   FIF_RAG.recommend("tamer", question) // -> { topic, owners:[ids] } when ANOTHER character's texts hold the answer
 *
 * Data: data/rag-data.js (built by build_rag.py from rag/<PSI-ID>_<NAME>/) is about 4 MB, so it is loaded in the
 * background after the page, not with it; ask()/summarize() wait for it (FIF_RAG.ready()).
 * Constraints: a character searches only the folders content/rag-map.json gives them ("*" = all, the guide); chunks
 * marked "policy" (instructions about a corpus file) are never used as answers; each source carries its chunk ID and
 * evidence label, and answers drawn from flagged, inferred or disputed passages carry a caution.
 * Retrieval: BM25 over the chunks of the folders mapped to that character (content/rag-map.json), made forgiving:
 * related words count as the same word (big/size/larger, soot/smoke, hot/heat ...), word endings are ignored and
 * small typos / word variants are matched. Offline answer: the best sentences from the top passages (never invented).
 * Online answer (optional): with "api_url" in content/chat.json the question plus the top passages are POSTed there
 * (even loosely matching ones, so the model can handle paraphrases) and the endpoint returns {"answer": "..."}.
 * If it says "That is not in our data." this returns null so the chat can recommend another crew member.
 */
(function () {
  "use strict";
  const EMPTY = { map: {}, topics: {} };
  let DATA = window.FIF_RAG_DATA || null, loading = null;
  const D = () => DATA || EMPTY;
  function load() {   // a script tag (not fetch) so that it also works when the page is opened from disk
    if (DATA) return Promise.resolve(DATA);
    if (!loading) loading = new Promise((resolve) => {
      const s = document.createElement("script");
      s.src = "data/rag-data.js"; s.async = true;
      s.onload = () => { DATA = window.FIF_RAG_DATA || EMPTY; cache.clear(); resolve(DATA); };
      s.onerror = () => { DATA = Object.assign({ error: "data/rag-data.js could not be loaded" }, EMPTY); resolve(DATA); };
      document.head.appendChild(s);
    });
    return loading;
  }
  const STOP = new Set(("a an the and or of to in on at for with by from is are was were be been being it its this that " +
    "these those as what which who how why when where do does did can could should would will about into than then " +
    "there their they he she we you i not no me my your our us am if so up out get got make made give tell say said summary summarize summarise overview recap tldr answer answers ask asks question questions " +
    "happen happens happened please thing things much many very just also only some any more most other like").split(" "));

  // words that mean (nearly) the same for our texts; the first word of each group is the one all of them become
  const GROUPS = [
    ["size", "big", "bigger", "biggest", "large", "larger", "largest", "small", "smaller", "smallest", "tiny", "diameter", "grow", "grew", "growth", "width", "length"],
    ["age", "aging", "ageing", "aged", "old", "older", "later", "wait", "delay", "time", "duration"],
    ["flow", "airflow", "air", "ventilation", "fan", "breeze", "wind", "velocity", "speed"],
    ["detector", "detection", "detect", "alarm", "sensor", "sense", "warning"],
    ["material", "plastic", "fabric", "cotton", "foam", "sample"],
    ["smoke", "aerosol", "particle", "particulate", "soot"],
    ["heat", "heater", "hot", "hotter", "temperature", "warm", "overheat", "thermal"],
    ["burn", "fire", "flame", "combustion", "ignite", "ignition", "flammable", "flammability"],
    ["experiment", "test", "study", "investigation", "trial"],
    ["result", "finding", "outcome", "conclusion", "discover"],
    ["gravity", "microgravity", "freefall", "weightless", "weightlessness"],
    ["fuel", "propellant"],
    ["oxygen", "o2", "atmosphere"],
    ["moon", "lunar"], ["mars", "martian"],
    ["droplet", "drop", "liquid"],
    ["suppress", "extinguish", "suppression", "extinguishment"],
    ["measure", "measurement", "instrument", "device", "counter"],
    ["spacecraft", "ship", "station", "iss", "cargo"],
  ];

  function stem(w) {
    if (w.length > 4 && w.endsWith("ies")) w = w.slice(0, -3) + "y";
    else if (w.length > 5 && w.endsWith("ing")) w = w.slice(0, -3);
    else if (w.length > 4 && w.endsWith("ed")) w = w.slice(0, -2);
    else if (w.length > 4 && w.endsWith("ly")) w = w.slice(0, -2);
    else if (w.length > 4 && /(ss|x|z|ch|sh)es$/.test(w)) w = w.slice(0, -2);
    else if (w.length > 3 && w.endsWith("s") && !w.endsWith("ss")) w = w.slice(0, -1);
    if (w.length > 4 && w.endsWith("e")) w = w.slice(0, -1);
    return w;
  }
  const SYN = {};
  GROUPS.forEach((g) => { const c = stem(g[0]); g.forEach((w) => { SYN[stem(w)] = c; }); });
  const SYNKEYS = Object.keys(SYN);
  const tokens = (t) => (String(t).toLowerCase().match(/[a-z0-9]+/g) || [])
    .filter((w) => w.length > 1 && !STOP.has(w)).map((w) => { const s = stem(w); return SYN[s] || s; });

  function near(a, b) {            // at most one edit apart
    const la = a.length, lb = b.length;
    if (Math.abs(la - lb) > 1) return false;
    let i = 0, j = 0, e = 0;
    while (i < la && j < lb) {
      if (a[i] === b[j]) { i++; j++; continue; }
      if (++e > 1) return false;
      if (la > lb) i++; else if (lb > la) j++; else { i++; j++; }
    }
    return e + (la - i) + (lb - j) <= 1;
  }

  function buildIndex(chunks) {
    const docs = chunks.map((c) => {
      const tk = tokens(c.title + " " + c.title + " " + c.text);   // title counted twice = small boost
      const tf = new Map();
      tk.forEach((w) => tf.set(w, (tf.get(w) || 0) + 1));
      return { c, tf, len: tk.length };
    });
    const df = new Map();
    docs.forEach((d) => d.tf.forEach((_, w) => df.set(w, (df.get(w) || 0) + 1)));
    const N = docs.length;
    return { docs, df, N, vocab: [...df.keys()], avg: docs.reduce((s, d) => s + d.len, 0) / Math.max(N, 1) };
  }

  const cache = new Map();
  function topicsFor(charId) {
    const names = Object.keys(D().topics);
    if (charId === "*") return names;
    const wanted = D().map[charId] || [];
    if (wanted.includes("*")) return names;
    const low = wanted.map((x) => x.toLowerCase());
    return names.filter((n) => low.some((w) => n.toLowerCase() === w || n.toLowerCase().startsWith(w + "_")));
  }
  function indexFor(charId) { return indexOfNames(topicsFor(charId)); }
  function indexOfNames(names) {
    const key = names.join("|");
    if (!cache.has(key)) {
      const chunks = [];
      const seen = new Set();   // a chunk shared by several datasets is indexed once; "policy" chunks are never answers
      names.forEach((n) => (D().topics[n] || []).forEach((c) => {
        const k = c.id + "|" + c.source;
        if (c.kind === "policy" || seen.has(k)) return;
        seen.add(k); chunks.push(Object.assign({ topic: n }, c));
      }));
      cache.set(key, buildIndex(chunks));
    }
    return cache.get(key);
  }

  function expand(idx, w) {        // a query word -> the index words it can stand for
    if (idx.df.has(w)) return [{ w, wt: 1 }];
    const alts = [];
    for (const v of idx.vocab) {
      if (w.length >= 4 && v.length >= 4 && (v.startsWith(w) || w.startsWith(v))) alts.push({ w: v, wt: 0.7 });
      else if (w.length >= 5 && near(w, v)) alts.push({ w: v, wt: 0.6 });
      if (alts.length >= 4) break;
    }
    return alts;
  }

  // a misspelled word that is close to one of the related-word groups becomes that group's word
  function fixTypo(w, idx) {
    if (idx.df.has(w) || SYN[w]) return w;
    for (const key of SYNKEYS) {
      if ((w.length >= 5 && near(w, key)) || (w.length >= 4 && key.length >= 4 && (key.startsWith(w) || w.startsWith(key)))) return SYN[key];
    }
    return w;
  }

  function retrieve(charId, query, k, names) {
    const idx = names ? indexOfNames(names) : indexFor(charId);
    const base = [...new Set(tokens(query).map((w) => fixTypo(w, idx)))];
    if (!base.length || !idx.N) return [];
    const k1 = 1.5, b = 0.75, maxIdf = Math.log(1 + idx.N);
    const idfOf = (w) => { const n = idx.df.get(w); return n ? Math.log(1 + (idx.N - n + 0.5) / (n + 0.5)) : maxIdf; };
    const terms = base.map((w) => ({ w, alts: expand(idx, w) }));
    const tIdf = terms.map((t) => (t.alts.length ? Math.max(...t.alts.map((a) => idfOf(a.w))) : maxIdf));
    const total = tIdf.reduce((a, c) => a + c, 0) || 1;
    const out = [];
    for (const d of idx.docs) {
      let s = 0, got = 0, hit = 0;
      terms.forEach((t, i) => {
        let best = 0;
        for (const a of t.alts) {
          const f = d.tf.get(a.w);
          if (!f) continue;
          const sc = idfOf(a.w) * f * (k1 + 1) / (f + k1 * (1 - b + b * d.len / idx.avg)) * a.wt;
          if (sc > best) best = sc;
        }
        if (best > 0) { s += best; got += tIdf[i]; hit++; }
      });
      if (hit) out.push({ chunk: d.c, score: s, coverage: got / total, matched: hit, terms: base.length, rank: s * (0.5 + got / total) * (d.c.kind === "record" ? 0.6 : 1) });   // one data row rarely answers a general question
    }
    return out.sort((a, c) => c.rank - a.rank).slice(0, k || 5);
  }

  // a sentence ends at . ! ? followed by a space: decimals (9.75), cell refs and "e.g." stay inside their sentence
  const sentences = (t) => t.replace(/\s+/g, " ").trim().split(/(?<=[.!?])\s+(?=[A-Z0-9\[("“])/).filter(Boolean);
  const QA = /^\s*Question:\s*([\s\S]+?)\n\s*Answer:\s*([\s\S]+)$/;
  function extract(hits, query) {
    // the best passage is one of the author's own question-and-answer pairs: give its answer as written
    const qa = QA.exec(hits[0].chunk.text);
    if (qa && (!hits[1] || hits[0].rank >= 1.5 * hits[1].rank)) return qa[2].trim();
    const q = new Set(tokens(query)), cands = [];
    hits.slice(0, 3).forEach((h, hi) => {
      const m2 = QA.exec(h.chunk.text), text = m2 ? m2[2] : h.chunk.text;   // never quote the question line itself
      sentences(text).forEach((s, si) => {
        const m = tokens(s).filter((w) => q.has(w)).length;
        if (m) cands.push({ s: s.trim().replace(/^Answer:\s*/, ""), hi, si, score: m + (hi === 0 ? 1 : 0) + (3 - hi) * 0.1 });   // the best-ranked passage leads
      });
    });
    if (!cands.length) return hits[0].chunk.text.slice(0, 300);
    return cands.sort((a, b) => b.score - a.score).slice(0, 3)
      .sort((a, b) => a.hi - b.hi || a.si - b.si).map((c) => c.s).join(" ");
  }
  function sourcesOf(hits) {
    const seen = new Set(), out = [];
    hits.forEach((h) => {
      const key = h.chunk.id + "|" + h.chunk.source;
      if (seen.has(key)) return;
      seen.add(key);
      out.push({ topic: h.chunk.topic, source: h.chunk.source, title: h.chunk.title, psi: h.chunk.psi || "", id: h.chunk.id || "",
        evidence: h.chunk.evidence || "", kind: h.chunk.kind || "text",
        url: h.chunk.psi ? "https://psi.nasa.gov/physci/repo/data/investigations/" + h.chunk.psi : "" });
    });
    return out;
  }

  // the author's own uncertainty labels travel with the answer
  const RISKY = new Set(["third_party_conflict", "third_party_unverified", "documented_source_difference", "reasoned_not_measured"]);
  function cautionOf(hits) {
    const notes = [];
    hits.forEach((h) => {
      const c = h.chunk;
      if (RISKY.has(c.evidence)) notes.push(`${c.id} is labelled "${c.evidence.replace(/_/g, " ")}"`);
      else if (c.kind === "guidance") notes.push(`${c.id} is the author's usage caution`);
      else if (/\[(FLAG|INF|INTERP|QA)\b|OUR INFERENCE|\bprovisional\b|\bunconfirmed\b/i.test(c.text)) notes.push(`${c.id} contains flagged or inferred statements`);
    });
    return notes.length ? "Caution: " + [...new Set(notes)].slice(0, 3).join("; ") + ". Read the source before relying on it." : "";
  }

  // words that carry no topic ("what did SAME find?" is a request for an overview of SAME)
  const GENERIC = new Set(["result", "experiment", "data", "info", "information", "text", "find", "show", "say", "know", "detail",
    "explain", "describe", "about", "stuff", "topic", "overview", "summary"].map((w) => { const x = stem(w); return SYN[x] || x; }));
  // shown to people: the NASA acronym of the folder's record (PSI-68_FLEX_II -> FLEX-2), else the folder name without the PSI ID
  const folderName = (topic) => topic.replace(/^PSI-\d+_/i, "").replace(/_/g, " ");
  const labelOf = (topic) => { const m = /^PSI-\d+/i.exec(topic), r = m && window.FIF && FIF.data && FIF.data.records[m[0].toUpperCase()];
    return (r && r.acronym) || folderName(topic); };
  const plain = (t) => " " + String(t).toLowerCase().replace(/[^a-z0-9]+/g, " ").trim() + " ";

  // does the question name one of this character's experiments ("SAME", "SAME-R", "psi 102")?
  function topicMention(charId, question) {
    const q = plain(question);
    let best = null;
    for (const t of topicsFor(charId)) {
      const m = t.match(/^PSI-(\d+)/i), rec = m && window.FIF_DATA && window.FIF_DATA.records ? window.FIF_DATA.records["PSI-" + m[1]] : null;
      const names = [labelOf(t), folderName(t), rec && rec.acronym].filter(Boolean).map((x) => plain(x).trim())
        .flatMap((x) => [x, x.replace(/^acme /, "")]).filter((x) => x.length >= 3);
      // "PSI-26" written as a number is removed from the search words like a name is, so it does not match every chunk citing it
      const byNumber = m ? [`psi ${m[1]}`, `psi${m[1]}`].find((x) => q.includes(" " + x + " ")) || "" : "";
      const l = names.filter((x) => q.includes(" " + x + " ")).sort((a, b) => b.length - a.length)[0] || byNumber;
      const hit = !!l;
      if (hit && (!best || l.length > best.l.length)) best = { t, l };
    }
    return best;
  }

  // a spread of passages across topics (not the best match to a question): the raw material for a summary
  function overview(names, n) {
    const have = names.filter((t) => (D().topics[t] || []).length);
    const use = have.length > n ? Array.from({ length: n }, (_, i) => have[Math.floor(i * have.length / n)]) : have;
    const per = Math.max(1, Math.ceil(n / Math.max(use.length, 1)));
    const out = [];
    use.forEach((t) => {
      const all = D().topics[t], prose = all.filter((c) => c.kind === "text" || c.kind === "guidance");
      const list = prose.length ? prose : all.filter((c) => c.kind !== "policy"), m = Math.min(per, list.length);
      for (let j = 0; j < m; j++) { const c = list[Math.floor(j * list.length / m)]; if (out.length < n) out.push(Object.assign({ topic: t }, c)); }
    });
    return out;
  }
  const firstSentence = (t, max) => { const s = (sentences(t)[0] || t).trim(); return s.length > max ? s.slice(0, max - 1) + "…" : s; };

  async function summarize(charId, opts) {
    opts = opts || {};
    await load();
    const chunks = overview(opts.topics || topicsFor(charId), opts.n || 6);
    if (!chunks.length) return null;
    const hits = chunks.map((c) => ({ chunk: c }));
    const api = (window.FIF_DATA && window.FIF_DATA.chat && window.FIF_DATA.chat.api_url) || "";
    if (api) {
      try {
        const ctl = new AbortController(), t = setTimeout(() => ctl.abort(), opts.timeout || 8000);
        const r = await fetch(api, {
          method: "POST", headers: { "Content-Type": "application/json" }, signal: ctl.signal,
          body: JSON.stringify({ question: opts.question || "Summarize what these passages say.", character: charId, task: "summary",
            context: chunks.map((c) => ({ text: c.text })) }),
        });
        clearTimeout(t);
        if (r.ok) {
          const j = await r.json();
          if (j && j.answer && !/^\W*that is not in our data/i.test(j.answer)) return { answer: j.answer, sources: sourcesOf(hits), mode: "online", topic: (opts.topics || [])[0] || "" };
        }
      } catch (e) { /* offline summary below */ }
    }
    const lines = chunks.map((c) => firstSentence(c.text, 170));   // no topic / file labels in the answer
    return { answer: "Here is what I have. " + lines.join(" "), sources: sourcesOf(hits), mode: "offline", topic: (opts.topics || [])[0] || "" };
  }

  // true when another crew member's texts answer this clearly better than mine
  function betterElsewhere(charId, question, ownBest) {
    if (charId === "guide") return false;
    const mine = new Set(topicsFor(charId));
    const o = retrieve("*", question, 8).find((h) => !mine.has(h.chunk.topic) && ownersOf(h.chunk.topic).some((id) => id !== charId));
    return !!o && o.coverage >= 0.5 && o.coverage >= ownBest + 0.2;
  }

  // "what about its results?", "why?", "tell me more": no topic of its own, so it continues the previous topic
  const PRONOUN = /\b(it|its|that|this|they|them|their|those|these|there|one)\b/i;
  function isFollowUp(question) {
    const core = tokens(question).filter((w) => !GENERIC.has(w));
    return core.length === 0 || (core.length <= 2 && PRONOUN.test(question));
  }

  async function ask(charId, question, opts) {
    opts = opts || {};
    await load();
    let hits = null, scoped = false;
    let men = topicMention(charId, question);
    if (!men && opts.lastTopic && D().topics[opts.lastTopic] && isFollowUp(question)) men = { t: opts.lastTopic, l: "" };
    if (men) {
      const rest = men.l ? plain(question).split(" " + men.l + " ").join(" ") : question;
      if (!tokens(rest).filter((w) => !GENERIC.has(w)).length) return summarize(charId, { topics: [men.t], question, timeout: opts.timeout });
      hits = retrieve(charId, rest, opts.k || 5, [men.t]); scoped = hits.length > 0;
    }
    if (!hits || !hits.length) hits = retrieve(charId, question, opts.k || 5);
    if (!hits.length) return null;
    if (!scoped && betterElsewhere(charId, question, hits[0].coverage)) return null;   // the chat will recommend who to ask
    const api = (window.FIF_DATA && window.FIF_DATA.chat && window.FIF_DATA.chat.api_url) || "";
    const strong = hits.filter((h) => h.coverage >= 0.3);
    const usable = api ? hits.filter((h) => h.coverage >= 0.12) : strong;   // the model may judge loose matches itself
    if (!usable.length) return null;
    if (api) {
      const top = usable.slice(0, 4);
      try {
        const ctl = new AbortController(), t = setTimeout(() => ctl.abort(), opts.timeout || 6000);
        const r = await fetch(api, {
          method: "POST", headers: { "Content-Type": "application/json" }, signal: ctl.signal,
          body: JSON.stringify({ question, character: charId, history: opts.history || [],
            context: top.map((h) => ({ text: h.chunk.text })) }),
        });
        clearTimeout(t);
        if (r.ok) {
          const j = await r.json();
          if (j && j.answer) {
            if (/^\W*that is not in our data/i.test(j.answer)) return null;   // the model found nothing: no sources shown
            return { answer: j.answer, sources: sourcesOf(top), caution: cautionOf(top), mode: "online", topic: top[0].chunk.topic };
          }
        }
      } catch (e) { /* fall through to the offline answer */ }
    }
    if (!strong.length) return null;
    const top = strong.slice(0, 4);
    return { answer: extract(top, question), sources: sourcesOf(top), caution: cautionOf(top), mode: "offline", topic: top[0].chunk.topic };
  }

  // A simple question that is NOT in the texts ("what is a spacecraft?"): the model answers from general knowledge.
  // The endpoint replies "That is not in our data." when the question is off topic or it is not sure -> null.
  async function general(charId, question, opts) {
    opts = opts || {};
    const api = (window.FIF_DATA && window.FIF_DATA.chat && window.FIF_DATA.chat.api_url) || "";
    if (!api) return null;
    try {
      const ctl = new AbortController(), t = setTimeout(() => ctl.abort(), opts.timeout || 8000);
      const r = await fetch(api, {
        method: "POST", headers: { "Content-Type": "application/json" }, signal: ctl.signal,
        body: JSON.stringify({ question, character: charId, task: "general", history: opts.history || [], context: [] }),
      });
      clearTimeout(t);
      if (r.ok) {
        const j = await r.json();
        if (j && j.answer && !/^\W*that is not in our data/i.test(j.answer)) return { answer: j.answer, mode: "general" };
      }
    } catch (e) { /* no general answer */ }
    return null;
  }

  function ownersOf(topic) {
    const t = topic.toLowerCase();
    return Object.keys(D().map).filter((id) => id !== "guide" && (D().map[id] || [])
      .some((w) => w !== "*" && (t === w.toLowerCase() || t.startsWith(w.toLowerCase() + "_"))));
  }
  // Another crew member's texts match this question better than my own: who should be asked?
  function recommend(charId, question) {
    const mine = new Set(topicsFor(charId));
    const men = topicMention("*", question);          // "what is SPICE?" asked to someone else: SPICE's owner
    if (men && (charId === "guide" || !mine.has(men.t))) {
      const owners = ownersOf(men.t).filter((id) => id !== charId);
      if (owners.length) { const m = men.t.match(/^(PSI-\d+)/i); return { topic: men.t, psi: m ? m[1].toUpperCase() : "", title: "", owners, coverage: 1 }; }
    }
    for (const h of retrieve("*", question, 8)) {
      if (h.coverage < 0.4 || h.matched < Math.min(2, h.terms)) continue;
      if (charId !== "guide" && mine.has(h.chunk.topic)) continue;
      const owners = ownersOf(h.chunk.topic).filter((id) => id !== charId);
      if (owners.length) return { topic: h.chunk.topic, psi: h.chunk.psi || "", title: h.chunk.title, owners, coverage: h.coverage };
    }
    return null;
  }

  window.FIF_RAG = { ask, summarize, general, retrieve, recommend, topicMention, topicsFor, ownersOf, tokens, labelOf, ready: load };
  Object.defineProperty(window.FIF_RAG, "data", { get: D });
  // start loading once the page itself has finished, so the first question does not wait
  if (document.readyState === "complete") setTimeout(load, 200);
  else window.addEventListener("load", () => setTimeout(load, 200));
})();
