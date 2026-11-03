# Controlled refresh replay at primary720×480@30

This experiment compares refresh policies with the same immutable declared CPU
service table for each source and UI setting. It copies the v11 finite hybrid
link scheduler and adapter into this new directory; frozen v11 files remain
unchanged. Actual HG01/GM01 packets are newly encoded from the currently ACKed
reference after each run's capture/admission choices. GF02 chunking, GA01
content-bound feedback,48KiB cap,two credits,reader pins and150ms frame age
remain active. No target implementation or physical30fps proof is supplied.
The inherited150ms limit gates encode/decode age; presentation at the next
60Hz vblank can add up to16.667ms. It is not a strict150ms optical-age proof.

The baseline table uses separately pinned v11720×480 key/P preparation,
receiver and transport-stage means. BOX uses its pinned mean plus a declared
0.05ms thumbnail-observation allowance. Every cap-rejected preparation pays
a fixed declared120ms because those baseline traces contained no rejects.
The table is shared across policies; the number and kind of calls depend on
each causal run. This is a conditional workload scenario, **not** a claim that
each newly generated packet has the same measured execution cost as a v11
packet. Actual complete call wall times remain in separate fields, including
failed calls and any case whose measured work exceeds its charged allowance.
Costs use independent serialized virtual servers; they do not model one shared
physical host CPU. Forward/reverse8Mb/s,QSPI160Mb/s,10ms feedback propagation
and60Hz vblank retain the v11 assumptions.

Policies are periodic30capture IDs,periodic60,initial-only and a bounded
current/past-source thumbnail heuristic. The latter observes18×32RGB samples,
latches mean-absolute change≥28, waits at least30capture IDs after the last
key, and forces a key by120IDs. It reads no future source, decoded output,
future packet length or quality oracle. All policies perform the same source
observation work. In a clean60capture window,periodic60 has no second refresh
and is equivalent to initial-only; this does not qualify a60-ID refresh cadence
over longer runs. Native source clips are precompressed25/29.88fps with repeated
frames, decoded offline and scheduled at hypothetical30IDs/s.
GM01 P-frame acknowledgments release credits; they do not replace the immutable
ACKed key anchor. Initial-only therefore retains the initial key reference
until recovery requires a new key. It is not a rolling previous-frame codec.

The new scheduler copy also fixes a known v11 late-ACK issue: v11 could accept
a matching ACK after timeout had requested expiry while parse ownership still
delayed release. This copy rejects feedback after requested expiry, pays the
full parse cost and waits for physical-reader drain before reclaim. The old
experiment retains its original code and evidence. This repair is present in
all compared new policies and is separately tested; it is not silently credited
to a refresh-policy change.

Encoder-admission wait categories distinguish encoder busy,key-ACK wait,
refresh drain,P-credit limit and sender-slot pressure. These are exclusive
waiting-state intervals, not an additive causal attribution of lost frames.
Different policies can change references, packet sizes and every later outcome.

Preparation and actual receiver calls execute in Python; source/oracle/display
arrays and independent correctness reconstruction consume extra host memory.
Three metadata framebuffer roles do not prove a physical buffer allocation.
No capture,network socket,radio,shared target CPU,SDRAM/DMA/CDC or display
qualification is included. Primary resolution and scheduling stay720×480@30;
reduced resolution/fps is not substituted for success.

Using the pinned environment from the parent study:

```sh
/home/lori/gamebub-streaming-prototype/.venv/bin/python -m unittest -v test_refresh.py
/home/lori/gamebub-streaming-prototype/.venv/bin/python benchmark.py --fast-ablation
/home/lori/gamebub-streaming-prototype/.venv/bin/python analyze.py
/home/lori/gamebub-streaming-prototype/.venv/bin/python analyze.py --check
/home/lori/gamebub-streaming-prototype/.venv/bin/python verify.py
/home/lori/gamebub-streaming-prototype/.venv/bin/python check_stored_results.py
```

