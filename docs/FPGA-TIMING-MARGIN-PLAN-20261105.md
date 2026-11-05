# FPGA design improvements for repeatable timing margin

Date: 2026-11-05. Planned work, not implemented improvements or hardware results.
This supplements the [coordinated 30 fps plan](COORDINATED-30FPS-PLAN-20261104.md).
Use the [timing cleanup status](FPGA-TIMING-CLEANUP-STATUS-20261105.md) for exact
versions, hashes, executed tests and the selected image.

## Starting point and engineering target

The selected CPL1 diagnostic meets its declared routed timing at the original
clocks: setup +0.017 ns, hold +0.032 ns, pulse +2.000 ns; all four bus-skew
constraints meet. Its final physical recipe includes an equivalent QSPI FSM-bit
copy. This is a valid measured pass with small margin. Keep its sealed source,
checkpoint, BIT and reports unchanged as the comparison and rollback artifacts.
Installed v30/build50 stays unchanged during offline development.

Proposed next-candidate promotion target: **at least +0.250 ns routed setup
slack**, positive hold/pulse/bus-skew slack, zero violations and zero routing
errors, at the same clocks and external budgets. Report the minimum result from
three fresh implementation runs: two reproductions of the canonical recipe and
one explicitly documented, supported alternative implementation strategy. This
is an engineering margin target, not an achieved result or a retroactive change
to the existing timing pass. It does not establish board I/O signoff.

Preserve the 100 MHz processing/memory and 200 MHz service clocks, existing panel
and read-clock relationships, pins and delay budgets. Do not obtain margin by
reducing frequency, relaxing uncertainty, adding multicycle paths to ordinary
single-cycle logic, cutting synchronous reset paths, or reducing profile/buffer
limits silently. Keep the 17 missing-input-delay, two missing-output-delay and
one partial-input-delay coverage gaps visible; review those interfaces separately
against board/device timing evidence.

## Prioritized design work

| Priority | Improvement | Implementation notes and evidence required |
|---|---|---|
| 1 | Move measured FSM replication into maintainable RTL or a supported synthesis recipe | Reproduce the successful parallel state-bit copy without depending on incidental synthesized LUT suffixes or an opaque late ECO. Give local decode consumers separate registered drivers where routing dominates. Preserve identical D, clock, CE, reset, INIT and inversion behavior. Compare original and replicated versions cycle-for-cycle, including QSPI writes, reads, IRQs, CS transitions and reset. |
| 2 | Break identity/error/control chains at complete transaction boundaries | Target the observed owner/epoch/tag-to-state, HUD-enable and transpose-control paths. Reserve a complete tuple: payload, owner, epoch, frame, index/coordinates, last and associated status. Register validation results or validated descriptors before high-fanout use. Never pipeline payload without its identity and valid/error controls. |
| 3 | Reduce bounded arithmetic and counter widths | Derive widths from proven capacities. Retain full-width wire/header validation before narrowing. Use sized constants, cached end offsets and remaining-byte counters instead of repeatedly subtracting/multiplexing wide bounds. Preserve overflow rejection, error priority and legal maximum-size inputs. |
| 4 | Improve SHA control and, only if measured necessary, compression timing | Evaluate the existing byte-write reservation, final-byte flush, bounded tag-validation and counter-width experiments separately. Preserve bit-exact SHA results and the entire owner/epoch/tag check before completion. Change compression-round arithmetic only after its actual routed path is limiting. |
| 5 | Reserve complete memory commands before physical dispatch | Evaluate the prepared command reservation against accepted-request dispatch. Hold address, write/read kind, mask, data and client identity through dispatch. Pending commands must prevent an idle certificate. Cancellation must drain already accepted work and release ownership only after physical completion. Measure extra clocks per burst and the effect on LCD service. |
| 6 | Localize remaining high-fanout control; floorplan only measured residuals | Classify reset, enable, valid, flush/discard and status nets by load count, physical span and routed delay. Use small local registered enables or equivalent driver copies where justified. Try coarse placement of related logic only after RTL changes; retain a portable, explicit constraint recipe and measured before/after results. |

Start each change from a named source freeze. Keep changes isolated for A/B
measurement; combine them only after their own correctness and routed results
are known. A later candidate number or an OOC improvement is not an adoption gate.

## Pipeline and ready/valid rules

- Prefer elastic stages with a bounded occupancy and no data bypass when the
  objective is to split a long combinational path. Keep accepted output stable
  under backpressure; avoid READY-to-VALID-to-cancel feedback loops.
- Preserve one-sample-per-cycle throughput where the existing service provides
  it. Record added latency, capacity and the actual initiation interval for each
  stage. A deeper pipeline can improve MHz while making frame throughput worse.
- Include every new pending slot in start admission, completion, idle, bank
  release, cancellation and reset fences. Drain cropped physical tails before
  releasing a block. Never complete a frame while its tag validation is pending.
- Keep invalid/error transfers masked according to the existing interface
  contract. A previously accepted private operation may retire only where that
  contract permits it; it must never publish stale data. Re-derive and test any
  changed cancellation/drain bound rather than assuming the prior 16-cycle
  observed release remains universal.
- If a SHA round is split across cycles, preserve atomic a/b/c/d/e/f/g/h and
  rolling-schedule updates, padding and the final round/block transition. Count
  the additional cycles across every block and every hash engine before adoption.

