# Production observability: measured scope and proposed ABI

A narrow production wrapper is worth evaluating, but present reports do not prove that debug ports caused high Slice use or prevented the main memories from being inferred. This is a read-only inventory of the frozen refined 125 MHz composition; the final candidate may place differently. No wrapper, RTL or flow was changed.

The [inventory](../../experiments/python-gamebub-v115/inventory/observability-review.json), SHA256 `d93b645b1b93d22c8b3bb4f64defd730dfc5500f6f8938b9a9d66d95457667d3`, pins actual sources and `route-check-timing`, capacity, hierarchy, control-set and distributed-RAM reports from `/home/lori/gamebub-build/cu66-v69/v115-integrated-125-20261109T024836651775Z-7eb017/results/`.

## What is actually exposed

The report lists 12,887 output **bits** without output delay and 1,101 input bits without input delay. The source header declares 12,920 output bits and 1,102 input bits including clock; the inventory below counts exactly the report's listed outputs, not an assumed package pin count. This is an OOC component with zero bonded IOBs, not 12,887 physical GPIOs. No internal register endpoint is unconstrained in the same report. Undelayed outputs still need a real integration timing contract before external/service-path timing can be claimed.

| Reported output category | Bits | Source/role |
| --- | ---: | --- |
| `count_*` and `inverse_count_*` | 7,104 | 64-bit work/stall/ownership counters and state histograms |
| `ts_*` | 1,408 | Fence and per-band timestamps |
| `inverse_coefficients`, `inverse_dequantized` | 2,304 | Full 64×16-bit coefficient and 64×20-bit dequant observations |
| `dbg_*` | 243 | Scratch states, event signals, bank metadata and local flow taps |
| Other outputs | 1,828 | Mixture of operational interfaces, status, intermediate pipeline taps and smaller statistics; not all removable debug |
| Total | 12,887 | Exact sum of report-listed output bits |

Counters and timestamps are 8,512 bits (about 66%); adding the two wide inverse vectors reaches about 84%. These are substantial exposed networks, but bit counts are not unique flip-flop or LUT counts. Some signals alias functional nets; a wrapper can remove external observation loads without removing their functional logic.

Keep the real service ABI: command/credit, packet stream, candidate scratch memory requests/responses including epoch and error, reference requests/responses including generation and pixel payload, cache preload/accepted-reference state, canonical output plus frame/tile/index metadata, and completion/error/draining/publication integration. For example the 128-bit `mem_req_data` and 512-bit reference response are functional data, not debug buses. Current coefficient/residual readiness also controls real transfer and must not be removed or retimed merely because it is exposed for checks.

The current live wrapper `fpga/experiments/cu66-v115-live-parent/cs88_live_v91l.sv` propagates the wide inverse observations and counters to its own ports (`producer` connections include lines 432/433, 465 and 533). Its testbench compares inverse values through these ports. Thus the existing larger simulation wrapper does not itself demonstrate a narrow production integration.

## What observability does and does not force

- The top exposes `inverse_coefficients` through `dbg_coefficients=coefficients[math_bank]` and `inverse_dequantized` through `dq_data` in `cu66_inverse_stream_v91j.sv:999`. These can retain broad observation/fanout and selection loads. However the exact same coefficient vector feeds the real dequantizer at line 1025, and dequant output feeds the real IDCT. Removing the observation ports alone cannot make a 1,024-bit parallel functional read into a single BRAM read port.
- The coefficient banks are explicitly generated 64×16-bit per bank payload registers; result slots explicitly copy all 64×24-bit words in one edge and then select samples (`cu66_inverse_stream_v91j.sv:1004–1020`). Their register/parallel-access architecture is functional. BRAM replacement needs a new schedule/banking/read-during-write proof, not just a debug switch.
- Scratch `heads`, `head_positions` and `tile_payload` are internal arrays, **not** top raw-array output ports. The simulation's hierarchical probes/Verilator `--public-flat-rw` do not add native Vivado ports. The actual distributed-RAM report already lists `heads_reg...` and `head_positions_reg...` as RAM32X1S/RAMS32. Therefore “raw heads debug prevents RAM inference” is false for this report.
- Scratch tile storage is an explicit per-word write register structure plus pending-write forwarding and validity masks. Its arithmetic/ownership/public-cycle semantics, rather than a hypothetical raw output port, must be audited before changing inference. No source-level debug `KEEP`, `DONT_TOUCH` or `MARK_DEBUG` attribute was identified in these selected inverse/scratch bodies.
- The child wrapper has 7,141 FFs outside its children in the hierarchical report. Its source contains the extensive 64-bit counters, 16/32-state histograms and timestamps at `br88_pipeline_v91h.sv:222–270`. That supports investigating instrumentation cost, but it is not an exact per-register attribution.

