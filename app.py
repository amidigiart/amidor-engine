# -*- coding: utf-8 -*-
"""
AmiDor — aplicatia companion (Sprint 2): scam-shield + motor dual + persona,
cu chat prietenos pentru varstnici si panou de familie (consimtamant + jurnal
semnat) + i18n (RO/EN) + voce (STT browser / TTS local piper).

Config prin mediu (vezi .env.example). Fara chei hardcodate.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel

from adapters import OpenAICompatAdapter
from engine import DualEngine
from i18n import bundle, t, available, DEFAULT as DEFAULT_LANG
from scam_shield import detect_scam, scam_response
from voice_local import tts_available, synthesize
from alerts import build_from_env, AlertEvent
import threading
from ukbe_core.notary import generate_keypair, notarize, verify, NotarizedRecord

BASE = Path(__file__).parent
DATA = BASE / "data"; DATA.mkdir(exist_ok=True)
LOG = DATA / "amidor_log.jsonl"
KEYS = DATA / "notary_keys.json"

ENV = os.getenv("AMIDOR_ENV", "dev")
QID = os.getenv("QID", "1820209090023")
FAMILY_PIN = os.getenv("AMIDOR_FAMILY_PIN", "1234")
CONSENT = os.getenv("AMIDOR_JOURNAL_CONSENT", "false") == "true"  # consimtamant varstnic
ACCESS_CODE = os.getenv("AMIDOR_ACCESS_CODE", "")  # poarta pt instante pilot publice
CONC_THRESHOLD = float(os.getenv("AMIDOR_CONCORDANCE", "0.45"))

# Doua modele, configurabile. Implicit: acelasi Ollama la 2 temperaturi
# (dezvoltare). In productie: 2 endpointuri EU distincte (vezi BLUEPRINT).
A = OpenAICompatAdapter(
    os.getenv("MODEL_A_URL", "http://localhost:11434/v1"),
    os.getenv("MODEL_A_NAME", "gemma3:4b"),
    api_key=os.getenv("MODEL_A_KEY"), temperature=0.2, name="A", max_tokens=260)
B = OpenAICompatAdapter(
    os.getenv("MODEL_B_URL", "http://localhost:11434/v1"),
    os.getenv("MODEL_B_NAME", "gemma3:4b"),
    api_key=os.getenv("MODEL_B_KEY"), temperature=0.8, name="B", max_tokens=260)

if ENV == "prod" and FAMILY_PIN == "1234":
    raise RuntimeError("Refuz pornirea in productie cu PIN implicit. Seteaza AMIDOR_FAMILY_PIN.")

# Un motor per limba (gate/dinamica proprie per sesiune de limba)
_ENGINES: dict[str, DualEngine] = {}
def engine_for(lang: str) -> DualEngine:
    lang = lang if lang in {l['code'] for l in available()} else DEFAULT_LANG
    if lang not in _ENGINES:
        _ENGINES[lang] = DualEngine(A, B, system_prompt=bundle(lang)['system_prompt'],
                                    threshold=CONC_THRESHOLD, locale=lang)
    return _ENGINES[lang]

_RATE: dict[str, list] = {}
def _rate_ok(ip: str, mx=25, win=60.0) -> bool:
    now = time.time()
    _RATE[ip] = [t for t in _RATE.get(ip, []) if now - t < win] + [now]
    return len(_RATE[ip]) <= mx


def _keys():
    if KEYS.exists():
        d = json.loads(KEYS.read_text())
        return bytes.fromhex(d["private"]), bytes.fromhex(d["public"])
    pr, pu = generate_keypair()
    KEYS.write_text(json.dumps({"private": pr.hex(), "public": pu.hex()}))
    return pr, pu
PRIV, PUB = _keys()

# Alerte catre familie (Sprint 4). Canalele se configureaza din mediu; log-ul
# e mereu activ. Alertele NU contin continutul conversatiei (minimizare GDPR).
ALERTS = build_from_env(os.environ, str(DATA / "alerts.jsonl"))
ALERT_ON_SCAM = os.getenv("ALERT_ON_SCAM", "true") == "true"

def _fire_alert(ev: AlertEvent):
    # in thread separat: protectia/raspunsul utilizatorului are prioritate
    threading.Thread(target=ALERTS.dispatch, args=(ev,), daemon=True).start()


def _log(entry: dict):
    """Jurnal semnat — scris DOAR daca varstnicul si-a dat consimtamantul
    pentru panoul de familie (GDPR + demnitate). Fara consimtamant: nimic."""
    if not CONSENT:
        return
    payload = json.dumps(entry, ensure_ascii=False, sort_keys=True)
    rec = notarize(intent=payload, actor="amidor", qid=QID, private_key_bytes=PRIV)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"entry": entry, "record": rec.to_dict()}, ensure_ascii=False) + "\n")


app = FastAPI(title="AmiDor", version="0.5.0")


class Msg(BaseModel):
    message: str
    lang: str = DEFAULT_LANG
    access_code: str = ""


@app.get("/")
def ui():
    return FileResponse(BASE / "static" / "amidor.html")

@app.get("/family")
def family_ui():
    return FileResponse(BASE / "static" / "family.html")

@app.get("/api/health")
def health():
    return {"service": "amidor", "version": "0.5.0",
            "engine": "dual anti-confabulation + REAI gate",
            "scam_shield": "v0", "journal_consent": CONSENT,
            "notary_pubkey": PUB.hex()}

@app.get("/api/greeting")
def greeting(lang: str = DEFAULT_LANG):
    return {"reply": t(lang, "greeting"), "lang": lang,
            "speech": t(lang, "speech")}


@app.get("/api/langs")
def langs():
    return {"default": DEFAULT_LANG, "available": available(),
            "local_tts": tts_available(), "access_gated": bool(ACCESS_CODE)}


@app.get("/api/tts")
def tts(text: str, lang: str = DEFAULT_LANG):
    """TTS local (piper) — calea GDPR-curata pentru deploy pe server.
    501 daca piper nu e configurat; browserul foloseste atunci speechSynthesis
    (cu nota de confidentialitate afisata)."""
    wav = synthesize(text[:500], lang)
    if wav is None:
        raise HTTPException(501, "TTS local neconfigurat (seteaza PIPER_BIN si PIPER_VOICE_<LANG>)")
    from fastapi.responses import Response
    return Response(content=wav, media_type="audio/wav")


@app.post("/api/chat")
def chat(inp: Msg, request: Request):
    ip = request.client.host if request.client else "?"
    if not _rate_ok(ip):
        raise HTTPException(429, "prea multe mesaje — ia o pauză scurtă")
    if ACCESS_CODE and inp.access_code != ACCESS_CODE:
        raise HTTPException(403, "cod de acces necesar (instanță pilot privată)")
    msg = inp.message.strip()
    if not msg:
        raise HTTPException(400, "mesaj gol")
    if len(msg) > 800:
        raise HTTPException(400, "mesaj prea lung")

    t0 = time.time()
    lang = inp.lang if inp.lang else DEFAULT_LANG
    # 1) SCAM-SHIELD inaintea oricarui model (mesajul de avertizare: localizat)
    scam = detect_scam(msg)
    sresp = scam_response(scam)
    if sresp and not sresp["continue_flow"]:
        warn = t(lang, "scam_interrupt")
        _log({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "user": msg,
              "reply": warn, "decision": "scam-interrupt", "lang": lang,
              "scam": scam.categories, "flag_family": True})
        if ALERT_ON_SCAM:
            _fire_alert(AlertEvent(kind="scam_likely",
                        at=time.strftime("%H:%M, %d %b %Y"),
                        category=",".join(scam.categories), lang=lang))
        return {"reply": warn, "decision": "scam-interrupt",
                "scam_warning": True, "flag_family": True, "lang": lang}

    # 2) MOTORUL DUAL, in limba utilizatorului
    r = engine_for(lang).ask(msg)
    flag_family = bool(sresp and sresp["flag_family"]) or r.decision in ("disagree",)
    _log({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "user": msg,
          "reply": r.reply, "decision": r.decision, "mode": r.mode,
          "concordance": r.concordance, "scam": scam.categories, "lang": lang,
          "flag_family": flag_family, "latency_s": r.latency_s})
    return {"reply": r.reply, "decision": r.decision,
            "scam_warning": scam.risk.value != "none",
            "flag_family": flag_family, "lang": lang,
            "speech": t(lang, "speech")}


@app.get("/api/family/alerts")
def family_alerts(pin: str):
    if pin != FAMILY_PIN:
        raise HTTPException(403, "PIN greșit")
    return {"channels": [getattr(c, "name", "?") for c in ALERTS.channels],
            "cooldown_s": ALERTS.cooldown, "recent_errors": ALERTS.errors[-5:]}


@app.get("/api/family/log")
def family_log(pin: str):
    if pin != FAMILY_PIN:
        raise HTTPException(403, "PIN greșit")
    if not CONSENT:
        return {"consent": False, "turns": [],
                "note": "Jurnalul e dezactivat: persoana nu și-a dat consimțământul."}
    out = []
    if LOG.exists():
        for line in LOG.read_text(encoding="utf-8").splitlines():
            row = json.loads(line); rc = row["record"]
            rec = NotarizedRecord(intent=rc["intent"], actor=rc["actor"],
                qid=rc["qid"], timestamp=rc["timestamp"],
                content_hash=rc["content_hash"], signature_hex=rc["signature"],
                witness_signatures=rc.get("witnesses", []))
            out.append({**row["entry"], "signature_valid": verify(rec, PUB)})
    return {"consent": True, "turns": out, "notary_pubkey": PUB.hex()}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8124)
