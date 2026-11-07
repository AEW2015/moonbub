# V91l physical packed scratch and common-memory control

This extends the [physical accepted-reference control](../cu66-v91l-reference-reader/README.md)
by moving the packed coefficient scratch endpoint from a finite C++ responder
onto the same actual RTL SDRAM controller used for candidate writes,
accepted-reference reads and base RGB output. All four external memory
endpoints are now RTL clients in this experiment. Native HUD interpretation
remains a software endpoint; native decode/display overlap and complete-system
qualification remain open. V91l remains partial and V91m is not promoted.

The coding syntax, quality and 720×480 source resolution are unchanged.
This measures a previously excluded memory cost and provides a firmer control
for subsequent scheduling improvements. It introduces no HEVC/AV1 quality or
bitrate improvement.

The [measured result table](results.md),
[independent audit](../../experiments/python-gamebub-v91l-scratch-service/audit.json)
and [machine-readable summary](../../experiments/python-gamebub-v91l-scratch-service/summary.json)
bind the selected source snapshots, exact outputs and simulation scope.
The delta's simulated start-to-commit window alone is 33.460–33.465 ms,
slightly over a 33.333-ms frame slot. Decode/display overlap must therefore
be paired with lower decode cost; overlap alone does not establish 30 fps.
Use measured scratch/reference/writer waits and validation costs to select
the next optimization.

## Memory contract

Scratch requests are full, aligned 16-byte lines with an 18-bit byte offset,
32-bit nonzero epoch and one outstanding request. The controller aperture is
SDRAM bank 3, byte offsets 0–262143. Its x16 word address is
`0xc00000 + (byte_offset >> 1)`. The last legal line starts at 262128 and
occupies words `0xc1fff8..0xc1ffff`. Existing candidate/reference/display
bridges continue to reject bank 3; their bank 0–2 bounds remain unchanged.
This is an explicit address allocation in the modeled controller, not board
capacity, whole-design fit or placement/timing signoff.

The unchanged controller uses mode register 0x233: eight-word burst reads and
single-word writes. Each 128-bit scratch WRITE therefore issues eight actual
x16 WRITE commands; each READ issues one BL8 command and captures all eight
words. There are no partial writes, byte-mask shortcuts or implicit RMWs.
The bridge stages one 128-bit line plus ownership/control metadata; the
262144-byte scratch aperture is external memory, not an on-chip RAM claim.
See the [executable address/payload model](../../experiments/python-gamebub-v91l-scratch-service/model-contract.md).
Scratch uses separate child epochs for the three decoded planes. Per-frame
accounting binds observed scratch requests to native source IDs and retains
child-epoch totals separately; a child epoch is not an outer frame epoch.

An outer round-robin arbiter selects complete video or scratch transactions.
The existing video arbiter still schedules candidate writes and the
reference/display read mux. Grants survive accepted commands, recovery,
read capture and held responses. Reset/cancel suppresses unissued commands,
drains accepted physical work and returns one error response. Already offered
responses remain immutable. The caller must consume even a canceled response;
a stalled response intentionally retains the memory grant.

## Evidence and reproduction

Use the existing `gamebub-cu66-v69-build` container with Verilator 5.020 and
GCC 13.3.0. HDL/C++ warnings and assertions remain enabled, builds use two
compile jobs, and every simulation has finite watchdogs. The functional timed
pin model uses the retained clock phases, refresh and 2/7 ns tAC corners;
this is not a routed timing/SDF/PVT or hardware result.
`scratch_line_bridge.sv` is the standalone RTL adapter. The generated
`scratch_sdram_timed.sv`/`scratch_shared_timed.sv` wrappers include the timed
simulation pin model and delayed read clock; they are verification tops, not
board-ready bitstream sources. Hardware integration must extract the reviewed
outer arbitration into the real top, preserve its drain contract and qualify
the actual memory aperture, clocks and I/O constraints.

```sh
python3 fpga/experiments/cu66-v91l-scratch-service/generate_wrappers.py
python3 scripts/cu66-v91l-scratch-service/run.py
python3 fpga/experiments/cu66-v91l-scratch-live/make_wrapper.py
python3 fpga/experiments/cu66-v91l-scratch-live/make_bench.py
python3 scripts/cu66-v91l-scratch-live/run_test.py
python3 experiments/python-gamebub-v91l-scratch-service/scratch_model.py --check
python3 experiments/python-gamebub-v91l-scratch-service/verify_generation.py
python3 experiments/python-gamebub-v91l-scratch-service/verify_results.py
python3 scripts/cu66-v91l-scratch-summary/summarize.py
```

Independent replay learns SDRAM contents only from actual pin WRITE commands.
It checks native and SV scratch handshakes, physical addresses and DQ, all
captured read words, response assembly, fairness, cancellation/drain and held
response identity. It retains the source-backed canonical/reference/RGB
oracles, actual RTL SHA job checks and protected-bank/publication checks.
Corrupted receipts must fail for their intended causal reason. Generator
replay intercepts writes and reproduces all four generated outputs without
rewriting qualified sources. Attempts retain exact snapshots, input hashes,
commands, raw diagnostics and losslessly compressed event/output receipts.
The [packaging check](../../experiments/python-gamebub-v91l-scratch-service/packaging-check.json)
records exact whitespace exceptions for byte-identical frozen source snapshots
and raw compiler-version output. Other staged files pass Git whitespace checks;
no compiler warning or assertion is waived.

## Next work

1. Qualify native bank-safe decode/display overlap against this serial control
   and reduce decode cost below the source-frame budget.
   Connect real consumer leases and publication/scanout drain; measure
   contention, wait cycles and deadlines for the entire shared workload.
2. Compare bounded reference prefetch, scratch scheduling or copy/reference
   reuse only after complete contention is measured. Keep the current serial
   workload and exact pixels as the control; promote one measured change at a
   time.
3. Close all-RTL HUD decode/composition and mixed entropy or an explicit tested
   fallback. Run V91m's fixed 30-Hz, distinct-source-frame workload.
4. Continue actual ESP32/transport budgeting and the V100–V110 7-series
   mapping, placement, routing and hardware qualification gates.

Sustained hardware 30 fps and complete validated decoding strictly below
10 ms remain open. Two native source images and a serial simulated workload
cannot establish either milestone.
