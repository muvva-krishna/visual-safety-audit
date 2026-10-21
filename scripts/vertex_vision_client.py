#!/usr/bin/env python3
"""Vertex AI vision client via Application Default Credentials (stdlib only).

Mirrors the auth + ledger pattern of job-intelligence/scripts/gemini_client.py:
- ADC refresh-token → oauth2.googleapis.com (~0.3s), gcloud fallback.
- Project strictly YOUR_GCP_PROJECT, location global.
- Records official usageMetadata + USD cost per call into results/token_usage.json
  (separate ledger from job-intelligence; same pricing source).

Adds what job-intelligence's text-only client lacks:
- inlineData image parts (base64 PNG/JPEG).
- optional systemInstruction (the §6 mitigation lever).
- text-only mode for the §5 leakage control.

Pricing (Vertex AI Generative AI, Global Standard, checked 2026-10-17):
  gemini-2.5-flash: $0.30 / 1M input tokens (image+text), $2.50 / 1M output
  (candidates + thoughts). No grounding used in this pilot ($0).
"""
from __future__ import annotations
import base64, datetime as dt, json, os, socket, subprocess, threading, time, urllib.parse, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
LEDGER = RESULTS / "token_usage.json"
PROJECT = "YOUR_GCP_PROJECT"
LOCATION = "global"
MODEL = "gemini-2.5-flash"
RATES = {"input": 0.30, "output": 2.50}  # USD per 1M tokens

_ORIG = socket.getaddrinfo
def _ipv4(host, port, family=0, type=0, proto=0, flags=0):
    try: return _ORIG(host, port, socket.AF_INET, type, proto, flags)
    except Exception: return _ORIG(host, port, family, type, proto, flags)
socket.getaddrinfo = _ipv4

ADC_FILE = Path(os.getenv("GOOGLE_APPLICATION_CREDENTIALS",
    str(Path.home() / ".config" / "gcloud" / "application_default_credentials.json")))
_TOK = {"t": "", "exp": 0.0}
_LEDGER_LOCK = threading.Lock()   # guards ledger read-modify-write across pool threads

def adc_token() -> str:
    now = time.time()
    if now < _TOK["exp"] - 60 and _TOK["t"]: return _TOK["t"]
    if ADC_FILE.exists():
        try:
            c = json.loads(ADC_FILE.read_text())
            if all(k in c for k in ("client_id", "client_secret", "refresh_token")):
                body = urllib.parse.urlencode({"client_id": c["client_id"],
                    "client_secret": c["client_secret"], "refresh_token": c["refresh_token"],
                    "grant_type": "refresh_token"}).encode()
                req = urllib.request.Request("https://oauth2.googleapis.com/token", data=body,
                    headers={"Content-Type": "application/x-www-form-urlencoded"})
                with urllib.request.urlopen(req) as r: d = json.load(r)
                if d.get("access_token"):
                    _TOK.update({"t": d["access_token"], "exp": now + int(d.get("expires_in", 3500))})
                    return _TOK["t"]
        except Exception: pass
    out = subprocess.check_output(["gcloud", "auth", "application-default",
        "print-access-token"], text=True).strip()
    _TOK.update({"t": out, "exp": now + 3000}); return out

def _url(model: str, action="generateContent") -> str:
    return (f"https://aiplatform.googleapis.com/v1/projects/{PROJECT}"
            f"/locations/{LOCATION}/publishers/google/models/{model}:{action}")

def generate(image_b64: str | None, mime: str, prompt: str,
             system: str | None = None, temperature: float = 0.0,
             max_tokens: int = 300, model: str = MODEL) -> dict:
    parts = ([{"inlineData": {"mimeType": mime, "data": image_b64}}] if image_b64 else []) \
        + [{"text": prompt}]
    body: dict = {"contents": [{"role": "user", "parts": parts}],
                  "generationConfig": {"temperature": temperature,
                                       "maxOutputTokens": max_tokens}}
    if system: body["systemInstruction"] = {"parts": [{"text": system}]}
    t0 = time.monotonic()
    req = urllib.request.Request(_url(model), data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {adc_token()}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req) as r: d = json.load(r)
    ms = int((time.monotonic() - t0) * 1000)
    cand = d.get("candidates", [{}])[0]
    text = "".join(p.get("text", "") for p in cand.get("content", {}).get("parts", [])).strip()
    u = d.get("usageMetadata", {})
    pt, ct, th = int(u.get("promptTokenCount", 0)), int(u.get("candidatesTokenCount", 0)), int(u.get("thoughtsTokenCount", 0))
    cost = round(pt / 1e6 * RATES["input"] + (ct + th) / 1e6 * RATES["output"], 8)
    # Safety-block transparency: a response that stops after a few tokens with
    # finish != STOP may indicate a mid-stream block. Record verbatim.
    rec = {"ts": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
           "project": PROJECT, "location": LOCATION, "model": model,
           "model_version": d.get("modelVersion", model),
           "prompt_tokens": pt, "candidates_tokens": ct, "thoughts_tokens": th,
           "total_tokens": int(u.get("totalTokenCount", pt + ct + th)),
           "modalities": u.get("promptTokensDetails", []),
           "cost_usd": cost, "latency_ms": ms,
           "finish": cand.get("finishReason"),
           "safety": cand.get("safetyRatings", []),
           "image_present": bool(image_b64),
           "system_present": bool(system)}
    with _LEDGER_LOCK:
        RESULTS.mkdir(parents=True, exist_ok=True)
        try:
            led = json.loads(LEDGER.read_text()) if LEDGER.exists() else None
        except Exception:
            q = LEDGER.with_suffix(".json.corrupt"); LEDGER.replace(q); led = None
        if not isinstance(led, dict) or led.get("project") != PROJECT:
            led = {"project": PROJECT, "calls": 0, "tokens": 0, "cost_usd": 0.0, "events": []}
        led["calls"] += 1; led["tokens"] += rec["total_tokens"]; led["cost_usd"] = round(led["cost_usd"] + cost, 8)
        led["events"] = (led.get("events", []) + [rec])[-2000:]
        tmp = LEDGER.with_suffix(".json.tmp"); tmp.write_text(json.dumps(led, indent=2) + "\n"); tmp.replace(LEDGER)
    return {"text": text, "usage": rec}

def image_to_b64(path: str | Path) -> tuple[str, str]:
    p = Path(path); suf = p.suffix.lower()
    mime = "image/png" if suf == ".png" else "image/jpeg"
    return base64.b64encode(p.read_bytes()).decode(), mime

if __name__ == "__main__":
    import sys
    # smoke: python3 scripts/vertex_vision_client.py <image> "<prompt>"
    b64, mime = image_to_b64(sys.argv[1]) if len(sys.argv) > 2 else (None, "image/png")
    print(json.dumps(generate(b64, mime, sys.argv[2] if len(sys.argv) > 2 else "Say ok."), indent=2)[:1500])
