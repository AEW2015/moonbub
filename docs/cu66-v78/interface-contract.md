# V78 decoder/direct-scanout integration contract

Keep all V69–V77 sources/evidence frozen. New receiver and scanout production
components live in V78, reusing the qualified V77 bounded cache/converter and
frozen V74 memory/V72 SDRAM/V70 LCD line buffers. Do not fake a painter success
response to bypass validation: remove the RGB-copy transaction stage explicitly.

## Receiver `cu78_receiver`

Fork the V70 receiver, preserving packet/ref/write/HUD/software/start/diagnostic
ports and their handshakes. Remove the painter and RGB-slot interfaces entirely.
Add output `validated_ready` (sticky while that transaction is validated and
committing, identity given by active_generation/frame_id). Direct presentation:

```
output presentation_valid; input presentation_ready
output [63:0] presentation_generation
output [31:0] presentation_frame_id; output [1:0] presentation_bank
input vblank,scanout_drained
input [63:0] presented_generation; input [31:0] presented_frame_id
input [1:0] presented_bank
output front_valid; output [1:0] front_bank
output [63:0] front_generation; output [31:0] front_frame_id
```

Keep actual canonical/HUD validation and all physical write/HUD drains before
validated-ready and commit. Keep irreversible canonical/reference commit,
processor idempotent COMMIT acknowledgment retry, abort fences and stale identity
checks. Presentation descriptors are globally committed; latch their bank at
commit. The existing three-bank controller must retain reference, front and
pending leases. A front bank is retired only on exact matching presentation ID,
generation and bank plus old-front drain at a qualified boundary. Display work
on a committed front must not be treated as a candidate operation to abort.

A pending descriptor may coexist with decoding into the third free bank. Never
reuse front/reference/pending storage merely because the local cache finishes a
raster. `memory_drained` covers decoder/ref/HUD adapters and accepted operations;
it excludes independent scanout work that holds its separate front/pending lease.

## Scanout `cu78_direct_scanout`

```
input mem_clk,mem_rst,pixel_clk,pixel_reset_n
input descriptor_valid; output descriptor_ready
input [63:0] descriptor_generation; input [31:0] descriptor_frame_id
input [1:0] descriptor_bank
output presented,error
output front_valid; output [1:0] front_bank
output [63:0] front_generation; output [31:0] front_frame_id
output pending_valid; output [31:0] presented_count
output frame_boundary,scanout_drained
output mem_req_valid; input mem_req_ready; output [23:0] mem_req_addr
input mem_rsp_valid; output mem_rsp_ready; input [15:0] mem_rsp_data
input mem_rsp_last,mem_rsp_error
output [31:0] underruns,memory_errors
output hsync,vsync,data_enable; output [9:0] physical_x,physical_y
output [7:0] red,green,blue
output [31:0] cache_read_commands,cache_read_words,cache_pixel_queries,raster_count
```

Use the V77 bounded cache + elastic converter and frozen `cu70_lcd_lines` native
line buffers. Accept one committed pending descriptor and reject stale metadata
without publication. Only switch the externally visible front at a qualified
native frame boundary after old accepted source reads, queries, converted line
work and cache epoch drain. `scanout_drained` means the old front's work retired;
new pending-source prefill need not be mistaken for an old-front read.

The cache is a per-raster epoch. Refill/repeat the same immutable front for each
native refresh without counting that refresh as a new source. It may prepare a
committed pending source after all old source lines have been converted/drained,
while the existing line buffers finish scanning their old pixels. Keep visible
front identity unchanged until vblank. If a late descriptor cannot safely replace
an already prepared repeat epoch, retain it for the next safe raster; do not drop
it or relabel old pixels as the new source. Counters and later deadline tests must
expose any resulting delay.

Native line requests are ordered physical rows 40..759. An explicit expected-line
counter can avoid reversing a wide `line*480` address with a variable divider;
check the held request address and epoch, and stream exactly 480 converted pixels
per accepted line. Release a cache strip after its final converted line has
entered the output line buffer and the pixel pipeline is drained. Bound cache
prefetch to three live strips and account for initial preroll. Protect output
line tokens across the existing pixel/memory clocks.

Keep exact RGB and source generation through the final active pixel. Memory or
cache errors must be visible; do not silently classify black lines as correct.
Any whole-system recovery not actually implemented/tested remains an explicit
open gate. Continuous positive scanout and safe committed-source switching are
required in the V78 replay, without per-source resets or reseeding.

## Integration evidence

Root will feed actual compressed native fixture packets through the FPGA receiver,
write real HUD data through the guarded wide transfer/readback interface, and
check actual RTL-produced canonical memory, tags and native output against an
independent native oracle. No predecoded canonical seeding or golden reference
injection is allowed in that full-system proof. Record immutable packet release,
actual admission, validated-ready, canonical commit/processor ACK, presented ID
and complete correct rasters separately. Count distinct source IDs separately
from repeats. Keep performance FAIL independent from functional PASS.
