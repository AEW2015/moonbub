# Iteration 14: acknowledged-P references and coded residual decisions

The target remains **720×480 coded video, 720×405 active native game content and
30 distinct displayed frames/s**. This iteration implements actual custom packet
syntax and reference ownership rather than attributing gains to a smaller image.
The paired handoff branch is `handoff/gamebub-app-codec-v14-20261103`.

AR01/AF01 adds acknowledged reconstructed-P references with two retained YUV banks.
SR01 adds zero/DC/full-block coefficient syntax and optional bounded residual
pruning. These are separate Python research dialects. SR01 is not yet an AR01
inner codec, and neither is installed in Sunshine, ESP32 firmware or FPGA RTL.
HG01 exact-source UI is absent from the new reference transport experiments.
Their base-only cadence cannot be compared directly with v13's UI cadence.

## AR01: a recent reconstructed P can reduce residual bytes

The [recent-reference study](../experiments/python-game-recent-reference-study/README.md)
keeps the ACKed key in bank 0 and one explicitly promoted reconstructed P in bank 1.
A P uses bank 1 only after feedback confirms the retained decoded content. Every
reference binds epoch, frame ID and a 128-bit reconstructed-content tag. Normal
P ACKs release credit; only an explicit publication ACK advances a retained bank.

The first implementation is conservative: promotion drains all sender pending
transactions and read leases, reserves bank 1 and blocks new preparation until
feedback or drained expiry. Lost promotion feedback leaves bank 1 unselectable,
because the receiver may have replaced its old contents. Key-bank fallback and
later promotion recover without assuming that an unacknowledged source is a
reference. Receiver begin/complete/abort and typed leases prevent overwrite while
readers own a bank. Physical DMA/CDC timing is not supplied by those Python leases.

Promotion reconstructs and hashes its actual quantized P as paid encoder work.
The expected-image verification oracle cannot provide that reference for free.
The complete cap is checked before a candidate consumes a transaction or reserves
a bank, including candidates whose reconstruction/tag work later fails admission.

AR01 adds a 56-byte header and four-byte outer CRC around a complete GM01 body.
AF01 feedback is 43 bytes and binds the outer frame body CRC plus actual stored
bank, ID and tag. Canonical reference tags hash dimensions followed by little-
endian int16 Y/Cb/Cr planes; native ports must reproduce that byte convention.
Hashes/CRCs identify content and are not authentication. AR01 is not wire-compatible
with a receiver that understands only GM01 or standard Moonlight codecs.

| Common source window | Same-envelope immutable mean bytes | Recent-P every 8 mean bytes | Saving |
| --- | ---: | ---: | ---: |
| Combat, 60 IDs | 8,862 | 6,635 | 25.1% |
| Second, 60 IDs | 12,085.5 | 8,729.9 | 27.8% |
| Held-out second, 180 IDs | 12,343 | 8,798 | 28.7% |

These controls all refresh keys every 30 source IDs and use immediate serialized
feedback. The same-envelope immutable control avoids crediting the extra AR01
header as a coding improvement. Mean preparation changes 19.90→20.27 ms,
19.68→19.86 ms and 19.82→19.93 ms, including promotion reconstruction and tags.
Mean receive changes 21.10→18.51, 24.12→20.76 and 24.48→20.98 ms.

Recent references change reconstruction history even with identical quantizer
maps. Standalone active PSNR, comparing RGB888 source with RGB565-expanded
decoded output, changes 34.020→34.031 dB, 35.203→35.215 dB and
35.207→35.203 dB. This is not an equal-distortion comparison or a subjective
quality qualification. There are 924 actual attempts and 916 independent decodes,
with eight paid synthetic noise rejections and 36 accepted promotions. Twelve
tests cover reference tags/publication, parser atomicity, reader reservations,
credit, loss/uncertainty, expiry and recovery.

The later SR01 and finite-model quality tables convert both source and decoded
output through RGB565. Do not compare their MSE/PSNR numerically with this
standalone reference table as if the color conventions were identical.