`check_stored_results.py` remaps recorded checkout source paths to this checkout
for handoff verification. The original verifier remains unchanged; neither command
reruns the performance workload. External media is separately pinned by the parent
manifest and reported unavailable when not installed.

The default benchmark declares12native cases (two60-frame clips×GM/UI×three
refresh policies), plus three720×480synthetic cut/noise cases. Optional
`--fast-ablation` adds two second-clip UI scenarios with every CPU service
halved; this is a declared acceleration what-if, never measured fast execution.
`--native-frames` allows a longer available native source without repeating
frames to invent distinct acquisition. Current test coverage includes identical
virtual traces despite different observed clocks; immutable tables; source-only
causality; paid rejection; key credit drain; post-timeout feedback and parse
ownership; corruption,loss,duplicates and recovery with actual small packets.

## Retained results

The17cases completed in72.88seconds of host wall time. All use720×480 and
30scheduled capture IDs/s, with strict capture window`[0,2000)`ms and separate
1,000ms drain. Diagnostic rate counts distinct presented IDs in`[500,1500)`ms.
It is not all-frame delivery or a sustained physical throughput measurement.
They retain1,020capture-policy events,892actual preparations and886complete
hash-checked decodes; the remaining six preparations are paid noise rejects.

| Native clip / UI | Periodic30 strict / eventual / diagnostic | Periodic60 or initial-only strict / eventual / diagnostic |
| --- | ---: | ---: |
| Combat / GM base | 54 /55 /28 | 56 /58 /30 |
| Combat / adaptive exact UI | 49 /51 /24 | 51 /53 /27 |
| Second clip / GM base | 54 /56 /28 | 56 /58 /30 |
| Second clip / adaptive exact UI | 40 /42 /21 | 42 /44 /23 |

Within each of these four groups,periodic60 and initial-only have identical
**checked event and packet identity traces**, including actual packet identities,
references, verified selected-region exactness, wire, feedback, publication, ownership and
service times. Actual observed call wall times differ and are excluded from
that equality. [controlled-comparison.json](controlled-comparison.json) records
the comparison and pins its input results and analysis source.

Removing periodic30refresh adds two strict presented IDs in every native group
and2–3diagnostic IDs/s, while UI still falls short of30 under the same pinned
CPU-service assumptions. This supports refresh as one source of the gap and
shows it does not explain the complete UI deficit. For example,second-clip UI
initial-only records647.13ms waiting on P credits and440.67ms waiting on the
encoder; its P sender slots are held88.71ms on average. These are exclusive
waiting-state diagnostics in this finite scenario, not additive attribution
of lost frames or a physical bandwidth/CPU measurement.

The declared half-CPU-service second-clip UI ablation gives55strict/57eventual/
28diagnostic with periodic30 and57/59/30 with initial-only. Every real call is
still executed and separately timed; halving its charged scenario time does
not accelerate that call. **No case delivers all60IDs within the strict primary
720×480@30window.** Startup and final-tail losses remain even in30diagnostic
cases; no hardware30fps or sustained-native30 acquisition success is claimed.

The synthetic cut/noise cases give44/46/25 for periodic30,46/48/27 for
initial-only and44/46/25 for the bounded scene heuristic. The scene policy
chooses keys0/32 rather than periodic0/31 and provides no delivery gain in this
case. All three policies reject noise IDs42and46; each rejected complete call
pays the fixed120ms scenario allowance. Actual noise-preparation wall time here
is lower than that allowance; other workloads can reverse that relationship.
Rejected work is never refunded or silently assigned zero cost. This does not
qualify long scene recovery, the120-ID maximum refresh interval or a production
initial-only policy.

Nine tests and the retained-results verifier pass. The verifier checks executed
source hashes, paired source/table identity, every charged stage, causal ACKed
reference use, key drain, publication/read-pin order, finite ownership, wire
totals, selected RGB565 exactness and capture-outcome conservation. The results
retain both actual wall and charged service per call; no newly measured call
wall feeds the declared scheduling table. Error/loss/reordering behavior uses
actual small protocol/codec packets in the regressions, rather than pretending
the clean native runs exercised injected faults.
