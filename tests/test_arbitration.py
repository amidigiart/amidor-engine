# -*- coding: utf-8 -*-
"""Arbitration Support — testele care GARANTEAZA ca instrumentul nu se preface
judecator. Cel mai important: acordul unanim GRESIT nu e certificat ca adevar."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from arbitration import assess_arbitration, ArbitrationAssessment, RISK_NOTE
from dataclasses import fields


def test_outputul_NU_contine_niciun_camp_de_verdict():
    # gardă structurală: nicio noțiune de adevăr/câștigător/verdict în output
    names = {f.name for f in fields(ArbitrationAssessment)}
    for forbidden in ("correct", "winner", "truth", "verdict", "guilty", "right"):
        assert forbidden not in names, f"camp interzis: {forbidden}"


def test_SEMNATURA_acord_unanim_gresit_NU_e_certificat_ca_adevar():
    # 3 analize identice DAR gresite: instrumentul raporteaza ACORD, dar NU adevar
    wrong = "Clauza 7 permite rezilierea fără preaviz."   # sa presupunem ca e gresit
    a = assess_arbitration([wrong, wrong, wrong], tau=0.6)
    assert a.status == "converged"                    # da, concorda
    assert a.escalate_to_human is True                # dar OMUL decide, mereu
    assert "NU înseamnă că au dreptate" in a.risk_note
    # interpretarea e oferita ca "majoritara", nu ca adevar — si nu exista camp de verdict
    assert a.agreed_interpretation == wrong
    assert not hasattr(a, "verdict")


def test_divergenta_flagheaza_puncte_contestate_si_nu_livreaza_interpretare():
    analyses = [
        "Partea A are dreptate: livrarea a fost la termen.",
        "Partea B are dreptate: livrarea a întârziat trei zile.",
        "Contractul e ambiguu; depinde de fusul orar al livrării."]
    a = assess_arbitration(analyses, tau=0.6)
    assert a.status == "contested"
    assert a.agreed_interpretation is None            # NU alegem o tabara
    assert a.escalate_to_human is True
    assert a.contested_indices                        # exista puncte de escaladat


def test_conflict_numeric_forteaza_omul_chiar_la_text_similar():
    analyses = ["Penalitatea este 2% din valoare.",
                "Penalitatea este 2% din valoare.",
                "Penalitatea este 9% din valoare."]
    a = assess_arbitration(analyses, tau=0.3)
    assert a.numeric_conflict and a.status == "contested"
    assert a.agreed_interpretation is None            # nicio cifra afirmata ca adevar


def test_acord_bun_reduce_sarcina_dar_tot_escaladeaza():
    analyses = ["Clauza impune notificare scrisă cu 30 de zile înainte.",
                "Este necesară o notificare scrisă, cu 30 de zile înainte.",
                "Notificarea trebuie făcută în scris, 30 de zile în avans."]
    a = assess_arbitration(analyses, tau=0.5)
    assert a.status == "converged"
    assert a.review_burden in ("low", "medium")
    assert a.escalate_to_human is True                # high-stakes: mereu la om


def test_o_singura_analiza_e_insuficient():
    a = assess_arbitration(["O singură părere."])
    assert a.status == "insufficient" and a.escalate_to_human is True


def test_risk_note_e_mereu_prezent():
    for anals in (["x", "x"], ["a foarte diferit", "b cu totul altceva qwerty"]):
        assert assess_arbitration(anals).risk_note == RISK_NOTE
