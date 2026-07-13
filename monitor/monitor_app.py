# -*- coding: utf-8 -*-
"""
REAI Engine — Live State Monitor (VAULT: AGPL-3.0 / comercial).

Panou de monitorizare care afiseaza starea REALA a motorului REAI in timp real:
alpha/beta (ponderile adaptive), H (entropia = 1-Phi_intern), RSI, lock_ratio.
Toate vin din ukbe_core.engine.UKBEEngine.get_state_snapshot() / step() — nu
valori inventate. Un driver sintetic (proxy uman = faza care variaza lin) misca
motorul ca sa vezi dinamica vie.

Acces demo: gated prin MONITOR_ACCESS_CODE (demo doar cu NDA — vezi ../COMMERCIAL.md).
Sursa e AGPL/comercial; accesul la instanta demo se acorda dupa NDA.
"""
from __future__ import annotations

import math
import os
import threading
import time
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

from ukbe_core.engine import UKBEConfig, UKBEEngine
from ukbe_core.calibration import recommend_beta_min

BASE = Path(__file__).parent
ACCESS = os.getenv("MONITOR_ACCESS_CODE", "")   # gol = deschis local; setat = NDA-gated
TWO_PI = 2 * math.pi

_cal = recommend_beta_min(delta_omega_max=0.19, K_ext=1.5, safety_margin=1.5)
_cfg = UKBEConfig(N=30, K_ext=1.5, K_int=1.2,
                  beta_min=_cal["recommended_beta_min"], seed=7)
_engine = UKBEEngine(_cfg)
_state: dict = {"t": 0.0}
_running = True


def _driver():
    """Misca motorul cu un proxy uman sintetic (faza care avanseaza lin, cu
    o mica modulatie de ritm), ca dinamica REAI sa fie vizibila live."""
    ref = 0.0
    k = 0
    while _running:
        omega_h = 1.0 + 0.25 * math.sin(k * 0.01)   # intentie care respira
        ref += omega_h * _cfg.dt
        out = _engine.step(ref)                      # pas real de motor
        snap = _engine.get_state_snapshot()
        _state.update({
            "t": round(out["t"], 2),
            "alpha": round(out["alpha"], 4),
            "beta": round(out["beta"], 4),
            "beta_min": round(_cfg.beta_min, 4),
            "RSI": round(out["RSI"], 4),
            "H": round(snap["h"], 4),                 # entropia = 1 - Phi_intern
            "phi_intern": round(snap["phi_intern"], 4),
            "phi_extern": round(out["Phi_extern"], 4),
            "locked_pct": round(snap["lock_ratio"] * 100, 1),
            "n_events": snap["n_unexpected_events"],
        })
        k += 1
        time.sleep(_cfg.dt)


app = FastAPI(title="REAI Engine Monitor", version="0.1.0")


@app.on_event("startup")
def _start():
    threading.Thread(target=_driver, daemon=True).start()


@app.get("/")
def ui():
    return FileResponse(BASE / "dashboard.html")


@app.get("/monitor/state")
def state(code: str = ""):
    if ACCESS and code != ACCESS:
        raise HTTPException(403, "acces demo prin NDA (setați ?code=…)")
    return {**_state, "gated": bool(ACCESS),
            "calibration": {"recommended_beta_min": _cal["recommended_beta_min"],
                            "threshold_beta_min": _cal["threshold_beta_min"]}}


@app.get("/monitor/health")
def health():
    return {"service": "reai-engine-monitor", "gated": bool(ACCESS),
            "engine": "ukbe_core.UKBEEngine (real state)"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8125)
