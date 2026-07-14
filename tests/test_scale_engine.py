# -*- coding: utf-8 -*-
"""ScaleEngine: echivalenta EXACTA cu referinta (acelasi seed => aceleasi
traiectorii) + speedup masurat, nu pretins."""
import time
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))

from ukbe_core.engine import UKBEConfig, UKBEEngine
from scale_engine import ScaleEngine


def _cfg(N, seed=7):
    return UKBEConfig(N=N, dt=0.02, K_int=1.2, K_ext=1.5, beta_min=0.2,
                      omega_mean=1.0, omega_std=0.05, seed=seed)


def test_ECHIVALENTA_traiectorii_identice_cu_referinta():
    # acelasi seed, acelasi proxy, pas cu pas: O(N) trebuie sa dea EXACT
    # aceeasi dinamica precum O(N^2) (identitate, nu aproximare)
    ref, fast = UKBEEngine(_cfg(40)), ScaleEngine(_cfg(40))
    rng = np.random.default_rng(123)
    for k in range(300):
        z = 0.5 * k * 0.02 + 0.05 * rng.normal()      # proxy uman zgomotos
        a, b = ref.step(z), fast.step(z)
    np.testing.assert_allclose(ref.theta_i, fast.theta_i, rtol=0, atol=1e-9)
    assert abs(a["RSI"] - b["RSI"]) < 1e-9
    assert abs(a["Phi_intern"] - b["Phi_intern"]) < 1e-9
    assert len(ref.unexpected_events) == len(fast.unexpected_events)


def test_SPEEDUP_masurat_la_N_mare():
    N, steps = 2000, 15
    ref, fast = UKBEEngine(_cfg(N)), ScaleEngine(_cfg(N))
    t0 = time.perf_counter()
    for _ in range(steps):
        ref.step(0.0)
    t_ref = time.perf_counter() - t0
    t0 = time.perf_counter()
    for _ in range(steps):
        fast.step(0.0)
    t_fast = time.perf_counter() - t0
    assert t_fast < t_ref / 5          # cel putin 5x (tipic mult peste)


def test_N_10000_ruleaza_rapid_si_sanatos():
    e = ScaleEngine(_cfg(10_000))
    t0 = time.perf_counter()
    for _ in range(100):
        d = e.step(0.0)
    assert time.perf_counter() - t0 < 10.0     # sub 10s pentru 100 pasi la N=10k
    assert 0.0 <= d["RSI"] <= 1.0 and 0.0 <= d["Phi_intern"] <= 1.0
    s = e.get_state_snapshot()
    assert 0.0 <= s["lock_ratio"] <= 1.0


def test_drop_in_pastreaza_contractul_snapshot():
    e = ScaleEngine(_cfg(50))
    e.step(0.0)
    s = e.get_state_snapshot()
    for key in ("t", "phi_intern", "h", "rsi", "theta_mean", "lock_ratio",
                "n_unexpected_events"):
        assert key in s
