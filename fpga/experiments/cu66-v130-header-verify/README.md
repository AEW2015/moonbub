# Extended header-fetch comparison

This verification-only experiment copies the existing V129 paired actual-ingress
RTL, retaining its 67-public-output comparison and its candidate's RECEIVE
index assertion. It does not change the selected design or prove timing.

The bounded, source-frozen `run.py` runs a new C++ testbench against those two
actual RTL instances. In addition to four fetch-purpose controls, it sends
valid packets with input gaps, applies deterministic metadata, output, and
band-end backpressure, asserts `in_last` at five premature positions and omits
it on the final byte, then checks error 2 and successful recovery. It cancels
in receive, while header fetch is pending, while metadata is held, and while a
coefficient is held; each case is followed by a valid recovery packet. Runtime
assertions and comparisons are enabled. A PASS establishes only this directed
finite two-state simulation, not formal equivalence, full-composition coverage,
or routed timing.

Run on the pinned toolchain container with `python3
fpga/experiments/cu66-v130-header-verify/run.py`; the runner freezes hashes and
copies all test inputs before execution, uses 2 CPUs, 8 GiB RAM plus swap
limit and a 900-second watchdog, and records attempts under
`experiments/python-gamebub-v130/header-verify/attempts/`. Failed attempts are
retained; no assertion or warning is downgraded.

## Executed result

The [2026-11-10 attempt](../../../experiments/python-gamebub-v130/header-verify/attempts/20261111T023151282166Z/receipt.json)
passed on Verilator 5.020: 10,753 clocks and 41,677 evaluation comparisons,
1,254 input-gap cycles, 3,195 cycles with at least one stalled output interface,
six malformed cases, four cancellations and ten successful recovery packets.
All four fetch purposes were observed. Its receipt SHA-256 is
`f93d6d23b6ede9a89c101cbd3e15537e57988918d417ff151dea8eba6ec2f27f`.
Nine source/snapshot pairs and all 105 receipt-listed artifacts were rehashed.
The launch gate passed; during compile the minimum available RAM was 16.22 GiB
and maximum full-memory PSI avg10 was 4.36%, below the stop threshold.

This is a directed comparison of paired ingress implementations with a common
downstream reference, not an independently verified complete decoder or an
exhaustive/formal proof. It tests error code 2 for malformed last markers and
successful recovery; the overlap count is a cycle count, not an individual
per-interface distribution. It does not establish physical timing, actual ESP32
or FPGA behavior, sustained 30 fps, or under-10-ms decoding.

The local generated `obj/` is retained but ignored by Git. The corresponding
`obj.tar.zst` is 25.9 MiB and includes every generated object named by the
unchanged receipt. Run `python3 fpga/experiments/cu66-v130-header-verify/verify_archives.py`
with `zstd` installed to stream the trusted archive and verify its file hashes
without extracting. Restore the objects only after verification by extracting
that attempt's archive inside its own directory using `tar --zstd -xf obj.tar.zst`.
