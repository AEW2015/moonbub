# V71 native-rate LCD burst reader

`fpga/experiments/cu66-v71/display/cu71_scanout.sv` replaces the v70 scalar
480-request line reader with **60 aligned BL8 requests per line**. It reuses
`cu70_lcd_lines.sv` unchanged, including the dual 480-word line banks, held
request tokens, synchronized completion tokens, and whole-line black fallback
when a line misses its deadline. No v70 source or result is edited.

The descriptor interface and lease semantics are unchanged. A descriptor is
already globally committed before admission. Its generation/frame/slot becomes
the front identity only at the LCD's memory-domain frame boundary when all line
requests and accepted burst work have drained. The resulting `presented` pulse,
with the actual front identity, remains the RGB-owner release event. Raw vblank
alone does not release a slot.

## Memory interface

All addresses are x16 word addresses. Each request is aligned to eight words.

| Signal | Contract |
| --- | --- |
| `lcd_req_valid`, `lcd_req_ready`, `lcd_req_addr[23:0]` | One held aligned BL8 request; address remains stable until accepted. |
| `lcd_rsp_valid`, `lcd_rsp_ready`, `lcd_rsp_data[15:0]` | Eight ordered response beats per accepted request; arbitrary gaps are allowed. |
| `lcd_rsp_last` | Must be false on beats 0–6 and true on beat 7. |
| `lcd_rsp_error` | The errored word is delivered as black and increments `memory_errors`. |

The reader owns an accepted burst until its eighth accepted reply. The memory
adapter must not drop a reply during an abort. Early/late LAST raises a diagnostic
and increments `memory_errors`; the reader still counts exactly eight beats to
keep a malformed LAST from changing the following line's word count. A source
that never completes those eight beats requires coordinated recovery; this leaf
module has no independent timeout/cancel protocol. Full reset flushes both clock
domains and the memory adapter together.

The fixed response-beat counter is three bits; the line counter remains nine
bits. Response framing errors do not authorize presenting a provisional RGB
buffer. Descriptor errors and memory errors share the existing one-cycle `error`
observation, while `memory_errors` separately counts errored beats.

## Measured component results

Run from the repository root:

```sh
python3 scripts/cu66-v71/run_display.py
```

The explicit backend is Verilator 5.020 with fatal `--Wall`; an independent
control probe uses Icarus Verilog 12. The recorded transcripts and source hashes
are in `fpga/experiments/cu66-v71/display/results.json`.

The memory clock period is **10,000 ps** and the unrelated pixel clock period is
**34,058 ps**, preserving the root model's 17,029 ps half-period. With H_TOTAL541
and V_TOTAL834, the native panel model is **65.0755044 Hz** and one line is
**18.425378 µs**, or 1,842.5378 memory clocks. This is panel scanout cadence; it is
not a 65 fps streaming or decoder result.

| Schedule | Complete rasters | Exact pixels checked | Underruns | Other expected observations |
| --- | ---: | ---: | ---: | --- |
| Ideal service | 2 | 768,000 | 0 | 86,400 requests, 691,200 beats |
| Seed7101, held requests and reply gaps | 2 | 768,000 | 0 | 21,491 request-stall clocks |
| Seed7102, held requests and reply gaps | 2 | 768,000 | 0 | 21,486 request-stall clocks |
| Seed7101, deliberately slow burst service | 2 | 768,000 | 1,440 | Exactly1,440 whole-black lines |
| Seed7103, reply gaps plus early LAST and read error | 2 | 768,000 | 0 | Both errors counted; one errored pixel black |

Every schedule checks the two front generations/IDs, queued slot replacement,
rejection of one stale descriptor, exact portrait pixels and black borders,
request stability, eight-beat completion, and drained readers at the final
margin. Each non-starved schedule performs exactly60×720×2=86,400 requests and
691,200 accepted response beats. Total coverage is **10 complete rasters and
3,840,000 pixels**. The Icarus probe passes **31 checks** covering an accepted
partial burst, 20-cycle response gap with ownership retained, early LAST,
coordinated reset, an orphan reply ignored after flush, and fresh descriptor
presentation after reset.

These component tests model memory service latency; they do not issue SDRAM
commands. The full system must separately prove the shared SDRAM arbiter can
meet the 1,842.5-clock line budget while decoder, HUD, and painter traffic run.
This result does not establish sustained30 fps decoding, target FPGA fit/Fmax,
formal CDC signoff, physical display quality, or under10 ms validated decoding.
