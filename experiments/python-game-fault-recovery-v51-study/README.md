# V51 receiver fault and keyframe recovery

This study replays deterministic packet loss, corruption, identity failure,
duplicates, reordering and retry against the V48 arithmetic-only stream receiver.
An independent replay runs the same deliveries through the V43 direct receiver.
Both are software receivers using archived packets; no network, socket, FPGA,
ESP32, panel or new encode is involved.

## Recovery results

The campaign has 24 cases: six fault traces for each of four v40 source cohorts.
It reuses 33 source frame IDs per cohort across those cases (132 distinct source
IDs total). The aggregate log reports 804 delivery actions, 800 receiver calls,
588 accepted packets, 212 rejections and four dropped packets. Every case
recovers through the independent periodic key at frame 24 and accepts through
frame 32. Rejected, duplicate and out-of-order inputs leave receiver state
unchanged; valid output reference and HUD/display hashes match the retained
source records.

| Fault plan | Behavior |
| --- | --- |
| Drop frame 7 | No receiver call for the dropped packet; dependent frames reject until key 24. |
| Corrupt frame 7 | CRC failure and unchanged committed state; dependent frames reject until key 24. |
| Bad identity tag at frame 7 | Tag validation rejects without publishing state; key 24 restores the chain. |
| Duplicate frame 6 | Duplicate is rejected without advancing state; ordered delivery continues. |
| Reorder frames 7 and 8 | Out-of-order frame is rejected; state remains at the last accepted frame. |
| Retry frame 7 | Corrupted attempt rejects, then valid retry can be accepted without state damage. |

These are deterministic stored-packet traces, not elapsed recovery times. The
scenes have different source cadences, and no network keyframe request or
transport resynchronization is implemented. The final keyframe recovers these
software histories; this does not prove panel recovery or a physical display
fence.

## Evidence and limits

The benchmark makes 800 actual V48 receiver calls across the 24 scenarios.
Independent V43 replay checks all deliveries and confirms 24/24 cases recover,
all rejected states remain unchanged, valid outputs match retained source data,
and no encoder is called. The verifier reports `transport_or_physical_display_recovery_proven: false`.

The study establishes atomic software state handling and periodic-key recovery
for these packet traces. It does not establish recovery latency, real network
behavior, USB/UART transport semantics, FPGA/ESP32 recovery, panel behavior or
30-fps operation.

```sh
/home/lori/gamebub-streaming-prototype/.venv/bin/python benchmark.py
/home/lori/gamebub-streaming-prototype/.venv/bin/python verify.py
```
