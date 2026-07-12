# -*- coding: utf-8 -*-
"""
AmiDor — aplicatia companion (Sprint 2): scam-shield + motor dual + persona,
cu chat prietenos pentru varstnici si panou de familie (consimtamant + jurnal
semnat). Voce: Sprint 3.

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
from persona import AMIDOR_SYSTEM, AMIDOR_GREETING
from scam_shield import detect_scam, scam_response
from ukbe_core.notary import generate_keypair, notarize, verify, NotarizedRecord

BASE = Path(__file__).parent
DATA = BASE / "data"; DATA.mkdir(exist_ok=True)
LOG = DATA / "amidor_log.jsonl"
KEYS = DATA / "notary_keys.json"

ENV = os.getenv("AMIDOR_ENV", "dev")
QID = os.getenv("QID", "1820209090023")
FAMILY_PIN = os.getenv("AMIDOR_FAMILY_PIN", "1234")
CONSENT = os.getenv("AMIDOR_JOURNAL_CONSENT", "false") == "true"  # consimtamant varstnic
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

ENGINE = DualEngine(A, B, system_prompt=AMIDOR_SYSTEM, threshold=CONC_THRESHOLD)

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


def _log(entry: dict):
    """Jurnal semnat — scris DOAR daca varstnicul si-a dat consimtamantul
    pentru panoul de familie (GDPR + demnitate). Fara consimtamant: nimic."""
    if not CONSENT:
        return
    payload = json.dumps(entry, ensure_ascii=False, sort_keys=True)
    rec = notarize(intent=payload, actor="amidor", qid=QID, private_key_bytes=PRIV)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"entry": entry, "record": rec.to_dict()}, ensure_ascii=False) + "\n")


app = FastAPI(title="AmiDor", version="0.2.0")


class Msg(BaseModel):
    message: str


@app.get("/")
def ui():
    return FileResponse(BASE / "static" / "amidor.html")

@app.get("/family")
def family_ui():
    return FileResponse(BASE / "static" / "family.html")

@app.get("/api/health")
def health():
    return {"service": "amidor", "version": "0.2.0",
            "engine": "dual anti-confabulation + REAI gate",
            "scam_shield": "v0", "journal_consent": CONSENT,
            "notary_pubkey": PUB.hex()}

@app.get("/api/greeting")
def greeting():
    return {"reply": AMIDOR_GREETING}


@app.post("/api/chat")
def chat(inp: Msg, request: Request):
    ip = request.client.host if request.client else "?"
    if not _rate_ok(ip):
        raise HTTPException(429, "prea multe mesaje — ia o pauză scurtă")
    msg = inp.message.strip()
    if not msg:
        raise HTTPException(400, "mesaj gol")
    if len(msg) > 800:
        raise HTTPException(400, "mesaj prea lung")

    t0 = time.time()
    # 1) SCAM-SHIELD inaintea oricarui model
    scam = detect_scam(msg)
    sresp = scam_response(scam)
    if sresp and not sresp["continue_flow"]:
        _log({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "user": msg,
              "reply": sresp["message"], "decision": "scam-interrupt",
              "scam": scam.categories, "flag_family": True})
        return {"reply": sresp["message"], "decision": "scam-interrupt",
                "scam_warning": True, "flag_family": True}

    # 2) MOTORUL DUAL
    r = ENGINE.ask(msg)
    flag_family = bool(sresp and sresp["flag_family"]) or r.decision in ("disagree",)
    _log({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "user": msg,
          "reply": r.reply, "decision": r.decision, "mode": r.mode,
          "concordance": r.concordance, "scam": scam.categories,
          "flag_family": flag_family, "latency_s": r.latency_s})
    return {"reply": r.reply, "decision": r.decision,
            "scam_warning": scam.risk.value != "none",
            "flag_family": flag_family}


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
