# Shared AR03 source analysis across bounded map retries

This v23 Python component reuses actual source prediction and the three
unquantized forward transforms while a controller tries bounded quantization
maps. It retains the frozen AR03/GM01/SR01 arithmetic and byte grammar. No source
approximation, reference change or new receiver interpretation is introduced.
`SharedEncoder` is a local subclass of the frozen candidate encoder, with an
adapted build body; it never patches a module global, class or shared function.

## API and work ownership

`SharedEncoder` accepts the same constructor as `candidate_codec.Encoder`.
Without a context, `build` invokes the frozen superclass implementation.
For a retry group:

1. `begin_source(rgb, frame_id, force_key=False, promote=False,
   reference_bank=None)` validates current geometry/identity/bank ownership,
   hashes the borrowed input, and actually computes one GM prediction/analysis.
   It increments the real cumulative analysis counter once and forward counter
   three times. It retains the actual prepared analysis and local encoder.
2. `build` accepts the frozen map/quantization/flags API. Each invocation checks
   the exact borrowed ndarray, full source hash, frame/key/promotion/reference
   identity, epoch/configuration and current semantic encoder state. It then
   pays map quantization, all actual entropy alternatives, reconstruction/tagging
   when required, outer serialization, patch callback validation and cap checks.
   Losing candidates must be explicitly discarded exactly as before.
3. `end_source()` releases only the context's source hold, drops its prediction/
   transform arrays and records final statistics. A retained winning candidate
   still owns its separate source lease. End the context before `commit`; this
   lifecycle is explicitly enforced. Discard/commit then follows the frozen API.

Use a `try/finally` around the group so exceptions also end the source context.
`build` exceptions release their own candidate lease while leaving the explicit
context hold until `end_source`. Context cleanup does not release another
external reader. No issued frame ID or bank publication occurs just from analysis,
candidate rejection or ending a context.

A referenced context requires **one extra reader descriptor**, in addition to
the ordinary candidate lease. `begin_source` preflights two available descriptors
and fails before analysis/ownership changes if capacity is insufficient. It does
not silently raise the configured reader bound. At seven external readers with
an eight-reader cap, the baseline can have one candidate while this optimization
cannot start; universal admission equivalence is therefore not claimed. A reader
arriving later can still consume capacity and cause a bounded build failure.
Keys without a source bank need no context read descriptor.

## Cost and storage accounting

`last_source_info` and `last_shared_info` expose the same JSON-safe final context
record. Counters distinguish one actual analysis/three forward transforms from
cached attempts and eliminated repeated analyses. Each cached build reports
`analyze_calls=0` and `forward_calls=0`; source preparation is charged separately
and is included by the enclosing joint-controller build timer. All attempted
quantization/entropy work and failed candidate builds remain paid.

The source is borrowed, not duplicated persistently. SHA256 guards use a bounded
canonical transient `tobytes` copy on begin and every attempt; count/time/bytes
are recorded. The caller must exclusively own a stable source until context end.
These checks are not a lock or protection against concurrent/malicious Python
code. Retained banks follow the existing trusted immutable-array contract.

At 720×480 coded geometry, the retained prepared arrays are **1,036,800 bytes
of int16 prediction plus 4,147,200 bytes of int64 raw transform coefficients =
5,184,000 bytes**. The borrowed source RGB has 1,036,800 bytes. Reference-bank
arrays are separately owned and retained by the context lease. Source conversion,
hash copies, transform intermediates, candidates, packets, reconstruction,
interpreter objects and allocator overhead are additional. These are named
host-array sizes, not an ESP32 SRAM plan, peak process heap, physical bus count,
FPGA BRAM/DSP mapping or speed claim.

The enclosing [HD22 joint study](../python-game-hd22-joint-study/README.md) compares
normal and shared adaptive controllers on the same native frames. Equality of
packets/ACKs/display/reference output must precede any timing comparison. Python
wall timings do not establish native host or target throughput, hardware frame
rate, RF/QSPI capacity or memory deadlines.

## Tests

Sixteen tests cover exact packet/ACK/decoded-output parity over multiple maps for
key, P and repeated promotion frames, including source equal to promotion
destination. They include GM/exact/prune2/prune4 modes, four rejected cap attempts
and reuse of the unissued ID, input/config/reference mutation, callback failure,
external leases, descriptor pressure and the required end-before-commit lifecycle.
Small 64×64 inputs keep these ownership/arithmetic tests fast; they are not native
720×480 gameplay or timing evidence.

```sh
python -m unittest -v test_model.py
```

Use the project environment with NumPy/Pillow. Frozen dependency sources and the
native campaign are pinned by the v23 aggregate evidence; no installed endpoints,
old experiments, hardware or Git branches are modified by this component.
