# -*- coding: utf-8 -*-
"""
ScaleEngine — UKBEEngine cu pasul de cuplaj in O(N) mean-field, pentru rulari
mari (VAULT: AGPL-3.0 / comercial).

POZITIONARE ONESTA (aceeasi ca in README-ul ukbe-core): identitatea matematica
NU e un secret —

    (K/N) Σ_j sin(θ_j − θ_i)  =  K · R · sin(ψ − θ_i),   R·e^{iψ} = (1/N) Σ_j e^{iθ_j}

e reducerea mean-field standard pentru cuplaj all-to-all uniform (aceeasi din
lucrarea P6 si din microgrid.py). Ce vinde seiful nu e identitatea, ci
INGINERIA LIVRATA: implementarea drop-in, testata pe ECHIVALENTA numerica cu
motorul de referinta (acelasi seed => aceleasi traiectorii), benchmarked, si
intretinuta impreuna cu restul stack-ului de produs.

Echivalenta e EXACTA matematic (nu o aproximare): pentru topologia all-to-all
uniforma din UKBEEngine, cele doua forme difera doar prin ordinea operatiilor
in virgula mobila. Testul de echivalenta ruleaza ambele motoare pas-cu-pas pe
acelasi proxy si cere traiectorii identice la tolerante de float.

LIMITA DECLARATA: reducerea O(N) e valabila pentru cuplaj ALL-TO-ALL UNIFORM
(cazul UKBEEngine). Pentru topologii de retea generale (grafuri rare, ponderi
pe muchii) suma nu se factorizeaza printr-un singur camp mediu — acolo se
folosesc metode pe matrice rara, nu acest motor.
"""
from __future__ import annotations

import numpy as np

from ukbe_core.engine import UKBEConfig, UKBEEngine


class ScaleEngine(UKBEEngine):
    """Drop-in pentru UKBEEngine: aceeasi stare, acelasi contract, acelasi
    rezultat numeric — pasul de cuplaj in O(N) in loc de O(N^2)."""

    def step(self, human_proxy_observation: float) -> dict:
        cfg = self.cfg
        self.t += cfg.dt

        theta_human_est, _ = self.kalman.update(human_proxy_observation)

        beta = max(1 - self.RSI, cfg.beta_min)
        alpha = 1 - beta

        # --- singura diferenta fata de referinta: O(N) in loc de O(N^2) ---
        # campul mediu R·e^{iψ}; Σ_j sin(θ_j−θ_i) = N·R·sin(ψ−θ_i)
        z = np.exp(1j * self.theta_i).mean()
        R, psi_field = np.abs(z), np.angle(z)
        kuramoto_term = cfg.K_int * R * np.sin(psi_field - self.theta_i)
        # -------------------------------------------------------------------
        ext_term = cfg.K_ext * np.sin(theta_human_est - self.theta_i)
        dtheta = self.omega_i + alpha * kuramoto_term + beta * ext_term
        self.theta_i = self.theta_i + cfg.dt * dtheta

        # restul pasului e identic cu referinta (metrici, RSI, evenimente)
        Phi_intern = np.abs(np.mean(np.exp(1j * self.theta_i)))
        theta_mean = np.angle(np.mean(np.exp(1j * self.theta_i)))
        psi = np.angle(np.exp(1j * (theta_mean - theta_human_est)))
        Phi_extern = (1 + np.cos(psi)) / 2.0

        Phi_t = alpha * Phi_intern + beta * Phi_extern
        self._rsi_history.append(Phi_t)
        if len(self._rsi_history) > cfg.rsi_window:
            self._rsi_history = self._rsi_history[-cfg.rsi_window:]
        self.RSI = float(np.mean(self._rsi_history))

        if self._last_Phi is not None and abs(Phi_t - self._last_Phi) > 0.3:
            self.unexpected_events.append((self.t, Phi_t))
        self._last_Phi = Phi_t

        return {
            "t": self.t,
            "RSI": self.RSI,
            "Phi_intern": float(Phi_intern),
            "Phi_extern": float(Phi_extern),
            "psi": float(psi),
            "alpha": float(alpha),
            "beta": float(beta),
            "theta_human_est": float(theta_human_est),
        }


__all__ = ["ScaleEngine", "UKBEConfig"]
