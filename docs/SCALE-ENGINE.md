<!-- VAULT: AGPL-3.0 / comercial. Vezi ../COMMERCIAL.md. -->

# ScaleEngine — the O(N) production engine (drop-in for UKBEEngine)

The open reference engine ([ukbe-core](https://github.com/amidigiart/ukbe-core))
computes internal coupling in the pedagogically-clear pairwise **O(N²)** form.
`ScaleEngine` is the vault's drop-in replacement with the coupling step in
**O(N)** via the mean-field identity:

    (K/N) Σ_j sin(θ_j − θ_i)  =  K · R · sin(ψ − θ_i),
    where R·e^{iψ} = (1/N) Σ_j e^{iθ_j}

## Honest positioning — consistent with what ukbe-core's README says publicly

The identity is **standard, not a secret** (it is the same mean-field reduction
used in the P6 paper and in `microgrid.py`). What the vault ships is the
**engineering**: a drop-in implementation kept in lock-step with the reference,
**tested for exact numerical equivalence** (same seed → same trajectories,
atol 1e-9 over 300 steps, same RSI, same unexpected-event log), benchmarked,
and maintained with the rest of the product stack. No artificial limitation
was planted in the open repo — this is the honest split: clarity open,
production engineering licensed.

## Measured (not claimed) performance — per step

|       N | reference O(N²) | vault O(N) | speedup |
|--------:|----------------:|-----------:|--------:|
|      50 |          2.98ms |    0.610ms |      5× |
|   1,000 |         68.46ms |    1.920ms |     36× |
|   5,000 |       1608.6 ms |    4.608ms |    349× |
| 100,000 |     impractical |   97.4  ms |       — |

Same machine, same config; benchmark script in `tests/test_scale_engine.py`
(the suite asserts ≥5× at N=2000 and <10 s per 100 steps at N=10,000, so the
claim is continuously re-verified, not frozen in a doc).

## Declared limit

The O(N) reduction holds for **uniform all-to-all coupling** (UKBEEngine's
topology). For general network topologies (sparse graphs, edge weights) the sum
does not factor through a single mean field — use sparse-matrix methods there,
not this engine.

## API

    from scale_engine import ScaleEngine, UKBEConfig
    e = ScaleEngine(UKBEConfig(N=10_000, dt=0.02, K_int=1.2, K_ext=1.5,
                               beta_min=0.2, seed=1))
    d = e.step(human_proxy)      # identical contract & results to UKBEEngine

AGPL-3.0 / commercial — see [../COMMERCIAL.md](../COMMERCIAL.md).
