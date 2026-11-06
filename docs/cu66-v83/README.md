# V83 causal pipeline study for the application-specific codec

V83 advances V82's COPY-aware execution profile from separate work counts to
**causal Python schedules**. Hashing waits for group payloads and child digests;
reconstruction waits for inverse results and reference reads; publication waits
for stores, maps, content sealing and HUD readback. Four independently reset
histories contain **457 native sources**, evaluated in **eight configurations**.
All **3,656 schedules** completed their in-process timeline audits and retain
the same native content roots/seals and priced work counts as V82.

This is a prospective architecture study, not a new FPGA decoder or measured
speed. It preserves the existing quantized pixels and residual entropy coding
as its data baseline; it does not improve bitrate or introduce a deployed wire
format. V82's explicitly negotiated content-commitment semantics remain a
prerequisite for avoiding the old full-frame SHA reads.

## Conditional results

All times below are isolated-source model milliseconds at an assumed 100 MHz,
with 64-cycle inverse and 64-cycle reconstruction tasks unless indicated.
"Current intervals" means 18 clocks/read BL8 and 16 clocks/write BL8; it does
not mean the current RTL executes with this latency. Each task is charged its
entire interval, including the last operation. Group size is 16 tiles.

| Configuration | Minimum ms | Median ms | Maximum ms | Sources below 10 ms in this model |
|---|---:|---:|---:|---:|
| One group, one SHA lane, current intervals | 3.79365 | 12.05550 | 15.42237 | 140/457 |
| Four groups, one SHA lane, current intervals | 2.91192 | 8.45600 | 11.70392 | 413/457 |
| Four groups, four SHA lanes, current intervals | 2.91192 | 8.45600 | 11.70392 | 413/457 |
| Four groups/four lanes, current intervals, 20% reserved | 3.67096 | 10.63560 | 14.73432 | 182/457 |
| Four groups/four lanes, hypothetical 12-cycle service, 20% reserved | 2.54120 | 7.43448 | 10.38344 | 417/457 |
| Four groups/four lanes, idealized 8-cycle service | 1.34248 | 4.00872 | 5.51432 | 457/457 |
| Four groups/four lanes, idealized 8-cycle service, 20% reserved | 1.68280 | 5.02904 | 6.89432 | 457/457 |
| Same idealized reserved case, inverse cost increased to 256 cycles | 1.68280 | 8.45480 | 20.00425 | 291/457 |

The 20% reservation blocks clocks 0–1999 of every 10,000-clock period, restarting
at phase zero for each source. It is illustrative interference, not actual
LCD/refresh traffic or deadline qualification. Eight clocks/BL8 is only the x16
payload-transfer ideal, with no command, row or turnaround cost. Twelve-cycle
service and the compute costs are also unimplemented assumptions.

## What to implement first

**Bounded group buffering is the useful next experiment.** With memory service
and SHA lanes held fixed, increasing one group to four improves every source's
conditional schedule: paired reductions are **0.66296–4.72168 ms**, median
**3.57657 ms**. Four SHA lanes instead of one, with four groups held fixed, help
only the 20 keys by **0.08897 ms each**; all 437 deltas are unchanged in this
current-service comparison. This supports starting the RTL experiment with four
groups and one SHA lane, then reassessing lanes if memory service changes.

Memory service remains decisive. The cold delta requires **68,904 data/HUD BL8
operations**. With the illustrative 20% reservation, a necessary average for
strictly less than 10 ms is below approximately **11.61 clocks/operation**,
before unhidden computation or additional arbitration loss. Faster SHA alone
cannot satisfy that requirement. The slower-inverse sensitivity also shows
that an idealized memory result cannot establish the full decoder's timing.

**Four output groups are 4 KiB, not the complete workspace.** Conservatively
reserving 64-byte references, the existing 192-byte signed-24-bit inverse
results, and 64-byte output tiles across four groups requires **20 KiB**.
The four retained full witnesses observe combined staging peaks from 4,288 to
14,912 bytes under this accounting. The existing g16 tree/maps add 71,547
logical bytes and cloning uses another 32-byte temporary. Coefficients,
dequant/inverse working storage, hash state, bounded descriptors, control,
response FIFOs, ports and RAM rounding still need an implementation budget.

## Evidence and limits

The evidence verifier checks all 3,656 retained rows against native identities,
V82 roots/seals, priced counts, source archives and independently recomputed
statistics. **37 scheduler checks, 206 workload checks and 10 auditor checks**
pass. Four complete DAG/timeline witnesses are retained and independently
reaudited; the remaining 3,652 have in-process audits, timeline hashes and
summaries, rather than retained full timelines. Generic timeline validation
checks supplied edges; selected structural tests are not a formal proof that
every required dependency was modeled.

The model starts with encoded input and tile modes available. Entropy/dequant
arrival timing, actual ESP32 forwarding, physical bank leases, hardware FIFO
backpressure and RAM/hash-input port timing remain outside it. A hardware
implementation must generate bounded streaming control, not retain the entire
Python future-task graph. The corpus is four reset histories from one gameplay
walkthrough family. No sustained 30-fps, strict validated under-10-ms, target
fit/timing, or HEVC/AV1 quality/bitrate milestone is closed.

- [Pipeline architecture and staged RTL experiments](pipeline-design.md)
- [Application-specific codec and milestone plan](next-steps.md)
- [Evidence scope and reproduction](evidence-scope.md)
- [Audited aggregate results](../../experiments/python-gamebub-v83/summary.json)
- [Controlled paired comparisons](../../experiments/python-gamebub-v83/tradeoffs.json)
- [Workspace analysis](../../experiments/python-gamebub-v83/workspace.json)
