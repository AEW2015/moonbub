# AR03/AF03 bank-local independent refresh

This Python prototype changes reference ownership rather than reducing resolution
or quantization quality. The canvas is 720×480, with 720×405 native game content,
30 scheduled IDs/s and the same four exact original-RGB565 UI patches.

## Protocol change

AR03 and AF03 use version 3 and the same 65-byte/43-byte envelope layouts as
AR02/AF02. GM01/SR01 inner coding, complete 49,152-byte cap, patch lengths/CRCs,
canonical YUV tags and content-bound feedback are unchanged. Old peers reject
AR03/AF03, and the new profile rejects AR02/AF02. This is an experimental dialect,
not an installed Sunshine/ESP32/FPGA mode or a standard Moonlight codec.

An independent key now replaces **bank 0 only**. It waits for bank-0 readers and
pending bank-0 consumers, while confirmed bank-1 work can continue. A promoted P
still replaces bank 1. Only one publication writer can be pending at a time;
ordinary frames may use the other confirmed bank within the three-frame credit
limit. No unconfirmed bank, future pixel, ACK prediction or fake free work is used.

When refresh is due and bank 0 is draining/reserved, the finite scheduler explicitly
uses bank 1 for ordinary P frames and stops adding bank-0 readers. Once the new
key is acknowledged, default prediction chooses the newest confirmed bank by
frame ID. Thus old bank 1 is retained for continuity without being preferred over
a newer confirmed independent key. Promotion can subsequently replace bank 1.

Prepare reserves only its destination; ACK/expiry changes only that bank. Lost
key feedback leaves bank 0 unusable, preserving a confirmed bank 1 and permitting
a later independent retry. AF03 still binds the outer body CRC and exact stored
bank/frame/tag. Receiver completion publishes only its destination; unrelated
read leases remain valid. Every UI patch is fully validated before any lease or
publication. CRC and tags are identity checks, not authentication.

Geometry is fixed after the sender's first admitted frame and receiver's first
published frame, even if sender banks later expire. Rejected candidates do not
lock geometry. Change dimensions through a freshly negotiated epoch/session.
The finite model stages geometry along with bank publication through paid work.

## Measured finite results

Four native runs use the same previously used 180 distinct source IDs at four
seconds of the Mass Effect clip. This is regression material, not new held-out
validation. Two further 64-frame synthetic cases inject refresh chunk/ACK loss.

| Profile | Strict / eventual presentations | Unique source/decoded IDs in [500,5500) ms | Diagnostic IDs/s |
| --- | ---: | ---: | ---: |
| Frozen AR02 global refresh every 30 | 159 / 161 | 133 | 26.6 |
| AR03 local refresh every 30 | 176 / 178 | 151 | 30.2 |
| AR03 local refresh repeat | 176 / 178 | 151 | 30.2 |
| AR03 initial independent key only | 174 / 177 | 149 | 29.8 |

**30.2 is a rolling-window phase/catch-up count under 30 scheduled IDs/s.** It is
not a new capture rate or a sustained >30 fps result. Local refresh drops only
startup IDs 1 and 2. Its repeat has the same complete packet hashes and presented
source IDs, but remeasured costs yield different exact presentation times.
The largest in-window presentation gap is still **66.667 ms**, versus 116.667 ms
for global refresh; it is not perfectly spaced 30 fps. Maximum presented age is
116.667 ms local versus 133.333 ms global. Long-run timing margin remains open.

Local keys are IDs 0,30,60,90,120,150; global keys are 0,31,62,93,124,155. For each
of the five local refresh keys, two following bank-1 P frames are prepared while
the key writer remains pending. This is actual coded bank-1 continuity, not a
scheduler-only hypothetical. Every decoded native frame selects all 21,120
original RGB565 UI words with zero mismatch.

Mean preparation is 29.855 ms global, 30.067 ms local and 29.749 ms local repeat.
Source active RGB565 MSE means are 13.9856 global and 13.9866 local. On common
decoded IDs, local MSE is lower by 0.01392; histories/key IDs differ, so this is
not a same-output/lossless or causal quality-improvement claim. Quantization maps
and exact-UI coverage remain fixed. Wire bytes increase 3,786,275→4,158,821 as
more frames are delivered; this is not a net-wire compression saving.

Synthetic ACK-loss delivers 64/64 IDs; chunk-loss delivers 63/64. Their quantized
flat images contain only ten distinct decoded hashes in the diagnostic window.
These cases test ownership/recovery, not distinct gameplay FPS.

## Evidence and checks

The campaign has six cases, 848 capture events, 37 source snapshot bindings and
82.56 seconds of host wall time. Sources are pinned before execution and checked
afterward. `analyze.py --check` is an explicitly untimed supplement bound to both
the result and analyzer hashes; it rederives IDs, exact coverage, timing gaps,
continuity, repeat equivalence and matched-ID quality. Full packet bytes are
actually encoded/decoded in the run; this report is not a native implementation.

All **25 tests pass**: initial AR02-equivalent reconstruction; legacy rejection;
key/P/promotion and explicit bank choice; only-destination read ownership;
key ACK loss/expiry/stale ACK; exact cap-before-commit and geometry lifetime;
abort/retry; finite continuity/lost-key retry; and inherited late-publication,
expiry, conflicting-feedback, overload and physical-drain regressions.

```sh
python verify.py
python analyze.py --check
python -m unittest discover -s . -p 'test_*.py' -v
```

Use the project NumPy/Pillow/PyAV environment. `benchmark.py` regenerates timings
and overwrites evidence; the above checks preserve this snapshot. `local_codec.py`
is an explicit copy/variant of frozen v15 `unified_codec.py`; `model.py` copies the
v16 refresh scheduler and retains paid staged ACK/decode/expiry semantics. No
older source, firmware or bitstream is modified.

Host stages are remeasured Python wall time on independent serialized virtual
servers. Links at 8 Mb/s, QSPI160 Mb/s, feedback10 ms and vblank60 Hz are assumed.
Offline precompressed 29.88 fps RGB is hypothetically scheduled at 30 IDs/s;
actual BOX scaling is charged, acquisition is not. The model has three sender
transactions, two actual GF ingress buffers, two retained reference banks and
three display roles, with scratch/cache/output/copies extra. It does not jointly
execute ESP32 firmware, bounded SDRAM/scanline service or native shared CPUs.
The separate pacing/memory studies cannot be added arithmetically to this result.
No physical 30 fps, fitted resources or production recovery proof is supplied.

Next export AR03 golden/negative vectors and integrate real gateway admission
before encoder prepare. Keep packet-consumption credits distinct from reference
publication ACKs, then connect measured memory/decoder/gateway service to this
state machine and test a fresh corpus plus longer loss/refresh runs.
