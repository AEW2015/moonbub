# Bank-specific overlap with unchanged AR01/AF01

The first recent-reference prototype drains **all** pending frames before promoting
a reconstructed P reference, then blocks all preparation until its ACK. This can
save bytes while reducing delivered cadence. This experiment changes that
scheduling restriction without changing AR01 frames, AF01 feedback or reconstruction.
The target remains 720×480 coded / 720×405 native active content and 30 fps.

## Policy and safety contract

Bank 0 remains the acknowledged immutable key; bank 1 is the acknowledged recent
reconstruction. A new promotion needs a free transaction credit, no other writer,
no outstanding bank-1 consumers and no bank-1 read leases. Pending bank-0 frames
and bank-0 read leases do not block a bank-1 writer. The promotion still computes
and hashes its reconstructed candidate as paid sender work, reserves bank 1 and
waits for exact AF01 publication acknowledgment before bank 1 is selectable.

While old bank-1 consumers drain, the controller stops admitting additional bank-1
consumers and instead encodes ordinary P frames from confirmed bank 0. It also
uses bank 0 while a promotion ACK is pending or uncertain. This prevents new recent-
bank consumers from perpetually extending the drain barrier. When an exact ACK
arrives, future frames may use the new bank 1. A lost ACK never permits reuse of
an old bank-1 ID that the receiver might have overwritten; bank-0 continuity and
a later safe promotion remain possible. Full key changes still drain all pending
transactions and leases.

`overlap_codec.Encoder` subclasses the frozen recent-reference encoder. Its
`prepare(..., reference_bank=None|0|1)` copies the frozen transform, quantization,
reconstruction, hashing, framing and cap admission arithmetic, adding explicit
reference choice. It does not temporarily hide or replace a bank to influence
the old encoder. Ordinary frames under a pending promotion are standard AR01 P
frames referencing bank 0. The frozen receiver's bank-specific lease/write checks
already support this sequence. Wrong content/session/publication feedback, stale
frame IDs and unknown references retain the original validation rules.

The new finite model has a `reference_policy` selector. Its serial control uses
the frozen encoder; the overlap arm uses the new subclass. Both arms use this
same new model, stages, framing, caps and link assumptions. A fixed unit-test clock
proves serial parity with the parent ownership model for packets, display/drop
traces, feedback/publication times, wire and waiting intervals. The overlap model
retains staged semantic ACK/receiver publication, expiry/deadline priority,
reverse-transmitted NACKs, paid aborts and actual ingress/decode read pins.

## What is measured

The retained experiment has nine cases and 828 capture-policy events:

- Two 60-frame native windows compare serial and overlap recent-8 with keys every
  30 capture IDs: four runs, 240 events.
- A held-out 180-frame native window compares immutable-initial, serial recent-16
  and overlap recent-16: three runs, 540 events.
- A 24-frame full-canvas synthetic lost-promotion-ACK workload compares serial
  and overlap: two runs, 48 events.

These are repeated policy runs, not 828 distinct native acquisitions. The files
are related, precompressed 25/29.88 fps sources. BOX resize is paid; offline file
read/decode is excluded. Hypothetical 30-ID/s scheduling does not prove live native
30 Hz acquisition. All performance canvases stay 720×480; these are base-only
AR01 experiments with no HG01 exact UI or SR01 block skip integration.

Every actual map/prepare/reject, full promotion reconstruction/tag, packetization,
feed batch, decode begin/complete/abort and AF01 parse/apply pays measured host
wall cost. Each stage has its own serialized virtual server. Forward/reverse
8 Mb/s, QSPI 160 Mb/s, 10 ms feedback propagation and 60 Hz vblank remain declared
assumptions. Forward wire/feed is frame-batched like the parent AR01 model;
this is not the earlier v13 per-chunk UI pipeline or shared target-CPU execution.

Read-only verification checks exact content-bound sender/receiver reference IDs,
cap and pool bounds, stage costs, publication/release order, all capture outcomes,
wire totals and common-reference packet identity. For each overlap promotion,
bank-1 pending consumers/readers and other writers must be zero. Fallback records
must reference confirmed bank 0, with current header/CRC and normal credit use.

Nine tests cover matching packets when reference choices match; simultaneous
key-0 consumers and a bank-1 writer; old recent-bank drain and subsequent progress;
bank-specific leases; lost ACK continuity/forged content feedback; paid rejected
promotion without bank/pending mutation; invalid references and atomic receiver
rejection; fixed-clock serial parity; and bounded recovery under key/ACK loss and
conflicting feedback. Small test geometries are unit fixtures, not rate results.

