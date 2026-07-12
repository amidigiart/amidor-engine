# -*- coding: utf-8 -*-
"""
AmiDor DualEngine — motorul dual anti-confabulatie.

Fluxul unei intrebari:
  1. RegisterGate (ecuatiile REAI) observa tura.
     REANCOREAZA -> nu interogam modelele; cerem re-ancorare (si economisim API).
  2. Ambele modele raspund INDEPENDENT (in paralel), fara sa se vada.
  3. check_concordance: acord lexical + zero conflict numeric.
  4. Acord      -> livram raspunsul (al modelului A), in registrul cerut.
     Dezacord   -> RASPUNS ONEST: nu afirmam; spunem ca sursele nu concorda
                   si punem o intrebare / recomandam verificare umana.
     Un model cazut -> mod degradat: raspunsul celuilalt + eticheta explicita
                   "necoroborat" (fail-open cu avertisment, nu fail-silent).

Ce NU pretinde motorul (v. concordance.py): concordanta nu e adevar.
Reducem expunerea la confabulatie si refuzam afirmatiile necoroborate.
"""
from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field

from adapters import AdapterError
from concordance import check_concordance
from register_gate import RegisterGate, AFFIRM, ASK, REANCHOR

HONEST_DISAGREEMENT = (
    "Nu pot să-ți dau un răspuns sigur aici — sursele mele interne nu spun "
    "același lucru, iar decât să ghicesc, prefer să fiu sincer. {hint}"
    "Putem reformula întrebarea, sau o verificăm împreună cu cineva de încredere."
)
NUMERIC_HINT = ("Diferența e la cifre — iar la cifre nu am voie să "
                "aproximez. ")
REANCHOR_REPLY = (
    "Hai să ne oprim o clipă și să ne asigurăm că suntem în pas: "
    "am înțeles bine ce mă întrebi? Spune-mi cu alte cuvinte, te rog."
)
UNCORROBORATED_TAG = ("\n\n(Notă: acest răspuns vine de la o singură sursă "
                      "și nu a putut fi verificat încrucișat acum.)")


@dataclass
class DualResult:
    reply: str
    decision: str            # "affirm" | "disagree" | "reanchor" | "degraded"
    mode: str                # registrul REAI al turei
    concordance: float | None = None
    reason: str = ""
    answers: dict = field(default_factory=dict)
    latency_s: float = 0.0
    engine_state: dict = field(default_factory=dict)


class DualEngine:
    def __init__(self, adapter_a, adapter_b, system_prompt: str,
                 threshold: float = 0.45, gate: RegisterGate | None = None):
        self.a, self.b = adapter_a, adapter_b
        self.system_prompt = system_prompt
        self.threshold = threshold
        self.gate = gate or RegisterGate()

    def ask(self, user_msg: str) -> DualResult:
        t0 = time.time()
        state = self.gate.observe(msg_len=len(user_msg))
        mode = state["mode"]

        if mode == REANCHOR:
            return DualResult(reply=REANCHOR_REPLY, decision="reanchor",
                              mode=mode, reason="coerenta prabusita - "
                              "nu interogam modelele inainte de re-ancorare",
                              latency_s=round(time.time() - t0, 2),
                              engine_state=state)

        system = self.system_prompt + state["directive"]
        with ThreadPoolExecutor(max_workers=2) as ex:
            fa = ex.submit(self.a.complete, system, user_msg)
            fb = ex.submit(self.b.complete, system, user_msg)
            ans_a = self._safe(fa)
            ans_b = self._safe(fb)

        answers = {"a": ans_a, "b": ans_b}

        if isinstance(ans_a, Exception) and isinstance(ans_b, Exception):
            return DualResult(
                reply=("Am o problemă tehnică chiar acum și nu vreau să "
                       "improvizez. Încearcă, te rog, puțin mai târziu."),
                decision="degraded", mode=mode,
                reason=f"ambele modele indisponibile: {ans_a}; {ans_b}",
                answers={}, latency_s=round(time.time() - t0, 2),
                engine_state=state)

        if isinstance(ans_a, Exception) or isinstance(ans_b, Exception):
            good = ans_b if isinstance(ans_a, Exception) else ans_a
            bad = ans_a if isinstance(ans_a, Exception) else ans_b
            return DualResult(
                reply=good + UNCORROBORATED_TAG,
                decision="degraded", mode=mode,
                reason=f"un model indisponibil: {bad}",
                answers={k: v for k, v in answers.items()
                         if not isinstance(v, Exception)},
                latency_s=round(time.time() - t0, 2), engine_state=state)

        conc = check_concordance(ans_a, ans_b, self.threshold)
        if conc.agree:
            return DualResult(reply=ans_a, decision="affirm", mode=mode,
                              concordance=round(conc.score, 3),
                              reason=conc.reason, answers=answers,
                              latency_s=round(time.time() - t0, 2),
                              engine_state=state)

        hint = NUMERIC_HINT if conc.numeric_conflict else ""
        return DualResult(reply=HONEST_DISAGREEMENT.format(hint=hint),
                          decision="disagree", mode=mode,
                          concordance=round(conc.score, 3),
                          reason=conc.reason, answers=answers,
                          latency_s=round(time.time() - t0, 2),
                          engine_state=state)

    @staticmethod
    def _safe(future):
        try:
            return future.result()
        except Exception as e:            # AdapterError sau orice runtime
            return e if isinstance(e, AdapterError) else AdapterError(str(e))
