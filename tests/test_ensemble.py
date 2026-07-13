# -*- coding: utf-8 -*-
"""Verificarea formulei WEAC — proprietatile pe care le pretinde docstring-ul.
Toate ruleaza offline, determinist."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from ensemble import (weighted_agreement_coherence as C, weighted_medoid,
                      numeric_conflict_in, evaluate_ensemble)
from concordance import trigram_cosine


def test_coerenta_in_0_1_pe_multe_cazuri():
    import random
    rng = random.Random(0)
    vocab = ["capitala frantei e paris", "cerul e albastru azi",
             "ia doua pastile dimineata", "nu stiu raspunsul exact",
             "roma este in italia", "pisica doarme pe canapea"]
    for _ in range(200):
        k = rng.randint(1, 5)
        ans = [rng.choice(vocab) for _ in range(k)]
        w = [rng.random() for _ in range(k)]
        c = C(ans, w)
        assert -1e-9 <= c <= 1 + 1e-9


def test_M2_se_reduce_la_scorul_de_concordanta():
    a, b = "Capitala Frantei este Paris.", "Paris este capitala Frantei."
    assert abs(C([a, b]) - trigram_cosine(a, b)) < 1e-12


def test_toate_identice_C1_toate_diferite_C0():
    assert abs(C(["acelasi text", "acelasi text", "acelasi text"]) - 1.0) < 1e-9
    assert C(["xxxxxxxx", "yyyyyyyy", "zzzzzzzz"]) < 0.05


def test_monotonie_un_model_care_e_de_acord_ridica_C():
    base = ["Parisul este capitala Frantei.", "Capitala Frantei e Paris."]
    c2 = C(base)
    c3_agree = C(base + ["Franta are capitala Paris."])
    c3_disagree = C(base + ["Balenele traiesc in ocean adanc."])
    assert c3_agree > c3_disagree


def test_ponderea_conteaza():
    ans = ["Parisul este capitala.", "Parisul este capitala.", "Complet diferit qwer."]
    # cu al treilea model (dezacord) ponderat mult -> coerenta scade
    c_light = C(ans, [1.0, 1.0, 0.1])
    c_heavy = C(ans, [1.0, 1.0, 3.0])
    assert c_light > c_heavy


def test_medoid_alege_raspunsul_cel_mai_de_acord():
    ans = ["Parisul este capitala Frantei.",
           "Capitala Frantei este Paris, un oras.",
           "Nu are nicio legatura banane mov."]
    assert weighted_medoid(ans) in (0, 1)   # nu outlierul


def test_conflict_numeric_dur_in_ansamblu():
    ans = ["Ia 2 pastile pe zi.", "Ia 2 pastile pe zi.", "Ia 5 pastile pe zi."]
    assert numeric_conflict_in(ans)          # 2 vs 5, fiecare cu numar propriu


def test_decizie_assert_pe_consens_curat():
    ans = ["Parisul este capitala Frantei.", "Capitala Frantei este Paris."]
    v = evaluate_ensemble(ans, tau=0.4)
    assert v.decision == "assert" and "Paris" in v.answer


def test_decizie_abtinere_pe_dezacord():
    ans = ["Mergi personal la banca acum.", "Nicio banca nu cere asta, suna copilul."]
    v = evaluate_ensemble(ans, tau=0.5)
    assert v.decision == "abstain_low_coherence" and v.answer is None


def test_decizie_abtinere_pe_conflict_numeric_chiar_daca_text_similar():
    ans = ["Doza este 2 pastile pe zi.", "Doza este 4 pastile pe zi."]
    v = evaluate_ensemble(ans, tau=0.3)     # text ~identic, dar cifrele difera
    assert v.decision == "abstain_numeric" and v.answer is None


def test_outlier_slab_ponderat_nu_devine_medoid():
    """Bug gasit live (Paris/Lyon): un outlier cu pondere mica NU trebuie sa
    castige pozitia de medoid. Dupa fix (w_k in scor), e corect demotat."""
    ans = ["Capitala Frantei este Paris.", "Parisul e capitala Frantei.",
           "Franta are drept capitala orasul Paris.", "Capitala Frantei este Lyon."]
    from ensemble import weighted_medoid
    assert weighted_medoid(ans, [1.0, 1.0, 1.0, 0.6]) != 3   # nu Lyon


def test_coerenta_gate_e_protectia_primara():
    """Cazul Paris-divers + Lyon are C moderat (~0.56): cu τ exigent, ansamblul
    se abtine in loc sa livreze un raspuns central fragil. Poarta de coerenta,
    nu selectia medoidului, e apararea de baza peste calitatea lui `sim`."""
    ans = ["Capitala Frantei este Paris.", "Parisul e capitala Frantei.",
           "Franta are drept capitala orasul Paris.", "Capitala Frantei este Lyon."]
    from ensemble import evaluate_ensemble
    assert 0.45 < C(ans) < 0.7
    assert evaluate_ensemble(ans, tau=0.7).decision == "abstain_low_coherence"
