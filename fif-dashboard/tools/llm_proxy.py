#!/usr/bin/env python3
"""Answer server for the crew chat. Keeps the API key OFF the web page.

The page POSTs {"question", "character", "context":[{topic,source,title,text}, ...]} (this is what
rag.js sends when content/chat.json has "api_url"). This server asks a Llama model to answer ONLY from
that context and returns {"answer": "..."}. If it fails, the page falls back to its offline answer.

Works with any OpenAI-compatible chat endpoint (Llama 3.1 / 3.3 on Together, Fireworks, OpenRouter,
a local Ollama, ...). Configure with environment variables - nothing to pip install:

    export LLM_BASE_URL="https://api.together.xyz/v1"          # provider's OpenAI-compatible base URL
    export LLM_API_KEY="..."                                    # your key (never put it in the page)
    export LLM_MODEL="meta-llama/Llama-3.3-70B-Instruct-Turbo"  # exact id from YOUR provider's model list
    python llm_proxy.py                                         # serves http://localhost:8787/ask

Groq (free tier):  LLM_BASE_URL=https://api.groq.com/openai/v1  LLM_MODEL=openai/gpt-oss-20b
    (Groq retired its Llama 3.1 / 3.3 models on 16 Aug 2026; list current ids with the /models call in the README.)

Local, no key:  LLM_BASE_URL=http://localhost:11434/v1  LLM_MODEL=llama3.3  (Ollama; LLM_API_KEY can be empty)

Then set  "api_url": "http://localhost:8787/ask"  in content/chat.json and run build_site_data.py.
For a public site, host this file (or the same logic as a serverless function) and use its https URL.
"""
from __future__ import annotations

import json
import os
import re
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib import error, request

BASE = os.environ.get("LLM_BASE_URL", "").rstrip("/")
KEY = os.environ.get("LLM_API_KEY", "")
MODEL = os.environ.get("LLM_MODEL", "")
ORIGIN = os.environ.get("ALLOWED_ORIGIN", "*")      # set to your site's URL when you publish
PORT = int(os.environ.get("PORT", "8787"))
HOST = os.environ.get("HOST", "127.0.0.1")          # this computer only; use 0.0.0.0 only when you host it publicly
MAX_CHUNKS, MAX_CHARS = 6, 1500

NO_LEAKS = (
    "Never mention how the data is stored or prepared: no file names, document or section titles, passage numbers, "
    "table or column names, row counts, removed duplicates or other cleaning steps. Talk about the science and the findings, not the files. "
)

SYSTEM = (
    "You are a crew member in an educational site about NASA microgravity fire experiments. "
    "Answer the question using ONLY the context passages. Do not use outside knowledge and never invent numbers. "
    + NO_LEAKS +
    "If the question uses words like 'it', 'that' or 'more', use the earlier conversation only to work out what they refer to; "
    "the facts still come only from the passages. "
    "If the passages answer only part of the question, give that part and say what is missing. "
    "Only if they contain nothing relevant, reply exactly: \"That is not in our data.\" "
    "Keep the answer to 2-4 short sentences in plain language."
)

SYSTEM_SUMMARY = (
    "You are a crew member in an educational site about NASA microgravity fire experiments. "
    "Summarize the numbered context passages in 3-5 short sentences of plain language. Use ONLY the passages and never invent numbers. "
    + NO_LEAKS +
    "Say what was tested and what was learned. Do not describe the layout of tables or list their columns or settings."
)

SYSTEM_GENERAL = (
    "You are a friendly crew member in an educational site about NASA microgravity fire experiments. "
    "The visitor's question is not in our texts. If it is a simple, general-knowledge question that fits this theme "
    "(space, spacecraft, the space station, cargo vehicles, fire and combustion, physics, basic science and engineering terms), "
    "answer it in 1-3 short sentences of plain language using well-established general knowledge. "
    "Do not quote numbers from NASA experiments and do not say the answer comes from our data. "
    "If the question is not about this theme, or you are not sure, reply exactly: \"That is not in our data.\""
)


def history_messages(body: dict) -> list[dict]:
    out = []
    for h in (body.get("history") or [])[-3:]:
        if not isinstance(h, dict):
            continue
        q, a = str(h.get("q", ""))[:300], str(h.get("a", ""))[:400]
        if q and a:
            out += [{"role": "user", "content": q}, {"role": "assistant", "content": a}]
    return out