Two retained native-canvas YUV banks represent 1,036,800 logical YUV8 bytes per
peer, or 2,073,600 bytes in the Python int16 arrays. Pending promotion reconstruction,
coefficient/prediction/RGB arrays, source frames, queues and display storage are
additional. Logical pass counters are not measured SDRAM traffic or peak memory.

## SR01: actual zero/DC/full syntax, with a separate lossy decision

The [skip/residual study](../experiments/python-game-skip-residual-study/README.md)
uses the existing immutable ACKed key, zero-motion prediction, macroblock quantizer
map and Q14 rounding. It evaluates actual dense CP02 bytes against a split plane
containing a two-bit zero/DC/full map, explicit nonzero DC words and CP02-coded
full blocks. Every plane header, mode-map byte, DC word and CRC counts.

The exact profile changes syntax only. Separate prune-2 and prune-4 P profiles
may zero a background residual block or remove its AC coefficients only when an
actual reconstructed YUV comparison stays within two or four levels of quantized
GM. Keys and protected priority coefficients are not pruned. Both GM and SR
receivers use the same exact zero/DC inverse bypass, making the syntax comparison
independent of introducing that earlier optimization.

| Native temporal source | GM mean bytes | SR exact | SR prune-4 |
| --- | ---: | ---: | ---: |
| Combat | 8,802.37 | 8,511.15 | 7,679.05 |
| Second | 12,025.50 | 12,088.50 | 10,479.08 |

Exact syntax saves 3.3% on combat and loses 63 header bytes on the second source,
where all planes prefer dense CP02. The chooser minimizes its new plane modes;
it does not yet fall back to an entire raw GM01 packet. That full-packet choice
is an explicit next integration task, not an assumed saving.

Prune-4 saves about 12.8% of bytes in both windows. Receive falls 18.20→10.84 ms
and 21.80→13.54 ms, but preparation rises 19.11→28.36 and 19.91→29.30 ms because
the actual inverse/error checks are paid. Whole preparation-plus-receive service
does not generally improve. The stage trade-off can matter when the host and
receiver have different resources, but no native parallel throughput follows
from these Python stage times.

Pruning is explicitly lossy. Source active RGB565 MSE changes 22.750→20.492 on
combat and 14.969→16.186 on the second source. A bound against quantized GM is
not a bound against the original source or proof of better subjective quality.
Protected priority output matches quantized GM, not lossless original-source UI.

The initial test exposed an important filter footprint: bilinear chroma upsampling
uses right/down neighboring blocks, so preserving only the priority block could
still change its boundary RGB pixels. The final pruning guard includes right,
lower and lower-right chroma neighbors. The complete benchmark was rerun after
a regression proved that halo keeps protected RGB output unchanged.

Nine tests and retained verification cover 154 source IDs across five actual
profiles: 770 decisions, 755 admissions and 15 paid noise rejections. The final
results retain exact coefficients/pixels, observed YUV error, protected RGB565
checks, all losing syntax work and full cap accounting. No SR01 finite transport
or recent-P integration is supplied in this component study.

## Finite ownership exposes the cost of conservative promotion

The [reference-ownership study](../experiments/python-game-reference-ownership-study/README.md)
carries real AR01 bodies in GF02 chunks through two ingress slots, decoder leases,
AF01 feedback and three bounded host transactions. There are three metadata
display-buffer roles and four feedback descriptors. Every actual BOX, map,
prepare/reject, packetize/feed, decode begin/complete/abort, feedback parse/apply
and expiry call pays measured host wall time on an independent virtual server.

It uses frame-batched wire/feed rather than v13's chunk-level scheduling: complete
forward bytes consume wire service before the real feed batch. Links, QSPI,
propagation and vblank remain declared assumptions. Predecoded source acquisition,
physical buffers, DMA/CDC, RF and concurrent target CPU execution remain unmeasured.

| Held-out 180-ID source / policy | Strict / eventual | Diagnostic IDs/s |
| --- | ---: | ---: |
| Immutable key every 30 | 167 / 169 | 28.0 |
| Recent-P every 8 plus key every 30 | 145 / 146 | 24.2 |
| Immutable initial key | 177 / 179 | 30.0 |
| Recent-P every 16, initial key | 158 / 160 | 26.6 |

