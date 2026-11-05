# CU66 v69 reproducibility and handoff

This handoff records independently reproducible software/RTL component evidence. The frozen native decoder, entropy, hash, row, inverse, bank, packet and layout studies have completed their local checks. A base-layer integration simulation also passes its recorded cases. These are not a complete CU66-to-panel implementation: integration is still being extended, and target synthesis, routed timing, physical memory behavior and board qualification remain open.

## Build environment

The recorded tool environment is Docker container `gamebub-cu66-v69-build`, image `sha256:b35d0961607ab885b8024ef37ebcac0c3a0d010af00fe6bbdbc63264079a49cf`, with the repository mounted at its usual absolute path. On 2026-11-05 it reported Verilator 5.020, Icarus 12.0, g++ 13.3.0, Yosys 0.33 and CMake 3.28.3. Host PATH does not provide the HDL/native tools. The source pins and actual result/log paths are summarized in [component-matrix.md](component-matrix.md).

The Vivado container is `gamebub-cu66-v69-vivado`, image `sha256:6d2f9bb53968bff852af10ab37e7e64872aab557a94c261cf605dc82f6dac58`. Vivado 2025.2 is installed, but exact part `xc7a100tcsg324-1` is absent. A reviewed Add Devices attempt stopped because AMD requires an installer authentication token; no token was present or inspected. See `fpga/experiments/cu66-v69/integration/target-preflight.log` and `host/build/part-add-private.log` (the latter is private and must not be copied into public evidence). Vivado synthesis/implementation therefore remains `NOT_RUN`. The root-owned container recipe is `fpga/experiments/cu66-v69/build-env/Dockerfile`.

## Targeted reproduction commands

Run one study at a time. The commands below reproduce checks without making the generic entrypoint launch an expensive collection of suites:

```sh
# Source and environment metadata
python3 scripts/cu66-v69/runner.py --check-sources
python3 scripts/cu66-v69/runner.py --doctor

# Frozen native fixture checks (see that study's README for per-check commands)
bash experiments/cu66-native-v69/run_native_checks.sh

# Verilator behavioral component studies; each has its own exporter/auditor
bash fpga/experiments/cu66-v69/entropy/run_regression.sh
bash fpga/experiments/cu66-v69/hash/run_regression.sh
bash fpga/experiments/cu66-v69/rows/run_regression.sh
bash fpga/experiments/cu66-v69/packet/run_regression.sh

# Inverse math/IDCT and bank controls
python3 scripts/cu66-v69/runner.py --idct-regression
python3 scripts/cu66-v69/run_math_regression.py
python3 fpga/experiments/cu66-v69/inverse/expand/run_regression.py
python3 fpga/experiments/cu66-v69/banks/export_vectors.py
# For bank RTL compile/run argv, see banks/results.json and banks/README.md.

# Native portrait orientation / layout replay
/home/lori/gamebub-streaming-prototype/.venv/bin/python \
  fpga/experiments/cu66-v69/layout/prove_layout.py
```

Use each study's `README.md`, `results.json`, and retained logs as the command/result authority. Some studies require the repository Python venv, while HDL/native execution uses the named container. Commands above are intentionally separate: they do not claim a single command has rerun the complete corpus. The new expander runner records both Icarus and Verilator logs, all seed summaries, mask/source hashes, and tool/container identity.

The older generic `scripts/cu66-v69/run.sh` remains a **scaffold**. Its run plan does not silently reinterpret historical PASS records as fresh executions; `--run` reports unresolved tasks until explicit runnable task records are added. It is not the command for reproducing all evidence.

## Evidence boundary and remaining gates

Component PASS means the named checker matched its local oracle and gates. It does not prove their interfaces have all been composed into a complete receiver. In particular, physical SDRAM controller scheduling, asynchronous clock crossing, HUD semantic decode/overlay, complete reconstruction/hash/publication ordering, end-to-end frame latency, target part fit, routed Fmax, ESP32 transport, physical LCD output and recovery remain integration/hardware work. Recorded cycle counts use the studies' behavioral service schedules; they are not device timing or a 30 fps claim.

The existing controller maps one SDRAM chip. The repository's portrait layout proof checks all coded pixels and compares storage-locality models, but it does not implement the new layouts in RTL or establish the board's total memory fit. The source catalog and pins record external board sources separately; they do not claim remote files are repository contents. Preserve frozen V67 evidence and the completed study directories unchanged while integrating new work.

## Final full-pipeline evidence gate

Run `python3 scripts/cu66-v69/check_full_pipeline.py` to check both complete 457-frame schedules, explicit shared-bus flags, fault/drain counts, input pins and retained log hashes. A smoke `--per-chain 2` cannot satisfy this gate. The [handoff](hardware-handoff.md) and [independent integration audit](integration-audit.md) describe the remaining physical-memory/HUD/bank/scanout boundaries. The software HUD gate has its own `fpga/experiments/cu66-v69/hud-partition/run_contract_tests.sh` and scope contract.

## Retained-evidence integrity

`python3 scripts/cu66-v69/verify_components.py` independently reconciles ten frozen component scopes and their declared pins; integration and the software HUD gate are qualified separately. It reports the original inverse result’s missing historical transcript hashes as a provenance warning. `python3 fpga/experiments/cu66-v69/hud-partition/audit_results.py` checks the HUD partition. After transfer, `python3 scripts/cu66-v69/bundle_manifest.py` verifies every packaged v69 file and the two updated indexes against the handoff manifest. File integrity is distinct from test verdicts and hardware qualification.