def build_messages(body: dict) -> list[dict]:
    q = str(body.get("question", ""))[:300]
    task = body.get("task")
    if task == "general":
        return [{"role": "system", "content": SYSTEM_GENERAL}] + history_messages(body) + [{"role": "user", "content": q}]
    # only the passage text is shown to the model: no topic, file or title names it could repeat
    parts = [f"[{i}]\n{str(c.get('text', ''))[:MAX_CHARS]}" for i, c in enumerate((body.get("context") or [])[:MAX_CHUNKS], 1)]
    if task == "summary":
        user = "Context:\n\n" + "\n\n".join(parts) + "\n\nTask: write a short summary (3-5 sentences) of what these passages say, covering the different topics."
        return [{"role": "system", "content": SYSTEM_SUMMARY}, {"role": "user", "content": user}]
    user = "Context:\n\n" + "\n\n".join(parts) + f"\n\nQuestion: {q}"
    return [{"role": "system", "content": SYSTEM}] + history_messages(body) + [{"role": "user", "content": user}]


# safety net: even if the model slips, sentences about files / tables / cleaning never reach the page
LEAK = re.compile(r"(\b\d[\d,]*\s+(?:data\s+)?rows?\b|\bduplicates?\b|\b(?:original|source|data) table\b|"
                  r"\b[\w\-]+\.(?:txt|csv|json|pdf|md|xlsx?|docx?)\b|\bPSI-\d+\w*)", re.I)


def clean(text: str) -> str:
    text = re.sub(r"\s*\[\d+\]|\bpassages?\s+\d+\b", "", text, flags=re.I)
    kept = [s for s in re.split(r"(?<=[.!?])\s+", text) if not LEAK.search(s)]
    return " ".join(kept).strip()


def ask_llm(messages: list[dict]) -> str:
    payload = json.dumps({"model": MODEL, "messages": messages, "temperature": 0.2, "max_tokens": 1200}).encode()
    headers = {"Content-Type": "application/json", "Accept": "application/json",
               "User-Agent": "fif-dashboard/1.0 (+local proxy)"}   # the default Python-urllib agent is blocked by some providers (403)
    if KEY:
        headers["Authorization"] = f"Bearer {KEY}"
    req = request.Request(f"{BASE}/chat/completions", data=payload, headers=headers, method="POST")
    with request.urlopen(req, timeout=30) as r:
        text = json.loads(r.read())["choices"][0]["message"].get("content") or ""
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.S).strip()   # some reasoning models print their thinking
    text = clean(text)
    if not text:
        raise ValueError("empty answer")                                   # page falls back to the offline answer
    return text


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, obj: dict | None = None):
        self.send_response(code)
        self.send_header("Access-Control-Allow-Origin", ORIGIN)
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        data = json.dumps(obj or {}).encode()
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_OPTIONS(self):
        self._send(204)

    def do_POST(self):
        if self.path.rstrip("/") != "/ask":
            return self._send(404, {"error": "not found"})
        try:
            n = int(self.headers.get("Content-Length", 0))
            if n > 100_000:
                return self._send(413, {"error": "too large"})
            body = json.loads(self.rfile.read(n))
            if not body.get("context") and body.get("task") != "general":
                return self._send(200, {"answer": "That is not in our data."})
            self._send(200, {"answer": ask_llm(build_messages(body))})
        except (error.URLError, error.HTTPError, KeyError, ValueError, TimeoutError) as e:
            detail = ""
            if isinstance(e, error.HTTPError):
                try:
                    detail = " | " + e.read().decode("utf-8", "replace")[:300]
                except Exception:
                    pass
            print("upstream error:", repr(e) + detail, file=sys.stderr)   # details stay in the server log, not the page
            self._send(502, {"error": "model unavailable"})

    def log_message(self, fmt, *a):
        pass


if __name__ == "__main__":
    if not (BASE and MODEL):
        raise SystemExit("Set LLM_BASE_URL and LLM_MODEL (and LLM_API_KEY if your provider needs one). See the top of this file.")
    print(f"crew answers on http://localhost:{PORT}/ask  ->  {BASE}  model={MODEL}")
    try:
        server = ThreadingHTTPServer((HOST, PORT), Handler)
    except OSError as e:
        raise SystemExit(f"Cannot use port {PORT} ({e}). Pick another one, e.g. PowerShell:  $env:PORT=\"8899\"  then run again, "
                         f"and use http://localhost:8899/ask as api_url.")
    server.serve_forever()
