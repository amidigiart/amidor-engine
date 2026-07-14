# -*- coding: utf-8 -*-
"""Monitorul de stare REAI: expune valori REALE din motor, in interval valid,
si respecta poarta de acces NDA."""
import importlib
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "monitor"))


def _client(**env):
    for k in ["MONITOR_ACCESS_CODE"]:
        os.environ.pop(k, None)
    for k, v in env.items():
        os.environ[k] = v
    import monitor_app
    importlib.reload(monitor_app)
    from fastapi.testclient import TestClient
    return monitor_app, TestClient(monitor_app.app)


def test_starea_e_reala_si_in_interval():
    mod, c = _client()
    with c:                      # ruleaza startup (porneste driverul)
        time.sleep(0.3)          # lasa cateva pasi de motor
        d = c.get("/state").json()
    for key in ("RSI", "alpha", "beta", "H", "phi_intern", "phi_extern"):
        assert 0.0 - 1e-9 <= d[key] <= 1.0 + 1e-9, f"{key}={d[key]} in afara [0,1]"
    assert 0.0 <= d["locked_pct"] <= 100.0
    assert abs(d["alpha"] + d["beta"] - 1.0) < 1e-6      # α + β = 1
    assert d["beta"] >= d["beta_min"] - 1e-9             # planseul Adler respectat


def test_motorul_de_scara_e_cel_care_ruleaza():
    mod, c = _client()
    with c:
        time.sleep(0.3)
        d = c.get("/state").json()
        h = c.get("/health").json()
    assert d["N"] >= 1000                      # scara de productie, nu jucaria N=30
    assert d["step_ms"] >= 0.0                 # costul real pe pas, masurat
    assert "ScaleEngine" in h["engine"]        # motorul O(N) din seif


def test_poarta_nda_blocheaza_fara_cod():
    mod, c = _client(MONITOR_ACCESS_CODE="nda-secret")
    with c:
        assert c.get("/state").status_code == 403
        assert c.get("/state?code=nda-secret").status_code == 200
        assert c.get("/health").status_code == 200   # health ramane public


def teardown_module(module):
    os.environ.pop("MONITOR_ACCESS_CODE", None)
