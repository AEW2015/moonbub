# Iteration 17: bank-local refresh, bounded pacing and scanline service

This iteration advances a codec designed for the host–ESP32–FPGA split. It keeps
720×480 coded / 720×405 active game content and 30 scheduled source IDs/s. The
three Python studies address different layers: actual codec/reference behavior,
prospective transport admission, and conditional memory/scanout scheduling.
They are not one integrated end-to-end simulation or physical 30 fps proof.

## AR03: refresh one bank while confirmed work continues

The [bank-local refresh study](../experiments/python-game-local-refresh-study/README.md)
implements real AR03/AF03 version-3 packets. Independent keys replace bank 0 only;
confirmed bank 1 remains available while bank 0 drains or waits for publication.
Only destination-bank readers/consumers block a writer, with one publication
writer and three bounded sender transactions. New default prediction uses the
newest acknowledged bank. Geometry is fixed for the admitted/published epoch.
A lost key ACK invalidates bank 0 without destroying a confirmed bank 1.

GM01/SR01 coding, full 49,152-byte cap, exact display patches and canonical YUV
reference tags remain. AF03 binds the actual outer body CRC and published bank/
frame/tag. Receiver publication is private until validated completion. UI never
enters YUV prediction. Expiry/deadline wins over paid staged ACK/decode work.
Old AR02 peers reject AR03; no installed Sunshine/ESP32/FPGA peer implements it.

Four native runs use the same 180 distinct precompressed regression source frames
as v16. There are also two 64-frame synthetic loss cases: 848 capture events total,
37 source snapshots, 25 passing tests and 82.56 seconds of host wall execution.

| Native profile | Strict / eventual presentations | Distinct IDs in [500,5500) ms | Maximum in-window gap ms |
| --- | ---: | ---: | ---: |
| AR02 global refresh-30 | 159 / 161 | 133 | 116.667 |
| AR03 bank-local refresh-30 | 176 / 178 | 151 | 66.667 |
| AR03 local repeat | 176 / 178 | 151 | 66.667 |
| AR03 initial-only | 174 / 177 | 149 | 66.667 |

The local repeat has the same complete packet hashes and presented source IDs;
remeasured costs yield different exact presentation timestamps. Its only drops
are startup IDs 1 and 2. Each of five refresh keys permits two actual bank-1 P
frames while the key remains pending. All decoded native frames preserve all
21,120 selected original RGB565 UI words, with zero mismatch.

**151 IDs in five seconds is a rolling-window phase/catch-up count, not a >30 fps
capture rate.** Input remains 30 IDs/s. Two-frame presentation gaps remain, and
no long-run margin or perfectly spaced 30 fps is established. Maximum presented
age falls from 133.333 to 116.667 ms. The same quantization maps are used; source
RGB565 MSE means are 13.9856 global and 13.9866 local. On common decoded IDs local
MSE differs by −0.01392, but key IDs and reference histories differ. This is not
a lossless or causal quality-improvement claim. Wire bytes rise as 17 additional
frames are delivered, so no net-wire compression saving is asserted.

The synthetic loss cases establish ownership/retry behavior, not gameplay FPS:
flat quantized content has only ten distinct decoded hashes in their diagnostic
windows. The new codec is a state/refresh optimization, not HEVC/AV1 compatibility.

## Pacing: prevent overflow without hiding dropped source IDs

The [paced gateway study](../experiments/python-game-paced-gateway-study/README.md)
replaces v16's implicit unbounded producer backlog with one active frame plus one
latest pending candidate, complete-body admission, six consumed-packet credits
and one reserved control query. Data and queries share modeled worker/forward-
link service; replies consume reverse-link service. Reply-construction CPU work
is not separately modeled. Fixed-size ledgers bind session/slot/sequence; stale replies
cannot release reused tokens. Lost credit feedback can recover through an actual
bounded query; total feedback loss stops with ownership retained.

Credit identity is not free. A prospective 16-byte extension makes the header
56 bytes and reduces payload to 1,008 bytes, preserving the 1,064-byte maximum
UDP datagram within the existing 1,065-byte DMA allocation. These fields are not
a serialized/authenticated implementation. Current firmware remains ordered
MSV1 JPEG; its compiled six-packet mailbox and source-shaped CPU/QSPI costs are
constraints/assumptions, not calibrated ESP32 execution or real RF emulation.

