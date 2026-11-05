# V70 reproduction and review

Start with [the handoff](hardware-handoff.md). Functional reconstruction and
memory safety evidence pass; clean native scanout cadence does not. No board
was programmed, and no live CU66 Sunshine/ESP32 backend was installed.

## Environment

The retained runs use the dedicated `gamebub-cu66-v69-build` container (the
historical name is shared with the v69 study), image
`sha256:b35d0961607ab885b8024ef37ebcac0c3a0d010af00fe6bbdbc63264079a49cf`.
Tools: GCC13.3, Verilator5.020, Icarus12.0, Yosys0.33, CMake3.28.3 and Python3.
The full command model needs Verilator `--timing` or the recorded Icarus flow.
All retained clocks, seeds, defines and command argv are in result JSON files.

The source recipe is the frozen v69
`fpga/experiments/cu66-v69/build-env/Dockerfile`. Its base image is pinned;
package installation is not an immutable apt snapshot. Tool version checks and
recorded image identity are therefore part of reproduction, not a claim that
any fresh apt build is byte-identical.

For a fresh Linux host with Docker, from this repository's root:

```sh
docker build -t gamebub-cu66-v70-tools \
  -f fpga/experiments/cu66-v69/build-env/Dockerfile .
repo_root="$(pwd -P)"
build_root="${TMPDIR:-/tmp}/cu66-v70-build"
mkdir -p "$build_root"
docker run -d --name gamebub-cu66-v69-build --cpus=4 --memory=4g \
  --mount "type=bind,src=$repo_root,dst=$repo_root" \
  --mount "type=bind,src=$build_root,dst=/build" \
  gamebub-cu66-v70-tools sleep infinity
```

Reuse an already-running container with that name instead of creating a second
one. Build UID/GID arguments can be set to match the host workspace. The repo
must be mounted at the same absolute path because compile commands use it.
The replay inputs are committed; fixture export and video-download dependencies
are not required for the listed native/RTL qualification runs.

## Review existing evidence first

```sh
python3 scripts/cu66-v70/verify_baseline.py
python3 scripts/cu66-v70/verify_evidence.py
python3 scripts/cu66-v70/bundle_manifest.py
```

The first checks the 15 reviewed inputs and 4,879-file v69 bundle. The evidence
auditor reconciles source/log hashes and numerical scopes, including cadence
failure. The handoff manifest checks packaged file bytes; file integrity alone
is not a functional or hardware verdict. Producer evidence and retained failed
development logs are distinct. Historical pre-fix results are not current-
source qualification, and the audit does not silently repin them.

## Rebuild one qualification scope

Run these in a disposable checkout when preserving the original retained logs
matters: producers regenerate their own logs/results in place. They use
separate external build directories under `/build` and at most two build jobs.
Do not run several heavy builds simultaneously inside the shared4GiB cap.

| Scope | Command |
|---|---|
| Full packet/reference owner, 457 frames | `python3 scripts/cu66-v70/run_receiver.py` |
| Watchdog/stale responses/diagnostic ring | `python3 fpga/experiments/cu66-v70/owner-control/run.py` |
| All28 malformed/unsupported replay cases | `python3 fpga/experiments/cu66-v70/negatives/run_negatives.py` |
| Controller/tile/aux memory, two simulators | `python3 fpga/experiments/cu66-v70/memory/run_regression.py` |
| Painter and asynchronous scanout components | `python3 fpga/experiments/cu66-v70/display/run_regression.py` |
| Exact strip comparison | `python3 fpga/experiments/cu66-v70/display/run_strip_comparison.py` |
| Dirty-strip abort/recovery | `python3 fpga/experiments/cu66-v70/display/run_strip_control.py` |
| Integrated real-controller control guards | `python3 fpga/experiments/cu66-v70/system/run_control.py` |
| Full key/P, direct painter, real commands/LCD | `python3 scripts/cu66-v70/run_system.py --frames 2` |
| Full key/P, strip painter, real commands/LCD | `python3 scripts/cu66-v70/run_system.py --frames 2 --strip` |
| Compare the two declared schedules | `python3 scripts/cu66-v70/compare_system.py` |
| Bounded bank checks and witnesses | `python3 fpga/experiments/cu66-v70/formal/run_bounded.py` |

The `control-abi` Python-only codec has its own README and unittest entrypoint.
The native `software-control` endpoint has a separate README/runner. These
control-plane tests do not turn the full system's typed processor sidebands
into a physical ESP32 transport implementation.

Explicit terminal PASS, normal exit, matching counts and unchanged input hashes
are required for functional qualification. The system runners also record
`cadence_status=FAIL_UNDERRUNS`; a successful simulator exit must not hide that
failure. A receiver `--per-chain 2` run is eight frames, not the full457 gate.

The full receiver uses transactional external RAM plus painter/scanout completion
models. The command-level system instead uses actual memory/painter/LCD RTL and
checks two chronological frames with each painter. Their timings/scopes must not
be mixed. Native HUD CPU time, live Wi-Fi/QSPI and actual device clocks are not
measured by either simulation.

## Exact-device implementation gate

The current Vivado2025.2 install does not include `xc7a100tcsg324-1`.
`fpga/experiments/cu66-v70/build/preflight.log` records the unavailable gate;
`build/status.json` separates that result from synthesis and routing.

The staged `build/ooc_system.tcl` lists hardware sources only, excluding the
32MiB simulation model. Run it from a fresh output directory once exact-part
support is installed. The optional Tcl argument selects `USE_STRIP=0/1`.
Its declared external-clock assumptions are not PLL/pad/jitter qualification.
The falling-before-rising waveform notation follows AMD's
[Vivado2025.2 create_clock reference](https://docs.amd.com/r/2025.2-English/ug835-vivado-tcl-commands/create_clock).
The separate virtual-clock probe failed because no elaborated design was open;
it is retained as a diagnostic, not a successful constraint test.

Review utilization, RAM inference/ports, unconstrained paths, timing, CDC and
DRC reports. A completed route is not automatically a board signoff: live
ingress/processor control, board wrapper, I/O constraints and hardware testing
are still required. General RTL development and these behavioral simulations
need no DAP/JTAG connection.
