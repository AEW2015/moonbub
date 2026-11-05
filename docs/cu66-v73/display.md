# V73 explicit strip-lane banking

`cu73_painter_burst` preserves the V72 memory interface, exact YUV420 conversion,
HUD overlay, portrait layout and completion/abort rules. Its strip store is now
**eight explicit 720×16 row-lane arrays**, replacing one logical 5,760×16 array
with eight simultaneous read expressions.

One produced pixel writes only bank `y[2:0]` at coded column `x`. The drain reads
one word from each bank at `drain_x`; lane 0 occupies the low 16 payload bits and
lane 7 the high 16 bits. The gathered payload is still registered in the existing
write-data stage. No new memory transaction or pipeline clock was introduced,
no strip-array reset/clear loop was added, and logical capacity remains
**92,160 bits / 11,520 bytes**.

The source declaration makes the lanes explicit. Actual target RAM mapping is a
separate question; the [frontend and family-mapping report](elaboration.md)
provides the measured unplaced 7-series mapping scope.

## Exact-output evidence

```sh
python3 scripts/cu66-v73/run_painter.py
```

Native SystemVerilog simulations use Verilator 5.020, the original native
CU66/color/HUD oracle, three schedules (seeds 0, 7201 and 7202), and an ideal
memory service with delayed completion and backpressure. All three pass:

- 39 complete raster executions, each comparing every one of 384,000 portrait
  RGB565 words: **14,976,000 exact word comparisons**.
- Eight actual key/P fixtures from the retained four cohorts, four synthetic
  color/rounding patterns and one recovery execution per schedule. These are
  repeated test executions, not 39 distinct source captures.
- 48,000 full-mask aligned BL8 write requests / 384,000 written words, 280,320
  scalar source/HUD reads and 345,600 composed canvas pixels per complete frame.
- Ten accepted-operation abort/memory-error probes across the two randomized
  schedules; a pending accepted operation must drain before the painter becomes
  ready again. Held request identity, address, payload and mask remain stable.
- Thirty rejected starts: invalid generation/frame ID, RGB misalignment, address
  overflow and allocation overlap. They issue no memory work or valid result.

The native results are in `display/results.json`, with producer commands,
source/fixture hashes, logs and per-case counters. The banked writer's per-case
cycle counts match the V72 oracle schedule for the same seed and input.

An additional **39-raster** campaign compiles the sv2v-generated V73 Verilog and
runs the same benchmark in a different build directory. This repeats output,
fault and rejected-start checks after language lowering; it is not a new source
capture campaign or formal equivalence proof. Its results are retained in
`memory/elaboration/results.json`.

The painter bench applies each accepted full write at response time. It checks
ownership/drain but is not a physical beat-by-beat SDRAM test. Real masked-burst
behavior, partial accepted aborts and reset recovery are qualified separately by
the memory/controller and command-level system benches. These tests establish
no board timing, physical 30 fps or target decode latency.