| Initial-only size workload: 177 supplied bodies / 180 capture IDs | Strict / eventual gateway completion | Source candidates dropped | Maximum age ms |
| --- | ---: | ---: | ---: |
| Paced, no aggregation | 175 / 176 | 1 | 68.367 |
| Two-ms delivery aggregation | 175 / 176 | 1 | 65.427 |
| Eight-ms delivery aggregation | 141 / 142 | 35 | 90.308 |
| Twenty-ms feedback latency | 42 / 43 | 134 | 77.570 |

All 36 cases have zero modeled mailbox overflow; this trades admission/throughput
for bounded occupancy. Feedback blackhole cases intentionally retain unresolved
credits instead of inventing permits or claiming successful drain. A corrected
long-delay boundary test prevents unresolved-drop timestamps beyond the declared
horizon. Eleven tests and fourteen source snapshots pass retained replay.

For sixty maximum-body candidates, the controller accepts/completes 35 and drops
25, keeping observed age below 79 ms. That is not 30 fps. New framing needs
12.78432 Mb/s at 30 maximum-size bodies/s, before reverse credits/Wi-Fi overhead.
An assumed 8 Mb/s link cannot carry that average load.

These are **opaque encoded-size traces, not decoder-valid replay**. Dropping an
already encoded key/promotion can invalidate later P references. Live integration
must gate codec candidate commit, protect reference publications or apply safe
expiry/fallback, and distinguish consumed-packet credits from decoded-reference
AF03 ACKs. No such integrated controller is implemented. Separate forward/reverse
virtual links do not prove shared Wi-Fi airtime or native CPU/heap/DMA behavior.

## Memory: frame-pointer rate is not clean video

The [streaming memory study](../experiments/python-game-streaming-memory-study/README.md)
adds bounded burst arbitration, refresh, row changes, read/write turnaround,
nonpreemptible stalls and a finite line-prefetch FIFO. It uses three retained
native coefficient/traffic templates repeatedly: model IDs are not distinct
rendered gameplay or a valid AR03 dependency replay. It does not decode pixels.

The baseline explicitly charges full coefficient-scratch writes/reads omitted
from v16's traffic estimate. The conditional streaming path uses bounded stripe
buffers and inline canonical hashing; SHA compute remains charged. Entropy bytes
are apportioned to stripes from offline coefficient counts, so this is not an
implemented CP02 parser or proof of its causal release/stall behavior. Both pay
reference, reconstruction, color, packet and 800×480 RGB565/60 Hz scanout traffic.
Capacity includes private reconstruction, two reference banks, two ingress slots,
three panel buffers and local staging rather than hiding temporary storage.

Prefetch chooses only an already-complete framebuffer and freezes its buffer/
model-ID identity for the entire panel epoch. Accepted reads pin old storage;
no old-front row is relabeled as a new image. The early prefetch-commit boundary
is separate from actual epoch start and completion. Clean epochs require all
480 line deadlines and consistent buffer/model identity. Untimed boundary
reconciliation separately reports strict epoch-start versus full-epoch-finish
counts; partial epochs after the horizon cannot become complete evidence.

The retained cases show why both metrics matter:

| Memory service case | Logical model IDs/s | IDs/s with a complete clean panel appearance | Line misses |
| --- | ---: | ---: | ---: |
| Nominal full-scratch baseline | 12 | 12 | 0 |
| Nominal conditional streaming | 20 | 20 | 0 |
| Hypothetical fast baseline | 26 | 26 | 0 |
| Hypothetical fast streaming | 30 | 30 | 0 |
| Fast streaming, four FIFO lines, 200 µs stalls | 30 | 0 | 3,689 |
| Same stall case, eight FIFO lines | 30 | 30 | 0 |

The fast scenario assumes read8/write8 burst service, sixteen MAC issue lanes,
eight entropy bits/cycle and four sample/paired-chroma positions/cycle at 100 MHz.
Nominal uses read15/write13, eight MAC lanes, four entropy bits/cycle and two
sample positions/cycle. The line geometry here is 800×480 landscape-equivalent;
the baseline documents 480×800 physical scanout. Equal frame bytes do not imply
equal line deadlines or FIFO coverage. Re-run the fitted raster/blanking before
choosing a hardware FIFO depth. These are conditional settings, not fitted DDR/DSP/clock
measurements. The 200 µs stall repeats every millisecond. Four phase sweeps show
that alignment also matters; the same aggregate workload can have a line miss.

