# Finite-buffer delivery and ownership study

This extends the earlier [ideal queue model](../python-codec-study/README.md)
with finite compressed slots and framebuffer ownership. It is a deterministic
Python event/architecture model, not ESP32 execution, RF simulation, memory
controller verification or a claim of physical 30 fps.

## Run

Standard-library Python 3.10+ is sufficient:

```sh
cd experiments/python-delivery-study
python3 -m unittest -v test_model.py
python3 run.py
```

`tests.log` records 12 passing tests. `results.json` binds `model.py`, the tests,
driver and input result artifact by SHA-256; it includes 44 scenario summaries
and detailed event traces for a normal and overloaded combat case. Every case
retains presented IDs and dropped IDs grouped by reason. `run.log` records
the concise scenario output. Regeneration replaces these files, so preserve
previous artifacts if comparing implementations.

The input is the prior codec study's `jpeg-budget8` sizes: 60 decoded frames
from each short, already-compressed Mass Effect video. The driver repeats each
60-element **size trace** 30 times to create 1,800 scheduled inputs. It does
not encode/decode 1,800 fresh game images or manufacture a native 30 fps video.
The combat source's selected 60 images include only 32 unique canvases; the
second clip has 60 unique canvases. Source hashes/PTS are retained in the input
manifest. No additional hardware, codec quality or gameplay evidence comes
from repetition. Presentation counts concern distinct simulated frame IDs.

## Explicit finite ownership

```text
capture + assumed preparation delay
  → one replaceable host waiting image
  → one nonpreemptive network transfer, with a receiver slot reserved
  → finite slot-owned QSPI wait/transfer
  → finite slot-owned decoder wait/reconstruction
  → latest pending framebuffer → immutable front at vblank
```

The default model has two compressed slots, each allowing 49,152 payload
bytes. It reserves a whole slot before starting network transmission; a
full receiver applies immediate abstract backpressure to network admission.
The reserved slot stays owned through network delivery, QSPI and decoder
completion. It is freed at completed reconstruction or explicit rejection,
never on mere network receipt. Allocation traces and assertions enforce no
reuse while in flight. Metadata, packet assembly scratch and padding are not
charged to these logical slots; full-design BRAM/SDRAM packing remains open.

There is one active network transfer, one active QSPI transfer and one active
decoder. These overlap, but each individual stage serializes its work. The
waiting image at the host can replace an older waiting image; a transfer
already started cannot be preempted. Complete frames over the cap are rejected
before allocating a slot. Stale work is rejected before transmission. Seeded
ready-time jitter can reorder host arrivals; older IDs are rejected instead
of regressing the displayed sequence. Queue counts are bounded by slot count.

Three RGB565 framebuffer roles are modeled: immutable front, latest pending,
and reconstruction back. A buffer becomes reusable only after all of its
roles clear. An optional reconstructed reference role and read pin keep the
exact temporal predecessor alive while it is read. Decoder completion updates
the committed reference independently of presentation. Replacing a pending
frame does not mutate the front; vblank transfers front ownership atomically.
The optional reference chain rejects dependent frames after a missing
predecessor until a subsequent independent frame arrives. No guessed reference
or automatic temporal healing is allowed. Two-framebuffer scenarios use the
same ownership rules and wait for a free back buffer when necessary.

These roles are a Python oracle. They do not compute/check pixel CRCs, implement
CDC, physical write-drain acknowledgments or a production feedback protocol.
Three 720×480 RGB565 buffers alone require 2,073,600 bytes; the simulator does
not validate their physical addresses alongside compressed storage or existing
reserved regions. References name frame IDs, not validated memory pointers.

## Timing assumptions and windows

* Default capture schedule: 30 inputs/s for 60 seconds. Preparation delay is
  an assumed 2 ms, not measured capture/encode time. It is a fixed latency per
  input rather than a serialized host CPU model; it must not be used to claim
  an overloaded encoder meets cadence.
* Network rates: ideal 8/12 Mb/s, with 4 Mb/s overload. Wire accounting is
  payload plus 40 assumed application and 28 IPv4/UDP bytes per 1,024-byte
  chunk. Link-layer/RF overhead, contention, retransmission, audio and input
  traffic are excluded. Link-stall scenarios pause serialization without
  deleting the remaining service time.
* QSPI: assumed 160 or 40 Mb/s payload service, no command/turnaround/CDC cost.
  These are scenario values, not measured ESP32 concurrent Wi-Fi/QSPI rates.
* Decoder/reconstruction: assumed 8, 20 or 40 ms fixed service per accepted
  image. No JPEG entropy/IDCT/SDRAM transaction stream is executed. Memory
  contention, line FIFOs and arithmetic must be measured or composed into a
  future model. Do not add/subtract the independent memory study's timings to
  claim this is one qualified pipeline.
* Refresh: hypothetical 60 or 65.076 Hz, with atomic next-vblank ownership.
  Actual panel clocks/raster/blanking are unqualified here. A decoder completion
  exactly on a vblank is available for that vblank; completion events are
  processed first at equal timestamps. At most one pending frame is presented.
