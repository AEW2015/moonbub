# V87 evidence, reproduction and limits

V87 keeps all published V86 and older tracked bytes frozen. The new branch
adds only `docs/cu66-v87`, `scripts/cu66-v87` and
`experiments/python-gamebub-v87`. The unrelated untracked
`fpga/experiments/throughput30/burst/marker-recovery` directory is preserved.

## Native quantizer wire experiment

The selected [CS87 native campaign](../../experiments/python-gamebub-v87/quantizers/results.json)
links its unique attempt. It binds producer/receiver sources, old qualified
controls, native decoder headers and archived source copies. The two native
receiver processes both exited zero after 457 sources each. Complete packet
bytes and native coefficient, canonical/HUD/display/root/seal identities are
retained per source/configuration. Twelve `.cs87` fixtures are retained.

The [independent packet audit](../../experiments/python-gamebub-v87/quantizer-audit.json)
rebuilds all 914 bytestrings through an independent field/map assembler and a
separately written quantizer candidate builder/cache. It checks method choice,
inheritance eligibility, every packet/qmap SHA, summaries, source identities
and the retained fixtures. It does not call the producer's quantizer encoder.

The selected [quantizer tests](../../experiments/python-gamebub-v87/quantizers/tests.json)
contain 37 checks. They exercise all seven methods in independent Python and
native C++ parsers, exact geometry, malformed data, actual receiver retention,
late content-root failure, recovery, replay and alternate cache branches. The
older 33-check test attempt is development history, not an additional 33 test
cases in the current verdict. Its executed test source is archived alongside
its report; selected current sources are checked separately.

```sh
python3 scripts/cu66-v87/prototype_quantizers.py
python3 scripts/cu66-v87/test_quantizers.py
python3 scripts/cu66-v87/audit_quantizers.py
```

The native campaign/test commands use the existing
`gamebub-cu66-v69-build` Docker container and its mounted workspace/compiler.
Python codec/model/audit utilities otherwise use the standard library. Native
host execution time is not FPGA decode latency. The host receiver's whole-frame
arrays and 2-MiB research limit are not ESP32/FPGA memory allocations.

## Coupled fixed-CS86 timing study

The [coupled study](coupled.md) joins actual re-encoded context observations,
fixed CS86 byte counts, native residency and C2 work into one task graph. Its
six configurations cover the zero-frontend control, LOW/HIGH one/two-lane
arithmetic and a LOW two-lane periodic-memory-reservation sensitivity. All four
histories run in separate subprocesses; complete witnesses retain jobs,
dependencies, resource assignments, credit bindings and timestamps.

Every source/configuration performs in-process dependency, resource, group,
credit, context-order and complete-publication checks. Retained row verification
also reconstructs primitive work totals from the context index and checks all
457 zero-frontend results against the already published V84 timings. Five full
witnesses have an independent timeline/consumer audit, tied to their exact
campaign row hashes. Seven synthetic model checks and nine targeted auditor
mutation checks are separate from the actual-data schedules.

```sh
python3 experiments/python-gamebub-v87/coupled/test_model.py
python3 scripts/cu66-v87/prototype_coupled.py
python3 experiments/python-gamebub-v87/coupled/verify_results.py \
  --session experiments/python-gamebub-v87/coupled/sessions/20261106T142747813379Z-3c46f71f
```

The native content proof belongs to V86/CS86; this Python model does not execute
the inverse transform. The new CS87 packet proof and the alias layout have
separate inputs and scopes. Their savings are not silently substituted into
the fixed-CS86 latency numbers.

## Memory accounting and alias layout

The [memory accounting](../../experiments/python-gamebub-v87/memory/results.json)
and [independent arithmetic audit](../../experiments/python-gamebub-v87/memory-independent-audit.json)
cover four scenarios on all 457 native sources. They are necessary traffic
budgets, not scheduled completion predictions. Counterfactual write deletion
is labeled explicitly and retains all reference reads.

The [alias-layout result](../../experiments/python-gamebub-v87/alias/results.json)
is a separate sequential functional model using already decoded tiles. It
checks 914 scenario/source replays and 61 retained checks. The
[independent alias audit](../../experiments/python-gamebub-v87/memory/alias-audit.json)
rejoins native tile/presentation identities and tests 1,024 seeded symbolic
updates against an immutable-image oracle. Neither executes the physical
display, encoded packet parser or a memory bus. Initial alias development
artifacts are retained but excluded from the selected result.

```sh
python3 experiments/python-gamebub-v87/memory/analyze.py
python3 scripts/cu66-v87/audit_memory.py
python3 experiments/python-gamebub-v87/alias/prototype.py
python3 experiments/python-gamebub-v87/memory/audit_alias.py
```

Some regeneration commands overwrite their selected reports. The native and
coupled campaigns create unique attempt/session directories. The combined
summary supports creation followed by exact verification:

```sh
python3 scripts/cu66-v87/verify_baseline.py
python3 scripts/cu66-v87/verify_evidence.py
python3 scripts/cu66-v87/verify_evidence.py --verify-summary
python3 scripts/cu66-v87/bundle_manifest.py --write
python3 scripts/cu66-v87/bundle_manifest.py
```

For the checked-in summary, use `--verify-summary`. The bare creation command
requires that `summary.json` does not already exist and refuses to replace it.

## Claims still open

There are only **457 source frames from one walkthrough family in four reset
histories**. Configurations, replays and synthetic sequences are not additional
distinct gameplay coverage or a sustained 30-fps source run. No new FPGA RTL,
ESP32 firmware, target synthesis/clock result or physical testing is included.

The coupled model uses assumed primitive weights, nominal arithmetic-stage
costs, resources and 100 MHz. It omits qualified semantic HUD processing,
physical COPY/CONST and RAM ports, controller row/refresh timing, indirect
scanout, asynchronous drain and ESP32/transport execution. LOW/HIGH are
sensitivity assumptions, not physical bounds. None of these results closes
sustained hardware 30 fps, full validated decoding below 10 ms or HEVC/AV1
rate/quality superiority.