All displayed rates use interior epoch windows; strict startup and drain counts
are separate. In fast streaming, 29 logical starts and 29 complete clean panel
appearances finish strictly before the one-second capture endpoint; all 30 finish
within drain. Both start-based and finish-based [250,750) ms windows contain 15
model IDs. No future epoch chosen during early prefetch is counted as already
visible. “Clean” means modeled row timing and consistent framebuffer/model-ID,
not image correctness or distinct decoded gameplay.

External allocation falls 4,997,120→3,959,808 bytes, while local allocation grows
82,624→88,384 bytes (94,784 with eight FIFO lines). Coefficient/prediction/output
stripes, bounded parser/tag passes, color-pair buffers and UI words are included.
The assumed implemented external window is 8 MiB; the current 2 MiB functional
window is rejected. Neither allocated bytes nor issue lanes establish BRAM
packing, board addressability, actual bus service or timing closure.

The study retains eight main cases, four phase cases, 28 source snapshots and
12 passing tests: nine frozen model guards plus three supplemental epoch-boundary
guards. Its untimed reconciliation is bound to result/analyzer hashes. Full
replay takes roughly 35 seconds on this host; that Python run duration is not
hardware service time or a claimed speedup.

## Progress toward an application-specific implementation

The target architecture has two different feedback contracts:

```mermaid
flowchart LR
  A[Source and bounded candidate work] --> B[Transport admission then codec commit]
  B --> C[AR03 packets and paced datagrams]
  C --> D[ESP32 bounded forwarding]
  D --> E[FPGA parse and private reconstruction]
  E --> F[Validated bank and framebuffer publication]
  F --> G[Epoch-tagged scanout]
  D -->|consumed packet credits| C
  F -->|content-bound AF03 publication ACK| B
```

This diagram is the integration target; the studies above remain separate.
The next work is concrete:

1. Split AR03 expensive candidate construction from stateful commit. Bind the
   candidate to current bank identities/generation; transport rejection must not
   reserve a bank or consume codec identity. Charge rejected work. Then integrate
   bounded pacing with real encoded packets and decode them after loss/admission.
2. Export AR03 golden/negative vectors and implement the negotiated forwarding
   contract. Keep packet consumption, physical drain and reference publication
   distinct; test feedback loss, session reset, reordering and timeout races.
3. Drive memory/compute releases from those actual AR03 packet/reference traces,
   then verify bounded integer stripe reconstruction against stored pixel/YUV
   oracles. Preserve late-error cancellation, canonical hash order and ownership.
4. Calibrate ESP32 packet/CRC/driver service, Wi-Fi batching/RTT, DMA/internal heap,
   stack and FIFO behavior on remote hardware. A small credit window is sensitive
   to RTT; increasing it requires measured queue/RAM capacity, not fictitious RAM.
5. Qualify mapped SDRAM ranges, arbiter/line-watermark timing, resource fit and
   actual clocks. Keep a larger framebuffer pool explicit; the 2 MiB functional
   model window is not the board's advertised total physical memory.
6. Validate on fresh gameplay and longer runs. Report unique displayed IDs,
   timing gaps, quality/UI coverage, complete wire bytes, losses and clean scanout
   together. Reused regression footage and a nominal assumption sweep cannot
   establish production or physical 30 fps.

## Reproduction

The three studies record 48 passing tests; six independent audit guards bring
the total to **54**, with 79 conservative source/dependency snapshot bindings.

`python experiments/verify_prototype_v17.py` checks the source-inventoried retained
snapshot, each study verifier, untimed analyses and independent audit. Use the
project NumPy/Pillow/PyAV environment. It replays conditional models rather than
measuring hardware or regenerating timed codec performance. Source/dependency
pins include conservative ancestry and are not counts of exclusively executed
files. External media are hash-checked if present and otherwise reported missing.
The matching Moonbub and Sunshine branch is `handoff/gamebub-app-codec-v17-20261103`;
older branches remain frozen.
