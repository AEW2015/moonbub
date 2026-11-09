# Reproduce V115

Use branch `study/gamebub-v115-timing-cuts-20261108`, based on
`6098d48e5c4b57576fddeec1ae6facbc25165a11`. Frozen source/evidence from older
versions remains a dependency; the V115 bundle does not replace those files.
No hardware, relay, installed Sunshine instance or stream is contacted.

## Tools and resource limits

The established behavioral backend is Verilator in
`gamebub-cu66-v69-tools:20261105`, image
`sha256:b35d0961607ab885b8024ef37ebcac0c3a0d010af00fe6bbdbc63264079a49cf`.
Owned C++ uses C++17 with warnings as errors. Main RTL campaigns retain
`--assert -Wall` with no `-Wno-fatal`; original functional assertions remain
enabled. Compile with one make job. Native timing uses Vivado 2026.1 build
6511674 from `acorn-nexys4-ddr:2026.1`, image
`sha256:dd51b5dd44148c23bb0059b929697243797022172d5efb01ffdd8b8dd7a89742`.
The installation and existing legitimate license are mounted read-only;
never include license contents in logs or source control.

Root grants at most two heavy study jobs across agents and all runners, each
with two CPUs and 8 GiB RAM plus an equal combined RAM/swap ceiling. A runner
is not permission to launch a third job independently. The full campaign's
optional two-slot grant must pin the completed actual-composition peer proof.
Without that grant its two seeds execute sequentially.

Available RAM and memory pressure govern launches: at least 8 GiB available,
memory-full PSI avg10 below 1; native timing additionally checks combined
RAM/swap usage below 85%. Stop below 4 GiB available or on persistent full PSI
at least 5; native runs also stop at 90% combined use. Swap need not be empty.
Per-command watchdogs and resource samples are retained in each attempt.

## Functional qualification

Run focused proofs before combined qualification, respecting the shared slots:

```sh
python3 scripts/cu66-v115/inverse/qualify.py --run
python3 scripts/cu66-v115/ingress/qualify.py --run
python3 scripts/cu66-v115/scratch/qualify.py --run
python3 scripts/cu66-v115/scratch-extra/qualify.py --run
python3 scripts/cu66-v115/control-peer/qualify.py --run
python3 scripts/cu66-v115/spatial.py --run
python3 scripts/cu66-v115/performance.py
```

Do not rerun source-preparation scripts during qualification. The native gate
checks the exact selected replacement body hashes (five initially/refined, six
finally), all 18 compilation origins,
selected focused receipts, current raw artifacts and the actual full-component
peer proof. The canonical reference is frozen V113 output, not regenerated
candidate output. Both the decoder and V97 transport models compile fresh.
Failed attempts remain distinguishable from selected successful receipts.

The separate `scripts/cu66-v115/jpeg-wire/` experiment uses different sources
and a JPEG baseline. It cannot substitute for custom CS88 parent qualification;
see [its exact scope](jpeg-wire.md) before running it.

## Refined and final selections

The commands above describe the initial five-body campaign. The refined body
pair is qualified by `refined-ingress/qualify.py` and
`refined-scratch/qualify.py`, then `refined_peer.py` and `spatial_refined.py`.
Read the selected receipts before choosing a composition; an initial result
does not qualify a later source body.

For the final six-alias selection, use these entrypoints under
`scripts/cu66-v115/`:

```sh
python3 scripts/cu66-v115/final-ingress/qualify.py --run
python3 scripts/cu66-v115/owner-cut-focus/qualify.py --run
python3 scripts/cu66-v115/final_peer.py --run
python3 scripts/cu66-v115/spatial_final.py --run
python3 scripts/cu66-v115/performance_final.py
python3 scripts/cu66-v115/prepare_live_final.py
python3 scripts/cu66-v115/live_final.py --run
```

The final full runner defaults to sequential seeds. A Root-authored optional
`--pair-grant-file` can permit two seed jobs only after its matching final-peer
receipt passes. Do not create that grant while another study heavy job still
owns a slot. The older initial/refined runners are frozen historical recipes;
when launching them alongside another job, pass an absent grant-file path and
keep it absent until the other job has completed. Their omitted-grant default
is not the final runner's sequential default.

The final LIVE emitter refuses to generate its immutable driver until the
actual final main selection passes. It retains the original wrapper, bench,
negative ACK ownership checks and abstract-memory limits; it does not add
physical SDRAM or LCD coverage. See [LIVE scope](live-parent.md).

## Native timing

The native [method](native-method.md) records the fixed tool flow, actual clock
constraints, complete report requirements, immutable source composition and
global six-initial-route/three-composition budget. First prepare, then audit the
exact cards; Root launches only after the independent audit is explicitly final:

```sh
python3 scripts/cu66-v115/native_final.py --trial integrated-125
python3 scripts/cu66-v115/native_final.py --trial integrated-100
python3 scripts/cu66-v115/native_final.py --run --preflight CARD --audit AUDIT
```

The final driver reuses the refined flow unchanged; use `native.py` or
`native_refined.py` only for their historical compositions. Published dispatch
records consume this version's budget. A new physical reproduction needs an
explicitly reassessed run namespace/budget; never delete dispatch records or
raise a frozen limit to force another route. Functional replays also update
selection pointers, so use an isolated checkout and keep published receipts
immutable.

Missing proofs stop preparation. Negative timing does not authorize an
unchanged-source reroute. A positive fresh repeat starts from RTL under the
same source, constraints, method and tool image. No bitstream is generated.
Build binaries/checkpoints remain outside the repository under
`/home/lori/gamebub-build/cu66-v69`; retained source snapshots, scripts, reports,
logs and receipts provide the reviewable handoff.

## Scope of results

Report actual component cycles separately from conditional clock conversions.
Even a repeatable OOC setup/hold pass is only component evidence: the complete
operational FPGA parent still needs I/O constraints, CDC, memory/controller,
frame-validation and publication qualification. A fixed corpus is not a
300-frame, 60/600-second or sustained hardware campaign. ESP32 target execution,
Wi-Fi timing calibration, hardware 30 fps and validated full decoding below
10 ms must each be supported by their own executed evidence.

## Read-only mapping inspection

After a final native receipt is terminal, regenerate `summarize.py`, then run
`query_registers.py --receipt FINAL_NATIVE_RECEIPT --run` while a heavy slot is
free. It opens the exact native-recorded DCP without synthesis or implementation;
DCP manifest identity and actual tool/part/clock are checked. Input snapshots,
selected-summary snapshot, register/fanin TSVs and failed diagnostic history
are retained. Its own source snapshots are mounted read-only, and tool work
stays external. This query is not a timing trial or a timing-closure verdict.
See [mapped-register evidence](mapped-registers.md).
