# v20 handoff evidence audit

This read-only audit records final readiness and checks the frozen hardware C11
kit, mandatory-HUD study, and inline reconstruction study. It validates declared
source hashes and test logs, checks the documented evidence limits, and replays
the retained deterministic verifiers and analysis checkers. It does not run timed
benchmarks or infer fitted RTL, ESP32 performance, or physical 30 fps.

Run from the repository root:

```sh
/home/lori/gamebub-streaming-prototype/.venv/bin/python experiments/python-game-audit-v20-study/audit.py
/home/lori/gamebub-streaming-prototype/.venv/bin/python experiments/python-game-audit-v20-study/audit.py --check
```

`audit.json` remains pending until the root sets all three explicit readiness
signals in `audit.py`. The final snapshot lists each study's source pin count,
test count, verifier replay, analysis replay where applicable, and any errors.
