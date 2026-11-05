# V44 one-block AB38 coefficient receiver

The new `TileReader` delivers coefficients as owned 8×8 int16 tiles without
staging a full coefficient plane or three full AC-band arrays. It preserves the
existing AB38 wire and reuses the frozen independent binary arithmetic primitive;
this is a buffering/delivery prototype, not a new entropy algorithm or target port.

All **3,462** archived full/compact alternatives from v38/v39/v40 were replayed:
**9,177,762** coefficient tiles, bit-exact against the old full-array decoder.
There are 1,731 full and 1,731 compact payloads. Real trials use arithmetic syntax;
raw fallback is additionally exercised by dense and malformed directed tests.
Six focused tests pass. Independent qualification checks every block immediately,
all hashes, geometry, source pins, exhaustion and live state ownership.

## Four concurrent cursors

The DC reader retains the previous DC value and resets it on the declared row
boundary. Each of three AC readers retains one pending nonzero index/value and
its remaining event count. For each output tile, the reader consumes only events
whose linear band index falls in that tile, then places values using the frozen
zigzag order. All four streams retain independent arithmetic interval/code and
probability state, including run/level contexts and exact termination checks.
Empty bands finish immediately; final checks occur before returning the last tile.

Logical coefficient staging is **128 bytes per tile**, compared with 691,200 bytes
for a 5,400-block luma coefficient plane in the full-array API. That comparison
covers coefficient output staging only. The iterator retains the complete compressed
payload (at most 23,937 bytes in this campaign), four arithmetic states, 352 logical
probability bytes, three pending AC events and control state. Python containers,
integers and objects have larger heap costs. Transform, prediction, reconstructed
frames, transport and frame publication remain outside this component.

CRC is checked before iteration, but a CRC-valid semantic failure can still occur
late. Returned tiles are provisional. A caller must stage reconstructed output
and publish a frame/reference only after the whole packet/frame has finished
successfully. The malformed raw test proves that earlier tiles can precede a late
range error and that the failed iterator cannot later report success. This API
alone is not an atomic frame receiver.

Compact payloads deliver only their declared visible sequence; the frame receiver
must supply implicit hidden zeros and map visible tiles to the fixed raster. The
iterator's declared `blocks_w=1` for compact DC prediction remains unchanged.

## Timing scope

Single alternating pairs across the retained payloads average 15.50 ms for the
old full-array decode and 19.21 ms for iteration plus per-tile hash accumulation.
The old array hash is outside its clock. This asymmetric diagnostic is not a
controlled speed comparison or a claim that iteration is faster. Correctness,
reduced logical staging and target-friendly delivery are the result; native
implementation, concurrent entropy engines, DSP integration, memory service,
routed clock and physical 30 fps remain unproved.

```sh
python -m unittest -v test_decoder
python benchmark.py
python verify.py
```

No FPGA RTL, ESP32 firmware or Sunshine service is changed. V43 separately removes
proof-adapter entropy re-encoding at the complete CS38 frame boundary; integrating
this iterator into that receiver and into a bounded transform pipeline is a later
step, with unchanged atomic publication requirements.
