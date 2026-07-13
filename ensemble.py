# -*- coding: utf-8 -*-
"""
Weighted Ensemble Agreement Coherence (WEAC) — o generalizare a verificarii
duale (2 modele) la N modele cu ponderi de incredere.

FORMULA (aplicabila acum, la orice ansamblu de LLM-uri):

    Fie a_1..a_M raspunsuri independente, w_k >= 0 ponderea de incredere a
    modelului k, si s(a_i,a_j) in [0,1] o similaritate semantica intre raspunsuri.

        C  =  ( Σ_{i<j} w_i w_j s_ij )  /  ( Σ_{i<j} w_i w_j )        (coerenta ansamblului)

    Raspunsul livrat = "medoidul ponderat" (cel mai de-acord raspuns):

        a* = argmax_k  Σ_{j≠k} w_j s_kj

    Decizie: livreaza a* DACA C >= τ SI nu exista conflict numeric dur;
    altfel abtine-te ("nu sunt sigur").

PROPRIETATI (verificate in test_ensemble.py):
- C ∈ [0,1] mereu (medie ponderata de valori in [0,1]).
- M=2  =>  C = s_12  (se reduce EXACT la scorul de concordanta existent).
- Toate identice => C=1;  toate diferite => C=0.
- Monotonie: un model care e de acord ridica C; unul care nu, scade C,
  proportional cu ponderea lui.

LEGATURA cu Kuramoto (linia REAI): daca fiecarui raspuns i se atribuie o faza
φ_k si s_kl = (1+cos(φ_k−φ_l))/2, atunci C e media ponderata a coerentei de
faza intre perechi — ruda directa a order-parameter-ului R = |Σ w_k e^{iφ_k}|/Σw_k.
E aceeasi familie matematica (coerenta corectata din SECTION-11-CORRIGENDUM),
aplicata la consensul intre modele. NU e o formula noua ca matematica; noutatea
e APLICATIA: scor de incredere + abtinere calibrata pentru ansambluri de LLM,
cu ponderi de fiabilitate.

ONESTITATE: C masoara ACORDUL, nu adevarul (modele antrenate similar pot gresi
identic). Reduce expunerea la confabulatie; nu o elimina. Pragul τ e un parametru
de design ce trebuie calibrat pe date reale (ca β_min), nu o constanta universala.

LIMITA GASITA LIVE (nu ascunsa): cand raspunsurile impart un SABLON ("Capitala
Frantei este ___"), similaritatea pe trigrame e dominata de sablonul comun, iar
diferenta de continut (Paris vs Lyon) e sub-ponderata. In acel caz medoidul poate
alege un raspuns central-textual-dar-gresit. Concluzii:
  (1) `sim` e injectabila: in productie folositi embeddings semantice, nu trigrame.
  (2) Apararea in miza mare NU depinde de calitatea `sim`: regula numerica dura
      (doze, sume) prinde conflictul indiferent de sablon — de aceea e separata.
  (3) C ramane un semnal corect de "acord partial" (in exemplul de mai sus C≈0.56,
      moderat) — cu τ mai mare, ansamblul s-ar abtine. Slabiciunea e in SELECTIA
      medoidului prin trigrame, nu in scorul C.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from concordance import trigram_cosine, numbers_in


def weighted_agreement_coherence(answers: list[str],
                                 weights: list[float] | None = None) -> float:
    """C ∈ [0,1] — coerenta ponderata a ansamblului (media ponderata a
    similaritatilor pe perechi)."""
    M = len(answers)
    if M == 0:
        return 0.0
    if M == 1:
        return 1.0
    w = weights or [1.0] * M
    num = den = 0.0
    for i in range(M):
        for j in range(i + 1, M):
            wij = w[i] * w[j]
            num += wij * trigram_cosine(answers[i], answers[j])
            den += wij
    return num / den if den > 0 else 0.0


def weighted_medoid(answers: list[str], weights: list[float] | None = None) -> int:
    """Indexul raspunsului cel mai de-acord cu ceilalti (medoid ponderat).

    Scorul candidatului k include PROPRIA lui pondere w_k, nu doar ponderile
    celorlalti: altfel un model cu pondere mica NU e demotat din pozitia de
    medoid (bug gasit live cu cazul Paris/Lyon). Cu w_k in fata, un outlier
    slab-ponderat e corect impins in jos."""
    M = len(answers)
    w = weights or [1.0] * M
    best_i, best_score = 0, -1.0
    for k in range(M):
        score = w[k] * sum(w[j] * trigram_cosine(answers[k], answers[j])
                           for j in range(M) if j != k)
        if score > best_score:
            best_i, best_score = k, score
    return best_i


def numeric_conflict_in(answers: list[str], weights: list[float] | None = None,
                        weight_floor: float = 0.0) -> bool:
    """Conflict numeric dur in ansamblu: exista doua raspunsuri (cu pondere peste
    prag) astfel incat fiecare are un numar propriu pe care celalalt nu-l are.
    Aceeasi regula stricta ca in motorul dual, extinsa la N."""
    w = weights or [1.0] * len(answers)
    nums = [numbers_in(a) for a in answers]
    idx = [i for i in range(len(answers)) if w[i] > weight_floor]
    for a in range(len(idx)):
        for b in range(a + 1, len(idx)):
            i, j = idx[a], idx[b]
            if (nums[i] - nums[j]) and (nums[j] - nums[i]):
                return True
    return False


@dataclass
class EnsembleVerdict:
    decision: str                 # "assert" | "abstain_low_coherence" | "abstain_numeric"
    coherence: float
    answer: str | None            # medoidul ponderat, daca assert
    medoid_index: int | None
    weights: list = field(default_factory=list)


def evaluate_ensemble(answers: list[str], weights: list[float] | None = None,
                      tau: float = 0.45) -> EnsembleVerdict:
    """Decizia ansamblului. Livreaza medoidul ponderat doar daca ansamblul e
    coerent (C >= τ) si nu are conflict numeric dur; altfel se abtine onest."""
    w = weights or [1.0] * len(answers)
    C = weighted_agreement_coherence(answers, w)
    if numeric_conflict_in(answers, w):
        return EnsembleVerdict("abstain_numeric", round(C, 4), None, None, w)
    if C >= tau:
        mi = weighted_medoid(answers, w)
        return EnsembleVerdict("assert", round(C, 4), answers[mi], mi, w)
    return EnsembleVerdict("abstain_low_coherence", round(C, 4), None, None, w)
