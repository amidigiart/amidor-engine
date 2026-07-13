# -*- coding: utf-8 -*-
"""
Micro-Grid Synchronization — aplicatia REAI unde matematica e LITERAL matematica
domeniului (VAULT: AGPL-3.0 / comercial).

Generatoarele dintr-o retea electrica SUNT oscilatori Kuramoto care se blocheaza
pe frecventa nominala a retelei (50 Hz UE). In cadrul rotitor la frecventa
nominala, faza fiecarui generator theta_i evolueaza dupa:

    dθ_i/dt = Δω_i + (K/N) Σ_j sin(θ_j − θ_i)

unde Δω_i = abaterea de frecventa a generatorului i fata de nominal, K = taria
cuplajului (topologie + linii). Cand K depaseste imprastierea abaterilor, reteaua
se sincronizeaza (order parameter R → 1). Aceasta e exact reducerea mean-field
din lucrarea P6 (doi:10.5281/zenodo.21269201).

DOUA REZULTATE APLICATE DIRECT DIN P6:
  1. MARGINEA DE CUPLAJ: pentru a ramane blocat sub o abatere maxima Δω_max,
     reteaua are nevoie de K ≥ m·Δω_max, cu m derivat din timpul-tinta de
     recuperare (regula de calibrare din lucrare). NU o valoare ghicita.
  2. TIMPUL DE RECUPERARE dupa o perturbatie: τ = (K² − Δω²)^(−1/2) —
     incetinirea critica langa pragul de blocare. Aproape de prag, recuperarea
     e arbitrar de lenta (avertisment timpuriu de desincronizare).

LIMITA ONESTA (nu ascunsa): acesta e un model REDUS de faza (Kuramoto), NU o
simulare electromecanica completa. NU modeleaza tensiune, flux de putere,
constante de inertie calibrate pe generatoare reale, sau protectii. E un
instrument de MARJA DE STABILITATE si AVERTIZARE TIMPURIE — util pentru
dimensionare si monitorizare, NU un inlocuitor pentru PSS/E, DIgSILENT etc.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

TWO_PI = 2 * math.pi


@dataclass
class MicroGrid:
    n_gen: int = 6
    K: float = 2.0                 # taria cuplajului (grid)
    nominal_hz: float = 50.0
    freq_spread_hz: float = 0.15   # imprastierea abaterilor de frecventa (rad/s convertit intern)
    dt: float = 0.005
    seed: int = 0

    def __post_init__(self):
        rng = np.random.default_rng(self.seed)
        # abateri de frecventa fata de nominal, in rad/s (cadru rotitor)
        self.domega = TWO_PI * rng.normal(0.0, self.freq_spread_hz, self.n_gen)
        self.theta = rng.uniform(0, TWO_PI, self.n_gen)
        self.t = 0.0

    def step(self, disturbance_rad_s: float = 0.0, gen: int = 0):
        dw = self.domega.copy()
        dw[gen % self.n_gen] += disturbance_rad_s      # perturbatie pe un generator
        z = np.exp(1j * self.theta)
        kuramoto = self.K * np.imag(np.exp(-1j * self.theta) * z.mean())
        self.theta = self.theta + self.dt * (dw + kuramoto)
        self.t += self.dt

    def order_parameter(self) -> float:
        """R ∈ [0,1] — gradul de sincronizare a retelei (1 = perfect blocata)."""
        return float(np.abs(np.mean(np.exp(1j * self.theta))))

    def is_locked(self, thresh: float = 0.98) -> bool:
        return self.order_parameter() >= thresh

    def settle(self, steps: int = 4000, disturbance_rad_s: float = 0.0, gen: int = 0):
        for _ in range(steps):
            self.step(disturbance_rad_s, gen)
        return self.order_parameter()


def coupling_margin(delta_f_max_hz: float, tau_target_s: float = 1.0,
                    safety_margin: float = 1.5) -> dict:
    """Cuplajul minim K pentru ca reteaua sa ramana blocata sub o abatere maxima
    de frecventa delta_f_max, cu recuperare in tau_target. Aplica regula P6:
    K ≥ m·Δω_max, m = √(1 + (Δω_max·τ_target)^(−2)); marja de siguranta explicita
    peste pragul de bifurcatie."""
    dw_max = TWO_PI * delta_f_max_hz                    # rad/s
    if dw_max <= 0:
        raise ValueError("delta_f_max_hz trebuie > 0")
    m_recovery = math.sqrt(1.0 + 1.0 / (dw_max * tau_target_s) ** 2)
    m = max(m_recovery, safety_margin)                  # cel putin marja de siguranta
    K_threshold = dw_max                                # pragul exact de blocare (K=Δω)
    K_recommended = m * dw_max
    return {
        "delta_f_max_hz": delta_f_max_hz,
        "K_threshold": round(K_threshold, 4),           # sub asta: NU se blocheaza
        "K_recommended": round(K_recommended, 4),
        "margin_used": round(m, 4),
        "note": ("K sub K_threshold => alunecare permanenta de faza (desincronizare). "
                 "Intre prag si recomandat => blocat, dar recuperare lenta (incetinire critica)."),
    }


def recovery_time(K: float, delta_f_hz: float) -> float | None:
    """Timpul de recuperare dupa o perturbatie de frecventa, τ = (K²−Δω²)^(−1/2).
    None daca K ≤ Δω (nu se re-blocheaza — alunecare)."""
    dw = TWO_PI * delta_f_hz
    if K <= abs(dw):
        return None
    return 1.0 / math.sqrt(K ** 2 - dw ** 2)