Case order reverses between the short clips, but host load is uncontrolled and
each run remeasures its service times. Different policies change admission,
reference history and decoded subsets. The results retain common admitted/decoded
IDs, exact packet matches when all reference/promotion choices match, subset means
and common-ID active RGB565 MSE deltas. Equal quantizer maps do not promise equal
distortion or a statistically isolated timing gain.

## Retained results

The nine cases completed in 61.54 seconds of host wall time, with 828 capture-policy
events, 768 preparations and 768 actual decodes. All admitted frames fit the cap.
The standalone verifier passes with 17 executed-source bindings and nine tests.

| Source / policy | Serial strict / eventual / diagnostic | Overlap strict / eventual / diagnostic |
| --- | ---: | ---: |
| Combat, recent-8, key-30, 60 IDs | 47 / 48 / 25 | 55 / 56 / 29 |
| Second, recent-8, key-30, 60 IDs | 48 / 49 / 25 | 56 / 57 / 28 |
| Held-out second, recent-16, initial key, 180 IDs | 158 / 160 / 26.6 | 177 / 179 / 30 |
| Synthetic lost promotion ACK, 24 IDs | 15 / 16 / not defined | 23 / 24 / not defined |

Strict counts stop at the capture-window end; eventual includes the separate
one-second drain. The short native diagnostic window is one second and the
long window is five seconds, excluding 500 ms at each end. The sub-second fault
cases intentionally have no diagnostic rate. Periodic-key short tests still
fall below 30; no unqualified all-case 30 fps conclusion follows.

For the held-out initial-key window, the immutable control and overlap policy
have **identical sequences of 179 admitted, decoded and presented source IDs**.
Both drop only source ID 1 during startup while waiting for the initial key ACK.
Within `[500,5500)` ms both present all IDs 13–162: **150 distinct source-image
hashes in five seconds**, with no interior ID missing. This is a concrete modeled
30-ID/s operating point under the stated link/CPU/scanout assumptions, not a
physical Game Bub demonstration or a longer-duration reliability result.

The overlap policy restores the immutable control's delivery while reducing
mean body size from **18,688.59 to 12,216.60 bytes (−34.63%)** on those same
179 source IDs. Complete forward GF02/UDP/IP bytes fall **3,542,023 → 2,317,634
(−34.57%)**; reverse bytes are 12,709 in each case. Including both directions,
wire savings are 34.44%. The modeled maximum presented age is **100 → 83.33 ms**.
Matched decoded active RGB565 MSE changes **14.98313 → 14.85872**; outputs and
references differ, so this is not an identical-distortion guarantee. These metrics
use the finite model's source/decoded RGB565 comparison, not the standalone
algorithm study's RGB888-source metric. Do not compare their absolute MSE values
as though definitions were equal.

The serial recent-reference run uses fewer mean body bytes (10,346.95), but only
delivers 160 eventual frames; it trades cadence for compressed references.
Overlap spends additional bits on old-key fallback frames and retains 179 eventual
frames while remaining smaller than the immutable control. Mean packet sizes
without matched ID counts would conceal this tradeoff.

The long overlap case makes ten promotions while key-0 consumers remain pending,
uses bank 1 for 131 prepared frames, and admits 32 key-0 fallback frames. Twenty
of those fallbacks occur while a promotion writer is pending. No promotion has
an old bank-1 pending consumer/read lease or a competing writer. In the synthetic
lost-ACK run, nine fallback frames continue during uncertainty instead of blocking
all host work. All sender/receiver/feedback/display pool bounds remain enforced.

The [matched-delivery analysis](matched-delivery.json) pins the input results and
its analysis source, rederives ID sequences, distinct steady images, wire bytes,
age and quality. Reproduce without rerunning timings:

```sh
python analyze.py --check
```

## Memory and implementation limits

There are at most three host transactions/credits, two receiver ingress slots,
four feedback descriptors, three display metadata roles and two retained YUV
reference banks per peer. Bank-specific overlap does not increase those counts.
Pending promotion output, source/prediction/coefficient/RGB/scratch arrays,
canonical hash copies, GF02 buffers and temporary old/new overlap are additional
storage. Logical YUV8 and int16 one-pass byte counters are not measured traffic,
peak RAM, BRAM/SDRAM fit or target bandwidth proof. Shared-memory arbitration and
real read/write timing remain separate hardware work.

AR01/AF01 remain a new experimental dialect absent from installed software and
hardware. No native codec, physical RF/QSPI/scanout or sustained hardware 30 fps
is established by this scheduling experiment.

```sh
python -m unittest -v test_overlap.py
python verify.py                    # read-only retained evidence check
python benchmark.py > run.log 2>&1   # regenerate timings; external media required
```

Use the study virtual environment. `results.json` pins executed sources and media;
`copy-origin.json` records the frozen inputs and copy deltas. The parent handoff
manifest pins documentation, tests and the complete evidence snapshot.
