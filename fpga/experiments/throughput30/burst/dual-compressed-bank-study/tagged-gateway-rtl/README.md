# Synchronous tagged command gateway experiment

This isolated RTL prototype places a command gateway in front of the existing
two-bank control state machine. It is a **single-clock research experiment**:
it does not change production RTL or firmware and does not instantiate the QSPI
transport, compressed RAM, JPEG decoder, SDRAM or display. It is not a complete
bank protocol, formal proof, target synthesis, timing or hardware result.

The gateway provides a starting point for the missing transaction identity and
ACK semantics described in [`../ABORT-OWNERSHIP-REVIEW.md`](../ABORT-OWNERSHIP-REVIEW.md):

* A BEGIN receives `(epoch, bank, generation)` only after the controller
  confirms its chosen bank. Generation increments globally on each successful
  BEGIN; the prototype permits only one receiving transaction at a time,
  matching the wrapped controller. A new BEGIN is refused when generation would
  wrap. This does not establish per-bank parallel receive capability.
* DATA, COMMIT and ABORT require the live epoch/bank/generation; DATA also
  requires the exact next byte offset. A stale abort or write cannot address a
  newly allocated transaction in the directed tests. Invalid token or offset
  consumes its accepted request sequence but leaves the active receive intact.
* Commands use 32-bit sequence numbers beginning at 1 per reset epoch. A new
  command must have the next expected sequence. The **single most recent**
  completed request is cached, including every request-body bit and the
  complete historical ACK. Exact retry replays that ACK without repeating the
  side effect; a different body with the same cached sequence gets ID_CONFLICT;
  an older or future sequence gets OUT_OF_ORDER. Rejected new requests are also
  cached and consume a sequence. The latest request can be replayed after the
  maximum sequence, but no new request is accepted after wrap would occur.
* `ack_valid` and its complete response stay stable until `ack_ready`. The
  source must keep request signals stable through `req_valid && req_ready` and
  wait for a matching ACK before advancing; the one-entry cache is not a
  pipelined or multi-client replay window. The internal epoch is sampled from
  `epoch_in` while reset is asserted. An external mechanism must guarantee a
  **new, never-reused epoch after every reset**, including power loss, or old
  tokens can become valid again. That persistence mechanism is not implemented.

The controller copy is generated with anchored substitutions from the existing
experiment. It exposes the selected bank on BEGIN and explicit accepted pulses
for COMMIT and ABORT; all other control logic remains the same. The gateway
raises an ACK after observing these pulses or, for DATA, the controller's
registered write strobe with matching bank/address/data. That means the
controller emitted a write to the synchronous output interface; it **does not
prove a physical RAM write, CDC drain, FIFO acceptance or durable transfer**.
There is no backpressure input for `mem_we`. A controller inconsistency faults
the gateway until reset. It does not implement timeout recovery, asynchronous
overflow, transaction-tagged decode completion, pending-frame cancellation,
reset coordination or a physical drain-before-reuse fence.

The host must treat the ACK as historical, rather than a current ownership or
presentation status. Frame IDs are payload metadata and are not checked for
uniqueness. The exact wire format, sequence/epoch persistence, authentication,
NACK recovery, clock-crossing protocol and bounded transfer policy remain to be
specified before any integration. A reset drops the replay cache; recovery from
an ACK lost across reset requires a separate status/reconciliation design.

## Directed verification

`tb_tagged_gateway.sv` checks a held ACK under backpressure and reset while an
ACK is stalled; BEGIN, DATA,
COMMIT and ABORT success and duplicate replay; changed-body conflict; exact
byte offsets; stale data/abort after reuse of the same bank; presentation of an
independent earlier frame; busy and CRC rejection; old-epoch rejection; and
fail-closed counter-wrap paths. The wrap paths **seed testbench internal state**
near the limits; they do not execute billions of commands. It reports
`TEST_PASS_TAGGED_GATEWAY acks=38 writes=10 cycles=224`. Two local mutants remove
generation checking and replay handling; both fail their intended assertions.
A separate injected missing COMMIT-accept pulse verifies that the gateway
returns INTERNAL and remains faulted; a third mutant that blindly treats the
missing pulse as success fails the fault test. The underlying controller may
already have committed in this injected-fault example, so an INTERNAL ACK is
not a rollback guarantee. These checks are directed two-state simulation, not
exhaustive verification.

With Verilator 5.x, C++, Python 3 and optional Yosys, set `BUILD_DIR` to a new
empty directory and run `./run.sh`. It checks source hashes, generates the
instrumented controller and mutants, compiles/runs five simulations, and
requires expected negative results. If Yosys is present it runs a generic
`hierarchy; proc; opt; check; stat`; this is only an RTL elaboration check, not
FPGA technology mapping. The recorded independent run and complete logs are in
`/home/lori/gamebub-tools/tagged-gateway-wrapper-v2/`; small logs and source
checks are under `results/`.