* Credit return has zero control latency and no bytes charged. Real firmware
  needs credits/ACKs, bounded retry, session reconciliation and feedback timing.
  Perfect instantaneous credit visibility is an optimistic assumption.

Windows were declared before inspecting the results: strict capture window
`[0, 60000)` ms, steady window `[5000, 55000)` ms, then 2,000 ms drain. The
steady window is a separate latency-accommodated observation, not a shifted
replacement for the failed strict count. All exact endpoints are excluded.
Report both. A successful steady rate does not turn 1,799 strict-window frames
into 1,800 or establish physical display/capture-to-photon performance.

## Results

Both size traces behave alike under the baseline: 1,800/1,800 reconstructed
and eventually presented, 1,799 inside the strict 60-second window, and
1,500 IDs presented in the predeclared 50-second steady window (**30.0 fps**).
There are no modeled drops; p95 age is 50 ms with the assumed 2 ms preparation,
8 Mb/s network, 160 Mb/s QSPI and 8 ms decode service. Occupancy remains within
two compressed slots and three framebuffer allocations.

| Scenario | Combat steady ID rate | Second-clip steady ID rate | Interpretation |
| --- | ---: | ---: | --- |
| Baseline, 8 Mb/s / decode 8 ms | 30.0 fps | 30.0 fps | Conditional capacity/ownership pass; strict count remains 1,799 |
| Decode 20 ms, other baseline inputs | 30.0 fps | 30.0 fps | More age; assumed decode still below source period |
| Decode 40 ms | 25.0 fps | 25.0 fps | Decoder capacity limits rate despite faster network |
| One compressed slot | 26.5 fps | 30.0 fps | Combat transfer + decode serialization needs overlap |
| Two framebuffers | 30.0 fps | 30.0 fps | Enough for this schedule; not a universal ownership proof |
| 100 ms link pause every 10 s | 29.8 fps | 29.8 fps | Ten old host frames replaced; subsequent frames recover |
| 4 Mb/s network | 17.62 fps | 22.2 fps | More buffering cannot fix an undersized sustained link |
| 17 lost independent frames | 29.7 fps | 29.7 fps | Subsequent independent JPEG frames remain decodable |
| Same losses with synthetic predecessor chain | 24.0 fps | 24.0 fps | 313 additional reference rejections until refreshes |

The temporal-loss comparison uses the **same JPEG size trace** with hypothetical
dependencies and an independent frame every 30 IDs; it is a protocol stress
case, not an encoded temporal video measurement. Actual temporal independent
frame peaks from the codec study can be much larger and must be modeled too.

Increasing the slot cap to 256 KiB does not change these baseline results:
every selected JPEG already fits 48 KiB. A 100 ms link pause and 40 ms
ready-time jitter have counted losses; they are not hidden successes. Higher
network rate can reduce age, but decode 40 ms still limits output to 25 fps.

## Tests and next qualification

### Capture-phase and jitter sweep

Run `python3 phase_sweep.py` to reproduce `phase-results.json`. It tests 128
declared combinations: two cyclic JPEG traces, 60/65.076 Hz hypothetical
scanout, capture phases 0/4/8/12/16/20/24/28 ms, assumed decode 8/20 ms and
seeded ready jitter 0/4 ms. Each uses 1,800 inputs and the same fixed windows.
No previously declared window is moved to improve a verdict.

No frame IDs drop in this sweep, and all 1,800 eventually present in every
case. Steady-window counts vary from 1,499 to 1,501 (29.98–30.02 IDs/s).
One case fails the declared count target of 1,500: combat, 60 Hz, phase8 ms,
decode8 ms and ready jitter4 ms. It remains a failed window criterion despite
eventual conservation. Other cases above the count do not cancel it out.

Even assumed decode8 ms has worst-case p95 age59.33 ms across these cases;
decode20 ms reaches72 ms. Maximum steady presentation gap is50 ms. A nominal
steady average near30 therefore does not prove a universal30 fps count,
uniform cadence or sub50 ms latency. These are modeled stage-to-vblank ages,
with no panel/optical response and the previously stated timing assumptions.

### Remaining validation

Tests check half-open endpoints, exact stall-service accounting, allocation
acquire/release balance, bounded overload, lost-reference rejection/recovery,
cap boundaries, immutable-front operation with only two framebuffers, jittered
ID order and recovery after a link pause. Invalid rates, clocks, storage,
overlapping stalls and references fail validation. Assertions run through every
scenario to check role/owner constraints and unique increasing presented IDs.

The actionable software-model result is to preserve two bounded compressed
slots for overlap and independent JPEG refresh, while measuring actual
decode/reconstruction and concurrent link service. Before a hardware claim,
replace optimistic timing/credit assumptions with observed traces, add finite
packet reassembly/CRC and memory service, bind firmware/bitstream versions,
and correlate actual presented IDs and optical/clock-qualified latency.
