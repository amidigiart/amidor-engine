# -*- coding: utf-8 -*-
"""i18n: completitudinea cataloagelor (o limba noua nu poate fi adaugata pe
jumatate) + motorul raspunde in limba ceruta."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from i18n import CATALOG, _KEYS, t, bundle, available
from adapters import CallableAdapter
from engine import DualEngine


def test_toate_limbile_au_toate_cheile():
    for loc, cat in CATALOG.items():
        lipsa = _KEYS - set(cat)
        extra = set(cat) - _KEYS
        assert not lipsa, f"{loc}: chei lipsa {lipsa}"
        assert not extra, f"{loc}: chei necunoscute {extra}"


def test_fallback_la_default():
    assert t("de", "greeting") == t("ro", "greeting")   # limba inexistenta -> RO


def test_format_cu_parametri():
    s = t("en", "honest_disagreement", hint="TEST-HINT ")
    assert "TEST-HINT" in s and "{hint}" not in s


def test_transparenta_ai_in_toate_limbile():
    # EU AI Act Art. 50: fiecare system prompt declara ca e program, nu om
    for loc in CATALOG:
        sp = CATALOG[loc]["system_prompt"].lower()
        assert "program" in sp
        # granita non-medicala prezenta peste tot
        assert "medic" in sp or "doctor" in sp


def test_motorul_dezacordul_vorbeste_engleza():
    eng = DualEngine(CallableAdapter(lambda s, u: "Take 2 pills.", "A"),
                     CallableAdapter(lambda s, u: "Take 4 pills.", "B"),
                     system_prompt="x", locale="en")
    r = eng.ask("How many pills?")
    assert r.decision == "disagree"
    assert "rather be honest" in r.reply          # textul EN, nu RO
    assert "sincer" not in r.reply


def test_motorul_implicit_vorbeste_romana():
    eng = DualEngine(CallableAdapter(lambda s, u: "Ia 2 pastile.", "A"),
                     CallableAdapter(lambda s, u: "Ia 4 pastile.", "B"),
                     system_prompt="x")
    r = eng.ask("Cate pastile?")
    assert r.decision == "disagree" and "sincer" in r.reply


def test_directiva_ask_este_in_limba_motorului():
    b_ro, b_en = bundle("ro"), bundle("en")
    assert "REGULĂ" in b_ro["ask_directive"] and "ACTIVE RULE" in b_en["ask_directive"]


def test_available_expune_codurile_de_voce():
    langs = {l["code"]: l for l in available()}
    assert langs["ro"]["speech"] == "ro-RO" and langs["en"]["speech"] == "en-GB"
