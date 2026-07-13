<!-- VAULT: AGPL-3.0 / comercial. Vezi ../COMMERCIAL.md. -->

# Micro-Grid Synchronization — REAI applied where the math IS the domain's math

Power-grid generators **are** Kuramoto oscillators: they phase-lock to the grid's
nominal frequency (50 Hz in the EU). This is not an analogy — it is the standard
model of grid frequency stability, and it is the exact mean-field reduction from
the reproduced paper ([doi:10.5281/zenodo.21269201](https://doi.org/10.5281/zenodo.21269201)).

In the rotating frame at nominal frequency, generator i evolves as
`dθ_i/dt = Δω_i + (K/N) Σ_j sin(θ_j − θ_i)`, with Δω_i its frequency deviation
and K the coupling (topology + line strength). When K exceeds the spread of
deviations, the grid synchronizes (order parameter R → 1).

## Two directly-applied results from the P6 paper

**1. Coupling margin — how much coupling a micro-grid needs to stay locked.**
For the grid to remain frequency-locked under a maximum anticipated deviation
Δf_max, it needs `K ≥ m·Δω_max`, with the margin `m = √(1 + (Δω_max·τ_target)⁻²)`
derived from a required recovery time — **not** a guessed constant. Below the
threshold `K = Δω`, generators slip (desynchronize); between threshold and
recommended, they stay locked but recover slowly.

**2. Recovery time after a disturbance — with an early-warning of desync.**
`τ = (K² − Δω²)^(−1/2)`. Near the locking threshold (K ≈ Δω) recovery time
diverges (critical slowing down): a grid operating just above threshold takes
arbitrarily long to re-lock after a frequency event — a measurable early-warning
that the grid is under-coupled for its disturbances.

Worked example (from `microgrid.py`): a micro-grid required to withstand ±0.25 Hz
deviations with ≤2 s recovery needs K ≥ 2.36 (vs a bare lock threshold of 1.57);
at that K it re-locks in ~0.57 s, but operated just above threshold it would take
~4.5 s — the critical-slowing warning.

## Where it is useful

- **Micro-grid / renewable integration sizing:** how much inter-generator /
  inter-inverter coupling is needed to stay synchronized under expected
  frequency excursions, with an explicit safety margin.
- **Live stability monitoring & early warning:** track R (grid sync) and the
  recovery-time margin; a rising recovery time warns of approaching desync
  before it happens.

## Honest limits (stated, not hidden)

This is a **reduced-order phase model** (Kuramoto), not a full electromechanical
simulation. It does **not** model voltage, power flow, generator inertia
constants calibrated to real machines, or protection systems. It is a
**stability-margin and early-warning** tool for sizing and monitoring — not a
replacement for PSS/E, DIgSILENT, or PowerFactory. Parameters must be calibrated
to a real grid before any operational use.

API: `MicroGrid`, `coupling_margin(delta_f_max_hz, tau_target_s, safety_margin)`,
`recovery_time(K, delta_f_hz)`. Built on the P6 result; AGPL-3.0 / commercial —
see [../COMMERCIAL.md](../COMMERCIAL.md).