## Replication, fanout and reset rules

Use reports to distinguish logic depth from wire delay. The earlier near-passing
QSPI path had roughly 59 state-bit loads and 70 decode loads; refresh these counts
on each new checkpoint instead of treating them as permanent design properties.
Target the limiting consumer group rather than applying blanket max-fanout or
DONT_TOUCH directives throughout the design. Record replica count, load split,
LUT/FF cost, clock load and effects on both source and destination paths.

For equivalent FF replication, prove equal initialization/reset behavior and
equal D/C/CE/reset inputs and inversion parameters. Prove that each transferred
transaction sees the same logical state; account for reset assertion and release.
Use the minimum preservation attributes needed to retain intentional copies.

Do not repeat blanket reset replication without new evidence: the guarded
distribution experiment regressed setup to -1.452 ns and was rejected. If reset
distribution is again limiting, preserve the protected synchronizer prefix,
review the final distribution stage separately, and verify asynchronous
assertion, synchronized release and clock-loss behavior. Any local copy must
preserve the required reset sequence; recovery/removal and CDC need review.
An asynchronous PRE/CLR exception is not permission to cut downstream synchronous
Q-to-R/D/CE paths. Do not duplicate CDC synchronizers as ordinary enable nets.

## How to use the existing experiments

| Candidate or work item | Current evidence | Next action before adoption |
|---|---|---|
| Selected raster-reservation source plus equivalent physical FSM copy | Full native-board model, routed timing and generated BIT pass | Reproduce the complete canonical build; replace the late copy with a maintainable source-level or synthesis-controlled implementation and compare margin |
| Tag-validation candidate | Full model and directed metadata/fault/cancel/late-hold tests pass; alternate route setup +0.003 ns, hold +0.016 ns | Keep as a comparison branch; its margin is below the proposed new target. Run whole-core lifecycle tests for any combined successor and obtain its own image binding |
| SHA counter-width corrected v002 | Default-bound known-answer/boundary suite: 27 cases, four negatives, 297 reset/abort cases | Test parameter boundaries and high-bit length aliases; implement the actual combined board and replay the full fixture. No routed/image claim yet |
| Complete memory-command reservation | Prepared source only | Test queued/issued cancellation, poisoned post-accept inputs, arbitration, command stability, idle certificates, physical drain and line deadlines before whole-board promotion |
| Pixel reservation, replay descriptor and SHA byte-write stages | Individual and combined records are in the timing cleanup history | Reuse exact tested files only; quantify the combined change instead of assuming independent gains add together |

## Verification and promotion sequence

1. Rebuild the current qualified source in a fresh directory, including every
   recorded physical step. Capture top path families in both clock domains,
   fanout/span/net-delay data, resources and source/constraint/asset hashes.
2. Screen one proposed RTL change with focused numerical, boundary, ownership,
   stall and reset/abort tests. Load the intended clocks before synthesis.
   OOC or synthesized estimates are screening evidence only.
3. Exercise every new pipeline phase and pending slot: empty/full, held output,
   final byte/sample, cropped tail, early/delayed error-ready, reset/abort,
   stale owner/epoch and fresh-job recovery. Compare complete output tuples and
   golden CRC/tag/pixels. Preserve malformed and maximum-size rejection behavior.
4. Run the actual-top native-pad/QSPI model and independent fixture checker,
   plus accepted-burst cancellation, late-tag failure, concurrent writes/reads
   and scanout. Require positive modeled line-service lead and no missed latch
   or underrun under the specified contention workload. Retain known starvation
   counterexamples; do not turn a conditional arbitration guarantee into a claim
   of an unconditional deadline.
5. Route the complete intended design at its original constraints. Require the
   proposed margin target across the documented fresh runs, all timing/bus-skew
   checks, complete routing and zero native DRC errors. Retain warning and CDC
   inventories. Include any telemetry/build-identity logic before the final
   qualified route, not as an unqualified later addition.
6. Generate the image from the selected checkpoint and seal exact sources,
   constraints, assets, build steps, numerical/lifecycle/model evidence, reports,
   licenses and hashes. Keep failed trials and the prior working control.
7. Coordinate a separate hardware window: verify loaded identity and recovery,
   first run the restricted local fixture, then test cancellation/reset and
   physical memory/display behavior. Keep ESP32/host behavior fixed for this FPGA
   comparison. No automatic flashing or new stream is part of these plan notes.

## Keep timing closure separate from the 30 fps capacity gate

Measure complete valid-frame service and steady-state initiation interval before
claiming more throughput. At 100 MHz, 33.333 ms is approximately 3.333 million
cycles; overlapping stages may have a longer end-to-end latency, but must sustain
one new frame per interval without progressive backlog. Report decode, each hash,
patch/HUD, memory drain, bank-ready, publication and presentation waits separately.

The current fixed-ROM diagnostic produces one unique input with CAPS=0; repeated
scans do not provide this benchmark. A sustained test needs distinct-frame input,
ownership-safe bank reuse and an agreed receiver/host contract. Preserve the
coordinated FPGA-only, concurrent-receiver and then physical unique-presentation
gates. Keep the 30 fps objective and the separate audio/controller coexistence
qualification unchanged. Do not reuse JPEG ports or advertise unsupported custom
profiles as a side effect of a timing optimization.
