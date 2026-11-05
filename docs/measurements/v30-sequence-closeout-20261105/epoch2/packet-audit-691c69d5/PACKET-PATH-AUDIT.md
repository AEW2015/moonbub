# Retained packet-path audit — frames 2,013,421 and 2,013,422

Read-only evidence analysis. No device queries, hardware runs, firmware/config
changes or fix selection. V30, build50, overlap and 32 slots remain unchanged.
`path-audit.json` binds the selected events, exact sources and downloaded
Windows JSON snapshot; its SHA-256 is
`fb6c126dd13a15fdc4051f2b04377e2665e3aeda5ed1a9cc3a477e88a4ca7634`.

Windows source: https://github.com/AEW2015/Sunshine/blob/691c69d5/tools/gamebub/measurements/v30-requested-packet-times-20261104.json

## Identity and clock limits

Host capture identities are 2,013,421 / `1793859711151542` Unix µs and
2,013,422 / `1793859711202169` Unix µs. All requested packets and both SOFs have
successful host post-send records. These are not NIC/RF departure timestamps.

**The receiver trace does not store numeric `capture_us`.** `diagnostic_position`
copies only frame ID/offset/validity; the retained Event/Failure schemas have no
capture field or raw UDP bytes. The receiver-side join is consequently by
frame ID and offset within this unique run, with the host capture value carried
as a host identity label. A fully independent three-field join cannot be made.
For 421/5,120, reason bit 64 alone establishes that its capture field and other
checked metadata matched the receiver's accepted SOF; it does not reveal the
numeric capture value. Zero capture-mismatch bit is not a logged timestamp.

All receiver times below are **ESP monotonic microseconds**. Host monotonic
seconds are reported separately and never subtracted from ESP values. UART
log-prefix ticks and recorder wall time are not substituted for ESP event time.

## Frame 2,013,421

| Offset | Host successful post-send, monotonic s | ESP socket return | ESP enqueue-boundary observation | ESP dequeue | Assembly evidence |
| --- | ---: | ---: | ---: | ---: | --- |
| 3,072 | 1354793.5134483 | 433741371 | 433741480; pre-submit q=7 | 433758765; post-pop q=12 | Incoming ID 2013421; pre-accept active ID 2013421, expected 3072. Recycle 433758978 and Complete 433759009 retained. Acceptance is supported by the next active expected offset advancing to4096; there is no separate assembly-accept event. |
| 4,096 | 1354793.5164743 | **Not retained** | **Not retained** | **Not retained** | No incoming-packet observation or per-ID rejection retained. The expected-offset value4096 is assembler state, not observation of this datagram. |
| 5,120 | 1354793.5196654 | 433742481 | 433742577; pre-submit q=8 | 433759091; post-pop q=11 | Incoming ID 2013421, active ID2013421, expected4096. Failure/trigger433759380, detail64: offset-only Sequence rejection. |

**4,096 is last positively observed in the Windows successful post-send record,
at1354793.5164743 s. There is no positive receiver-side observation of it.**
This does not establish that the socket never returned it: 2,376 trace calls
were lost, without per-kind/per-packet localization. A missing record cannot be
classified as network loss, enqueue loss, consumer rejection or reordering.

The Enqueue record is emitted only after successful channel submission, while
its timestamp and q sample are taken immediately before that operation. It
therefore proves successful submission but does not timestamp an atomic queue
push. Dequeue time is the immediate receive-return observation. At Enqueue the
producer does not sample assembler state: active-valid=0 means **not sampled**,
not a proven inactive assembler. Consumer active fields are pre-accept snapshots.
Packet acceptance is separate from FPGA forwarding/commit/presentation.

## Cleanup after 421/5,120

`protocol::Receiver::accept()` calls its software `abort()` before returning a
Sequence error, clearing active assembly, offset and CRC accumulator. Thus the
software reset occurs after the pre-accept snapshot and before the Failure event
at433759380; no distinct reset event/time was logged. The stream error handler
then clears the DMA batch, records Failure, requests FPGA recovery for an open
frame, calls receiver.abort again, updates counters/status and replies. That
ordering is source-derived, not a complete per-stage executed-event trace.

The first offending packet's Recycle and Complete are not retained; its failure
table completion duration is **unavailable**, not zero. Exact cleanup/FPGA-abort
completion time and per-stage duration cannot be recovered. A contended Complete
is plausible but not proven. Ring freezing alone does not suppress failure-tail
association, which runs before the frozen-ring return.

Positive subsequent consumer observations are:

| ESP time | Incoming packet | Consumer assembly / nearby queue |
| ---: | --- | --- |
| 433768101 | 421/7,168 dequeue | No active assembly; q=13. |
| 433770479 / 433770731 | 421/7,168 recycle / complete | Recycle retained; full consumer duration2626 µs. Context remains the pre-accept inactive snapshot. |
| 433770907 | 421/9,216 dequeue | No active assembly; q=13. |
| 433773802 | 421/12,288 dequeue | No active assembly; q=13. |
| 433777143 | 421/13,312 dequeue | No active assembly; q=13. Last event in the frozen ring. |

Continuation errors from already-dropped421 do not create a new first-failure
identity each time. No per-event reset/admission history can be invented from
global phase maxima. The observed inactive contexts confirm reset consequences,
not the exact duration or every intermediate operation.

## Frame 2,013,422 and its SOF

- SOF offset0: host successful post-send at1354793.5550626 s, capture label
  `1793859711202169`. **No retained socket-return, enqueue, dequeue,
  admission or rejection event for this SOF.** Its receiver path is unobserved.
  It cannot be classified as definitely admitted, rejected or lost at a layer.
- Offset1,024: host post-send1354793.5574626 s; ESP socket return433744611,
  enqueue-boundary433744698, pre-submit q=12. The producer does not sample the
  active assembler here.
- Its Failure entry is433780214, sequence29159, detail128: incoming2013422/1024,
  **no active assembly** (active-valid=0; active zero is not frame0), dequeue
  context q=13. It was therefore consumed and rejected by assembly.
- Its exact Dequeue/Recycle/Complete event timestamps are outside the retained
  ring. The failure table retains a valid full dequeue-through-recycle duration
  of3219 µs; it does not retain an absolute completion time from which to recover
  the dequeue time. RX-return→Failure is35.603 ms, not pure queue wait.

The ring ends at sequence29154 before the second failure29159. This is a known
retention boundary, not evidence that422 stopped arriving. No active assembly
at1,024 proves only that no assembly was active **then**; it does not establish
that its SOF was never observed or accepted earlier and subsequently reset.

## Coverage and unresolved points

- Ring: epoch2,96 records,79 preceding + trigger +16 following,125.834 ms;
  sequences29059–29154. Trigger context is valid and not lost.
- Global trace losses:2,376 record calls; zero phase-publication losses;
  zero lost Failure calls, failure-table overflow or ambiguous-tail markers.
  Those counters do not locate losses inside this specific window or identify
  the first missing Complete call.
- Queue drops0; whole-run peak15/32, captured-window peak14. Queue samples are
  observations, not atomic occupancy tied to another event's later timestamp.
- A Failure table's q is its preserved dequeue-context sample. q11 at the first
  failure and q13 at the second are not fresh counter reads at Failure time.
- Receiver numeric capture timestamps, raw UDP payloads, NIC/RF arrival times,
  the missing datagrams' receiver paths and exact first cleanup timing remain
  unavailable. No fix is selected and no additional run was started.
