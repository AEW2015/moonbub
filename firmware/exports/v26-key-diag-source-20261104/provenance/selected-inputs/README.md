# v26 restricted AKD1 diagnostic access — source review candidate

This isolated candidate starts from sealed v25. It connects the admission core
and restricted local diagnostic worker to SDK call sites. Offline target/package
outcomes and selected ELF frames are recorded in BUILD-RESULTS.md. All physical
stack/logging/heap/SPI and diagnostic acceptance gates remain NOT_RUN.
It does not fix or explain the observed v22 reboot. Sealed v24/v25 and installed
v22 are unchanged. Firmware v26 is a local firmware namespace, separate from the
remote host codec study `study/gamebub-codec-v24-comparison-20261104`.

The FPGA contract is [AKD1-COMPUTE-DIAGNOSTIC-20261104.md](../../../docs/AKD1-COMPUTE-DIAGNOSTIC-20261104.md).
The worker requires all eight exact identity words: AKD1/schema1 at 000/004,
zero capabilities at 008, MBK1 `0x4d424b31` at 184, AKD1/schema mirrors at
400/404, fixture length48203 and watchdog10000000. MBK1 must also match the
future image's USR_ACCESS. There is no currently qualified physical image or
access result in this candidate.

## Actual SDK integration

There is one `core_coordinator::CONTROL`. The former private streaming mutex is
an alias to that authority. Source requests reserve the receiver before publishing
WANTED or enqueueing work. The lease covers the **whole existing connected or
TestReady receiver**, including zero-frame AV input/tone workloads. It remains
held for a stopped-but-still-WANTED receiver until existing disconnect. Existing
WiFi/shared GENERATION/button polling, receiver queue/pools, `_av` Guard and full
disconnect lifecycle are retained. AV HELLO and START, flags0 and1, acquire AV
ownership before Session mutation or Offer. AV ownership ends only after the
existing Guard join and confirmed feeder/queue/power-save cleanup. A failed join
or cleanup retains AV/receiver reservations and quarantines. This candidate does
not implement standalone cold-boot AV or independent network lifetime. The pure
v25 policy's independent AV capability remains available for a future task.

| Physical programming entry | Reservation before outer locks | Authorization inside driver |
|---|---|---|
| main → `bitstream::program_boot` | before startup Device guard | consumed before epoch/pins |
| Worker → CurrentBitstream → `program_fpga` | before CURRENT, then existing Device order | consumed before epoch/pins |
| receiver `ensure_core` → SD reader | matching receiver permit, AV absent, before Device | consumed before epoch/pins |

`ProgramPermit::authorize_call` borrows the noncopyable permit. Driver `begin`
consumes the one-use authorization without locking CONTROL. Driver error after
begin poisons that permit; caller post-initialization failure also retains the
reservation. Confirmed successive calls may share one exclusive worker job
(including existing ROM error boot fallback). File/scratch denial before the
driver is clean and Busy propagates as an error instead of an old programming
unwrap. There is no fabricated RecoveryConfirmed path. Unknown programming
requires operator restart; losing a permit never frees its reservation.

Benchmark, rate change and queued restore now enter the same authority, so their
admission is symmetric with diagnostic admission. Queued restore reserves intent
before spawning and waits for receiver/AV drain before exclusive programming.
QSPI benchmark START marks its local maintenance token unconfirmed before the
write; only ordered STOP readback of inactive permits release, including a
transfer error path. Ambiguous start/stop/read retains token and quarantine.
CRC computation and rate read-only checks can release without a hardware drain.

Normal Connect/local loops and AV HELLO/START refuse AKD1 or MBK1 before ensure_core
can reload the SD image or Session can mutate. Zero capability bits alone are
not relied on. MRG/TIM accept only `(MBV1, MB_OI or MB_OP)` or `(AKD1, MBK1)` with
exact core schema1 and their existing MRG1/TIM1/schema/status checks. Crossed
magic/build pairs fail. Audio APC1 identity remains unchanged. MSV1/AV1 layouts,
ports, SDK configuration, task priorities, existing stack sizes, UI selectors,
queue/overlap defaults and audio pools remain unchanged.

## Lock map and retained ownership

1. Acquire CONTROL only for state/token mutation; drop it before Device, CURRENT,
   AV/session guards, callback invocation, thread spawn/send, waiting or logging.
   Error formatting in `core_access` explicitly follows guard drop.
2. Keep existing CURRENT→Device order for bitstream programming. Receiver and
   startup Device guards end before any later CURRENT/CONTROL acquisition.
   Driver authorization is token-local and never reacquires CONTROL.
3. Maintenance guards are declared before inner Device/CURRENT scopes. Their
   release runs after those guards on normal and error returns. Side-effectful
   benchmark ownership needs explicit inactive proof before guard release.
4. Receiver activation invariant failure cancels intent, counts/reports failure
   outside CONTROL, and retains/quarantines reservations. It does not invent a
   clean AV/program drain. Failed program/diagnostic/maintenance releases retain
   returned tokens and, where present, exit proof in Coordinator.

Host-only checked CONTROL guards track per-thread depth at the same production
lock call sites. A global try_lock test would incorrectly flag another thread's
legitimate hold. Fake Device callbacks assert zero local CONTROL depth. This
instrumentation is absent from target production builds.