The compression result survives byte accounting, but the all-pending drain and
ACK barrier hurt cadence. The recent-8/key-30 held-out run waits 1,471 ms on
reference drain over six seconds; recent-16/initial waits 804 ms. These are
exclusive wait-state intervals, not additive attribution of dropped frames.
The immediate-ACK algorithm result therefore cannot be promoted to a stream FPS.

Thirteen cases contain 1,152 capture-policy events, 1,028 preparations and 1,027
successful decodes. All work drains. Fault cases use actual full-canvas packets
for lost initial key data, lost promotion ACK and conflicting ACK/NACK feedback.
Receiver rejection must travel back as AF01 before it can expire sender state.
A wholly lost single chunk fabricates no receiver message and waits for timeout.

Review reproduced a simulator correctness bug during development: an ACK call
could install a bank at the start of its paid interval, then timeout during that
interval still allowed promotion at its end. The repaired model stages semantic
publication until completion and lets requested expiry win. A decoder deadline
during paid completion similarly aborts future publication. Actual work counters
are not refunded. Eight tests include injected 100 ms ACK/decoder work to expose
these cases, alongside reader drain, content identity, loss and cap rejection.
Those declared unit clocks are never used for performance runs.

The displayed immutable-initial 30.0 is only a conditional short model operating
point: 179/180 IDs eventually display. Qualification must separate startup and
drain from interior drops, rolling cadence and age. Initial-only refresh is not
a qualified production default, and none of these figures proves hardware 30 fps.

## Bank-specific promotion retains cadence without waiting for every P

The [overlap-reference study](../experiments/python-game-overlap-reference-study/README.md)
keeps the AR01/AF01 wire format and receiver unchanged. The encoder only waits
for consumers and leases of bank 1 before replacing bank 1; bank-0 consumers
do not prevent that independent write. A full key still drains every consumer.
While a promotion is pending, only the confirmed key bank is used for new P
frames. No candidate can use the uncertain bank or its pre-promotion identity.

When promotion is due but old bank-1 users have not drained, the policy admits
bank-0 fallback frames rather than more bank-1 consumers. This prevents a
continuously busy stream from starving its own promotion. Exact publication ACK
then makes the new bank-1 frame selectable. ACK loss keeps key-bank video moving
while the destination remains uncertain. These rules use reference/ownership
state only, not future images or candidate quality.

| Source / reference policy | Serial strict / eventual / diagnostic | Overlap strict / eventual / diagnostic |
| --- | ---: | ---: |
| Combat, recent every 8, keys every 30 | 47 / 48 / 25 | 55 / 56 / 29 |
| Second, recent every 8, keys every 30 | 48 / 49 / 25 | 56 / 57 / 28 |
| Held-out 180, recent every 16, initial key | 158 / 160 / 26.6 | 177 / 179 / 30.0 |

The held-out overlap run reaches **150 distinct presentations in the five-second
diagnostic window**. It delivers exactly the same 179 source IDs as the newly
measured immutable-initial control: both omit startup ID 1 and no later capture
ID. Each has 177 presentations before capture stops and two more during drain.
The six-second test contains 180 distinct precompressed native-source images,
scheduled at 30 IDs/s; it is not live native 30 Hz capture or a long-run test.

At that matched delivery set, mean complete AR01 body size falls from 18,688.59
to 12,216.60 bytes, **34.63% less**. Complete GF02/IPv4/UDP forward bytes fall
from 3,542,023 to 2,317,634, **34.57% less wire data**. Maximum modeled presented
age is 83.33 ms versus 100 ms in the immutable control. Mean active RGB565 MSE
changes 14.98313→14.85872; the prediction histories differ, so this is not lossless
original-source coding, an equal-distortion guarantee or a universal quality gain.

