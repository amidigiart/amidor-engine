# Weighted Ensemble Agreement Coherence (WEAC)
### A calibratable formula for "when to trust an ensemble of LLMs, and when to abstain"

**Author:** Mihai Roșca · July 2026 · part of [amiecosystems](https://amidorai.com)
**Lineage:** the corrected multi-reference coherence from
[SECTION-11-CORRIGENDUM](https://github.com/amidigiart/ukbe-core/blob/main/docs/SECTION-11-CORRIGENDUM.md),
applied to model consensus. Implementation & tests: [`ensemble.py`](../ensemble.py),
[`tests/test_ensemble.py`](../tests/test_ensemble.py) (50 tests, offline).

> Honest framing up front: this is **not new mathematics** — it is the weighted
> Kuramoto order parameter / weighted mean pairwise agreement, which is standard.
> The contribution is the **application**: a single, calibratable coherence score
> for an N-model LLM ensemble with per-model reliability weights, plus a principled
> abstain rule. It measures **agreement, not truth**.

---

## The formula

Given M independent model answers a₁…a_M, reliability weights w_k ≥ 0, and a
similarity s(aᵢ,aⱼ) ∈ [0,1]:

**Ensemble coherence:**

    C = ( Σ_{i<j} wᵢ wⱼ s(aᵢ,aⱼ) ) / ( Σ_{i<j} wᵢ wⱼ )     ∈ [0,1]

**Delivered answer (weighted medoid — the most-agreed-upon answer):**

    a* = argmax_k  w_k · Σ_{j≠k} wⱼ s(a_k,aⱼ)

**Decision:** assert a* iff `C ≥ τ` **and** no hard numeric conflict; else abstain.

## Properties (all verified in tests)

- **C ∈ [0,1]** always (weighted average of values in [0,1]).
- **M = 2 ⟹ C = s(a₁,a₂)** — reduces exactly to the existing dual-model concordance
  score, so WEAC is a strict generalization of the shipping engine.
- **All identical ⟹ C = 1; all unrelated ⟹ C = 0.**
- **Monotone:** an agreeing model raises C; a disagreeing one lowers it, scaled by
  its weight.
- **Kuramoto kinship:** if answers carry phases φ_k with s = (1+cos(φᵢ−φⱼ))/2, then
  C is the weighted phase-agreement across pairs — the coherence corrected in the
  §11 corrigendum, here between models instead of oscillators.

## Two bugs found live while building this (kept, not hidden)

1. **Medoid weighting semantics.** The first medoid used only the *others'* weights,
   so a low-weight outlier was **not** demoted from being selected (it delivered
   "Lyon" over "Paris" when 3/4 models said Paris). Fixed by including the
   candidate's own weight w_k in its score. Regression-tested.
2. **Boilerplate sensitivity of trigram similarity.** When answers share a template
   ("The capital of France is ___"), trigram similarity is dominated by the shared
   text and under-weights the content difference (Paris vs Lyon). Consequences,
   stated plainly:
   - `s` is **pluggable** — for production, use semantic embeddings, not trigrams.
   - The **coherence gate τ is the primary defence**, not medoid selection: set τ
     high enough that `assert` happens only on genuine agreement.
   - The **hard numeric rule is independent of `s`** and protects the high-stakes
     case (doses, amounts) regardless of phrasing — which is why it is separate.

## What it is NOT

- Not a truth oracle. Models trained on similar data can agree and be wrong
  together; C caps the *disagreement-driven* error, not the *shared-bias* error.
- τ is a **design parameter to calibrate per deployment** (like β_min in the
  engine), not a universal constant.
- Not novel mathematics; novel only as an applied, weighted, abstaining ensemble
  score with a clean reduction to the 2-model case.

## Why it is useful now

Most multi-LLM products do naive majority vote or pick one model. WEAC gives, in
one number, a **calibratable confidence-and-abstention signal** for any ensemble,
with per-model reliability weighting and a hard numeric guard — droppable into
AmiDor (N-model mode) or any product that runs more than one model and needs to
know when to shut up. That "knowing when to abstain" is the exact market gap the
whole AmiDor line is built around.

---

**Licensing note:** the *formula* is free (mathematics cannot be owned — that is the point). This **implementation** (`ensemble.py`) is AGPL-3.0 / commercial dual-licensed like the rest of amidor-engine: closed/commercial use requires a license — see [../COMMERCIAL.md](../COMMERCIAL.md).
