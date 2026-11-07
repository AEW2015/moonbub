# V99 RC1: fresh input, exact native decoding and a bounded hardware handoff

V99 now has an actual fresh-RGB encoder, independent native reconstruction,
and an RTL-facing **CS88/all-BR88 q16 research candidate**. This closes V98's
missing current-codec encoder lane. The candidate's complete packet bytes,
canonical pixels, exact fixed HUD patches and displayed RGB565 have executable
goldens. [Results](results.md), the [candidate contract](candidate-contract.md)
and [hardware/software handoff](hardware-handoff.md) define the boundary.

The research candidate is frozen; **V99 product promotion remains open**.
This branch does not install a custom firmware/bitstream, connect the complete
RTL display path, demonstrate physical 30 fps or validate FPGA decoding under
10 ms. The Python sender is not real-time. Retain the existing JPEG/MSV1 image
as the production fallback.

## What is selected

The [profile JSON](../../experiments/python-gamebub-v99/profile.json) specifies
720×480, zero base motion, block size 32, all-BR88 residuals, key map method 0,
P grouped-map method 3, QM87 run method 2/inherited method 6, uniform quantizer
16 and a 49,152-byte complete packet cap. These choices match the existing V91
parser's documented subset. Native support for a wider CS88 grammar does not
make that wider grammar an RTL capability.

All 120 q16 frames in four complete short histories fit the packet cap. The
upstream CU66/GU66 arithmetic profile remains a software control, independently
decoded through unchanged v69 code. CS88's C2 content tree/seal and words-only
HUD digest differ from CU66's canonical tag and geometry/rectangle/HUD digest.
Neither format is installed by the current active ESP32 worker or JPEG core.
No existing MB97 opaque profile number is reassigned to CS88.

## Rebuild the software experiments

Python needs NumPy, Pillow, PyAV and imageio-ffmpeg at the retained V98 versions.
The tested interpreter is
`/home/lori/gamebub-streaming-prototype/.venv/bin/python`. Native code uses
C++17; the retained Linux environment has GCC 13.3. Existing scripts compile
the helper/receiver with warnings treated as errors in
`gamebub-cu66-v69-build`. Its repository bind must expose the same absolute
checkout path and its `/build` directory must be writable. Use `--container`
to select an equivalently prepared environment. The native runner can also
use a host `g++` when available. No build directory or compiler binary needs
to be tracked in Git; receipts pin tool versions, source and binary hashes.

From the repository root, choose new output directories rather than overwriting
the retained attempts:

```sh
python scripts/cu66-v99/run_fresh.py
python scripts/cu66-v99/validate.py
python scripts/cu66-v99/audit_fresh.py
python scripts/cu66-v99/run_native.py --ledger /path/to/new/accepted-ledger.jsonl --output /path/to/new/native-attempt
python scripts/cu66-v99/run_cs88.py --fresh-index experiments/python-gamebub-v99/fresh/index.json --profile v91-group3 --output /path/to/new/cs88-attempt
python scripts/cu66-v99/run_direct.py --control-report /path/to/new/cs88-attempt/results.json --output /path/to/new/direct-attempt --synthetic32
```

Use `--help` on the independent native, CS88 and direct auditors to point them
at a new attempt. `freeze.py` intentionally verifies the specific retained
checkpoint; selecting new evidence requires updating those selections under
review. `bundle_manifest.py` packages and verifies the exact handoff scope.
In CS88 attempt directories, `receipt.json` is the initial launch snapshot;
its initial `FAIL` default is not a final verdict. Use the indexed, hash-bound
`results.json` and independent audit as the authoritative terminal result.
The retained V98 NPZ inputs are sufficient to regenerate this experiment;
the external videos need not be copied into the container. Their source
compression and native/selected cadence remain recorded in V98's manifest.

The resource gate uses available RAM and memory pressure, not swap occupancy:
at least 8 GiB available and PSI memory full avg10 below 1 before heavy work.
Keep at most two compiler/codec jobs active on this shared host. This work
does not require Docker pruning, image scans, firmware flashing or a connected
Game Bub.

## Evidence and boundaries

The four source sequences contain 120 frame identities and 109 per-clip unique
RGB hashes. They remain compressed-source video or generated content, rather
than independent raw gameplay captures. Re-encoding them at multiple settings
does not enlarge distinct source coverage. The extra 32-frame synthetic control
checks keys 0/30 and P31 referencing 30; it is not a frame-rate qualification.

The bounded RTL-facing bundle supplies a fresh key/P pair from the new user
video and a late-CRC rejection fixture, signed dequant/residual goldens, source
pins and existing testbench-contract notes. **Those new vectors were not run
through RTL in this iteration.** The exact native coefficient reader and
pixel reconstruction audits are separate software evidence.

Original held-out captures, perceptual/HUD checks, native host acceleration,
ESP32 resource/service calibration, complete live RTL/HUD/C2/shared-display
integration, physical memory fit and routed timing remain prerequisites.
V100–V110 retain the requested 7-series mapping/P&R/timing focus, with the
remaining complete-path endpoints explicitly identified.
