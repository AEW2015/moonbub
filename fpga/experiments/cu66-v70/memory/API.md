# V70 memory interface (implementation in progress)

`cu70_memory_system` uses one memory clock `clk`, a pad-sampling `read_clk`, synchronous `rst`; `abort_i` cancels only canonical tile work and drains it. `aux_abort_i` cancels only the aux transaction. Reset requires the caller to reset/flush all clients together. All addresses are **x16 word** addresses.

Canonical read request: `read_valid`, `read_ready`, `read_generation[63:0]`, `read_bank[1:0]`, `read_plane[1:0]`, `read_index[16:0]`.
Read response held until consumed: `read_rsp_valid`, `read_rsp_ready`, `read_rsp_generation[63:0]`, `read_rsp_bank[1:0]`, `read_rsp_plane[1:0]`, `read_rsp_index[16:0]`, `read_rsp_pixels[511:0]`, `read_rsp_error`.
Canonical write request: `write_valid`, `write_ready`, `write_generation[63:0]`, `write_bank[1:0]`, `write_plane[1:0]`, `write_index[16:0]`, `write_pixels[511:0]`.
Write completion (held until ready): `write_done_valid`, `write_done_ready`, `write_done_generation[63:0]`, `write_done_bank[1:0]`, `write_done_plane[1:0]`, `write_done_index[16:0]`, `write_done_error`.

One canonical tile request is outstanding, read/write RR arbitration. Pixel i is bits8*i+:8; each pair is little-endian x16, canonical planar row-major storage. No golden reference source exists in this component. `tile_busy` stays set until accepted controller transactions drain, including after abort. `tile_aborted` pulses after abort drain; no successful response is exposed for an aborted partial tile. Faulted full requests report error with matching identity. Completion marks actual controller recovery completed, not queue acceptance.

Aux request: `aux_req_valid`, `aux_req_ready`, `aux_req_write`, `aux_req_addr[23:0]`, `aux_req_data[15:0]`. One outstanding scalar word request. Response `aux_rsp_valid`, `aux_rsp_ready`, `aux_rsp_data[15:0]`, `aux_rsp_error` holds until consumed for **both reads and writes**. Write response is controller recovery completion, never queue acceptance. Internal per-client alignedBL8 read caches reduce sequential read traffic; aliasing writes invalidate both cache copies. `aux_busy` until response or abort drain; `aux_aborted` pulses on drain. Illegal/unallocated word addresses return one error response and issue no controller command.

At the lower controller boundary, requests have valid/ready, write, address24, data16; reads return eight valid16-bit response beats. A wrapper derives write completion only after the conservative controller has returned idle following the accepted operation. Controller is existing readBL8/write-single logic with REFRESH_CYCLES=750 default. No queued write is acknowledged early. Memory grants are nonpreemptive only per BL8 read/single write; RR canonical/aux grants permit scanout/painter use without whole-tile monopolization.

Read/write responses hold stable while stalled. Abort may withdraw an unaccepted response/request, but accepted controller operations still drain. The root bank owner must keep all candidate/reference allocations leased until tile_busy=0 and all other clients are idle.

The combined simulation module will instantiate a checked 32MiB command-level model. This is functional/command timing evidence, not pad timing, vendor model or electrical signoff. Production fpga/rtl files are unchanged.

Integration abort note: aborting this adapter suppresses the canceled tile/aux response after accepted operations drain. An upstream engine that expects a normal response to drain must either let this adapter finish normally while aborting the engine, or coordinate an explicit cancel/flush acknowledgment. Do not blindly assert both abort inputs and wait for a canceled response.
