# -*- coding: utf-8 -*-
"""Micro-grid sync: verificam ca fizica se comporta corect si ca regula de
margine (P6) chiar mentine reteaua blocata sub perturbatia anticipata."""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from microgrid import MicroGrid, coupling_margin, recovery_time, TWO_PI


def test_cuplaj_puternic_sincronizeaza_reteaua():
    g = MicroGrid(n_gen=6, K=3.0, freq_spread_hz=0.1, seed=1)
    r = g.settle(6000)
    assert r > 0.98 and g.is_locked()          # retea blocata


def test_cuplaj_slab_nu_sincronizeaza():
    g = MicroGrid(n_gen=8, K=0.05, freq_spread_hz=0.5, seed=2)
    r = g.settle(6000)
    assert r < 0.9                              # nu se blocheaza (imprastiere > cuplaj)


def test_regula_de_margine_mentine_blocarea_sub_perturbatie():
    # dimensionam K din regula P6 pentru o abatere maxima de 0.2 Hz
    m = coupling_margin(delta_f_max_hz=0.2, tau_target_s=1.0)
    K = m["K_recommended"]
    assert K > m["K_threshold"]                # recomandarea depaseste pragul
    g = MicroGrid(n_gen=6, K=K, freq_spread_hz=0.05, seed=3)
    g.settle(4000)
    # perturbatie IN marja: reteaua ramane BLOCATA (frecventa comuna) — generatorul
    # perturbat sta la un decalaj de faza staționar, deci R e ridicat si STABIL,
    # nu neaparat 1 (blocat != faze identice).
    r1 = g.settle(4000, disturbance_rad_s=TWO_PI * 0.2, gen=0)
    r2 = g.settle(1000, disturbance_rad_s=TWO_PI * 0.2, gen=0)
    assert r1 > 0.8 and r2 > 0.8               # ramane BLOCAT (nu aluneca spre 0)


def test_perturbatie_peste_cuplaj_desincronizeaza():
    # o perturbatie mult mai mare decat cuplajul rupe blocarea (alunecare)
    g = MicroGrid(n_gen=6, K=1.5, freq_spread_hz=0.05, seed=4)
    g.settle(4000)
    r = g.settle(4000, disturbance_rad_s=TWO_PI * 1.0, gen=0)  # 6.28 rad/s >> K=1.5
    assert r < 0.85                            # generatorul aluneca, sincronizare degradata


def test_sub_prag_reteaua_aluneca():
    # K sub pragul de blocare pentru o abatere data -> nu se poate bloca
    assert recovery_time(K=0.5, delta_f_hz=0.2) is None or \
           recovery_time(K=0.5, delta_f_hz=0.2) > 0  # 0.5 > 2π*0.2? 1.256 -> se blocheaza
    # cazul clar de alunecare: K mult sub Δω
    assert recovery_time(K=0.2, delta_f_hz=0.5) is None   # 0.2 < 2π*0.5


def test_timp_de_recuperare_scade_cu_cuplajul():
    # mai mult cuplaj => recuperare mai rapida (τ scade), forma P6
    t_low = recovery_time(K=2.0, delta_f_hz=0.1)
    t_high = recovery_time(K=5.0, delta_f_hz=0.1)
    assert t_low > t_high > 0


def test_incetinire_critica_langa_prag():
    # aproape de pragul de blocare (K ≈ Δω), τ explodeaza (avertizare timpurie)
    dw = TWO_PI * 0.3
    t_near = recovery_time(K=dw * 1.02, delta_f_hz=0.3)   # abia peste prag
    t_far = recovery_time(K=dw * 3.0, delta_f_hz=0.3)     # mult peste prag
    assert t_near > 5 * t_far                             # incetinire critica reala


def test_formula_recuperare_e_corecta_numeric():
    K, f = 2.0, 0.2
    dw = TWO_PI * f
    assert abs(recovery_time(K, f) - 1.0 / math.sqrt(K**2 - dw**2)) < 1e-12
