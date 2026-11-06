# DY71 local CSR integration

Owned source: `dy71_local_control.sv`; complete actual-RTL simulation wrapper:
`dy71_platform_sim.sv`. The wrapper binds every actual port of the selected
PIPE system, unchanged stager/arbiter, grouped backend and qualified SDRAM
model. It has no painter/USE_STRIP assumptions or physical RGB-slot alias.

`evidence/control02` passed83typed CSR checks with the real owner and memory:
generation/bounds rejection without side effects, maximum staging length,
immutable packet CRC/readback, an actual early abort/drain, and completed
HUD writes plus actual SDRAM/CSR readback. Five HUD auxiliary requests complete:
two writes, two reads and one rejected noncontiguous write. The model records
16physical write beats and2read bursts. No HUD_RESULT, HUD_DRAIN or SOFTWARE_ACK
is invented. The final post-HUD abort intentionally remains in DRAIN awaiting
the actual native ABORT result, retaining ownership and fencing reuse.

The initial control01failure is preserved: the test wrongly expected fresh
reference/front FID0; frozen RTL specifiesffffffff. Only that oracle changed.

`driver.cpp` supports `--control <original-key-packet>` for these checks. Its
default mode is the same bounded stdin/stdout CSR RPC protocol used by the
sealed v35platform harness, enabling an independently derived v36host harness
with explicit DY71profile selection. Native HU key/P execution is a separate
gate whose result is recorded only when it completes.

Use `scripts/cu66-v71/direct-system/local-control/run.py` with a new output
directory for the actual RTL build/control suite. Use `run_native.py` to bind
the frozen v36source snapshot, actual native endpoint and complete HUD
write/readback algorithm to that exact server executable. All selected source
and model hashes are retained. No network, board build, BIT, flash, serial or
JTAG operation is performed.

See `ABI.md` for exact register/tag ordering, explicit identity, sentinel IDs,
cache-context semantics and the intentionally unmodeled hardware boundaries.


## Actual v36 native integration

`evidence/v36-native01` passed the frozen v36 Rust local algorithm and actual
native C++ HU endpoint through this real CSR/PIPE/grouped/SDRAM implementation.
The explicit DY71 profile accepted and presented the original KEY and P frames,
with zero rejections or LCD underruns. All **42,240 HUD words** were written via
completed hardware requests and read back through actual SDRAM/CSR responses,
then compared word-for-word against native READ_CANDIDATE output. Actual native
PREPARE and COMMIT responses completed; no semantic ACK was synthesized.

The run used 58,394,568 ideal RTL clocks, 787,090 scalar RPC calls, 659,304
model reads and 856,320 model writes. Reported elapsed 583,945 microseconds is
**virtual RTL time only**. Native CPU work does not advance the HDL clock;
`hud_cpu_us=[0,0]` is consequently not a CPU benchmark. This is a correctness
gate, not target latency or 30 fps evidence. The 30-second laboratory watchdog,
eight virtual clocks per CSR access and ideal generated clocks remain disclosed.
The actual target SPI/QSPI transaction/CDC, FreeRTOS locking, vendor PLLs and
board electrical behavior remain untested here.

The compiled server and all frozen v36/native inputs were hash-checked before
and after execution. This proof explicitly selects the frozen PIPE/grouped
manifest, not the subsequently derived board-math successor. The component
source manifest can be reused only with an explicitly compatible DY71 system;
it conveys no board timing or image qualification.
