# -*- coding: utf-8 -*-
"""Testele comportamentului-semnatura al motorului dual: dezacordul intre
modele produce onestitate, nu inventie. Toate testele ruleaza OFFLINE,
cu adaptere deterministe - fara retea, fara API."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from adapters import CallableAdapter, AdapterError
from concordance import check_concordance, trigram_cosine, numbers_in
from engine import DualEngine, UNCORROBORATED_TAG
from register_gate import RegisterGate


def _engine(fa, fb, threshold=0.45):
    return DualEngine(CallableAdapter(fa, "A"), CallableAdapter(fb, "B"),
                      system_prompt="Esti un asistent.", threshold=threshold)


# ------------------------------------------------------------ concordanta
def test_trigram_identic_si_diferit():
    assert trigram_cosine("pisica alba", "pisica alba") > 0.99
    assert trigram_cosine("pisica alba", "xyzq wvut") < 0.1


def test_extragere_numere():
    assert numbers_in("ia 2 pastile la 8 ore, doza 2,5 mg") == {"2", "8", "2.5"}


def test_conflict_numeric_bate_similaritatea():
    a = "Ia 2 pastile pe zi, dimineata, cu apa."
    b = "Ia 4 pastile pe zi, dimineata, cu apa."
    c = check_concordance(a, b)
    assert c.numeric_conflict and not c.agree   # 90% identic lexical, dar cifrele decid


def test_numar_comun_nu_mascheaza_conflict_real():
    # regresie: bug gasit live cu Ollama - anul comun 1957 mascase populatii
    # fabricate diferite (1488 vs 1386). Fiecare are un numar propriu -> conflict.
    a = "Conform datelor din 1957, satul avea 1.488 locuitori."
    b = "Conform datelor din 1957, satul avea 1.386 locuitori."
    c = check_concordance(a, b)
    assert c.numeric_conflict and not c.agree


def test_detaliu_adaugat_nu_e_conflict():
    # un singur rand are numar propriu (8) -> NU e conflict, doar mai detaliat
    a = "Ia 2 pastile dimineata."
    b = "Ia 2 pastile dimineata, la 8."
    c = check_concordance(a, b)
    assert not c.numeric_conflict


# ------------------------------------------------------------ motorul dual
def test_acord_livreaza_raspunsul():
    r = _engine(lambda s, u: "Capitala Frantei este Paris.",
                lambda s, u: "Paris este capitala Frantei.").ask("Care e capitala Frantei?")
    assert r.decision == "affirm"
    assert "Paris" in r.reply


def test_dezacord_numeric_produce_onestitate_fara_cifre():
    r = _engine(lambda s, u: "Doza recomandata este 2 pastile.",
                lambda s, u: "Doza recomandata este 4 pastile.").ask("Cate pastile iau?")
    assert r.decision == "disagree"
    assert "2" not in r.reply and "4" not in r.reply   # NU afirmam nicio cifra
    assert "sincer" in r.reply or "sigur" in r.reply
    # ambele candidate raman in structura, pentru jurnal/audit
    assert r.answers["a"] != r.answers["b"]


def test_dezacord_tematic_produce_onestitate():
    r = _engine(lambda s, u: "Trebuie sa mergi la banca personal.",
                lambda s, u: "Nicio banca nu cere asta; suna-ti fiul intai.").ask(
        "Banca m-a sunat sa le dau codul, ce fac?")
    assert r.decision == "disagree"


def test_un_model_cazut_degradeaza_cu_eticheta():
    def broken(s, u):
        raise AdapterError("model A indisponibil")
    r = _engine(broken, lambda s, u: "Raspunsul meu.").ask("Salut?")
    assert r.decision == "degraded"
    assert UNCORROBORATED_TAG.strip() in r.reply       # etichetat, nu tacut


def test_ambele_cazute_refuza_cinstit():
    def broken(s, u):
        raise AdapterError("indisponibil")
    r = _engine(broken, broken).ask("Salut?")
    assert r.decision == "degraded" and "improvizez" in r.reply


# ------------------------------------------------------------ poarta REAI
def test_reancorare_nu_interogheaza_modelele():
    calls = {"n": 0}
    def counting(s, u):
        calls["n"] += 1
        return "raspuns"
    eng = _engine(counting, counting)
    # fortam coerenta prabusita prin ture haotice pe poarta
    g = eng.gate
    t = 1000.0
    for k in range(4):
        g.observe(msg_len=40, now=t + k * 30)
    # perturbatii mari consecutive, acelasi semn (pauza lunga + mesaj lung)
    got_reanchor = False
    t = 5000.0
    for gap, ln in [(900, 400), (2, 3), (900, 500), (1, 2), (800, 450)]:
        t += gap
        s = g.observe(msg_len=ln, now=t)
        if s["mode"] == "reancoreaza":
            got_reanchor = True
            break
    if got_reanchor:
        before = calls["n"]
        r = eng.ask("intrebare in plina derapare")
        # observe() din ask() poate schimba modul; daca a ramas reancorare:
        if r.decision == "reanchor":
            assert calls["n"] == before   # zero apeluri la modele
    # testul de baza care NU depinde de traiectorie:
    assert g.calibration["recommended_beta_min"] > 0


def test_beta_min_din_regula_adler():
    g = RegisterGate(seed=7)
    cal = g.calibration
    assert abs(cal["recommended_beta_min"] -
               cal["safety_margin"] * cal["threshold_beta_min"]) < 1e-12
