# -*- coding: utf-8 -*-
"""
Arbitration Support — un METRU DE ACORD ȘI INCERTITUDINE pentru arbitraj
asistat de AI. NU un judecator. (VAULT: AGPL-3.0 / comercial.)

CE FACE, EXACT:
  Primeste N analize AI INDEPENDENTE ale aceleiasi intrebari/clauze/dispute,
  si raporteaza:
    - cat de mult CONCORDA (coerenta WEAC),
    - UNDE nu concorda (analizele divergente -> escaladare la om),
    - se ABTINE explicit cand acordul e slab sau exista conflict numeric.

CE NU FACE, NICIODATA (limita gravata in cod, nu doar in text):
  - NU stabileste cine are dreptate. Coerenta = ACORD intre modele, NU adevar.
    N modele pot fi de acord si gresi impreuna (bias comun, date comune). Vezi
    testul-semnatura: acord unanim GRESIT -> raportat ca RISC, nu ca verdict.
  - NU emite un verdict, un castigator, sau "adevar juridic".
  - NU decide autonom. `escalate_to_human` e True in regim high-stakes chiar si
    la acord perfect — omul decide, instrumentul doar reduce/semnaleaza sarcina.

De aceea outputul nu contine niciun camp "correct", "winner", "truth" sau
"verdict". Contine doar: nivel de acord, puncte contestate, si un avertisment
permanent ca acordul nu e corectitudine.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ensemble import (weighted_agreement_coherence, weighted_medoid,
                      numeric_conflict_in)
from concordance import trigram_cosine

RISK_NOTE = (
    "AVERTISMENT: acordul între modele NU înseamnă că au dreptate. Modele "
    "antrenate similar pot greși împreună. Acest instrument măsoară acordul și "
    "incertitudinea ca SPRIJIN pentru un arbitru uman — nu stabilește adevărul, "
    "nu emite un verdict și nu desemnează un câștigător. Decizia aparține omului."
)


@dataclass
class ArbitrationAssessment:
    coherence: float                       # WEAC C, ∈ [0,1] — ACORD, nu adevar
    status: str                            # "converged" | "contested" | "insufficient"
    agreed_interpretation: str | None      # medoidul, ETICHETAT ca interpretare, NU verdict
    contested_indices: list = field(default_factory=list)  # analize divergente -> revizuire umana
    numeric_conflict: bool = False
    escalate_to_human: bool = True         # in high-stakes: MEREU True
    review_burden: str = "high"            # "low" | "medium" | "high" — cat de mult trebuie sa verifice omul
    risk_note: str = RISK_NOTE             # avertisment permanent


def assess_arbitration(analyses: list[str], weights: list[float] | None = None,
                       tau: float = 0.6, contest_floor: float = 0.4,
                       high_stakes: bool = True) -> ArbitrationAssessment:
    """Evalueaza un set de analize AI independente. Prag τ mai exigent decat
    companionul (miza e mai mare). NU returneaza niciun verdict."""
    M = len(analyses)
    if M < 2:
        return ArbitrationAssessment(
            coherence=1.0 if M == 1 else 0.0, status="insufficient",
            agreed_interpretation=None, escalate_to_human=True,
            review_burden="high")

    w = weights or [1.0] * M
    C = weighted_agreement_coherence(analyses, w)
    numeric = numeric_conflict_in(analyses, w)

    # analize contestate = cele cu similaritate medie mica fata de restul
    contested = []
    for i in range(M):
        others = [trigram_cosine(analyses[i], analyses[j]) for j in range(M) if j != i]
        if others and (sum(others) / len(others)) < contest_floor:
            contested.append(i)

    if numeric or C < tau:
        return ArbitrationAssessment(
            coherence=round(C, 4),
            status="contested",
            agreed_interpretation=None,        # NU livram o interpretare cand nu e acord
            contested_indices=contested or list(range(M)),
            numeric_conflict=numeric,
            escalate_to_human=True,
            review_burden="high")

    # acord peste prag, fara conflict numeric: exista o interpretare majoritara
    mi = weighted_medoid(analyses, w)
    # in high-stakes escaladam MEREU; sarcina de revizuire scade doar cu acordul
    burden = "low" if (C >= 0.8 and not contested) else "medium"
    return ArbitrationAssessment(
        coherence=round(C, 4),
        status="converged",
        agreed_interpretation=analyses[mi],    # ETICHETAT ca interpretare majoritara
        contested_indices=contested,
        numeric_conflict=False,
        escalate_to_human=high_stakes,         # True in high-stakes chiar si la acord
        review_burden=burden)
