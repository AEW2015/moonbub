# V97: bounded transport and live native-Rust/RTL ingress

V97 now has an opt-in compact host packetizer, portable Rust receiver/gateway,
explicit credit/commit fences, and an interactive native-Rust-to-Verilator test.
The checkpoint covers transport and ingress. The production Wi-Fi worker still
uses MSV1; the new gateway and FPGA capability adapter are not deployed.
See [results](results.md), [wire/state contract](protocol.md),
[resource/fidelity audit](audit-notes.md) and the
[qualified summary](../../experiments/python-gamebub-v97/summary.json).

## Implemented pieces

- [PC preparation](../../host/moonshine/transport97_sender.py) requires an exact
  setup ACK, uses the existing restricted 720×480 JPEG encoder, charges complete
  datagram cost and retains one latest unsent frame. Explicit opaque research
  configuration can packetize frozen custom-codec bytes; it installs no decoder.
- [Python wire codec](../../host/moonshine/protocol97.py) and
  [portable Rust gateway](../../firmware/handheld/src/streaming/protocol97.rs)
  agree on a 40-byte setup/ACK, 12-byte fragment header and 16-byte frame-start
  metadata. Profiles, caps, epochs and core generation are explicit. The normal
  configuration is JPEG only. Legacy MSV1 code and controls remain intact.
- The gateway owns two fixed, four-byte-aligned 1,400-byte stages. Exact logical
  transfer length excludes alignment padding. Query tokens, epoch/generation
  checks and conservative completion debt prevent stale credit inflation.
  Completion releases a stage without inventing FIFO credit. Commit requests
  retain frame ownership until an authoritative matching ingress ACK.
- [FPGA ingress](../../fpga/experiments/cu66-v97-forward/README.md) implements
  an actual 2,048-byte FIFO, two held descriptor slots, CRC/count checks,
  cancellation and a distinct ingress commit. The boundary is synchronous
  parallel commands/DMA, not physical QSPI pins or the existing production core.
- A native C ABI calls the real portable Rust gateway from the C++ Verilator
  bench. Actual RTL free-space and ACK events control Rust progress. The bridge
  maps the separate software/hardware token namespaces and feeds exact bytes
  back to independent payload/CRC checks. An older open-loop trace is retained
  as a control, and the final selected trace uses the current producer source.

`streaming/mod.rs` exports the portable module but its network-worker body is
byte-identical to the baseline. MSV1 remains the default and release firmware
images were not rebuilt or flashed. The existing standalone Moonshine source
is not a Sunshine pairing client; these helpers do not modify the installed
Windows Sunshine server or the separate fork's local edits.

## Reproduction

Dependencies are Python 3.10+ for the protocol helpers, Python with Pillow for
JPEG tests (retained run: Python 3.14/Pillow 13), the installed native Rust
compiler in `gamebub-esp32-dev`, and Verilator 5.020/GCC 13.3 in
`gamebub-cu66-v69-build`. No new toolchain download or board access is required.
The native Rust version is recorded in each receipt. Retained V92 packet inputs
and legacy firmware sources come from baseline
`bd8fcc49c1c6b069432dd1ae93109640359fea8e`.

```sh
/home/lori/gamebub-streaming-prototype/.venv/bin/python scripts/cu66-v97/run_host.py
/home/lori/gamebub-streaming-prototype/.venv/bin/python scripts/cu66-v97/check_host.py
python3 scripts/cu66-v97/run_protocol.py
python3 scripts/cu66-v97/build_ffi.py
python3 - <<'PY'
import json
from pathlib import Path
import subprocess
area = Path('experiments/python-gamebub-v97/protocol')
native = json.loads((area / 'index.json').read_text())
ffi = json.loads((area / 'ffi-index.json').read_text())
subprocess.run(['python3', 'scripts/cu66-v97/run_forward.py',
                '--trace', native['native_trace'],
                '--live-attempt', str(Path(ffi['receipt']).parent)], check=True)
PY
python3 scripts/cu66-v97/summarize.py
python3 scripts/cu66-v97/bundle_manifest.py
```

Use a suitable Pillow-enabled interpreter instead of the local venv path on
another machine. New runs create immutable attempts and preserve failures.
The summary requires selected producer traces, libraries and source hashes to
match; a previously retained PASS does not qualify changed sources. Tests use
finite watchdogs, one RTL build with two compiler jobs, at least 8 GiB available
RAM and low memory pressure. No Docker filesystem scans or cleanup run here.

## Next integration gate

Bind setup to a real FPGA capability probe and epoch installation, implement a
versioned production QSPI/register adapter with actual logical lengths and
ordered status/completion semantics, then integrate the portable receiver into
an opt-in ESP-IDF UDP worker. Retain a blocked datagram before reading later
ones, bound mailbox/staging storage, and pace the PC producer. Measure internal
DMA heap/largest block and task high-water marks with UI, input, audio and Wi-Fi
active. No PSRAM or full compressed-frame allocation is assumed on the ESP32.

Calibrate actual capture/encode/service distributions and loss/reconnect/core
replacement on hardware. Custom profiles still need their supported decoder,
accepted-reference/key recovery and C2/HUD/root/seal/publication path. Renode
was not run; the native bridge is explicitly a host substitute, with no ESP32
CPU, FreeRTOS, Wi-Fi/lwIP or physical DMA timing model. V97's device-integration
and calibration gates, V91l/V92d/V94/V96 integration and both hardware goals
remain open. V100–V110 retain the 7-series physical implementation focus.
