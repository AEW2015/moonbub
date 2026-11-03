# Offline streaming telemetry correlation

This isolated standard-library tool joins normalized per-frame JSONL events for
future host/receiver hardware runs. It does not change sender, firmware or RTL
code. The report keeps groups separate by both `session_id` and
`evidence_kind` (`hardware` or `simulated`). Simulated values are never merged
into hardware summaries.

## Event format

Each event is one JSON object with these required fields:

```json
{"session_id":"run-001","frame_seq":42,"frame_id":42,"stage":"capture","clock_domain":"host_monotonic","timestamp_ns":1234567890,"evidence_kind":"hardware"}
```

- `session_id` is a fresh identifier for one run/reboot/session. Do not reuse
  it across a reset whose frame IDs may restart.
- `frame_seq` is an unbounded, monotonically increasing session-local frame
  sequence assigned at capture. It disambiguates repeated wire IDs after wrap.
- `frame_id` is the finite-width ID carried through transport. The default width
  is 32 bits; use `--frame-id-bits` for a different protocol or test fixture.
- `stage` is `capture`, `encode`, `send`, `ingress`, `decoded`, or `presented`.
  `ingress` means the receiver accepted the complete frame. `presented` must be
  instrumented at the actual display/framebuffer swap boundary. An ingress ACK,
  decode completion, or LCD refresh counter is not a presentation event.
- `clock_domain` names the clock that produced `timestamp_ns`. Use
  `host_monotonic` for host `perf_counter_ns`, `receiver` for a monotonic device
  timer, or `simulation` for model/testbench time. Convert source units to
  nanoseconds before writing the normalized event. Timestamps from different
  domains are never directly subtracted.
- `evidence_kind` is exactly `hardware` or `simulated` and must reflect the
  source of the event. It is part of the grouping key.

A session/frame-sequence may have at most one event per stage. Repeated records
are reported as duplicates and that stage is excluded from latency calculations
for that frame because its timestamp is ambiguous. Differing raw IDs within a
single sequence are reported as ID mismatches.

## Clock calibration

Cross-clock latency is deliberately omitted unless the operator supplies both
an explicit offset and uncertainty, scoped to a session and evidence kind:

```json
{
  "run-001": {
    "hardware": {
      "receiver_minus_host_ns": 4000000000,
      "uncertainty_ns": 100000
    }
  }
}
```

The sign convention is `receiver_time = host_monotonic_time +
offset`. Thus `capture_to_ingress` is estimated as
`receiver_ingress - offset - host_capture`, with reported bounds of estimate
plus/minus the supplied uncertainty. Include synchronization error,
timestamping error, clock-read uncertainty, and worst-case relative clock drift
over the **entire measured session** in that bound. Treat the offset as constant
only within that stated uncertainty. A calibration from another run or boot is invalid; recalibrate after each boot
and use a session-local value. A session-start calibration is usable only if
its uncertainty conservatively covers clock drift through the end of that full
session. Otherwise, use session-local recalibration points and a documented
piecewise clock model. The program never estimates the offset from frame
traffic. Without a matching calibration,
cross-clock latencies have `status: not_computed`; same-clock intervals can
still be reported within their own domain.

## Detected gaps and interpretation

The report flags raw frame-ID wraps, unexpected ID regressions/steps, repeated
frame IDs, duplicate stage records, inconsistent IDs within a logical frame,
and missing ranges in capture sequences. It also lists captured frames missing
at later stages and stage events with no matching capture record.

These are telemetry coverage findings. A missing event can mean a dropped
frame, an unlogged event, or incomplete instrumentation; the tool does not
assign a drop cause. Ingress counts do not imply display. Only observed
`presented` events contribute to presentation coverage or capture-to-present
latency. Every output group retains its `evidence_kind` label.

The standalone Sunshine study sender can write normalized host events directly
with `--frame-telemetry PATH` (on the matching Sunshine study branch). Its
capture event uses `timestamp_ns` for capture start and also retains
`capture_end_ns` and `capture_wall_us` as separate fields. Capture start occurs
before source acquisition; skipped clip slots can add discarded-frame decoding
after that timestamp. Capture end follows selected-frame acquisition/decoding
and canvas fitting/scaling. Consequently capture-to-send includes source/canvas
preparation, encoding, queueing and local packet submission, not camera-only
capture time. Its `send` event marks local completion of packet submission.
Every record carries a run
`session_id` (fresh UUID by default; `--telemetry-session-id` coordinates it
with receiver instrumentation), capture-order `frame_seq`, and actual wire
`frame_id`. Optional
sender telemetry is bounded and can drop records; inspect its logging summary
before analysis. This host log has no ingress, decode or presented event. Do not
use send completion as receiver ingress or presentation, and do not relabel wall
time as monotonic time. The sender labels evidence `simulated` by default; use
`hardware` only for an actual identified hardware run.

Both `session_id` and `frame_seq` are host-only and are not sent in MSV1. For
receiver correlation, coordinate the session ID with instrumentation out of
band, then map observed 32-bit wire IDs to host capture sequences. Preserve the
session-local mapping across frame-ID wrap; raw IDs repeat after wrap and cannot
identify a unique capture on their own.

For sender capture/send-only analysis, pass the telemetry file directly to
`correlate.py`. If combining it with receiver events, normalize receiver events
to the same session ID, capture sequence and actual wire frame ID. Do not use a
different run's session ID or synthesize absent stages.

## Reproduce the synthetic example

From this directory:

```sh
python3 -m unittest -v
python3 correlate.py fixtures/synthetic-events.jsonl \
  --calibration fixtures/clock-calibration.json \
  --frame-id-bits 3 \
  --output fixtures/synthetic-report.json
```

The synthetic fixture includes separate hardware and simulation groups, a
three-bit ID wrap, a missing captured sequence, a missing ingress event, and a
duplicate ingress record. It is test data only; its calibration is illustrative
and makes no claim about actual hardware clocks.
