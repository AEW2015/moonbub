# Connected CU66 base-layer RTL

`cu66_base_pipeline.sv` connects the actual AB38 entropy decoder, compact/full
tile expander, quantizer lookup, dequantization, exact Q14 inverse transform,
zero-motion reconstruction, canonical tile-to-row serializer and SHA-256 RTL.
All decoded pixels and the complete 256-bit digest are checked by the bench.
The top compares the first 128 digest bits with the configured CU66 output tag.

This is a base-layer core, not a complete CU66 packet-to-panel receiver. Its
metadata and quantizer map come from testbench parsing of packets already
accepted by the qualified native decoder. The separately tested packet RTL,
HUD software partition, three-bank controller, physical SDRAM controller,
color conversion, filtering, rotated LCD scanout and ESP32 ingress are not
connected in this top. Reference samples are testbench arrays from the
qualified native prior frame; exact agreement of each reconstructed tile does
not replace a physical memory/reference-bank integration test.

## Interfaces

- Start config: frame ID, key flag and expected canonical tag. Per-plane config
  follows in Y/Cb/Cr order, with dispatch 5 or 6, AB38 byte length and encoded
  tile count. The compressed address excludes the dispatch byte.
- Compressed memory: one outstanding byte request/response, tagged by plane.
  Hold the immutable compressed allocation until all requests have drained.
- Quantizer map: one outstanding request and a synchronous response at least
  one cycle after acceptance; the response has no backpressure. Index is the
  shared 45×30 quantizer grid, not the full luma tile index. The bench assumes
  a separate local map port rather than competing for SDRAM slots.
- Reference memory: one outstanding 64-byte tile request/response. The tag is
  `{13'b0, plane[1:0], full_grid_index[16:0]}`. Key and hidden tiles need no
  reference read. Responses must remain stable until accepted.
- Candidate writes: `tile_valid && tile_ready` accepts a 64-byte provisional
  tile. Exactly one write can be outstanding. `write_done` acknowledges actual
  visibility/completion on a later clock; `write_error` is sampled with it.
  No result tag or new transaction is released while this lease is outstanding.
  This is an explicit completion protocol, not a DDR queue-ready assumption.
- The memory and canonical-hash branches each hold their own valid until
  acknowledged. The reconstruction tile retires only after both branches
  accept it. A slow branch cannot cause duplicate or dropped samples.
- `tag_valid` indicates only successful base-layer reconstruction and hash
  checking. Global publication must additionally require packet/HUD checks,
  all adapter drains, and the bank controller's safe ownership transition.

`abort_i` cancels provisional work and drains accepted compressed, quantizer,
reference and write transactions before another start. Errors remain available
until the next start. A local reset assumes **all external adapters are flushed**;
reset is not a substitute for draining a running memory controller. The external
bank owner must retain all allocations until both the core and its adapters are
quiescent. No CDC boundary is implemented here.

## Regression

Use the dedicated tools container and the repo's normal absolute mount:

```sh
python3 scripts/cu66-v69/run_pipeline_regression.py --seeds 6901 --shared-bus
```

The default per-chain limit is 9999, covering all 457 retained frames. A smoke
such as `--per-chain 2` covers only eight frames and must not be called a full
corpus qualification. Consult command argv and terminal counts in the result.

Five fault probes require distinct error codes: AB38 CRC (0x12), invalid
quantizer code (0x31), wrong reference tile tag (0x33), wrong output tag (0x50),
and write-completion failure (0x61). Seeded tests also abort with accepted
compressed reads, reference reads and writes outstanding, require drain before
restart, and reconstruct a clean key frame afterward. Output stalls, full
tile identity/last markers, all 518,400 sample bytes and full SHA-256 are checked.

The shared schedule has a single modeled x16 service slot per clock, rotating
compressed-byte, reference-tile and candidate-write clients. A compressed byte
uses one slot; a 64-byte tile uses 32 slots. Alternate clocks are reserved for
display traffic, 16 of every 7,800 clocks for refresh, and a seeded 10% of the
remaining slots are unavailable. This is an explicit contention experiment,
not an implementation of SDRAM command timing or a measured board schedule.
Seed 0 without `--shared-bus` is the ideal-port control.

The one Verilator warning selection, `-Wno-PINCONNECTEMPTY`, permits explicitly
unconsumed diagnostic output ports on subcomponents. Functional ports are
connected; other `--Wall` diagnostics remain fatal. Original failed and
interrupted development logs are retained separately from final results.

Neither simulated clock counts nor native host timings prove FPGA Fmax,
resource fit, physical 30 fps, ESP32 throughput or end-to-end latency. The exact
Artix-7 part is unavailable in the current Vivado installation. An in-memory
OOC build script is staged at `../scripts/ooc_base_pipeline.tcl`; its reports
remain a separate implementation gate.
