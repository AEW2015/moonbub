# V48 recovery/control integration review

Current verdict after root correction: the deferred-reset admission race described below is closed by a CONTROL-protected pending recovery barrier. No remaining blocker found in the reviewed integration; target/hardware proof remains pending.

Read-only production-source review on2026-11-07. Added only the authorized pure `tests/lab_recovery_gate.rs`; no native/handheld edits, hardware operations, target build or push.

## Blocker found in reviewed source

`lab_control_usb::dispatch` checks idle/completed/exporting, emits matching nonce result=OK, and calls `control::schedule_lab_reboot`. That uses the existing100ms deferred callback without taking a recovery reservation or revalidating state. Another legacy USB request or queued/UI receiver request can acquire ownership during the delay, after which the callback can reset active work. The Coordinator quiet query is correctly observational; it cannot serve as an atomic delayed-reset barrier. The pure regression `quiet_snapshot_alone_is_not_a_delayed_reboot_barrier` demonstrates that exact policy limitation with actual production Coordinator methods.

Root was notified immediately. Required before deployment: reserve a fail-closed recovery/pending barrier under CONTROL before ACK/scheduling so subsequent admissions cannot start work, or revalidate at execution with explicit cancellation semantics and host ACK handling. A barrier must also block diagnostic/program/maintenance/receiver paths and repeated reboot scheduling. This report describes the reviewed version; re-review root's final change separately.

## Checks that passed

- USB `lab.command(byte)` precedes both margin parser and legacy command dispatch through short-circuit&&. Parser captures from ! through LF; malformed/overflow/timeout cannot execute partial commands or leak embedded legacykeys. CRLF and exact16hexnonce rules pass parser host tests.
- PING is read-only and bypasses idle checks intentionally. Control ACK is `MBLAB1 nonce=<16lowerhex> action=<UPPERCASE> result=OK/BUSY`, matching `C:/moon/publish/host/lab-selftest-v1/lab_controller.py`'s exact nonce/action/result parser.
- HOST33/HOST47 store only a fixed IPv4 value in AtomicU32 RAM. The override is consulted only by custom_lab_wifi after saved credential configuration is read; no config/KVS/SD writes or credential printing are added. JPEG and regular streaming configuration do not consume the override. HOST is refused while a lab worker is active, including its held completed endpoint.
- Active DYN1 has REQUESTS busy and FINISHED false. FINISHED is cleared on reserve and set only after native driver result, passive diagnostics, snapshot publication attempt and failed-reply handling. A retained completed worker remains REQUESTS busy. The completed indication is not a forged commit/abort or lease release.
- report_snapshot::exporting observes the existing paced Store busy state; dispatch refuses recovery while it is true. Completed Benchmark may be recovered explicitly after export, including quarantine, while Rate/Restore and active video/AV/program/diagnostic states remain blocked by Coordinator's query. Passive held endpoint receive/re-ACK activity may still exist after FINISHED; it is not further decoding or ownership mutation.

## Executed pure coordinator tests

Actual production core_coordinator/core_admission/key_diag_core compiled with rustc stable. All7 tests passed: idle read-only observations; pending/active receiver; AV coexistence; Benchmark active-vs-completed versus Rate/Restore; program and diagnostic permits; quarantine+held recovery without releasing lease; and the delayed-reset reservation gap. Evidence: `C:/moon/builds/v48-recovery-gate01/{compile.log,test.log}`. One inherited unused-import warning is present; no compile errors.

These SDK-free tests validate the coordination policy only. They do not prove SDK timer scheduling, USB ACK delivery, exact installed image, reboot/DFU behavior or physical absence of concurrent work.

## Re-review after recovery barrier correction

Root added recovery_pending to Coordinator. lab_reboot_begin repeats the quiet/held check while holding CONTROL, then sets the barrier and refreshes admission blockers. All new receiver, AV, program (including restore), diagnostic and maintenance admission paths reject pending recovery; repeated reboot_begin is refused. The existing held Benchmark lease remains retained. Dispatch obtains this barrier before scheduling and emits nonce-matched OK only after the fallible250ms timer setup succeeds. Timer setup failure cancels the barrier and emits ERROR; there are no unwraps in the new scheduling function. Legacy vendor-control behavior remains outside this newly reviewed lab path.

Extended actual production policy tests pass11/11 at `C:/moon/builds/v48-recovery-gate02`: pending barrier rejects all exposed admission variants and repeat restart; cancel restores normal admission; cancel retains quarantine/held lease; completed held Benchmark can reserve recovery while a running/noncompleted one cannot. The previous observation-only test remains as a regression explaining why quiet() itself must not replace reboot_begin(). Reviewed root changes close the notified race without forced lease release. No production edits were made by this reviewer.

The completed_lab Boolean is a caller-supplied observation, not a generation-bearing capability; current native lab launches are serialized through the USB control loop, and held completed workers retain REQUESTS/Benchmark until reboot. If future threads can replace lab jobs concurrently, bind completion to the specific retained job/generation under the coordinator lock rather than reusing a previously sampled Boolean. This is a future concurrency constraint, not a demonstrated current hardware failure.
