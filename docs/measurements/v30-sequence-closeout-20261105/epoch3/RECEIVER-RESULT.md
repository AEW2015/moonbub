# V30 baseline repeat, IDs 2013600–2014199

Physical run, 2026-11-05 Denver. Installed v30/build50, overlap, 32 slots and sender pacing retained. Requested 20 fps / 4 Mbps / Q25, saved Xonotic clip from offset zero; input-only AV, audio/injection off. Windows configuration and packet-capture completeness await host reconciliation.

| Counter | Starting | Final | Increase |
|---|---:|---:|---:|
| Received | 523 | 1045 | 522 |
| Decoded | 523 | 1045 | 522 |
| Presented | 523 | 1045 | 522 |
| Dropped frames | 2 | 5 | 3 |
| Core completed | 523 | 1045 | 522 |
| Core drops | 1 | 3 | 2 |

Packet queue: zero drops, empty after STOP, cumulative high-water 15/32. High-water was already 15 before this run and is not an isolated repeat peak. Socket errors zero. Core faults, overflow, underruns and transport overflow zero. No reboot was observed in the retained log.

AV active at receiver logger UTC 07:01:10.189, stopped 07:01:40.951. Power-save readback restored from NONE (0) to initial MIN_MODEM (1); entry/restore errors zero. These logger times are not synchronized host-send timestamps.

## Explicit failure records

| Incoming frame / offset | Active frame / expected offset | Detail | Queue context |
|---|---|---:|---:|
| 2013780 / 11264 | 2013780 / 10240 | 64: offset mismatch | 6 |
| 2013900 / 3072 | inactive | 128: inactive assembler | 5 |
| 2014109 / 1024 | 2014108 / 17408 | 121: multiple header/offset mismatches | 6 |

Epoch 3 is manually sealed and COMPLETE_EXPORT. Its 96-event rolling window froze on the first Sequence failure; all three failure identities were retained separately. Trace recorded=41531, overwritten=12425, lost_records=2085, lost_phase=0, queue_overflows=0, lost_failures=0, failure_overflow=0, ambiguous_tails=0, trigger_lost=false. Complete export does not imply lossless capture.

For 2013780, offset 9216 has positive RX/enqueue/dequeue/completion records. Offset 11264 has positive RX/enqueue/dequeue/failure/recycle/completion records. No positive event for offset 10240 is retained. The expected-offset field is assembler state, not evidence of that packet's arrival. Trace contention prevents interpreting absence as proven network loss. Later failures are outside the frozen packet ring, so their SOF/cleanup histories remain unknown pending other evidence.

## Camera

Correct camera is DirectShow index 2 (Razer Kiyo); index 1 produced a virtual logo feed and was stopped before the run. Correct recording: `../camera-baseline-repeat-kiyo-2013600`. Full-panel coverage spans START through STOP: 320 samples from 07:01:10.046 to 07:01:41.945 UTC, largest sample gap 110 ms. Six sampled images in `camera-contact.jpg` show changing gameplay with the full display visible. This establishes image updating, not an exhaustive absence of brief freezes or a calibrated unique-frame rate.

No further run or firmware/FPGA change was made. Host counts, capture point/interface/link type, capture-drop count and packet records remain pending. Correlate frame IDs, capture timestamps and offsets without subtracting clocks across machines; numeric capture timestamps are not stored by this receiver trace.
