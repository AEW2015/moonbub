# V122 retained row stall baseline

This is a read-only audit of the V121 retained parent traces. Recompute with
`python3 scripts/cu66-v122/stall_audit.py`; it uses only Python's standard
library and writes `experiments/python-gamebub-v122/memory-study/results.json`.
The script verifies the V121 functional-index receipt binding before reading
the parent terminal receipt and checks hashes for the two retained row event
streams. It also checks the V121 selected-source hashes, the original Source B
18-source manifest, and the V120 marker hashes, sizes, and nanosecond mtimes.

## Timing baseline

The retained V121 125 MHz result is WNS **−1.347 ns**, TNS **−3248.192 ns**,
and **9,407** setup-failing endpoints. The qualified Source B 100 MHz result
remains the unchanged control. The preserved V120 marker files still match
their original SHA-256, byte count, and mtime.

## Two row profiles

| Profile | Retained last-outer to validated commit | Difference vs profile 0 |
|---|---:|---:|
| 0 | 1,145,104 cycles | — |
| 1 | 1,553,197 cycles | 408,093 cycles |

The difference is observational. The two profiles have different randomized
accepted traffic, so 408,093 cycles is not a causal stall attribution. For a
strict target below 1,250,000 cycles, profile 1 must save **303,198 cycles**.
At an assumed complete-parent 125 MHz, these traces correspond to 9.160832 ms
and 12.425576 ms; this does not establish that the full parent meets timing.

Both retained row runs record 518,400 canonical bytes and 42,240 HUD bytes,
with 70,080 successful write requests and ACKs. Each request represents 8
expanded bytes (560,640 total), in the row-write model. For profile 0, the
abstract service model reports 280,320 data edges and 140,160 overhead edges;
minimum and maximum service are both 6 edges per request. Profile 1 reports
the same number of data edges, 840,385 overhead edges, and service gaps from
12 to 20 edges per request. Both use a queue bound of one and report no
physical SDRAM. These per-request data and overhead counts should not be
reduced to a single fixed latency for profile 1.

The guarded terminal record includes ordered `phase_edges` for canonical
input/drain, root, HUD delivery/digest, seal, commit, presentation, and
terminal. The instrumentation explicitly assigns one priority phase per edge,
so these phase counts partition start-to-commit edges (verified in the audit
output). They identify which phase owned an edge under that priority rule,
not which hardware operation was active. The `phase_stalls` vectors count
conditions that can overlap; don't sum them. Validation has fence milestones
but no isolated validation duration.

The explicit post-reconstruction tail (reconstruct-done to commit) is 145,763
cycles for profile 0 and 193,865 for profile 1. After the last outer event,
profile 1 spends 1,359,332 cycles before reconstruction completes, already
109,333 cycles above the 1,250,000-cycle threshold (109,332 cycles are not
enough because the target is strict). This localizes a pre-reconstruction
interval, but doesn't identify its cause or prove those cycles are removable.

## Hypothetical burst-service sensitivity

Run `python3 scripts/cu66-v122/burst_sensitivity.py` to regenerate
`experiments/python-gamebub-v122/memory-study/burst-sensitivity.json`. This
standalone standard-library calculation binds the V121 parent receipt and
profile-1 event hashes from the retained audit. It uses the observed profile-1
70,080 requests, each representing 8 expanded bytes (560,640 total), 280,320
data edges, and 840,385 overhead edges. The exact-rational model sweeps burst
sizes 8, 16, 32, and 64 bytes while holding data edges fixed and charging the
observed mean overhead per original 8-byte request once per modeled burst.
That mean overhead is a **policy assumption for sensitivity**, not a physical
latency calibration.

The JSON reports modeled total busy edges and savings from the 8-byte case,
then applies unhidden fractions 0, 0.25, 0.5, 0.75, and 1 to those savings.
These fractions describe possible overlap and out-of-fence effects; none is
measured. It also reports the minimum fraction needed to save 303,198 cycles
and meet the strict cycle target. This analysis does not claim a memory
controller change, measured SDRAM behavior, real frame rate, or hardware
result.

| Assumed burst | Modeled total busy edges | Saved busy edges | Minimum hypothetical unhidden fraction |
|---:|---:|---:|---:|
| 8 B | 1,120,705 | 0 | Not possible |
| 16 B | 700,512.5 | 420,192.5 | 0.721569 |
| 32 B | 490,416.25 | 630,288.75 | 0.481046 |
| 64 B | 385,368.125 | 735,336.875 | 0.412325 |

Separately, ideally removing or fully overlapping the 193,865-cycle measured
post-reconstruction tail leaves 1,359,332 cycles, still 109,333 cycles above
the threshold under strict comparison. This tail scenario is not combined
with burst savings because they may include overlapping HUD/commit work.

The raw row event stream contains transform and canonical completion events
with cycle timestamps; it does not contain per-cycle waits or RF, CPU, or
physical memory timing. Do not infer CPU decode time from reciprocal throughput
or assign the observed profile delta to a single bottleneck.

## Instrumentation needed next

For an exclusive accounting experiment, add per-cycle wait ownership counters:
`wait_producer_full_edges`, `wait_software_hud_edges`,
`wait_physical_request_edges`, `wait_hash_delivery_edges`,
`wait_service_edges`, plus `wait_reason_priority_edges` to resolve cycles with
multiple asserted conditions. Record `cpu_decode_active_edges`,
`cpu_decode_blocked_edges`, and `exclusive_stage_owner_edges`, and assert that
the mutually exclusive owner totals sum to elapsed cycles. Keep request,
service-data, service-overhead, ACK, canonical-validation, HUD-validation, and
commit timestamps and byte counts. A later memory-service experiment can
vary declared service edges and queue depth as explicit model parameters, but
must label outcomes as sensitivity cases until measured against physical SDRAM.

The script fails closed if the raw receipt binding, either 18-source hash set,
marker metadata, or retained row event counts differ. It records the retained
hashes and detailed terminal vectors in machine-readable results. No
simulation or hardware timing measurement was run for this audit.
