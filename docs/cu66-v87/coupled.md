# Actual CS86 context work coupled to bounded consumers

This experiment keeps the published CS86 grouped-COPY whole-plane packets and
native content commitments unchanged. It joins the actual V86 context work to
the V83 reconstruction/memory/hash task graph and the V84 staging contract. One
causal schedule accounts for both producers and consumers; a standalone entropy
number is neither added to nor maximized with a precomputed backend time.

For each tile, shared setup waits for its output group and a coefficient slot.
The four ordered probability contexts fetch and compute their observed work,
then rendezvous at an ordered emission. A residual tile's coefficient slot is
held through inverse completion. A COPY/CONST tile releases its slot when its
map lookup consumes the operation. Emission alone never releases that slot.
Reference and inverse-result slots retain the original consumer fences, and a
four-entry ring owns the 16-tile output groups until stores, metadata and the
required leaf hash complete. The candidate publication fence includes every
modeled task as an ancestor.

The deterministic scheduler has one shared fetch/control resource, one/two
arithmetic lanes, one emitter, one dequant resource, one inverse resource, one
reconstruction resource and one pixel-memory resource. Tree, map and hash
resources retain the frozen V83 assumptions. Each probability context preserves
its previous compute-to-next-fetch dependency. Batched fetch before arithmetic
is a prospective architecture, not an instruction-level or RTL trace.

## Added conditional costs

The packet is fully buffered at release. A shared-resource scan charges its
complete wire-byte count at the LOW/HIGH CRC-byte weight, including reading the
trailing checksum field. A second byte scan charges the actual header, operation
map, quantizer map and chunk-directory lengths at the corresponding header-byte
weight. Mode/payload production and HUD stores wait for these scans. The scans
price byte access; they do not establish actual parser/bit-expansion hardware
cost or authenticated partial-packet admission.

Each visible residual tile additionally pays an explicit 64-cycle dequant task,
a 64-cycle inverse task and a 64-cycle reconstruction task. These are sensitivity
inputs, not observed hardware times. In particular, no DSP count, pipeline II or
clock frequency has been demonstrated. Entropy counts are the actual re-encoded
chunk observations; LOW/HIGH costs and 100 MHz are assumptions rather than
physical lower/upper bounds.

The zero-frontend control sets these new costs to zero and must reproduce the
frozen V84 eight-credit scheduler exactly on every source. This controls the
integration independently of any apparent speed improvement.

## Limits

HUD writes and readback are included, as are the base-pixel C2 tree operations
and the final seal task. HUD entropy decoding, semantic HUD hashing, actual map
parser work beyond the byte scan, physical COPY/CONST ports, display scanout,
refresh/controller row and direction timing, provisional abort/drain and ESP32
execution remain unqualified. The 20% memory-reservation sensitivity restarts
at phase zero for each frame and substitutes for none of those mechanisms.
The resulting finish time is a conditional coupled-model completion, not a
complete validated decoder latency or an end-to-end streaming measurement.

The study processes 457 content sources from one walkthrough family in four
reset histories. Multiple configurations and replays are not additional source
frames and do not qualify sustained 30 fps. The exact CS86 native reconstruction
proof is inherited from V86; this study schedules verified content identities
without executing an inverse transform in Python.

## Logical storage accounting

The inherited reference/inverse/coefficient/output-group allowance is 7,168
logical bytes: eight 64-byte reference slots, eight 192-byte inverse-result
slots, eight 128-byte quantized-coefficient slots and four 1,024-byte output
groups. The new dequant stage needs an additional allowance. Conservatively
retaining 64 signed 32-bit dequantized values for each of eight slots adds
2,048 bytes, for **9,216 logical staged bytes**. Its live interval starts with
dequant production and ends with inverse consumption; it is contained in that
tile's coefficient-credit lifetime, so it cannot create an unbounded result
queue under this contract. The independent witness auditor checks the subset
and capacity relation.

This is a staged-data allowance, not total decoder memory or proof of FPGA fit.
Probability state, inverse/DSP working registers, compressed input, descriptor
and ready queues, C2 tree/maps, HUD work state, physical RAM port replication,
alignment and BRAM rounding remain extra.

## Reproduction and evidence

Run the seven small dependency tests with:

```sh
python3 experiments/python-gamebub-v87/coupled/test_model.py
```

The tests include a deliberately slow inverse consumer. The next window reuse
must wait for inverse completion rather than the earlier entropy emission;
removing that edge advances the invalid producer and the audit rejects it.
A separate case checks scan-before-admission and explicit dequant work.

The actual-data campaign is:

```sh
python3 scripts/cu66-v87/prototype_coupled.py
```

