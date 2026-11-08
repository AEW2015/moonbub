# Reproduce V113

Use new external build directories and the exact selected receipts. Frozen
V110/V111/V112 sources, oracles and proof bytes are base dependencies and must
remain unchanged. Do not discard strict assertions or reinterpret old cycle
comparisons as a latency-changing proof.

## Focused and full simulations

```sh
python3 scripts/cu66-v113/geometry/qualify.py --run
python3 scripts/cu66-v113/scratch/qualify.py --run
python3 scripts/cu66-v113/inverse/qualify.py --run
python3 scripts/cu66-v113/inverse/benchmark.py --run
python3 scripts/cu66-v113/spatial.py --run
python3 scripts/cu66-v113/lanes.py
```

The published selection reuses the first attempt's successful complete
canonical stages for an adapter-only retry. Its parent attempt remains FAIL
overall. Reusing that compiled model requires the original external build
directory and the explicit `--reuse-canonical RAW_PARENT_RECEIPT` option;
the default `--run` command rebuilds and reruns both canonical seeds instead.
Never count the published retry's zero newly executed canonical rows as 44
new executions. Retained stdout, compressed canonical files and source
snapshots support independent review without the external compiled archive.

The source-pinned focused tests qualify the three body replacements separately.
The full spatial runner then qualifies their actual composition against the
unchanged independent bench and canonical pixel files, followed by its
separate actual forwarding-RTL/custom-decoder chain. Both contracts must pass;
a prepared manifest or clean compile does not constitute a simulation PASS.
The exact benchmark CLI and requirements are also documented in [inverse.md](inverse.md).

Obtain a Root heavy-job grant before compiling or running: at most two global
heavy jobs including non-container processes, two CPUs and 8 GiB memory=swap
per job, no extra swap, bounded watchdogs. Available RAM and memory PSI are
the main launch/stop gates. Native jobs additionally require combined usage
below 85% at launch and stop at 90%, where combined usage is
`(MemTotal - MemAvailable + SwapTotal - SwapFree)/(MemTotal + SwapTotal)`.

## Native component timing

Only after the selected full spatial proof passes:

```sh
python3 -m unittest discover -s scripts/cu66-v113/tests -p test_native.py
python3 scripts/cu66-v113/native.py --trial spatial-100
python3 scripts/cu66-v113/native.py --trial spatial-125
```

Independently audit each prepared card and its exact hashes before Root dispatch:

```sh
python3 scripts/cu66-v113/native.py --run \
  --preflight EXACT_PREFLIGHT --audit EXACT_AUDIT
```

Native tools use the actual Artix-7-enabled installation at
`/home/lori/acorn-nexys4-ddr/tools/2026.1/Vivado` and default read-only license
path `/home/lori/acorn-nexys4-ddr/cache/vivado.lic`; never print its contents.
The qualified container image and existing host-network licensing arrangement
are retained without changing host IDs/MACs. No hardware or Windows service
is contacted, and no bitstream is generated/programmed.

Only a genuinely positive actual result permits `--repeat-of` with its exact
terminal receipt. The single fresh repeat must preserve source, tool image,
clock, method and functional recipe. Failed initial routes do not permit a
strategy retry. Source-only simulation, component setup/hold and complete
parent/hardware qualification remain separate gates.

## Evidence summaries and handoff

After the selected proof and terminal native receipts are available:

```sh
python3 scripts/cu66-v113/performance.py
python3 scripts/cu66-v113/summarize.py
python3 scripts/cu66-v113/bundle.py --verify
```

`performance.py` rechecks original successful-frame transcripts before
converting cycles at hypothetical clocks. `summarize.py` rechecks selected
functional proofs and raw native reports; reused controls and new trials have
separate rows. The bundle manifest covers only V113-owned directories. Frozen
dependencies live in the pinned base revision; unrelated marker-recovery work
and external checkpoints/build binaries are excluded. A manifest verifies
artifact identity, not hardware timing or displayed frame rate.
