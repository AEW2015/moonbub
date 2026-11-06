# Matched three-frame map A/B

Runs: `burst-oldmap-three01` and `burst-crossbank-three01`.
Both compile the same pinned BRAM/RGB-burst hierarchy with the same clocks,
checked-model variant, native HUD endpoint and chronological KEY0/P1/P2 bytes.
Only generated RTL/C++ memory-map selection differs. Source snapshots and
producer command/log bindings are retained in each run.

**Both pass complete reconstruction/readback; both fail clean scanout cadence.**

| Frame | Old-map clocks | Cross-bank clocks | Old-map transaction underruns | Cross-bank transaction underruns |
|---|---:|---:|---:|---:|
| KEY0 | 7,759,549 | 7,759,549 | 0 | 0 |
| P1 | 15,795,607 | 15,569,365 | 1,316 | 284 |
| P2 | 17,423,269 | 18,069,524 | 1,262 | 434 |

Final totals including the same3.5-million-clock tail are44,478,533clocks /
2,580underruns for the old map and44,898,546clocks /718underruns for the new.
Raw underrun totals are not normalized across differing transaction durations.
Neither meets the zero-unexpected-underrun gate.

Every frame matches518,400canonical bytes,384,000RGB565 words and21,120HUD
functional readback words. The deliberate lost P1 COMMIT ACK retries correctly.
P2 exercises the next canonical bank while RGB1 is front; it is646,255clocks
(6.46255ms at modeled100MHz) slower with the cross-bank map. The candidate
therefore changes contention rather than proving a universal throughput fix.

Cross-bank P1 ACT/PRE counts are163,402/141,566 versus198,127/179,234 old map.
Cross-bank P2 ACT/PRE counts rise to215,157/199,501 versus200,633/176,104 old map.
This is consistent with moving RGB1 traffic away from bank3 and into bank2,
where canonical2/HUD2 also reside. The independent display component A/B
isolates corresponding same-bank effects; these whole-system counters include
all concurrent clients and should not be mistaken for an isolated bus test.

No automatic map or cache-variant selection was made. These are modeled
functional/system experiments, not target-fit, routed timing, ESP32 CPU, live
transport, physical presentation or30fps acceptance results. Further work must
preserve exact output and ownership while reducing real service costs and
meeting the sustained native line period, not merely first-line lookahead.
