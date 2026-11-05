# CU66 v72 milestone checklist

Status: the prototype and stated functional/model campaign are complete. Exact target implementation, sustained 30 fps and target validated decoding below 10 ms remain open. See [the results and limits](hardware-handoff.md).

## Frozen inputs and evidence

- [x] Run `python3 scripts/cu66-v72/verify_baseline.py` before any v72 implementation work; retain its report only under `fpga/experiments/cu66-v72/`.
- [x] Keep frozen v69, v70 and v71 files and source pins byte-identical; preserve existing untracked marker-recovery files.
- [x] Record source revision, tools, commands, seeds, fixture identities and hashes for each v72 result. Do not overwrite prior evidence; use unique filenames in the v72 experiment directory.
- [x] Keep functional reconstruction, cadence, target implementation and physical evidence as separate verdicts.

## Write API review

- [x] Agree on partial-mask byte order and document byte-enable to active-low DQM mapping.
- [x] Define canonical four-word row placement within aligned BL8 upper/lower halves, painter eight-word mapping, address boundaries and scalar HUD fallback.
- [x] Define accepted-burst ownership, when final-beat completion becomes visible, and the required tWR/recovery interval before ACK/read visibility.
- [x] Define fault, partial-abort, reset and drain behavior for accepted and not-yet-accepted beats; prove no early ACK and no false successful completion.
- [x] Define cache invalidation across every enabled byte and all scalar/cache aliases. Review bounded buffering and producer backpressure for deadlock.
- [x] Record the agreed interfaces and independent findings in [the API review](api-review.md).

## Memory and system evidence

- [x] Cover all byte lanes and masks, both canonical half-burst placements, full painter bursts and scalar HUD writes.
- [x] Cover alignment/range rejection, overlapping cache aliases, simultaneous clients, read-after-write ordering, row/bank conflicts, refresh, response holds, and bounded grants.
- [x] Cover the stated controller prefix/reset positions, adapter burst aborts, memory errors, final recovery, lost-ACK retry and fresh progress; retain exact coverage scope in the handoff.
- [x] Run Verilator and Icarus with reproducible seeds and established tAC corners; retain exact logs and compare outputs.
- [x] Require exact standalone and full-system key/P reconstruction, canonical YUV/HUD/RGB equality, complete ordered rasters, no partial acceptance, and zero normal-load LCD underruns.
- [x] Compare identical model input/clocks against v71: P transaction 260.18963 ms and validated-ready interval 90.66040 ms. Label model time accurately and retain all queue time.

## Sustained presentation: 30 distinct new frames/s

- [ ] Demonstrate 1,800 distinct chronological source frames at declared fixed 30 fps arrivals; do not loop retained histories.
- [ ] Separately demonstrate a ten-minute physical run averaging at least 30 distinct new complete presentations per second in predefined fixed windows, with bounded age/backlog and no unexplained drops or unexpected normal-load underruns.
- [ ] Count frame IDs through source, attempt, acceptance, commit and complete presentation. Include warm-up, drain, failures and deadline policy.
- [ ] Exercise deployed transport, CPU/HUD service, memory clients, refresh, scanout and achieved clocks. Simulation, model averages and source estimates do not prove this gate.

## Validated decode latency: strict observed maximum <10 ms

- [ ] On target, measure each supported valid frame from immutable complete-packet availability through integrity-checked canonical YUV plus exact HUD stored, required writes drained and validated-ready.
- [ ] Include admission and queue wait, checks, entropy/reconstruction/hash work, HUD processing/transfer, actual CPU and memory service, and failed/late/recovery attempts. Keep queue wait separately reported but inside the headline interval.
- [ ] Require strict campaign maximum below 10 ms and report p50/p95/p99/max. Bind events to frame/generation IDs and account for clock uncertainty.
- [ ] Keep RGB composition, vblank, scanout and visible latency separate. A finite model run is not a target latency or universal WCET proof.

## Target and physical gates

- [ ] Close exact-device implementation, resource fit, routed timing, CDC, board constraints, SDRAM electrical behavior, panel correctness, live ESP32/QSPI transport and deployed processor service.
- [ ] Make no target-fit or physical claim until reports and board measurements establish it. No physical gate is satisfied by generic elaboration or RTL simulation.

## Evidence audit

Run `python3 scripts/cu66-v72/verify_evidence.py` after the controller, adapter,
painter, guard/control, full key/P, four-frame history, and comparison evidence
are finalized. It is read-only: it checks frozen baseline integrity, source and
log hashes, terminal PASS markers, qualified-run counts, exact output and
underrun counters, plus the superseded pre-reset-gate archive internally. A
missing or stale history/comparison/result is an audit failure, not evidence of
qualification. The audit scope is functional/model evidence only; it cannot
establish target fit/Fmax/CDC, physical 30 fps, or target sub-10-ms decode.

## Exact-target OOC preflight

- [ ] Exact part `xc7a100tcsg324-1` availability is still unresolved. The staged
      v72 source list and exact-target preflight are under
      `fpga/experiments/cu66-v72/build/`; inspect `status.json` and its pinned
      Tcl, source/spec/include hashes, tool identity and logs. The recorded
      `UNAVAILABLE_EXACT_PART` result is not synthesis or implementation
      evidence. Retry only when that exact part package is installed.
