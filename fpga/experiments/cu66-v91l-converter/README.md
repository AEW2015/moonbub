# Actual RGB565 converter joined to retained tiled reads

`canonical_rgb565_tiled.sv` joins the frozen `canonical_rgb565_lines`, its actual
scalar chroma-prefill/registered-cache/bilinear RGB565 pipeline, and the frozen
three-plane `tile_rowpair_reader`. The wrapper latches bank/epoch/generation at
start, gives each canonical line a monotonic token, rejects invalid starts,
propagates errors/cancellation, and waits for both converter and physical-reader
ownership to close. Its physical128-bit interface can connect to either the
bounded actor or `bl8_read_bridge`. Original converter/cache/reader sources are
unchanged.

The declared-actor comparison compiles independent and retained gathers
separately, runs two seeds, and checks both complete native canonical frames
against the existing native RGB565 goldens. Every accepted pixel's address,
epoch and value is checked; each frame's actual output bytes are retained.
Row digests and timing receipts support the independent audit without logging
every pixel on every clock.

## Declared actor results

All four modes pass 13 checks, including invalid start IDs, competing descriptor
mutation, cancellation/reset while work is pending and on matching response
edges, wrong physical generation, memory error, held RGB output, and two complete
native outputs. Native full frames use the same physical bank with a changed
accepted generation and different content.

| Native converter | Independent gathers | Retained rows |
|---|---:|---:|
| Physical 16-byte bursts/frame | 64,800 | 32,400 |
| Actual RGB output words/frame | 345,600 | 345,600 |
| Accepted start → closed cycles | 3,500,170–3,500,771 | 3,067,328–3,067,925 |
| Accepted start → first RGB pixel cycles | 5,671–5,719 | 4,469–4,490 |

The whole joined conversion improves 12.35–12.37%, rather than the isolated
retention reader's earlier 42% result. The real scalar converter work is now
inside the window. The actor charges eight payload plus 1..5 wait cycles,
seeded physical request-ready stalls and seeded RGB output stalls; it does not
model controller row commands, refresh or competing clients. At a hypothetical
100 MHz this is about 30.67 ms/frame for retained conversion alone. It is not an
achieved-clock, live decoder, shared-service or hardware cadence result.

## Timed-controller top

`canonical_rgb565_timed.sv` adds the actual tagged BL8 read bridge, frozen
pipelined SDRAM controller and frozen timed pin-level model. It retains the
same joined converter wrapper. A separate timed C++ bench advances every pending
Verilator timing slot between clock edges, preserving the 10 ns source period,
4ns forwarded-clock flight and 7.75 ns read-capture phase. The default timescale
is explicitly 1ns/1ps for frozen converter modules that have no declaration;
existing declared timescales are retained.

The native tiled memory is directly preloaded with the read-bridge fixture
before frame timing windows. This is not physical candidate-write integration.
Bank 0 holds key canonical bytes and bank 1 holds the delta. Cancellation/reset
probes include unissued bridge requests and actual accepted READs after three
captured words; all eight words must drain before reuse. A held pixel is also
canceled. The controller only receives cold power-on reset.

The final timed campaign uses two seeds at both selected 2-/7-ns data delays,
with seven checks per mode and two complete native outputs per mode. The
accepted-start → closure window is 3,360,839–3,362,747 cycles; first RGB appears
at 5,299–5,312 cycles. At the assumed 100 MHz this is about 33.61–33.63 ms for
conversion alone, slightly above the 33.333-ms nominal 30-Hz budget. This is a
measured component bottleneck, not a sustained-frame-rate result.

The timed report retains converter first/last/closure cycle fences and
per-frame state histograms; wait counters overlap states and must not be added
as separate work. Each histogram samples every bench clock from accepted start through closure;
its entries sum to the reported tick-count fence. For one qualified delta
sample, converter states are IDLE4, CHECK_ROWS720, FILL_REQ172800,
FILL_WAIT456199, LUMA_REQ345600, LUMA_WAIT917070, LOOKUP_REQ345600,
LOOKUP_WAIT345600, CONVERT345600 and EMIT431876. The physical controller is busy
for 543034 of those cycles while the line adapter is pending for 822469;
those overlapping observations cannot be added. This points to scalar byte
handshake and per-pixel staging as further optimization candidates.

Native RGB outputs remain byte-exact. The actual controller
adds service cost that the earlier logical actor omitted. Refer to the selected
`timed-results.json` and independent audits for the qualified matrix and exact
numbers. No whole decode/publication or shared-memory claim follows.

## Contracts and remaining work

- The frozen line reader and retention reader hold `ready` for their single
  matching pending owner. Matching response backpressure is therefore not
  externally reachable in this joined converter. Tests cancel on those response
  edges; standalone reader/bridge tests separately exercise held responses.
- Warm cancellation never retracts accepted physical work. The wrapper cannot
  start another lease while an inner byte/line/burst owner remains outstanding.
- Live descriptor changes cannot change the accepted bank, generation or epoch.
  Invalid starts emit no memory work.
- Complete RGB golden agreement checks actual interpolation and chroma right/
  bottom edges, beyond the earlier canonical-byte replay.
- Hash/publication, live entropy/reconstruction, candidate writes, other memory
  clients, HUD semantics and physical target fit/timing are outside this gate.
  Sustained hardware 30 fps and complete validated decode below 10 ms remain open.

## Reproduce

Use `gamebub-cu66-v69-build`, Verilator 5.020 and GCC 13.3.0. Strict builds use
assertions, `-Wall`, C++20 `-Wall -Wextra -Werror`, and two compilation jobs.
Timed builds additionally enable `--timing -DSIMULATION`. No warning waiver is
introduced. All selected inputs/sources, raw output hashes, commands, tool
versions and return codes are retained by each runner.

```sh
python3 scripts/cu66-v91l-converter/run_comparison.py
python3 scripts/cu66-v91l-converter/run_timed.py
```

Preflight diagnostics retain the wrong-width command-line bit parameter,
C++ indentation errors and missing timescale warnings. Those were corrected
with an explicitly sized parameter, clear statement layout and the documented
default-timescale flag; source warnings were not disabled. Early expanded
inputs were removed only after recording their hashes; compressed source
inputs and qualified snapshot copies remain available.
