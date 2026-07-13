# amidor-engine

> **License:** dual **AGPL-3.0 / commercial**. Free to self-host if you open your whole stack; **closed/commercial use requires a commercial license** — see [COMMERCIAL.md](COMMERCIAL.md) · contact@kinderagi.com


**A dual-model anti-confabulation engine: two independent models must agree, and the REAI resonance equations decide when the system may assert vs. must ask. When sources disagree, it says so — it does not invent.**

Part of *amiecosystems* · built for [AmiDor](../amidor), a voice-first AI companion for the elderly · engine is domain-agnostic.

[![Tests](https://img.shields.io/badge/tests-12%2F12-brightgreen)]() [![License](https://img.shields.io/badge/license-AGPL--3.0%20%2F%20commercial-blue)](LICENSE)

## The idea in one paragraph

Single-model companions confabulate — they state fabricated facts fluently. That is unacceptable when the user is an 80-year-old asking about medication doses or a suspicious phone call. `amidor-engine` runs **two independent models** on every question and delivers an answer **only when they concur**; on disagreement it returns an honest "I'm not sure — let's check together" instead of a guess. A conversational-coherence gate (the [REAI engine](https://github.com/amidigiart/ukbe-core), analysed in [doi:10.5281/zenodo.21269201](https://doi.org/10.5281/zenodo.21269201)) decides the register — assert / ask / re-anchor — from the dynamics of the conversation, not a keyword rule.

**What it does NOT claim:** concordance is not truth. Two models trained on similar data can be wrong together. This engine *reduces exposure to confabulation and refuses to assert what it cannot corroborate* — the honest, sellable framing, not "it doesn't hallucinate."

## How a question flows

```
user ─▶ RegisterGate (REAI equations)
          │  re-anchor → don't even query the models; ask to re-sync
          ▼
       model A ║ model B      (independent, in parallel, OpenAI-compatible)
          ▼         ▼
       concordance check: lexical agreement + hard numeric-conflict rule
          │ agree      → deliver the answer
          │ disagree   → honest refusal + a question / "verify with someone"
          │ one down   → the other's answer, explicitly tagged "uncorroborated"
          ▼
       reply  (+ both candidates kept for the audit journal)
```

The **numeric-conflict rule** is deliberately strict: if each model has a number the other lacks (e.g. two different medication doses, or two fabricated populations), it is a conflict *even if the surrounding text is 90% identical* — so the engine never averages or picks a number when the sources differ. This rule earned its strictness the honest way: the first live run against Ollama confabulated a village population, and a shared incidental year masked the conflict. The bug, the fix, and a regression test are in the repo (`concordance.py`, `test_numar_comun_nu_mascheaza_conflict_real`).

## Universal by design

Any OpenAI-compatible endpoint plugs in via `OpenAICompatAdapter`: Ollama (local), Mistral, DeepSeek (open-weights self-hosted **or** API), Grok, vLLM, LM Studio. Pick the pair per deployment. **GDPR note:** for EU personal data, use EU-resident or self-hosted endpoints; non-EU APIs (DeepSeek China, Grok US) only with an explicit legal basis and consent — the operator's decision, never a silent default.

## Quickstart

```python
from adapters import OpenAICompatAdapter
from engine import DualEngine

A = OpenAICompatAdapter("http://localhost:11434/v1", "gemma3:4b", temperature=0.1, name="A")
B = OpenAICompatAdapter("https://api.mistral.ai/v1", "mistral-small-latest",
                        api_key="…", temperature=0.6, name="B")

eng = DualEngine(A, B, system_prompt="You are AmiDor, a calm assistant for older adults.")
r = eng.ask("How many pills do I take?")
print(r.decision, "→", r.reply)   # "affirm" | "disagree" | "reanchor" | "degraded"
```

```bash
pip install -r requirements.txt
pip install "ukbe-core @ git+https://github.com/amidigiart/ukbe-core@main"
pytest tests/          # 12 passed, fully offline (deterministic adapters)
```

## License — dual

- **AGPL-3.0** for open use: free to run, study, modify — provided your whole service is also AGPL (network-copyleft). See [LICENSE](LICENSE).
- **Commercial license** from Roșca IP for use in closed products, per instance/year. Contact: contact@kinderagi.com.

This is the open-core model (MongoDB/Grafana style): the code is public for trust and scrutiny; commercial use in proprietary products is licensed. The upstream [ukbe-core](https://github.com/amidigiart/ukbe-core) stays Apache-2.0.

© 2026 Mihai Roșca · amiecosystems

## N-model generalization (WEAC)

The dual (2-model) check generalizes to N models with reliability weights via the **[Weighted Ensemble Agreement Coherence](docs/ENSEMBLE-COHERENCE.md)** formula (`ensemble.py`): one calibratable coherence score in [0,1] that reduces exactly to the 2-model case, delivers the weighted-medoid answer, and abstains on low coherence or a hard numeric conflict. Built on the corrected coherence from the [REAI §11 corrigendum](https://github.com/amidigiart/ukbe-core/blob/main/docs/SECTION-11-CORRIGENDUM.md).

## Methodology & IP (in the vault)

These are the crown-jewel documents — **public for credibility, AGPL/commercial for reuse**:
- [REAI methodology note](docs/REAI-METHODOLOGY.md) — sober definition, anchored to the reproduced result, non-overclaiming.
- [Section 11 corrigendum](docs/SECTION-11-CORRIGENDUM.md) — verified self-correction, with [runnable proof](docs/verify_section11.py).
- [WEAC — ensemble coherence](docs/ENSEMBLE-COHERENCE.md) — the N-model formula.
- [COMMERCIAL.md](COMMERCIAL.md) — licensing terms.

The open door (free): the reproduced paper at [doi:10.5281/zenodo.21269201](https://doi.org/10.5281/zenodo.21269201).
