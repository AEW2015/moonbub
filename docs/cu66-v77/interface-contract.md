# V77 component interface contract

All coordinates are coded canvas u=0..719, v=0..479. Physical active pixels
are x=v, y=u+40. Data/cache/address layouts remain V76. Memory words are x16.
Clock inputs are `clk`, `rst`, with one common memory/core clock in component
benches. No real pixel-clock CDC or complete receiver/display integration is
implied by that component interface.

## Cache and streamed prefetch

Module `cu77_direct_cache` uses the following ports:

```
input clk,rst,abort_i
input desc_valid; output desc_ready
input [63:0] desc_generation; input [31:0] desc_frame_id; input [1:0] desc_bank
input finish_valid; output finish_ready
output active,aborted,error; output [7:0] error_code
output [63:0] active_generation; output [31:0] active_frame_id
input prefetch_valid; output prefetch_ready; input [6:0] prefetch_index
output prefetch_done_valid; input prefetch_done_ready; output [6:0] prefetch_done_index
input consume_valid; output consume_ready; input [6:0] consume_index
output [6:0] prefetched_count,consumed_count
output mem_req_valid; input mem_req_ready; output [23:0] mem_req_addr
input mem_rsp_valid; output mem_rsp_ready; input [15:0] mem_rsp_data
input mem_rsp_last,mem_rsp_error
input pixel_req_valid; output pixel_req_ready; input [9:0] pixel_u; input [8:0] pixel_v
output pixel_rsp_valid; input pixel_rsp_ready
output [9:0] pixel_rsp_u; output [8:0] pixel_rsp_v
output [7:0] pixel_y,cb00,cb10,cb01,cb11,cr00,cr10,cr01,cr11
output pixel_hud_hit; output [15:0] pixel_hud
output pixel_rsp_error
output [31:0] read_commands,read_words,pixel_queries,cache_misses
```

Only one memory burst may be outstanding. Every accepted request returns eight
streamed x16 words, lowest address first, with last on word 7; this connects to
the frozen dedicated LCD read port. The data mover writes one received word per
clock rather than adding eight unpack clocks after a 128-bit snapshot. One
frame uses 35,040 accepted BL8 reads and 280,320 received words when filled
through all 90 strips, without repeated/malformed operations.

Descriptor acceptance invalidates all tags and binds bank/generation/frame. The
component must not accept a replacement descriptor while active, while memory
is outstanding or while a pixel response is held. Generation must be nonzero,
frame ID valid and bank <3. Bad metadata is rejected/error-signaled before
memory work. Finish is allowed only after all 90 strips are consumed and both
memory/pixel responses are drained.

Prefetch is ordered: accepted index equals prefetched_count, and index is less
than consumed_count+3. Consume is ordered: index equals consumed_count and is
strictly below prefetched_count. Count a strip ready only after all required
accepted data has drained and required complete-column tags are valid. This
bounds current+next-ready+filling live storage. Do not overwrite live tags/data
on malformed, skipped or duplicate requests. It is acceptable to leave an
invalid ordered request backpressured without issuing work; directed tests must
exercise it and show no physical command escapes.

Pixel requests require u/v in range and the corresponding strip >=consumed_count
and <prefetched_count. All required Y/chroma/HUD global-column tags must match.
Invalid/missing pixels produce an explicit error response, never silent valid
zeros. Pixel output is held under backpressure. Use synchronous complete-word
reads before byte extraction. Expose a one-cycle, one-request-per-clock-capable
neighborhood read interface if practical; valid/ready means no sample is lost
or overwritten under stalls.

Abort suppresses new work and invalidates publication. An accepted memory burst
must drain before the cache reports aborted or accepts another descriptor. Held
pixel responses also need a declared drained/canceled boundary so a new source
cannot receive an old result. Do not reinterpret late accepted words under a
new generation. Reset is paired with resetting the memory subsystem in benches;
local abort is the drain-preserving operation.

Storage: three Y columns (3×1920 words), three Cb and three Cr columns
(3×960 words each), and four packed HUD block columns for each rectangle
(4×4×192 words). Total 29,184 bytes excluding tags/pipeline/output storage.
Partition Cb/Cr by row parity and packed-word parity for up to four synchronous
word reads, one per bank, with one concurrent streamed write per cycle. At
clamped row/word duplicates, reuse the same word rather than create read ports.

## Pixel converter

Module `cu77_yuv_rgb` ports:

```
input clk,rst,abort_i
input in_valid; output in_ready
input [9:0] in_u; input [8:0] in_v
input [7:0] in_y,in_cb00,in_cb10,in_cb01,in_cb11,in_cr00,in_cr10,in_cr01,in_cr11
input in_hud_hit; input [15:0] in_hud; input in_error
output out_valid; input out_ready
output [9:0] out_u; output [8:0] out_v
output [15:0] out_rgb; output out_error
```

Use exact CU66 parity-dependent bilinear rounding, Q8 color rounding, clamp and
RGB565 packing, with opaque HUD replacement. Match the native decoder renderer.
Preserve coordinates/error through an elastic pipeline, with II=1 when unblocked.
Abort flushes unaccepted output; accepted outputs remain accounted for by the
consumer. This arithmetic pipeline is not the reference decoder or a CDC bridge.