Overlap sends more frames and some larger key-bank fallbacks than the serial
recent-reference policy, whose mean body is only 10,346.95 bytes on its smaller
160-frame delivered set. Comparing those means alone would reward dropped frames.
Use the same-frame immutable comparison above for the delivery-and-rate claim.
Periodic-key short cases still show only 28–29 diagnostic IDs/s; the conditional
initial-key result does not qualify a production refresh strategy.

The long overlap case records 10 promotions while key-bank consumers remain
pending, 32 explicit bank-0 fallbacks, including 20 while a writer is pending,
and 131 uses of confirmed bank 1. Three sender transactions, two ingress slots,
two retained reference banks and three metadata display roles remain bounded.
All promotion reconstruction, hashing, fallback frames, parser work and feedback
application are paid. Existing semantic staging still makes expiry/deadline win
at completion rather than publishing future state at the start of a timed call.

The separate lost-promotion-ACK workload improves from 16/24 eventual frames to
24/24; the overlap client sends nine key-bank frames while the writer remains
uncertain. The native timing cases do not silently inject a loss or substitute
synthetic favorable content. Nine tests cover bank-specific readers, key drains,
wire identity and cap rejection, serial parity under a declared unit clock, lost
and conflicting feedback, recovery and finite resource bounds. There are nine
timed cases, 828 capture-policy events and 768 preparations/decodes.

This meets a short **Python finite-model cadence** target at full coded resolution
while improving matched-frame bytes. Declared links, frame-batched transport,
independent measured-host servers and metadata buffers still do not prove target
Wi-Fi, QSPI, SDRAM, native implementation or sustained hardware 30 fps.

## Progression to a unified application-specific codec

The experiments now provide concrete custom reference and residual syntax, plus
the earlier exact UI payload reuse and decoder arithmetic bypass. Their gains
must not be multiplied together: recent prediction changes coefficient sparsity,
pruning changes reconstruction history and UI exactness has a distinct contract.

Next, define one explicitly versioned profile that can dispatch GM/SR inner
residuals, bind the actual decoded result to reference promotion and apply exact
UI only to display output. A whole-packet GM fallback should avoid SR's dense-only
header penalty, while paying all candidates actually evaluated. Compare exact
syntax first; add bounded pruning as an explicit negotiated quality option.
Use the bank-specific continuity policy above as the reference-management
candidate, retaining the serial profile as a correctness/performance control.
The AR01 parser currently accepts GM01 bodies only; SR01 cannot simply be placed
inside that envelope without a versioned parser and new reconstruction/tag tests.

For FPGA work, the SR map can route zero/DC blocks around entropy/transform work
and send full blocks through a regular integer reconstruction pipeline. Preserve
the proven Q14 rounding and chroma footprint. Two reference banks belong in a
specified external-memory layout with tags/readers, not an assumed pool of spare
BRAM. DSP throughput, entropy serialization, memory reads/writes and display
service all need a measured implementation budget; this iteration supplies no
HLS synthesis, RTL fit or target timing.

Longer distinct-frame samples, scene cuts, loss, uncertain publication and common-
color quality checks remain gates. The current source clips are related and
precompressed at native 25/29.88 fps; repeated policy IDs are not distinct live
acquisitions. JPEG remains the installed hardware comparison. Native host,
ESP32 forwarding, receiver implementation, mode negotiation and physical display
qualification remain separate development work.

## Reproduction and handoff

There are **47 passing new tests**: 12 recent-reference, 9 skip/residual, 8 finite
ownership, 9 overlapped-reference and 9 independent audit tests. Each study has
source-pinned results, tests and a read-only verifier. Overlap also supplies
`matched-delivery.json` and `analyze.py --check` to rederive the same-frame rate,
wire and quality comparison without rerunning timings.

Run `python experiments/verify_prototype_v14.py` using the study virtual
environment. `docs/prototype-v14-provenance.json` pins code, results, documentation,
external-media hashes and the paired Sunshine handoff README. The independent
audit separates native/synthetic cohorts, unique image content, paid candidate
work, reference/tag/ACK bindings and logical pool bounds. Older handoff branches
remain frozen. No hardware was programmed or measured in this iteration.
