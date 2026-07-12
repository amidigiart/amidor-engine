# -*- coding: utf-8 -*-
"""Teste pentru Scam-Shield v0 — diferentiatorul de piata al AmiDor.
Include fals-pozitive care NU trebuie sa alarmeze (conversatie normala)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scam_shield import detect_scam, scam_response, ScamRisk


def test_conversatie_normala_nu_alarmeaza():
    for m in ["Ce vreme frumoasă azi!", "Mă doare puțin genunchiul.",
              "Vreau să-mi povestești ceva vesel.", "Cât e ceasul?"]:
        assert detect_scam(m).risk == ScamRisk.NONE


def test_cerere_cod_banca_este_LIKELY():
    s = detect_scam("Sunt de la bancă, spuneți-mi codul din SMS ca să vă deblocez contul.")
    assert s.risk == ScamRisk.LIKELY
    resp = scam_response(s)
    assert resp["action"] == "interrupt_and_warn" and not resp["continue_flow"]
    assert "cod" in resp["message"].lower() and resp["flag_family"]


def test_nepot_la_spital_trimite_bani():
    s = detect_scam("Sunt nepotul tău, am avut un accident și am nevoie urgent de bani, trimite acum!")
    assert s.risk == ScamRisk.LIKELY


def test_urgenta_plus_secret_doua_semnale_slabe_devin_LIKELY():
    s = detect_scam("Trebuie chiar acum, imediat, dar nu spune nimănui, să rămână între noi.")
    assert s.risk == ScamRisk.LIKELY   # urgenta + secret = tiparul clasic


def test_un_singur_semnal_slab_este_POSSIBLE_fara_intrerupere():
    s = detect_scam("Te rog rezolvă asta urgent.")
    assert s.risk == ScamRisk.POSSIBLE
    resp = scam_response(s)
    assert resp["continue_flow"] and resp["message"] is None and resp["flag_family"]


def test_card_cadou_si_transfer():
    assert detect_scam("Cumpără carduri cadou și trimite-mi codurile.").risk == ScamRisk.LIKELY
    assert detect_scam("Transferă suma urgent prin Revolut.").risk == ScamRisk.LIKELY


def test_engleza_acoperita():
    assert detect_scam("I am from your bank, your account is blocked, give me the verification code").risk == ScamRisk.LIKELY


def test_semnal_none_nu_produce_raspuns():
    assert scam_response(detect_scam("Bună dimineața!")) is None
