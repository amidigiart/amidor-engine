# -*- coding: utf-8 -*-
"""
Poarta de registru — ecuatiile REAI (ukbe-core) decid regimul conversatiei,
in varianta universala (fara persona): AFIRMA / INTREABA / REANCOREAZA.

Aceeasi mecanica validata in kinderagi-core si in lucrarea P6
(doi:10.5281/zenodo.21269201): ritmul conversatiei = faza de referinta;
modul se decide din ADANCIMEA dip-ului de coerenta din tura (metrica S),
nu din valoarea de la final; beta_min vine din regula Adler derivata.

La REANCOREAZA motorul dual NICI NU interogheaza modelele - cere intai
re-ancorarea conversatiei. (Comportament + economie de apeluri API.)
"""
from __future__ import annotations

import math
import statistics
import time

from ukbe_core.engine import UKBEConfig, UKBEEngine
from ukbe_core.calibration import recommend_beta_min

TWO_PI = 2 * math.pi
MAX_JITTER = 1.2
DELTA_OMEGA_MAX = MAX_JITTER / TWO_PI

AFFIRM, ASK, REANCHOR = "afirma", "intreaba", "reancoreaza"

DIRECTIVES = {
    AFFIRM: "",
    ASK: (
        " REGULĂ ACTIVĂ (coerența conversației a scăzut): nu introduce "
        "informații noi. Reformulează pe scurt ce a spus utilizatorul și "
        "pune o singură întrebare de clarificare."
    ),
}


class RegisterGate:
    def __init__(self, seed: int = 7):
        cal = recommend_beta_min(delta_omega_max=DELTA_OMEGA_MAX,
                                 K_ext=1.5, safety_margin=1.5)
        self.calibration = cal
        self.cfg = UKBEConfig(N=30, dt=0.02, K_int=1.2, K_ext=1.5,
                              beta_min=cal["recommended_beta_min"],
                              omega_mean=1.0, omega_std=0.05, seed=seed)
        self.engine = UKBEEngine(self.cfg)
        self.ref_phase = 0.0
        self.turn = 0
        self._intervals: list[float] = []
        self._last_ts: float | None = None
        self._last_len: int | None = None
        self.last: dict = {}
        for _ in range(3):                      # burn-in ancorat
            self._run_turn(0.0)

    def _run_turn(self, jitter: float) -> dict:
        steps = int(TWO_PI / self.cfg.omega_mean / self.cfg.dt)
        start = self.ref_phase + jitter          # salt de faza = perturbatia
        out, dip = {}, 1.0
        for s in range(steps):
            out = self.engine.step(start + TWO_PI * (s + 1) / steps)
            dip = min(dip, out["Phi_extern"])
        self.ref_phase = start + TWO_PI
        self.turn += 1
        out["Phi_dip"] = dip
        return out

    def _jitter(self, now: float, msg_len: int) -> float:
        j = 0.0
        if self._last_ts is not None:
            dt_real = max(now - self._last_ts, 0.5)
            self._intervals = (self._intervals + [dt_real])[-12:]
            med = statistics.median(self._intervals)
            if med > 0:
                j += max(-1.0, min(1.0, math.log(dt_real / med))) * 0.8
        if self._last_len:
            j += max(-0.5, min(0.5,
                     math.log(max(msg_len, 1) / max(self._last_len, 1)))) * 0.8
        self._last_ts, self._last_len = now, msg_len
        return max(-MAX_JITTER, min(MAX_JITTER, j))

    def observe(self, msg_len: int, now: float | None = None) -> dict:
        now = now if now is not None else time.time()
        s = self._run_turn(self._jitter(now, msg_len))
        dip = s["Phi_dip"]
        mode = AFFIRM if dip >= 0.75 else (ASK if dip >= 0.40 else REANCHOR)
        self.last = {
            "turn": self.turn, "mode": mode,
            "directive": DIRECTIVES.get(mode, ""),
            "RSI": round(s["RSI"], 4), "Phi_dip": round(dip, 4),
            "beta": round(s["beta"], 4),
            "beta_min": round(self.cfg.beta_min, 4),
        }
        return self.last