Each of four subprocesses owns one source history. Every schedule checks
resource/dependency/group occupancy, coefficient/reference/inverse lifetimes,
context order, full publication ancestry and exact frozen memory/hash work.
Every zero-frontend result is compared to the frozen credit scheduler. Reports
retain unique attempt directories, commands, observed process exit codes,
source pins/archives, row identities, timeline digests and representative full
DAG/timeline witnesses. The independent retained-row audit additionally compares
all zero-frontend times with V84's already-published rows and reconstructs the
frontend work totals from the V86 observation index.

The retained `consumer_release_wait_max_cycles` diagnostic is the largest gap
from a prior slot's entropy emission to its later setup reuse. It can include
other admission and resource waits as well; it is not an exclusive attribution
of stall cycles to the consumer edge. The synthetic mutation tests isolate that
edge causally. The inherited `counts.entropy_work_cycles = 0` field describes
the retired serial placeholder; actual fetch/arithmetic/emission work is in
`frontend.work_cycles` (or row `frontend.frontend_work_cycles`).

## Faster-memory replay of the hard source

Four additional schedules replay only the retained cohort 3 / source 50 graph,
keeping its packet, primitive work, dequant, reconstruction, hashes and credits
unchanged while changing every actual read/write BL8 service interval to a
hypothetical 12 cycles. The graphs, timelines, independent audits and source
witness hashes are retained separately from the 457-source campaign.

| Two arithmetic lanes | No memory reservation | 20% reservation |
|---|---:|---:|
| LOW costs, 12-cycle read/write | 10.68330 ms | 12.15841 ms |
| HIGH costs, 12-cycle read/write | 17.26770 ms | 18.22145 ms |

Even LOW does not reach 10 ms on this source merely by reducing memory service
to 12 cycles: memory busy work alone falls to 8.26848 ms, but real causal stalls
and the other priced work still matter. This is a selected-source sensitivity,
not a full-corpus or physical-controller result. It motivates a joint traffic,
frontend and staging experiment rather than treating a memory bandwidth bound
as the complete decoder latency.

## Full-corpus results

All four subprocesses exited zero. **457 sources × six configurations = 2,742
conditional schedules** passed. Every zero-frontend finish time exactly matches
its frozen V84 source control; the independent retained-row audit checks all
source identities, observed primitive totals, hashes, counts and summaries.

| Configuration | Median | Maximum | Strictly below 10 ms |
|---|---:|---:|---:|
| Zero-frontend eight-credit control | 8.45600 ms | 11.70392 ms | 413 / 457 |
| LOW, one arithmetic lane | 8.93480 ms | 17.11404 ms | 301 / 457 |
| LOW, two arithmetic lanes | 8.87090 ms | 12.82457 ms | 350 / 457 |
| HIGH, one arithmetic lane | 11.38461 ms | 28.65408 ms | 186 / 457 |
| HIGH, two arithmetic lanes | 9.37516 ms | 18.58340 ms | 269 / 457 |
| LOW, two lanes, 20% memory reservation | 10.97240 ms | 15.63288 ms | 166 / 457 |

Two lanes improve 143 LOW sources and leave 314 equal; their paired median
improvement is zero. The independently sorted medians differ by 0.06390 ms,
which is a different statistic. Under HIGH they improve 281 sources, leave 176
equal and have a 1.29491-ms paired median improvement. Neither cost case has a
regression. Two lanes help difficult frontend-heavy frames, but many sources
remain dominated by backend work. All modeled per-frame finish times fit a
33.333-ms period; the missing continuous ingress/display/ESP32 work means this
is not a sustained 30-fps hardware result.

On the retained hard source C3/f50, LOW two-lane arithmetic work has a
6.226035-ms two-lane work floor while memory alone requires 11.70192 ms. HIGH's
two-lane arithmetic work floor is already 11.901785 ms. Thus calibrating and
improving arithmetic matters as well as reducing physical traffic; faster
entropy alone cannot erase the current memory floor.

- [Selected full session](../../experiments/python-gamebub-v87/coupled/results.json)
- [Independent full-row verification](../../experiments/python-gamebub-v87/coupled/verification.json)
- [Captured verification runs](../../experiments/python-gamebub-v87/coupled/verification.log)
- [Seven synthetic dependency checks](../../experiments/python-gamebub-v87/coupled/synthetic-tests.json)
- [Independent five-witness audit](../../experiments/python-gamebub-v87/memory/final-coupled-audit.json)
- [Four faster-memory witness replays](../../experiments/python-gamebub-v87/coupled/memory-probe.json)

The retained verifier development failure was a tuple/list normalization error
when comparing JSON reservation windows; the archived source and failed log are
kept. The campaign/model was unchanged. The corrected independent verifier and
its exact repeat both exit zero, including independent re-audits of all four
faster-memory witness graphs. An earlier four-probe report is retained with its
original script under development history; the selected probe additionally
retains the mutated graphs and timeline hashes.
