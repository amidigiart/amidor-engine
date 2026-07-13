# -*- coding: utf-8 -*-
"""EnsembleEngine (N modele) — aceleasi garantii ca motorul dual, extinse la M>=3.
Offline, cu adaptere deterministe."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from adapters import CallableAdapter, AdapterError
from ensemble_engine import EnsembleEngine


def _eng(fns, weights=None, threshold=0.45, locale="ro"):
    adapters = [CallableAdapter(fn, f"m{i}") for i, fn in enumerate(fns)]
    return EnsembleEngine(adapters, system_prompt="x", weights=weights,
                          threshold=threshold, locale=locale)


def test_necesita_minim_doua_modele():
    import pytest
    with pytest.raises(ValueError):
        EnsembleEngine([CallableAdapter(lambda s, u: "x")], system_prompt="x")


def test_trei_modele_de_acord_afirma_medoidul():
    e = _eng([lambda s, u: "Capitala Frantei este Paris.",
              lambda s, u: "Parisul e capitala Frantei.",
              lambda s, u: "Franta are capitala Paris."])
    r = e.ask("Care e capitala Frantei?")
    assert r.decision == "affirm" and "Paris" in r.reply and r.n_models == 3


def test_outlier_intr_un_ansamblu_de_patru():
    fns = [lambda s, u: "Parisul este capitala Frantei.",
           lambda s, u: "Capitala Frantei e Paris.",
           lambda s, u: "Franta are drept capitala Paris.",
           lambda s, u: "Balenele inoata in ocean."]
    # cu formulari diverse + un outlier dur, coerenta e MODERATA (~0.29): la prag
    # exigent ansamblul se abtine onest (sigur), NU livreaza fortat.
    r_strict = _eng(fns, threshold=0.4).ask("Capitala Frantei?")
    assert r_strict.decision == "disagree"
    # la prag permisiv, livreaza medoidul — care e un raspuns Paris, nu outlierul
    r_loose = _eng(fns, threshold=0.25).ask("Capitala Frantei?")
    assert r_loose.decision == "affirm" and "Paris" in r_loose.reply


def test_dezacord_larg_duce_la_abtinere_onesta():
    e = _eng([lambda s, u: "Mergi la banca personal.",
              lambda s, u: "Suna-ti copilul mai intai.",
              lambda s, u: "Ignora complet mesajul primit."], threshold=0.5)
    r = e.ask("Ce sa fac?")
    assert r.decision == "disagree" and "sigur" in r.reply


def test_conflict_numeric_in_ansamblu_nu_afirma_cifre():
    e = _eng([lambda s, u: "Doza este 2 pastile pe zi.",
              lambda s, u: "Doza este 2 pastile pe zi.",
              lambda s, u: "Doza este 5 pastile pe zi."], threshold=0.3)
    r = e.ask("Ce doza?")
    assert r.decision == "disagree"
    assert "2" not in r.reply and "5" not in r.reply     # nicio cifra afirmata


def test_un_singur_model_ramas_degradeaza_cu_eticheta():
    def broken(s, u): raise AdapterError("cazut")
    e = _eng([broken, broken, lambda s, u: "Raspunsul meu."])
    r = e.ask("Salut?")
    assert r.decision == "degraded" and "o singură sursă" in r.reply


def test_toate_cazute_refuza_cinstit():
    def broken(s, u): raise AdapterError("cazut")
    r = _eng([broken, broken, broken]).ask("Salut?")
    assert r.decision == "degraded" and r.n_models == 0


def test_ponderea_de_incredere_conteaza_in_ansamblu():
    # doua modele slabe de acord pe X, unul de incredere pe Y -> spre Y sau abtinere
    fns = [lambda s, u: "Raspuns comun gresit qwerty.",
           lambda s, u: "Raspuns comun gresit qwerty.",
           lambda s, u: "Total diferit, alt continut zxcvb."]
    r_light = _eng(fns, weights=[1, 1, 0.2], threshold=0.4).ask("?")
    r_heavy = _eng(fns, weights=[1, 1, 5.0], threshold=0.4).ask("?")
    # cu al treilea puternic ponderat, coerenta ansamblului scade
    assert r_heavy.coherence <= r_light.coherence


def test_engleza_se_propaga_in_abtinere():
    e = _eng([lambda s, u: "Take 2 pills.", lambda s, u: "Take 5 pills.",
              lambda s, u: "Take 9 pills."], threshold=0.3, locale="en")
    r = e.ask("How many?")
    assert r.decision == "disagree" and "honest" in r.reply
