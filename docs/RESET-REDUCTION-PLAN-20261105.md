# Reset reduction and SDRAM diagnostic plan

The full CPL1 candidate has a measured job-reset fanout of 4,281 and a
9.496 ns routed reset path. Reduce unnecessary reset loads before considering
a global buffer. Keep the current clock frequencies, I/O budgets and recovery
contract unchanged.

## Implementation order

1. Isolate a fresh candidate from the capture274.5/CSA source. First remove
   runtime reset from the envelope's 128-bit base and HUD expected tags.
   Both are initialized at accepted job start before parsing or comparison.
   Put their updates in a separate clocked process so reset does not become
   an implicit clock enable on these 256 bits. Preserve the start clear and
   byte-write ordering. Keep state, validity, ownership and abort logic intact.
2. Compare the original and candidate envelopes through normal transactions,
   malformed input, stalls, reset and matched/stale aborts. Compare public
   outputs and readiness; permit private tag contents to differ only while
   no accepted transaction can consume them. Run both full-board timing-model
   fixtures and require the original golden canvas CRC.
3. Route the complete candidate and measure reset fanout, reset sinks, control
   sets, utilization and the new critical paths. Require positive setup,
   hold and pulse slack, complete routing and zero native DRC errors before
   generating a hardware image. Record failures without relaxing constraints.
4. Audit further datapath resets one module at a time. Require a concrete
   write-before-use argument and reset/abort recovery tests for each removal.
   Configuration INIT alone does not provide runtime cancellation or PLL-loss
   recovery. Invalid data must never become a valid result after reset.
5. If remaining control reset fanout still limits timing, evaluate local
   distribution registers after the synchronizer. Preserve coordinated
   assertion/release and interface quiescence; do not independently replicate
   asynchronous synchronizer chains. Evaluate BUFG distribution as a separate
   measured candidate only if necessary; retain reset setup/hold checks.

## SDRAM diagnostic in parallel

SDR1 implementation02 completed with +0.260 ns setup, +0.070 ns hold,
+2.000 ns pulse slack, all 6,151 routable nets routed and zero DRC errors.
It retains four vendor debug-IP DRC warnings. CDC review found a combinational
error reduction before the panel synchronizer. Register that status in the
source domain, rebuild in a new directory, and review CDC and timing again.
No image has been programmed from this build.

After qualification, generate a distinct SDR1 BIT/LTX, bind source/checkpoint
hashes and use volatile JTAG only. Capture raw SDRAM samples, response-valid
positions, independent expected/read words and timeout/error counters. Restore
the retained build50 image after the diagnostic as appropriate. A memory probe
pass is not full CPL1 correctness or network-streaming qualification.

## Status

The first candidate is `cp23-reset-tags-20261105-v001`. Directed comparison
passed 278,064 cycles, seven complete golden fixtures, four reset interruptions
in header/body, a matched abort and a stale abort. All public outputs were
compared cycle by cycle. This is directed simulation, not formal equivalence.
Both complete-board model runs pass the original `4c5725e5` golden CRC,
139 checks, 40 QSPI observer reads and 259,200 modeled pad writes. Routed
implementation02 remains in progress; bitstream generation requires its
positive final gates or a qualified physical-only derivative.
Implementation01 is retained as an exploratory run after a Vivado startup
directory error; it must not be used as clean qualification evidence.

SDR1 source-v005/implementation03 contains the registered source-domain panel
status correction and is rebuilding. No new hardware result or 30 fps result
is claimed. Build50 remains installed.

## Follow-on audit decisions

- Envelope `bh`/`hh`: selected first, 256 private bits. Split storage from the
  resettable process; job-start clear remains. The expanded negative/recovery
  comparison passes 475,986 cycles, nine complete golden fixtures, error
  reasons 1 through 6, and reset while holding a completed result. Full-board
  simulation and routed timing remain pending; no timing benefit is claimed.
- HUD decoder `reftag`/`newtag`: potential next 256-bit private header-storage
  candidate. Both are cleared at accepted start and filled before validation.
  Defer implementation until the first candidate's evidence is available;
  require its own decoder error/cancel comparison.
- SHA `hash[]`: reset controls externally visible digest bits even when
  invalid. Removing it changes invalid-cycle outputs. Do not bundle that
  semantic change into the private-tag experiment.
- Private-join `base_tag`/`hud_tag`: result outputs are cleared on reset and
  failure. Preserve this behavior until consumer requirements are verified.
