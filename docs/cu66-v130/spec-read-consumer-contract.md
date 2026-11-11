# V130 speculative admission read: consumer contract review

This note traces the selected full-parent consumers of the speculative
admission RAM data. It does not establish timing closure or a board-level
interface contract.

## Internal consumers

The V130 candidate drives both `replay_data` and `stage_read_data` from
`ram_data` (`fpga/experiments/cu66-v130-spec-read/admission_candidate.sv`,
lines 553 and 568). Its speculative physical read is enabled in `FETCH_REQ`
or `FINISHED`, with invalid replay addresses clamped to zero (lines 576–585).
The candidate keeps the logical response-valid and owner registers tied to
accepted requests: `replay_rsp_valid` is assigned from
`replay_req && replay_ready`, while `ram_addr` and `ram_epoch` update only on a
stage request or accepted replay request (lines 588–595).

The admission FSM uses `ram_data` in `FETCH_WAIT` to capture `byte_value`
(line 841); the corresponding public `stage_read_rsp` is true only in
`FETCH_WAIT` when reset, start, and abort are absent (line 560). The prepared
length calculation also samples `ram_data` only in `FETCH_WAIT` for the final
length byte (lines 374–377). The speculative read does not run in that state.
On reset/start/abort, the FSM reset branch takes priority over its state case,
so its state-machine consumer does not consume the data as a valid response.
The separate bounds-preparation block is not reset-qualified at this sampling
point, but it also samples only in `FETCH_WAIT`; the candidate does not issue a
speculative read in that state, so this change does not alter that sample.

In the selected parent, the admission instance is wired in
`fpga/experiments/cu66-v127-owner/cs88_coefficients_v91k.sv` lines 1196–1219.
Its `stage_read_data` output is connected to `unused_fork_data` at line 1210;
that net has no RTL reads. This is the candidate admission stage-data output.
The packet ingress has another, separate `stage_read_data` path. It is not
the candidate's signal and is unaffected by this experiment.

The active parent sets `REFILL_OVERLAP=1`
(`fpga/experiments/cu66-v115-owner/cs88_pipeline_v91k.sv`, line 384). In this
mode, `replay_data` enters the byte refill queue at coefficients line 1230.
The queue's `push_event` requires an active pending response with `rsp_valid`
and no block or response fault (`fpga/experiments/cu66-v121-request/byte_refill_queue_v91i2b.sv`,
lines 35–42); it writes `rsp_data` into storage only under `if(push_event)` at
line 86. Queue error/readiness logic does not inspect `rsp_data` when no
response is valid. In the non-overlap fallback, `refill_data` captures
`replay_data` only under `REFILL_WAIT: if(replay_rsp)` in coefficients lines
1333–1335.

The parent also exports `frame_read_data` and its response qualifier together:
`frame_read_rsp=replay_rsp` and `frame_read_data=replay_data` at coefficients
lines 1173–1177; the parent wrapper forwards these ports at
`fpga/experiments/cu66-v115-owner/cs88_pipeline_v91k.sv` lines 420–425. There
is no further RTL consumer of `frame_read_data` inside this parent hierarchy.
Existing controller benches use it only while checking a pending response,
for example `fpga/experiments/cu66-v127-owner/verification/tb_controller.cpp`
line 127 and the V129 live-guard bench at
`experiments/python-gamebub-v129/latency-monitor/full-parent/attempts/20261111T004718819050Z/sources/fpga/experiments/cu66-v129-observe/tb_keyframe.cpp`
lines 142–145.

## External boundary and comparison rule

These traces support valid-qualified use by the selected RTL's internal
consumers. They do **not** establish that every external wrapper or hardware
consumer treats the public `frame_read_data` port as meaningful only when
`frame_read_rsp` is high. The V130 change can alter that bus during invalid
cycles, so the external contract remains unconfirmed until the board wrapper
and every connected consumer are checked or the interface contract explicitly
declares the qualifier relationship.

Any paired or parent comparison must account for the bus difference only under
an explicit reviewed contract: compare `frame_read_data` on every
`frame_read_rsp` cycle, and compare all response-valid, request, address, epoch,
ownership, cancellation, error, and other public outputs at their required
cycles. Do not silently mask `frame_read_data` in a broad output comparator.
Record this precise exception in the comparison contract and keep an assertion
that every accepted read yields the original-cycle data/address/epoch response.
If invalid-cycle stability is part of the external ABI, the candidate needs a
separately proven hold mechanism or must be rejected.
