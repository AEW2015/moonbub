# V48 local controller independent review

Current verdict after author fixes: the reboot-monitor/COM blocker is resolved; no remaining bootstrap blocker found. Independently executed28/28 pure tests pass after the post-reenumeration open correction. Physical behavior remains unverified.

Read-only review requested against root readiness af5be52d2, covering host/lab-selftest-v1/lab_controller.py and test_controller.py. No controller source, firmware, target build, serial port, network or hardware operations performed by this reviewer. Existing15 pure tests passed; log `C:/moon/maintenance/v48-controller-review/tests-initial.log`.

## Operational blocker sent to root/author

Initial REBOOT verification arms its disappearance observer only after control() returns the matching ACK and SerialLog.close()/join finishes. Firmware schedules restart250ms after accepting the request. A200ms serial-read timeout and close latency can consume most/all of this interval, so a real disappearance/reappearance can occur before monitoring starts. A successful restart would then be reported unverified and autonomous progress stalls. Arm continuous presence observation before transmitting REBOOT, capture disappearance/reappearance times, and retain fail-closed behavior if either is unobserved. Never issue an automatic second reset.

Post-reset discovery must match the exact USB serial but allow a changed COM name; using the original --port selector for reenumeration can refuse the same correctly identified device after Windows assigns a new COM port. Initial port selection may remain constrained. Root assigned both corrections to the controller author; final code/test re-review is pending.

## Evidence/thread cleanup issue sent to author

read_session starts a daemon sender-stdout reader, returns just the session row and loses its thread handle. p.wait() proves child exit, not that the pipe has drained. The with block can close sender.stdout while the reader is still writing queued tail lines, causing a swallowed ValueError and incomplete stdout evidence. Retain and join the owned reader after child exit/termination, then close its pipe/output; bound the join and report failure if it cannot stop.

SerialLog.close currently joins2seconds then closes raw without checking the reader actually stopped. A delayed reader could still write to a closed file and lose its final serial tail. Close/cancel the read, join the owned reader and verify termination before closing raw. Constructor-open failures should close the raw file and partially opened port too. These are evidence/cleanup reliability issues; neither currently authorizes an extra hardware mutation.

## Admission/source/identity checks

The controller pins sender, adjacent dyn1_sequence_core, manifest and telemetry validator SHA256. Sender itself validates every selected fixture against its manifest before transmitting that frame; it is not a preflight claim that all later fixture reads already occurred. It binds .33 explicitly and gates arming on a live owned subprocess, the actual JSON session/profile/count/source/destination, matching manifest hash, fresh sender timestamps and sufficient remaining wait. It sends @ exactly once after fresh camera/program receipts. Marker freshness/PID/hash are reviewed assertions, not physical-camera/image proof by themselves.

USB selection requires exact serial802C0E7A. It sends a fresh random16hexnonce PING and accepts only matching nonce/action/result before fresh exact-ELF query and HOST33. Firmware ACK format matches the host regex. Identity query is not nonce-bearing; freshness relies on draining observations before explicit? plus an already responsive nonce-confirmed serial connection. No source-IP/fixture substitution was found in the normal pinned path.

## Exports and target12 acceptance

END is followed by a pinned validator requiring exactly one complete indexed/checksummed export; missing/truncated/multiple attempts fail closed. Receiver literal successful12-frame summary/counters and sender matching complete12 result/exit0 are both required. A valid negative export marks export_complete for an explicitly requested later recovery, but does not yield a passing trial; this is useful for recovery and must not be described as12-frame success.

The epoch/export has no direct DYN1-session field. Current exclusive-controller fresh-boot/idle-HOST33 prerequisite and sender's independently correlated replies provide operational correlation; do not describe the export as intrinsically session-authenticated. A stale queued END typically causes isolated export validation failure, not automatic success. If future code allows concurrent reexports/jobs, require an explicit expected snapshot epoch and bind final retained IDs/generations to the current manifest/session.

The pure tests initially cover admission/markers only, not serial thread cleanup or reboot timing. Add fake port/presence schedules where disappearance and reappearance occur during ACK/close, changed COM with same serial, wrong-serial replacement, bounded no-reenumeration, reader tail drain, and cleanup on each failure stage before treating recovery as automation-ready. Actual physical reboot/DFU remains unproven until the separately authorized hardware bootstrap.

## Final corrected-controller re-review

PresenceMonitor starts and validates initial exact-serial presence before the command is marked/transmitted. Its independent25ms requested sampling captures gone/returned events even while control waits for ACK or the old serial port closes. Monotonic/Unix event times and maximum observed sampling gap are recorded. A replacement port is accepted only through the exact serial selector, with a changed COM name permitted. Missing disappearance, ambiguous exact-serial ports or timeout still fail closed with no second reset. Scheduler/enumerator delays can still miss a sufficiently brief physical absence; that yields unverified recovery, not false acceptance.

SenderPump now retains its reader thread and is finished after stopping/waiting the child, before output file closure and before a success receipt is written. Reader failure/unfinished tail prevents success. On join failure it blocks later writes before allowing the evidence file to close. SerialLog cancels/closes the read, checks bounded join completion and leaves raw open rather than closing it under a live reader. The initial constructor-open error still relies on process-exit cleanup for its raw handle; this is a small local cleanup follow-up, not a hardware/bootstrap blocker. A genuinely stuck filesystem write while SenderPump holds its output lock can exceed the nominal cleanup bound; ordinary local-file operation is assumed.

Independent rerun at `C:/moon/maintenance/v48-controller-review/tests-final.log`:22/22 pass. New cases cover fast disappearance during consumer delay, changedCOM, missing/ambiguous presence, drained sender tail, late-write suppression and raw-log lifetime. Read-only source bindings saved alongside the log. No controller source edits or hardware actions by this reviewer.

## Post-reenumeration open correction re-review

Root reported the prior physical restart had an ACK and observed disappearance/return, then a transient port-open failure; this reviewer did not perform or reinterpret that physical operation. New source SHA25677e59dcad1671305e47cbd4fa478f2d303dc241235cac2a0032c4d571a9000db reviewed read-only.

SerialLog now opens/configures the serial port before reserving serial.raw. OSError during the open closes the partial port and becomes PortOpenPending; successful-open log/thread errors remain fatal and close the port/raw rather than being retried. Existing raw evidence is preserved by xb and is not overwritten on retry.

open_returned_serial reenumerates the exact USB serial each attempt and accepts changedCOM names; it retries only PortOpenPending, not arbitrary failures. It uses the same deadline established before REBOOT and shared with disappearance/reappearance waiting. It records attempts, timestamps, ports, errors and remaining time. No new REBOOT/DFU command is sent by this retry helper. Deadline checks bound attempts between OS calls; driver calls themselves remain synchronous, and post-open PING/ELF checks have their own bounded waits.

Independent rerun:28/28 tests pass at `C:/moon/maintenance/v48-controller-review/tests-postreenum.log`, including transient open failure then readiness/newCOM, missing enumeration, repeated open failure deadline, partial-port cleanup, post-open file failure refusal and preservation of existing evidence. No remaining blocker found for root's separately explicit new software-reboot qualification. This is source/pure-test approval, not proof of that upcoming physical result.
