# -*- coding: utf-8 -*-
"""Alerte familie (Sprint 4): minimizarea datelor (fara continut de conversatie),
de-duplicare (fara spam), fail-safe (un canal cazut nu blocheaza restul)."""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from alerts import (AlertEvent, AlertManager, CallableChannel, LogChannel,
                    build_from_env)


def test_alerta_nu_contine_continut_de_conversatie():
    ev = AlertEvent(kind="scam_likely", at="10:30", category="autoritate_falsa")
    s = ev.summary()
    assert "înșelăciune" in s and "autoritate_falsa" in s
    assert "NU este trimis" in s        # promisiunea de minimizare, explicita


def test_summary_bilingv():
    en = AlertEvent(kind="scam_likely", at="10:30", category="bank", lang="en").summary()
    assert "possible scam" in en and "No conversation content" in en


def test_dispatch_trimite_pe_toate_canalele():
    got = []
    mgr = AlertManager([CallableChannel(got.append, "c1"),
                        CallableChannel(got.append, "c2")], cooldown=0)
    res = mgr.dispatch(AlertEvent("scam_likely", "10:30", "x"))
    assert res["sent"] == 2 and len(got) == 2


def test_deduplicare_nu_spameaza_familia():
    got = []
    mgr = AlertManager([CallableChannel(got.append)], cooldown=300)
    ev = AlertEvent("scam_likely", "10:30", "autoritate_falsa")
    assert mgr.dispatch(ev)["sent"] == 1
    r2 = mgr.dispatch(ev)                # aceeasi categorie, imediat
    assert r2["throttled"] and r2["sent"] == 0
    assert len(got) == 1


def test_categorie_diferita_nu_e_throttled():
    got = []
    mgr = AlertManager([CallableChannel(got.append)], cooldown=300)
    mgr.dispatch(AlertEvent("scam_likely", "10:30", "autoritate_falsa"))
    r = mgr.dispatch(AlertEvent("scam_likely", "10:31", "transfer_bani"))
    assert not r["throttled"] and r["sent"] == 1


def test_canal_cazut_nu_blocheaza_restul():
    got = []
    def broken(ev): raise RuntimeError("SMTP down")
    mgr = AlertManager([CallableChannel(broken, "email"),
                        CallableChannel(got.append, "ok")], cooldown=0)
    res = mgr.dispatch(AlertEvent("scam_likely", "10:30", "x"))
    assert res["sent"] == 1 and len(got) == 1       # al doilea a mers
    assert mgr.errors and "email" in mgr.errors[0]


def test_log_channel_scrie_fara_continut(tmp_path):
    p = tmp_path / "a.jsonl"
    LogChannel(str(p)).send(AlertEvent("scam_likely", "10:30", "bank"))
    line = p.read_text(encoding="utf-8")
    assert "bank" in line and "scam_likely" in line


def test_build_from_env_are_mereu_log(tmp_path):
    mgr = build_from_env({}, str(tmp_path / "a.jsonl"))
    assert len(mgr.channels) == 1 and mgr.channels[0].name == "log"


def test_build_from_env_adauga_webhook(tmp_path):
    mgr = build_from_env({"ALERT_WEBHOOK_URL": "http://x/hook"}, str(tmp_path / "a.jsonl"))
    assert {c.name for c in mgr.channels} == {"log", "webhook"}
