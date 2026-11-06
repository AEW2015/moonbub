# V80 completed trace analysis

The overlap path restores most of the conservative prefetch regression in these
bounded runs, but the trace does not establish the strict validated-under-10-ms
goal or a predicted benefit from another memory change. Accepted prefetch
lookups already return in one cycle. The remaining concrete experiment is to
consume the existing 128-bit bridge snapshot as one block instead of eight
16-bit core beats, with new instrumentation to determine whether that conversion
is on the actual dependency path.

Run `python3 scripts/cu66-v80/analyze_trace.py` to reproduce the analysis using
only the six explicit completed attempt paths in the script. No active full
history file is selected. Runtime was approximately 18 seconds with Python's
standard library and no build or simulation.

The artifacts are:

- `fpga/experiments/cu66-v80/trace-analysis/results.json`: event validation,
  exact producer/source/log/compressed-and-raw-trace SHA bindings, frame counts,
  actual paired milestones, and nearest-rank distribution summaries.
- `tiles.csv.gz`: 178,200 joined tile records, including signed event ordering.
- `histograms.csv.gz`: exact integer distributions for every reported interval,
  including per-client and endpoint-pair command interaccept gaps.

There are 3,902,984 trace rows: 3,199,580 physical command acceptances, 178,200
each candidate write acceptances/completions, 124,896 each reference request/
response acceptances, 97,200 fill events, and 12 epoch completions. These
counts include key frames and the two baseline traces. The four prefetch traces
contain 93,672 accepted reference lookups across 12 delta epochs. Each epoch
has 8,100 fills and retirements, 7,806 lookups, 294 unused hidden tiles, and
32,400 physical prefetch reads.

## Identity and timing rules

The actual CSV header is
`cycle,ps,frame_generation,event,owner_generation,client,write,address,bank,plane,tile_index`.
The pinned bench samples tile events on accepted ready/valid handshakes before
the numbered rising edge; `prefetch_fill` observes the filled-counter increment
after that edge. `ref_request` is accepted lookup **Q**, not first asserted
lookup valid. Fill is **F**, accepted reference response **R**, accepted
candidate write **W**, and accepted receiver write completion **D**.

Tile joins require the actual owner generation, plane, and tile index, retaining
the distinct reference and candidate banks. Both cohorts use generation 2:
reference 0 to candidate 1; generation 3: reference 1 to candidate 2; generation
4: reference 2 to candidate 0. The analyzer validates all four accepted physical
write block addresses per tile and all four prefetch blocks per filled tile.
Reference-to-candidate translation uses this explicit map; it is never a direct
join of unequal bank fields. The previous completion is ordinal `n-1` in the
full Y/U/V walk, including hidden tiles and plane boundaries.

Raw `command` rows have `owner_generation=0`, meaning **unknown**. Their
`frame_generation` is the current trace window, including LCD work after the
receiver's ACK. Command-to-tile address joins are therefore explicitly labeled
context-window coordinate matches, not authenticated raw-command ownership.
Admission-through-ACK counts are reported separately and match every
`command_frames` field in the run JSON exactly. Whole-window counts and gaps
are also preserved, including the post-ACK LCD tail.

Every interaccept interval is a separation between actual controller command
acceptances. It may include another client, refresh, demand timing, or idle.
Even intervals with no intervening accepted command may include refresh or
internal idle. None is labeled controller service, removable overhead, or a
recoverable critical path. The stream counters report their actual RTL
predicates: candidate-valid cycles include grant cycles, and controller/bridge
idle with candidate valid does not imply the candidate was unserved. They are
not converted into a predicted latency improvement.

## Actual validated milestones

Times below are packet-complete to validated-ready from the selected paired
JSONs, including any admission queue. Each mode-1/mode-2 pair has identical
500 producer source pins and identical immutable packet release cycles. The
binary parameter differs. The baseline examples come from the explicitly
selected older traces; no source-equivalence claim is inferred for their
later producer revisions.

