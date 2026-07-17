# REAI Engine — Live State Monitor (vault)

A local-first dashboard showing the **real** state of the REAI engine in real
time — RSI, α/β (adaptive weights), H (entropy = 1−Φ_int), locked %, Φ_extern —
all from `ukbe_core.UKBEEngine`. No invented values, no external CDN (inline
CSS + SVG), theme-honest CRT aesthetic.

## Run
```bash
pip install fastapi uvicorn "ukbe-core @ git+https://github.com/amidigiart/ukbe-core@main"
python monitor/monitor_app.py     # http://localhost:8125
```

## NDA-gated demo
Set `MONITOR_ACCESS_CODE` to require a code (`/monitor/state?code=…`). The source
is AGPL-3.0 / commercial (see ../COMMERCIAL.md); **access to a running demo
instance is granted under NDA** — the ready-to-sign template (RO/EN, with the
access-code flow) is at [../legal/NDA-DEMO.md](../legal/NDA-DEMO.md); contact
contact@kinderagi.com. The engine behind the panel is `ScaleEngine` (O(N)) at
N=10,000 by default.

*Not Linux (not everything free), not a closed extractor either — open-core with
a protected value layer and NDA demos.*
