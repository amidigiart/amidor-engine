<!-- VAULT: AGPL-3.0 / comercial. Vezi ../COMMERCIAL.md. -->

# Arbitration Support — an agreement & uncertainty meter for AI-assisted arbitration

**What it is:** a decision-support tool for human arbitrators. It runs N
independent AI analyses of the same clause / dispute point and reports how much
they **agree**, **where they diverge** (escalated for human review), and it
**abstains** when agreement is weak or numbers conflict.

**What it is NOT — and this is enforced in code, not just stated:**
- It is **not a judge**. It never issues a verdict, a winner, or "legal truth".
- Its output type has **no field** named `verdict`, `winner`, `truth`, or
  `correct` — a structural test asserts this.
- Agreement between models is **not correctness**. N models can agree and be
  wrong together (shared training data, shared bias). The signature test feeds
  three identical-but-wrong analyses and asserts the tool reports *agreement*
  with a permanent risk warning — **never** certifies it as true.
- In high-stakes mode it **always escalates to a human** (`escalate_to_human =
  True`), even at perfect agreement. Agreement only lowers the human's review
  burden; it never removes the human.

## Why this framing, not "the AI judge"

A "Council of Resonance that determines objective justice" is a category error:
coherence measures inter-model agreement, which is subjective to the models
chosen — not objective truth, and not justice (which requires due process,
rights, appeal, accountability, jurisdiction). An autonomous AI judge is both
legally impossible (no court delegates a verdict to a coherence score) and
ethically unsafe (it would reward the most eloquently unanimous side, not the
right one). This tool deliberately stays a **meter**, not a **gavel**.

## Where it is genuinely useful (B2B / smart contracts / DAOs)

- **Arbitration & contract review:** surface, in one number, how much
  independent analyses converge on interpreting a clause — and flag the
  contested points a human must adjudicate. Triage, not ruling.
- **Off-chain oracles for smart contracts / DAOs:** a multi-model consensus
  signal on an ambiguous fact, with **explicit abstention** when models
  disagree, so the contract escalates to human governance instead of settling
  on a confident guess.
- **Due-diligence / e-discovery:** rank where AI analyses agree (lower review
  load) vs. diverge (human attention needed).

In all of these the value is the honest one WEAC was built for: **knowing when
to abstain and call a human.**

## API

    from arbitration import assess_arbitration
    a = assess_arbitration(analyses, weights=None, tau=0.6, high_stakes=True)
    # a.coherence, a.status ∈ {converged, contested, insufficient},
    # a.agreed_interpretation (labeled majority reading, NOT a verdict),
    # a.contested_indices (escalate to human), a.escalate_to_human, a.risk_note

Built on [WEAC](ENSEMBLE-COHERENCE.md); math anchored to
[doi:10.5281/zenodo.21269201](https://doi.org/10.5281/zenodo.21269201).
Licensing: AGPL-3.0 / commercial — see [../COMMERCIAL.md](../COMMERCIAL.md).