| Cohort | Frame | Baseline ms | Conservative mode 1 ms | Overlap mode 2 ms | Mode 2 minus mode 1 ms |
|---|---:|---:|---:|---:|---:|
| 0 | 0 | 14.08760 | 14.13410 | 14.13410 | 0.00000 |
| 0 | 1 | 28.76078 | 31.18542 | 28.64745 | -2.53797 |
| 0 | 2 | not in selected trace | 29.74557 | 26.41133 | -3.33424 |
| 0 | 3 | not in selected trace | 29.83092 | 25.71498 | -4.11594 |
| 3 | 0 | 21.62758 | 21.65702 | 21.65702 | 0.00000 |
| 3 | 1 | 35.63473 | 37.66016 | 35.47300 | -2.18716 |
| 3 | 2 | 38.02204 | 40.56410 | 37.71609 | -2.84801 |
| 3 | 3 | 39.03891 | 44.03127 | 38.82782 | -5.20345 |

These are observed paired differences. In cohort 3 the queue changes with prior
frame completion, so a per-frame difference also reflects that dependency.
None of the selected frames validates in under 10 ms. Full histories and
sustained-source conclusions belong to the separate campaign.

## Exact command counts and interaccept distributions

For every delta, candidate writes are 32,400 BL8 commands and HUD writes/reads
are 2,640 each. Baseline reference reads are 31,224; prefetch reads are 32,400,
including the 294 hidden tiles (1,176 additional BL8 reads). LCD counts differ
because display requests are timed work over different actual transaction
windows. The table gives admission-through-ACK counts for frame 1; the JSON
contains all frames, explicit zero counts, and both window scopes.

| Cohort | Mode | P0 reference reads | Candidate writes | HUD reads | HUD writes | LCD reads | Prefetch reads |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0 | 0 | 31224 | 32400 | 2640 | 2640 | 66288 | 0 |
| 0 | 1 | 0 | 32400 | 2640 | 2640 | 71184 | 32400 |
| 0 | 2 | 0 | 32400 | 2640 | 2640 | 66288 | 32400 |
| 3 | 0 | 31224 | 32400 | 2640 | 2640 | 83564 | 0 |
| 3 | 1 | 0 | 32400 | 2640 | 2640 | 88992 | 32400 |
| 3 | 2 | 0 | 32400 | 2640 | 2640 | 83205 | 32400 |

Interaccept examples below use those same frame-1 windows. Every entry is
`min / nearest-rank p50 / p99 / max` in memory cycles (10 ns each). Full exact
histograms, per-client read/write splits, all frames, and consecutive-command
endpoint pairs are in the artifacts.

| Cohort | Mode | Candidate-write gaps | HUD combined gaps | LCD-read gaps | Reference-read gaps |
|---|---:|---|---|---|---|
| 0 | 0 | 16 / 20 / 568 / 2984 | 18 / 48 / 234 / 254 | 18 / 26 / 52 / 192566 | 18 / 22 / 550 / 15490 |
| 0 | 1 | 16 / 45 / 430 / 2791 | 18 / 44 / 236 / 260 | 18 / 26 / 52 / 192538 | 26 / 45 / 428 / 40370 |
| 0 | 2 | 16 / 37 / 432 / 2866 | 18 / 44 / 236 / 260 | 18 / 26 / 52 / 192555 | 26 / 37 / 428 / 40370 |
| 3 | 0 | 16 / 20 / 818 / 4598 | 18 / 48 / 234 / 262 | 18 / 26 / 52 / 192544 | 18 / 30 / 815 / 5654 |
| 3 | 1 | 16 / 45 / 576 / 4067 | 18 / 44 / 234 / 260 | 18 / 26 / 52 / 192610 | 26 / 45 / 580 / 76062 |
| 3 | 2 | 16 / 37 / 590 / 3984 | 18 / 44 / 234 / 260 | 18 / 26 / 52 / 192552 | 26 / 37 / 600 / 76062 |

