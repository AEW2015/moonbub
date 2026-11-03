# Experimental JPEG-to-SDRAM burst writer

This isolated, synchronous RTL experiment packs a length-declared byte stream
into 16-byte (eight 16-bit word) write requests for the experimental SDRAM
controller. It is **not production firmware or RTL**, a complete frame commit
protocol, a hardware measurement, or a sustained streaming result. The related
[SDRAM reader study](../sdram-jpeg-reader-study/README.md) is separate: these
two candidates have not yet been connected into a real receiver-to-decoder
pipeline.

## Interface and assumptions

* BEGIN accepts a nonzero declared length up to **262,144 bytes** in a fixed
  256 KiB SDRAM slot. The default slot is word range `[0x060000,0x080000)` in
  the **functional model's** one-million-word address space. Configuration is
  rejected if the slot would exceed that model bound or is not BL8-aligned.
  Actual Game Bub memory size, geometry, aliases and safe slot reservation have
  not been verified.
* Input bytes use valid/ready; each accepted byte is counted once, and an input
  burst may stall while the single 16-byte output buffer is full. The last
  partially filled burst is padded with zeros. Its byte count and any CRC must
  be interpreted using the original declared length, not the padded length.
  The writer stops accepting bytes after that count; it does not parse or
  explicitly reject an overlong source transaction. The upstream protocol must
  validate byte sequence, length and transaction identity.
* A write request's valid, word address and 128-bit payload stay stable until
  ready. If abort or sink fault arrives while a request is **already stalled**,
  that offered request remains valid until accepted; only then can the writer
  wait for drain. A sink that cannot honor the outstanding handshake can leave
  the writer waiting indefinitely; no timeout or cancel channel is provided.
  A sink asserting fault must still honor any ready/valid handshake it permits;
  an interface that withdraws acceptance on fault needs its own cancel or
  quiesce protocol before it can be connected.
* `done` occurs only after the exact declared bytes have been accepted, every
  generated write burst has handshaken, and an external `write_drain_done`
  signal asserts on a later clock. That signal is a **contract supplied by the
  surrounding design**, not a physical proof created by this writer. It must
  cover all outstanding controller, arbiter and CDC queues. This candidate has
  no per-burst completion tag, CDC, asynchronous-reset coordination or physical
  memory acknowledgment.
* Abort discards unpublished local data, waits for any previously accepted or
  already-stalled offer to drain, and then pulses `aborted` instead of `done`.
  Already-issued writes are **not rolled back or erased**: the external bank
  owner must keep the slot invalid and prevent reuse until drain. A sink fault
  similarly drains and pulses `failed`; its `faulted` state stays set until
  reset. Reset immediately clears local state and does not itself quiesce an
  external memory controller. Cross-reset tokens and stale writes need a
  separate proven protocol.

`done` is **not a CRC check or display publication**. No data-integrity check,
receive sequence, bank generation, retry/NACK handling or authenticated
ownership is implemented. The caller must establish those separately and must
not expose a slot as valid until its actual byte count, CRC, ownership and
physical drain have all been verified.

## Bounded verification

Two separate self-checking simulations exercise the same writer:

1. A small endpoint model applies write backpressure and delayed drain.
2. The unmodified experimental `moonshine_sdram_burst` and its functional
   SDRAM model receive the write requests; the testbench inspects memory
   hierarchically after drain. It does **not** read the data back through the
   SDRAM controller or establish board electrical timing.

Both test all 16 final-burst remainder values, lengths through **262,144
bytes**, invalid zero/oversize lengths, byte order and every padding byte,
ordered/bounded addresses and an end guard. They also cover abort while writes
are busy, abort and sink fault while a valid offer is stalled, handshake/data
stability, sticky fault and delayed completion. The controller-backed test
checks its functional model's refresh and write-burst/word counts: the recorded
run observed 759 refresh commands and 18,119 write bursts. These are
directed two-state tests, not a formal proof or an independent vendor memory
model.

Five local mutants—nonzero padding, completion before drain, withdrawal of a
stalled offer, incorrect burst address and missing capacity rejection—fail
their intended checks. A generic Yosys `proc; opt; check` is an RTL elaboration
check only; it is not target FPGA mapping or timing. Compact logs and the
source manifest are in `results/`; full recorded output is
`/home/lori/gamebub-tools/sdram-jpeg-writer-wrapper-v2/`.

## Reproduction and next steps

With Verilator 5.x, a C++ compiler, Python 3 and optional Yosys, set `BUILD_DIR`
to a new empty scratch directory and run `./run.sh`. It checks source hashes,
generates the controller-backed bench and mutants, runs both positive cases
and five expected-failure cases, and optionally performs the generic Yosys
check. The included functional SDRAM model checks its own selected refresh and
timing rules but is not an independent physical-device model.

Before integration, connect a real packet/CRC/ownership layer and bounded CDC,
define and implement the end-to-end drain and cancellation contract, combine
this writer with the separate SDRAM reader under the LCD/decoder arbiter,
exercise simultaneous transfers and adverse reset/abort/response ordering,
and run target FPGA implementation and physical board tests.
