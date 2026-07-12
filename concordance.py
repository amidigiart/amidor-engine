# -*- coding: utf-8 -*-
"""
Concordanta intre doua raspunsuri independente — nucleul anti-confabulatie.

ONESTITATE (v0, declarata, nu ascunsa):
- Concordanta lexicala NU e adevar. Doua modele pot gresi identic (antrenate
  pe aceleasi date) — concordanta reduce expunerea la confabulatie, nu o
  elimina. Formularea corecta de produs: "refuza sa afirme ce nu poate
  coroborata", nu "nu halucineaza".
- Similaritatea e trigram-cosinus + verificare dura de FAPTE NUMERICE.
  Paraphraza bogata poate scora jos -> sistemul devine prudent degeaba.
  Directia de esec e cea SIGURA: fals-dezacordul duce la intrebare onesta,
  nu la afirmatie falsa. Fals-acordul (periculos) e atenuat de regula
  numerelor: cifre contradictorii = dezacord automat, oricat de asemanator
  suna textul. (Pentru doze, date, sume — exact ce conteaza la varstnici.)
"""
from __future__ import annotations

import math
import re
import unicodedata
from dataclasses import dataclass, field

_NUM_RE = re.compile(r"\d+(?:[.,]\d+)?")


def _normalize(text: str) -> str:
    t = unicodedata.normalize("NFKD", text.lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", t).strip()


def _trigrams(text: str) -> dict[str, int]:
    t = _normalize(text)
    out: dict[str, int] = {}
    for i in range(len(t) - 2):
        g = t[i:i + 3]
        out[g] = out.get(g, 0) + 1
    return out


def trigram_cosine(a: str, b: str) -> float:
    ta, tb = _trigrams(a), _trigrams(b)
    if not ta or not tb:
        return 0.0
    common = set(ta) & set(tb)
    dot = sum(ta[g] * tb[g] for g in common)
    na = math.sqrt(sum(v * v for v in ta.values()))
    nb = math.sqrt(sum(v * v for v in tb.values()))
    return dot / (na * nb)


def numbers_in(text: str) -> set[str]:
    return {n.replace(",", ".") for n in _NUM_RE.findall(text)}


@dataclass
class Concordance:
    score: float                 # 0..1
    numeric_conflict: bool
    numbers_a: set = field(default_factory=set)
    numbers_b: set = field(default_factory=set)
    agree: bool = False
    reason: str = ""


def check_concordance(a: str, b: str, threshold: float = 0.45) -> Concordance:
    """Acord = similaritate lexicala peste prag SI zero conflict numeric.

    Conflict numeric = FIECARE raspuns are cel putin un numar propriu pe care
    celalalt NU il contine. Asta prinde "1488 vs 1386" chiar cand impartasesc
    un an incidental (1957) - bug gasit live la primul test cu Ollama, unde un
    numar comun mascase doua populatii fabricate diferite. Nu mai folosim
    "niciun numar comun" (prea slab): un singur numar partajat ascundea
    conflictul. Adaugarea unui detaliu de o singura parte ("2 pastile" vs
    "2 pastile la 8 ore") NU e conflict - doar un rand are numar propriu."""
    score = trigram_cosine(a, b)
    na, nb = numbers_in(a), numbers_in(b)
    a_only, b_only = na - nb, nb - na
    numeric_conflict = bool(a_only) and bool(b_only)

    if numeric_conflict:
        return Concordance(score, True, na, nb, agree=False,
                           reason="cifre contradictorii intre modele")
    if score >= threshold:
        return Concordance(score, False, na, nb, agree=True,
                           reason=f"similaritate {score:.2f} >= prag {threshold}")
    return Concordance(score, False, na, nb, agree=False,
                       reason=f"similaritate {score:.2f} < prag {threshold}")
