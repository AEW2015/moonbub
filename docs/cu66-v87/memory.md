# V87 memory-service constraints and reference-layout opportunities

This is an independent accounting study of all 457 frozen native sources. It
uses their actual COPY/CONST/residual traffic after candidate-bank residency
checks, including the reference reads needed for changed group hashes. It does
not schedule a controller or execute a replacement physical layout.

## Necessary memory budgets

The baseline prices every read BL8 at 18 cycles and every write BL8 at 16 cycles.
The maximum busy work is **1,170,192 cycles, or 11.70192 ms at the assumed
100 MHz**. This counts completion service for every command. The frozen V82
successor-gap floor omits the final 18-cycle interval, so it is 18 cycles lower;
that convention difference is not a performance improvement.

The largest traffic source is cohort 0/frame 1: 33,864 reads and 35,040 writes,
**68,904 BL8 commands**. All reads include the existing 2,640 HUD readbacks;
writes include 2,640 HUD writes. A 20% memory reservation leaves at most
800,000 memory-service cycles in a 10-ms interval at 100 MHz. Therefore this
source requires an average service interval strictly below approximately **11.61036
cycles/BL8** to fit strictly under 10 ms, even before dependency stalls or other
unoverlapped work. Without reservation the necessary threshold is below
approximately 14.51295 cycles/BL8.

| Traffic/service scenario | Maximum busy-work ms | Maximum necessary ms with 20% reservation | Sources passing the strict 10-ms reserved memory-work condition |
|---|---:|---:|---:|
| Current 18-cycle reads / 16-cycle writes | 11.70192 | 14.62740 | 186/457 |
| Hypothetical 12-cycle reads and writes | 8.26848 | 10.33560 | 417/457 |
| Counterfactual COPY-store alias, current service | 10.62224 | 13.27780 | 298/457 |
| Counterfactual COPY-store alias, 12-cycle service | 7.45872 | 9.32340 | 457/457 |

Dividing busy work by 0.8 is a **necessary aggregate-service bound**, not a
predicted completion time. The actual nonpreemptive scheduler can waste gaps
at reserved-window edges, and memory may idle while waiting for decoding.
Passing the condition is insufficient to establish a 10-ms complete decoder.
In particular, merely switching to 12-cycle service cannot make all sources
fit a reserved 10-ms memory budget: 40 still exceed it.

## Application-specific reference layout to investigate

A COPY operation can skip entropy arithmetic without proving that the physical
candidate bank already holds that tile. The frozen workload correctly retains
stores for nonresident COPY tiles. It also retains reference reads when dirty
leaf hashes need actual tile payloads. These costs survive metadata compaction.

The counterfactual rows above remove only the candidate writes associated with
`materialize_copy_reference_tiles`; **every reference read is retained**. This
is a bounded opportunity estimate, not a claim that the writes can safely be
deleted from the existing design. A real implementation would need tile/page
indirection or a reference alias with explicit bank leases, a display addressing
path that honors aliases, atomic map publication and failed-candidate recovery.
The largest frame changes after this traffic transformation, so applying only
the cold-frame saving to the corpus maximum would give a wrong conclusion.

At current service intervals, this write elimination alone still leaves a
10.62224-ms necessary busy bound. Pairing a correct alias/layout strategy with
better controller overlap is more promising than assuming faster entropy alone
will remove the memory floor. Neither counterfactual is deployed or proven.

## Independent coupled-timeline audit

The companion [auditor](../../scripts/cu66-v87/audit_coupled.py) independently
checks supplied job/timeline membership, durations, dependencies, resource
capacities, memory reservation windows and the final all-operation publication
fence. It infers per-tile coefficient consumers rather than trusting supplied
credit records: capacity starts at frontend setup and ends only after inverse
or map consumption. It checks per-context ordering, group admission and
reference/inverse staging similarly. Passing this graph audit does not validate
inverse arithmetic, decoder pixel results or a hardware controller.

A materialized dequantized tile is an additional object. Assuming 64 signed
32-bit values gives 256 bytes per result, alongside the retained 128-byte
original coefficient slot. The auditor checks ownership from dequant start
through inverse completion. This interval is a subset of that tile's
coefficient-credit lifetime, so the eight-credit contract bounds it to eight
live results without adding timing edges. Reserving another 2,048 bytes raises
the conservative logical staging capacity from **7,168 to 9,216 bytes** for the
nonzero-dequant scenarios. This still excludes tree/maps, probability state,
engine working registers, ports, transport and physical RAM rounding.

The [targeted mutation tests](../../experiments/python-gamebub-v87/memory/auditor-tests.json)
reject nine changes that break consumer release, probability-context order,
group admission, publication coverage or resource/window capacity. A repeated
positive audit passes after restoring the witness. These tests exercise model
checks on one source; they are not a decoder fault-injection campaign.

The [retained memory results](../../experiments/python-gamebub-v87/memory/results.json)
and [per-source rows](../../experiments/python-gamebub-v87/memory/frames.jsonl)
include source hashes and all four scenarios. Regenerate with:

```sh
python3 experiments/python-gamebub-v87/memory/analyze.py
```

This study omits physical row/refresh behavior, actual target frequency/fit,
continuous LCD scheduling, transport/ESP32 execution, semantic HUD processing
and complete dequant/inverse implementation costs. It closes no sustained
hardware 30-fps or complete validated under-10-ms milestone.

## Final witness and alias audits

The [final coupled audit](../../experiments/python-gamebub-v87/memory/final-coupled-audit.json)
checks five immutable full-campaign witnesses: three configurations of cohort
3/frame 50, plus cohort 0/frames 0 and 1. These are three distinct native
sources, not five sources. The [row bindings](../../experiments/python-gamebub-v87/memory/final-coupled-bindings.json)
match their exact timeline hashes, completion cycles, resource totals and
coefficient peaks to the campaign rows. All remaining schedules retain the
campaign's in-process checks; this auditor does not independently reconstruct
all their graphs.

A separate [alias audit](../../experiments/python-gamebub-v87/memory/alias-audit.json)
checks 914 native source/scenario rows against the original tile arrays,
write counts and expected presented identities. It also runs 1,024 small
symbolic accepted updates against an immutable plaintext oracle, using mixed
COPY/non-COPY, held scanout, incomplete-candidate rejection, abort, nested-begin
rejection and failed-digest cleanup. This checks the proposed sequential layout
functionally. It does not add alias-port traffic to the coupled timing model.
The alias prototype's dense write-every-tile comparator is distinct from the
frozen bank-residency comparator used in this memory-budget table.