## Tile ordering and the remaining conversion

All 93,672 accepted prefetch lookups return after exactly one cycle. Baseline
frame-1 lookup-to-response medians are 73 cycles in cohort 0 and 77 in cohort 3.
Mode-2 candidate W-to-D median is 138 cycles in every selected delta, versus
65/69 in those baseline examples; mode-1 medians are 174 or 178. W-to-D includes
physical memory work and held retirement before the receiver's completion;
there is no separate backend-terminal-completion event to isolate that hold.
The shorter accepted reference response therefore does not establish removal
of the physical read/write workload.

For every one of the 8,099 noninitial tiles in every prefetch delta, F precedes
D of the previous full-walk ordinal. The latest lead is 19 cycles in mode 1
and 11 in mode 2. Accepted Q can occur before or after previous D; next W is
always after previous D, often one cycle later. F-to-Q median is one cycle,
but its long tail and the lack of first-valid Q prevent a claim that all fill
latency was hidden. The artifacts preserve every signed difference rather
than inferring consumer demand from its accepted handshake.

The last coordinate-matched prefetch command acceptance to F takes values 24, 28, or 32
cycles across tiles in both modes. It includes the physical read, bridge
snapshot, and core fill conversion; the trace cannot isolate those stages.
Successive same-tile block command gaps have median 42 cycles in mode 1 and
34 in mode 2. Even restricting to adjacent physical commands with no other
accepted command in between leaves a 26-cycle minimum and median in both
modes. Mode 2 has 2,370/1,699/1,509 such intervals in cohort 0 frames 1/2/3 and
4,895/4,850/4,916 in cohort 3. This is evidence of a repeated finite path to
investigate, not an estimate that its gap is removable.

Source inspection gives the implementable next experiment: the unchanged V74
bridge already returns a complete 128-bit BL8 snapshot; the adapter then emits
eight accepted 16-bit beats, and the frozen V79 core cannot request its next
block until that stream completes. A separate wide-fill variant could consume
one 128-bit block handshake instead. The existing mode-2 overlap remains the
control. This experiment should preserve all physical commands and compare
actual validated milestones; no seven-cycle-per-block subtraction is offered
as a speedup prediction.

The proposed wide contract, for a future version, is:

1. Keep the same canonical address sequence and four BL8 blocks per 512-bit
   tile. A held 128-bit response is stable until valid/ready acceptance, with
   data bits `[16*i+:16]` equal to the old stream's beat `i`.
2. Capture generation, reference bank, plane, tile, and block on accepted raw
   request; authenticate them against the pending fill slot. A block is
   committed once, a tile becomes FULL only after four successful blocks, and
   accepted physical ownership remains distinct from a held block response.
3. Preserve the two-slot bound, generation lease, independent candidate-write
   P0 ownership, hidden-tile retirement, and authentication of actual candidate
   write completion before reference-bank translation. No bank may release
   while an accepted physical read or held block response remains.
4. Abort/fault consumes or cancels the accepted block exactly once, returns a
   matching error for accepted decoder lookups, drains actual controller work,
   and never publishes a canceled block as successful reference data. Exercise
   abort on the block-accept edge and with a concurrent candidate write.
5. Before performance comparison, add trace events for first asserted lookup
   valid, raw request acceptance, bridge snapshot acceptance, core block commit,
   and actual backend write completion. Those events can distinguish demand
   waiting, conversion, arbitration, and held retirement without relying on
   controller interaccept gaps.

No RTL is changed by this analysis. The seven reference-wrapper component
cases, four actual-SDRAM overlap mode/corner configurations, and latest full
system fault campaign pass separately, with their exact result hashes bound
in `separate_validation_evidence`. The full fault campaign covers two rejects,
an accepted raw-read/abort coincidence, physical drain, retained reference/HUD,
and recovery; it does **not** cover a simultaneous pending decoder lookup at
that abort. No combined pending-lookup coincidence coverage is claimed here.
