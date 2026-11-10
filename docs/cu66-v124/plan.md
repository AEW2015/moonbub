# V124: spatial bank-owner qualification and native endpoint parity

V123's fresh 125 MHz route fails at −1.086 ns WNS, −1,709.649 ns TNS and 6,724
setup endpoints. Its new worst is scratch emit-bank selection through parent
owner comparison, readiness and final-tile retirement. Qualified Source B100
remains unchanged. This iteration targets that actual cone and advances the
endpoint-harness boundary with production serializer/parser code.

## Bounded RTL timing experiment

Change only the coefficients-controller origin relative to frozen V123. Compare
both raw bank epochs/full16 block tags against the expected full32/full16 owner
in parallel, then select one match bit by emit-bank. Non-tile output retains
the original scalar equation. Apply the exact same match to ready, valid and
DISPATCH bad-owner error 67 without changing other gates or priority. Invalid,
unready and child-invalid cycles must remain exact; do not gate a lane by
bank-ready or assume matching metadata. No register, public cycle, owner,
physical credit or interface is added.

The two scalar lane-result bits use an explicitly scoped KEEP attribute to
retain the intended comparison boundary. This is a new RTL synthesis hint
relative to V123, not a timing exception or a claim of placement. No DONT_TOUCH,
physical placement or broad synthesis-directive change is authorized by this
experiment. The fixed V120 Tcl/XDC implementation recipe remains byte-identical;
actual routed global/family results decide whether the trial helps.

Require focused whole-controller generic and real-packet tests, then fresh full
decoder/actual V97 transport, physical-debt peer and byte/row parent tests. Retain
all original assertions, goldens, error ordering and accepted-debt/drain oracles.
Compare all public cycles and raw streams directly to V123. Source, packaging,
proof scripts and plans freeze before execution; keep failed attempts.

After a complete source-bound functional PASS and independent audit, run fresh
8 ns RTL synthesis/place/route on xc7a100tcsg324-1 with pinned Vivado 2026.1.
No clock relaxation, guessed board I/O delays, false/multicycle paths or
checkpoint-based implementation. A positive complete internal timing result
requires a separate same-source/tool/core-recipe fresh repeat. A negative source
is not rerouted unchanged as qualification. Read-only matched checkpoint queries
retain explicit gaps and observe owner/ready, RAW, admission and refill families.

## Actual native endpoint boundary

Compile the sibling Sunshine fork's actual MSV1 C++ packetizer and Moonbub's
actual firmware Rust protocol receiver unchanged, with source/Git/image/compiler
provenance. Feed C++ datagrams directly into Rust; retain the original JPEG and
shared packet fixture for byte comparison, plus fault/recovery cases. This
replaces a Python-generated producer at that seam. It is a portable native
serializer/parser test, not full Sunshine capture/encoding, the firmware session
worker, ESP-IDF, CPU emulation, DMA, Wi-Fi, QSPI or custom CS88 deployment.
Do not interrupt an installed Sunshine instance or modify either production
endpoint source. Any remaining full endpoint/RTL single-timebase integration,
service calibration and custom-profile negotiation are explicitly open.

## System and preservation gates

The unchanged row fixtures remain 1,145,104/1,553,197 post-input→validated-commit
cycles until an actual changed parent measures otherwise. At an assumed complete
parent 125 MHz, stalled decode projects to 12.425576 ms and still needs 303,198 fewer
cycles for strict <10 ms. Complete-parent/board timing, physical ESP32/Wi-Fi/QSPI,
memory/scanout/CDC, sustained distinct hardware 30 fps and validated hardware <10 ms
remain separate goals. No board programming or complete board bitstream here.

At most two heavy jobs globally, each 2 CPUs/8 GiB RAM and 8 GiB RAM-plus-swap;
available RAM/full-memory PSI are the primary gates, combined utilization the
secondary gate, with finite watchdogs. No new swap. Preserve all original 18
Source B files, old proofs/receipts and unrelated marker SHA/size/mtime.
