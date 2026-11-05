# V29 independent Python codec audit

This audit checks the retained `gamebub-controller-v29` results and the full
decoder replay. It recomputes complete CP27 byte totals, nested GM27/HU25
framing and hashes, exact 21,120-word HUD coverage, candidate cap and
same-tier quality eligibility, chosen packet, own-history reference tags,
accepted ACK bindings, paid-work totals, summary arithmetic, v28 parity, and
the EC negative control. The full controller verifier owns pixel reconstruction
and source-SSE replay; this audit binds its retained `replay.json` hashes and
checks every accepted decoded tag follows that policy's previous output.

`audit.json` includes an explicit repository-relative SHA-256 inventory for the
v29 results, replay and verifier, the v28 baseline parser/results, this audit
code/tests, and the transitive frozen input pins recorded by the benchmark.
Generated `audit.json` is excluded from its own inventory to avoid a hash
cycle. The audit does not rerun the benchmark or full decoder campaign.

Run from the repository root with the inherited Python environment:

```sh
/home/lori/gamebub-streaming-prototype/.venv/bin/python -m unittest discover -s experiments/python-game-audit-v29-study -v
/home/lori/gamebub-streaming-prototype/.venv/bin/python experiments/python-game-audit-v29-study/audit.py
/home/lori/gamebub-streaming-prototype/.venv/bin/python experiments/python-game-audit-v29-study/audit.py --check
```

The audited figures describe Python host experiments and nominal byte-rate
projections at 30 source IDs per second. They do not establish native endpoint,
FPGA, RF, display, or physical 30-fps performance.
