# V28 independent Python codec audit

This audit independently verifies the v28 bounded motion search, tap-aware predictor probe, lazy encoder parity probe, and the full causal runtime campaign. It checks retained serialized objects, frame and reference lineage, CP27/GM27/HU25/JA27 framing, source/candidate pairing, integer SSE arithmetic, winner eligibility, every paid losing attempt, and summary calculations. The campaign verifier remains responsible for full pixel replay; this audit deliberately does not repeat that heavy decode.

The frozen comparison is `unified_causal` v27. Its retained summaries are checked directly: primary 524,016 complete bytes at MSE 14.058610039437585; complex 1,195,676 complete bytes at MSE 26.174528273129095. The native HEVC/AV1 comparison uses actual v24 access-unit lengths plus each current HU25 and 60-byte CP27 binding, with only measured operating points at least as good in aggregate MSE. Nominal 30-ID/s rate calculations remain projections.

All archive reads are size bounded, digest checked, and required to end exactly at the compressed stream boundary. `audit.json` inventories sorted repository-relative input/code SHA-256 values and excludes itself and `audit.log` to avoid a self-cycle.

Run with the repository Python environment:

```sh
/home/lori/gamebub-streaming-prototype/.venv/bin/python -m unittest discover -s experiments/python-game-audit-v28-study -v
/home/lori/gamebub-streaming-prototype/.venv/bin/python experiments/python-game-audit-v28-study/audit.py
/home/lori/gamebub-streaming-prototype/.venv/bin/python experiments/python-game-audit-v28-study/audit.py --check
```