## Why Slice 91% does not mean LUT 91%

The actual routed report has 14,443/15,850 Slices (91.12%), 36,687/63,400 LUTs (57.87%), 40,895/126,800 FFs (32.25%), 38 block-RAM tiles and 42 DSP48E1s. It also reports 1,177 control sets, 22,647 registers driven from outside their Slice, and 9,062 of those register locations with the preceding LUT unused. Used Slices average about 2.54 LUTs of four possible LUT sites; registers, carry/mux placement and route locality need not pack into the same Slices. The control-set report records 809 unused register locations in Slices containing registers; do not misread all globally unused FF sites as control-set waste.

These facts support a **packing/locality/architecture hypothesis**. Distinct enables/resets, replicated bit slices, wide register payloads and the placement needed for long routes can spread logic. The data do not attribute 33 percentage points of Slice use to debug. High Slice use can constrain placement and amplify routing delay even with nominal LUT capacity remaining. Only a controlled wrapper comparison, hierarchy/cell attribution and routed utilization/control-set/congestion reports can quantify the contribution.

## Proposed production debug ABI

Introduce a separately versioned production wrapper, leaving the verification top and all raw-port/original test contracts intact. Keep all operational service ports and required ownership/fault/fence metrics. Replace the thousands of unconstrained parallel observation outputs with:

1. A registered, bounded CSR request/response port for status, version/capabilities, errors, frame/epoch, accepted/emitted/write/reference counts, abort/drain counts, stall/watermark metrics and the packet/input/ACK/hash/root/HUD/seal/commit fence timestamps. Use explicit response latency and backpressure. A status read must never drive a data-path ready decision.
2. Atomic snapshots at a declared quiescent/frame-complete fence, or a bounded snapshot handshake while events continue. Define exact epoch attribution, event retirement and wrap behavior. Reading a 64-bit counter as two halves requires a coherent snapshot. Snapshot storage is not free: copying all counters can duplicate thousands of FFs; freezing a stable completed-frame bank or serializing a bounded capture has different cost/latency and needs a proof.
3. A small optional ILA/event-trace selection with registered local taps and explicit sampling trigger/ownership. Do not route all 2,304 inverse bits into ILA by default. Full payload examination can use a frozen owned-bank indexed snapshot port, but adding that port must respect real memory bandwidth and cannot introduce unproved live read/write collisions.
4. Raw heads/tile/inverse arrays remain accessible to simulation through bind/hierarchy or a verification-only interface. No physical memory-layout/latency conclusion may be drawn from that visibility. Detailed state histograms can be an explicit verification/debug feature; removing them from a production feature set is a **changed debug ABI**, not equivalent counter behavior.

A CSR mux alone preserves the counters' FFs and increment logic and may add logic; it mainly changes output connectivity. To reduce storage/arithmetic cost, a later design could encode events into a finite trace or time-multiplex counters, but it must prove handling of simultaneous events and overflow rather than losing counts. Required workload/ownership counters cannot be deleted simply to remove a critical endpoint. The earlier registered event-boundary proposal keeps event meaning and declares observation latency explicitly.

## Comparison gate

Before any later native work, make an exact port/consumer map for the actual full parent and distinguish functional consumers from terminal observations. Simulate the new wrapper with original service/value/owner oracles, CSR snapshot goldens, simultaneous counter events, reset/abort/drain and same-object retries. Reconcile essential counters and timestamps at the same fences. Then, only under a separately authorized budget, compare the same full parent with equivalent debug capabilities/service interfaces, real boundary clocks/delays and memory/CDC/publication integration. Report LUTs, FFs, Slices, RAM inference, control sets, high-fanout nets and timing by path family. Optional-debug comparisons must name the changed capability. No area saving, RAM conversion or timing gain is claimed by this inventory.
