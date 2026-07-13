# -*- coding: utf-8 -*-
"""
EnsembleEngine — motorul cu N modele (M>=2), pe formula WEAC (ensemble.py).
Generalizeaza DualEngine: aceeasi poarta REAI (RegisterGate), aceleasi texte
i18n, aceeasi regula numerica dura — dar peste un ansamblu de M modele cu
ponderi de incredere, nu doar doua.

Flux: gate REAI -> (reancorare fara apeluri) -> interoghez toate modelele in
paralel -> arunc modelele cazute -> daca raman <2 utilizabile, mod degradat;
altfel WEAC decide: assert (medoid ponderat) / disagree (abtinere onesta) /
disagree numeric (fara cifre).
"""
from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field

from adapters import AdapterError
from register_gate import RegisterGate, ASK, REANCHOR
from ensemble import evaluate_ensemble
from i18n import bundle, DEFAULT as I18N_DEFAULT


@dataclass
class EnsembleResult:
    reply: str
    decision: str                 # "affirm" | "disagree" | "reanchor" | "degraded"
    mode: str
    coherence: float | None = None
    n_models: int = 0
    answers: dict = field(default_factory=dict)
    latency_s: float = 0.0
    engine_state: dict = field(default_factory=dict)


class EnsembleEngine:
    def __init__(self, adapters: list, system_prompt: str,
                 weights: list[float] | None = None, threshold: float = 0.45,
                 gate: RegisterGate | None = None, locale: str = I18N_DEFAULT):
        if len(adapters) < 2:
            raise ValueError("EnsembleEngine necesita cel putin 2 modele")
        self.adapters = adapters
        self.weights = weights or [1.0] * len(adapters)
        self.system_prompt = system_prompt
        self.threshold = threshold
        self.gate = gate or RegisterGate()
        self.tx = bundle(locale)

    def ask(self, user_msg: str) -> EnsembleResult:
        t0 = time.time()
        state = self.gate.observe(msg_len=len(user_msg))
        mode = state["mode"]

        if mode == REANCHOR:
            return EnsembleResult(self.tx["reanchor_reply"], "reanchor", mode,
                                  engine_state=state,
                                  latency_s=round(time.time() - t0, 2))

        directive = self.tx["ask_directive"] if mode == ASK else ""
        system = self.system_prompt + directive
        with ThreadPoolExecutor(max_workers=len(self.adapters)) as ex:
            futs = [ex.submit(a.complete, system, user_msg) for a in self.adapters]
            raw = [self._safe(f) for f in futs]

        answers_log = {f"m{i}": (r if not isinstance(r, Exception) else f"[cazut: {r}]")
                       for i, r in enumerate(raw)}
        usable = [(r, w) for r, w in zip(raw, self.weights)
                  if not isinstance(r, Exception)]

        # sub 2 modele utilizabile: nu se poate verifica incrucisat
        if len(usable) < 2:
            if len(usable) == 1:
                return EnsembleResult(usable[0][0] + self.tx["uncorroborated_tag"],
                                      "degraded", mode, n_models=1,
                                      answers=answers_log, engine_state=state,
                                      latency_s=round(time.time() - t0, 2))
            return EnsembleResult(self.tx["degraded_reply"], "degraded", mode,
                                  n_models=0, answers=answers_log,
                                  engine_state=state,
                                  latency_s=round(time.time() - t0, 2))

        ans = [u[0] for u in usable]
        w = [u[1] for u in usable]
        v = evaluate_ensemble(ans, w, tau=self.threshold)

        if v.decision == "assert":
            return EnsembleResult(v.answer, "affirm", mode, coherence=v.coherence,
                                  n_models=len(ans), answers=answers_log,
                                  engine_state=state,
                                  latency_s=round(time.time() - t0, 2))

        hint = self.tx["numeric_hint"] if v.decision == "abstain_numeric" else ""
        return EnsembleResult(self.tx["honest_disagreement"].format(hint=hint),
                              "disagree", mode, coherence=v.coherence,
                              n_models=len(ans), answers=answers_log,
                              engine_state=state,
                              latency_s=round(time.time() - t0, 2))

    @staticmethod
    def _safe(future):
        try:
            return future.result()
        except Exception as e:
            return e if isinstance(e, AdapterError) else AdapterError(str(e))
