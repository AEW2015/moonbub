# Reproduce V112

Use the exact branch and source-bound receipts. Old V110/V111 proofs and reports
remain unchanged base dependencies. Generated native checkpoints and simulator
binaries live in external build directories rather than the source bundle.

## Resource coordination

Root serializes heavy-job grants across all agents, including native builds,
Verilator and emulator processes. At most two heavy jobs may run. Each receives
two CPUs and 8 GiB memory=swap, with no extra swap allowance. Available RAM and
memory pressure gate launch and continued execution; old swap occupancy alone
does not block useful work. Every job has a finite watchdog. Independent
concurrent launchers are unsupported; the Docker-name check is supplemental.
The native runner also records combined RAM/swap use as a secondary guard:
`(MemTotal - MemAvailable + SwapTotal - SwapFree) / (MemTotal + SwapTotal)`.
It requires less than 85% at launch and stops at 90%; available RAM and PSI
remain the main gates.

## Functional and physical runs

The focused original/candidate control proof and its source audit are:

```sh
python3 scripts/cu66-v112/control/qualify.py --run
python3 scripts/cu66-v112/control/audit.py
```

Full custom-decoder qualification, after the focused control proof passes:

```sh
python3 scripts/cu66-v112/canonical.py --variant combined --run
python3 -m unittest discover -s scripts/cu66-v112/tests -p test_native.py
```

The canonical runner recompiles the candidate and compares both seeds with
the actual frozen reference events, cycles and canonical pixels. Reused
reference evidence is explicitly separate from newly executed candidate runs.

Prepare each native trial only after all source/proof hashes agree:

```sh
python3 scripts/cu66-v112/native.py --trial control-100
python3 scripts/cu66-v112/native.py --trial control-125
```

Independently audit the selected unique preflight, then dispatch it:

```sh
python3 scripts/cu66-v112/native.py --run \
  --preflight EXACT_PREFLIGHT --audit EXACT_AUDIT
```

The read-only legitimate Acorn license defaults to
`/home/lori/acorn-nexys4-ddr/cache/vivado.lic`; its contents must not be printed.
The tool installation is `/home/lori/acorn-nexys4-ddr/tools/2026.1/Vivado`.
Native execution retains the validated host-network licensing arrangement,
without changing host IDs/MACs. No Windows service or hardware is contacted.

A negative result does not permit a strategy retry. One actual positive
terminal result may be prepared with `--repeat-of EXACT_POSITIVE_RECEIPT` and
independently audited for a fresh-RTL repeat with identical sources/clock/method.
Synthetic positive parser fixtures test the gate, not FPGA timing.

```sh
python3 scripts/cu66-v112/summarize.py
```

The summary keeps single-pass, repeated component qualification and full-system
gates separate. Behavioral simulation does not qualify timing, CDC or hardware
frame rate.

## Bounded adapter and CDC screens

Use the [portable fixture wrapper](portable-harness.md) when the original
machine-specific fixture locations are unavailable:

```sh
python3 scripts/cu66-v112/portable_harness.py --check-only
python3 scripts/cu66-v112/portable_harness.py
python3 scripts/cu66-v112/harness/audit_controls.py
python3 scripts/cu66-v112/cdc/run.py
```

The retained integration PASS was executed by the original harness runner;
only fixture preparation has been executed through the new wrapper. A fresh
wrapper run must earn its own result. The replay does not execute an ESP32
guest or native Sunshine, and the CDC run is behavioral rather than a new
physical clock/CDC qualification. Follow the same global heavy-job grants.