- Job reset synchronizer: all four stages carry `ASYNC_REG`. If distribution
  remains limiting, evaluate local distribution after the synchronizer rather
  than independently replicating asynchronous synchronizer chains. Verify
  reset release, cancellation and admission latency before selection.

Read-only checkpoint audits retain direct reset loads, reset/control pins,
tag reset/enable nets, control sets and utilization. The first two audit trials
had an invalid Tcl collection-to-pin query and are not reset-removal evidence.
The corrected baseline03 uses object-based pin selection and hierarchical net
segments. It confirms **4,281 direct loads, including 3,805 reset-pin loads**.
All 256 outer tag bits still have reset connections in that original baseline.
Candidate synthesis and final routed counts must be measured separately.

The corrected SDR1 implementation03 has no critical/warning CDC findings, but
fails setup by 0.107 ns on four endpoint control paths. A physical-only
optimization is running from that frozen checkpoint. BIT generation is gated
and was correctly blocked on the failing route; no hardware load occurred.
Both source-v005 native memory-model cases pass 32 writes/reads, busy request
rejection, retained trace/literal response checks and held-GO reset recovery.

The diagnostic's physical-only derivative now passes setup +0.059 ns, hold
+0.053 ns and pulse +2.000 ns. Its BIT/LTX and source-bound completion manifest
are complete; see [SDR1 bitstream completion](SDR1-BITSTREAM-COMPLETION-20261105.md).
No hardware programming occurred.

Matched synthesis comparison (only envelope RTL differs): direct job-reset
loads 4,206 to 3,957, direct reset-pin loads 3,784 to 3,528, LUTs 26,561 to
26,428, registers 24,666 to 24,665, control sets unchanged at 1,250. These
counts confirm reset-load removal, not routed timing improvement.

Full-design routing is still optimizing decoder and SHA block-storage paths.
A separate carry-save SHA plus registered-byte-write experiment is under
directed validation. It adds one block flush cycle per 64-byte compression
block to separate ingress/cancel control from the 512 block-storage enables.
It has not been selected into the reset-only candidate. Require its own
hash/recovery tests and complete-board/routed gates before selection.

The reset-only candidate's first final route misses setup by 0.520 ns. Its
worst path is `outer/epoch_reg[0]` to `outer/base_sha/block_reg[105]/CE`:
14 logic levels, 10.337 ns data delay (3.393 ns logic, 6.944 ns routing).
This measured ownership/cancellation-to-storage path justifies the separate
registered-byte-write experiment. It does not justify loosening reset or
ownership checks, changing the external protocol, or claiming the reset-only
candidate passed timing. Bounded physical-only repair passes remain separate.

The SHA reservation experiment passes 27 hash/boundary cases, four negative
cases, 295 reset/abort tests and recovery (2,111,086 cycles), plus explicit
pending-byte and COMP_FLUSH reset/abort coverage with two recovery hashes
(479 cycles). Integrated candidate `cp23-reset-tags-bytewrite-20261105-v001`
adds that one SHA file to the reset-only inputs. It is under independent
envelope comparison, full-board simulation and implementation02 routing.
The original reset-only physical-repair branch remains separately retained.

## Bitstream completion

Selected `cp23-reset-tags-bytewrite-20261105-v001/implementation02` passes
routed setup +0.022 ns, hold +0.018 ns, pulse +2.000 ns, all four bus-skew
constraints and all 49,156 routable nets. Both complete-board fixtures pass
the original golden CRC. Native pre-image DRC has zero errors, zero critical
warnings and 469 retained warnings. The generated BIT, complete source/report
manifest and verified ZIP are complete. See [the full completion record](CPL1-RESET-BITSTREAM-COMPLETION-20261105.md).

The selected route's direct job-reset loads are 3,961, including 3,561 reset
pins. These routed counts are distinct from the matched synthesis comparison.
The private-tag removal remains; four private byte-write reservations and
physical mapping account for additional control changes in the selected build.

Local packages:

- `fpga/exports/cpl1-reset-pipeline-completed-build-20261105-v001.zip`
- `fpga/exports/sdr1-completed-build-20261105-v001.zip`

Build completion is achieved. Physical raw-memory readback and CPL1 CRC remain
the next gates. No new image has been programmed; no ESP32, SD or persistent
FPGA flash changes were made. The full fixture remains fixed-ROM CAPS0 and
does not establish Sunshine readiness or 30 unique displayed fps.