## Restricted USB worker

`d` starts one fixture job; `a` requests STOP; `b` reports status; `y` requests
guarded CLEAR of a held owned result and subsequent worker exit. No command takes
an address/value. The production state machine alone emits fixed reads and
408 commands1/2/4. Existing `r` stays the CRC benchmark.

The worker is lazy: spawn an empty channel receiver first, then send only a small
permit. Spawn failure leaves the permit at the caller; send failure returns it.
Both release cleanly only when unissued-token release succeeds. Release failure
retains quarantine and busy state. Core is constructed inside the worker, never
on the USB stack. The single priority mailbox coalesces STATUS/CLEAR, and STOP is
processed first; there is no status queue ahead of STOP. The channel sender is
dropped after successful handoff. Worker holds its Core/permit until guarded
CLEAR→IDLE exit proof; failed proof release retains context and reports restart.

Initial epoch acquisition uses try_lock,200ms/200 attempts and STOP checks, with
clean unissued exit before any SPI. Each subsequent action uses one CSR inside
one try_lock Device hold; model completion, waits, formatting and logs happen
after Device drops. Read and command writes use the existing16MHz read-safe SPI
cap. Job budgets remain1s/512 actions, recovery200ms/64; a blocked synchronous SDK
SPI call is not preempted by these cooperative bounds.

Unowned FPGA RUN or terminal state after ESP boot is quarantined, never adopted
as this job's success. STOP cannot manufacture ownership. The explicit fallback
is operator device restart plus fresh qualified FPGA configuration, not automatic
reprogram/CLEAR or arbitrary CSR recovery. program_epoch is only an ESP attempt
fence. Exclusive operator/no external JTAG reset is required: AKD1 cannot observe
a reset ABA that reproduces identity/owner/sequence. No host result removes that
schema limitation.

Key pages use `USB_D24 v=2 p=key*`; inherited runtime pages retain v1 with a unique
v26 variant. Record/count/tag pages each carry full owner64 and result sequence.
After each report returns, separate `#[inline(never)] resource_sample` runs on
KeyDiag and emits `USB_D24 v=2 p=key_resource worker=KeyDiag` with its own
`uxTaskGetStackHighWaterMark(NULL)` in bytes, declared4096 bytes, internal free
heap and largest internal block. It holds neither Device nor CONTROL. The
watermark therefore follows the earlier report/SPI path; this sample precedes
its own formatting/logging, which a later sample can observe. Values are sampled
separately. Host fakeSys/logger tests assert worker routing, null task handle,
zero lock depth, exact fields and worst-width bounded lines. `?` still measures
the existing USB task. This meter is observability, not measured stack safety.

RUN status is sampled; a held terminal record is accepted only after the model's
before/after state+sequence+owner consistency checks. Pages are not an atomic
runtime snapshot. The existing recorder's `USB_D24` retention covers both
versions; command sender whitelist must explicitly allow d/a/b/y before later
operator use. No recorder or hardware action is run by these tests.

## Review budget and evidence limits

The **new** KeyDiag stack declaration is4096 bytes; existing USB4096, AV8192 and
other defaults are unchanged. Host layout: Core304, permit16, Operation32,
Line200 bytes; target layout/frames are not yet measured. Worker has no frame
buffer, PCM storage, Vec or boxed Core. Fixed mailbox is one byte; the transient
sync channel has capacity one permit plus standard-library allocation metadata.
The receiver retains that allocation until the spawn closure returns; detached
OS task/stack reclamation can overlap a later job after exit proof. There is no
measured hard peak-heap or task-reclamation bound.
Thread name/channel/FreeRTOS TCB allocation sizes and peak internal heap require
target evidence. A held/quarantined job deliberately retains its worker stack
and reservation until confirmed exit or operator restart.

Maximum tested record payload is165 bytes; resource-page worst-width host payload
is180 bytes (including 64-bit host usize maxima), with64-byte framing reserve244.
This is an allocation-free payload bound, not measured SDK logger framing or
stack safety. See [SDK stack units](../../../evidence/SDK-STACK-UNITS-20261104.md):
the pinned Xtensa SDK's StackType_t is u8, so historical USB716 minimum is bytes.
It does not prove this candidate safe. Actual generated target bindings are checked after each build. Required later gates include actual d/a/b/y USB frames and worker/model/
formatter/logger call chain, peak heap, stack minima, teardown and query-cadence
overhead versus no-query control. No hardware qualification is claimed.

`run_source_stage.py` runs the inherited39 model tests/24 compiler rejects,
the production SDK-orchestration host suite, Rust syntax parsing of changed
source and parent/invariant guards. Host tests compile exact coordinator,
core_access, dispatch, restricted worker, MRG/TIM controllers and AV policy with
fake Device/clock/SPI/logger. They run an actual lazy host worker through
d→terminal→y→exit. Three programming-site tests exercise the shared production
wrapper/token callback with fake epoch/pins, with source binding of actual SDK
call sites; they do not compile the ESP Driver/HAL or prove physical programming.
The source-stage manifest and unified integration diff bind those limits.
