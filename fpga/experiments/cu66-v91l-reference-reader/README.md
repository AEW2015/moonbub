# V91l accepted physical reference reads

`reference_tile_reader` converts the reconstruction core's reference request into
four aligned, sequential 16-byte reads. The accepted publication lease supplies
bank, frame ID (including zero), and the complete 64-bit generation. A legal
request must match both publication IDs exactly, have a nonzero epoch/generation,
and name Y tile 0..5399 or Cb/Cr tile 0..1349. The physical byte bases are 0,
345600, and 432000, plus tile*64. Bytes are assembled little endian in one 512-bit
response register: **64 bytes of additional payload storage**, with no cache.

Outer request IDs and bank are snapshotted on request acceptance. Physical
`mem_req_generation` is a separate nonzero 32-bit monotonically advancing ticket,
not any part of the publication generation. Epoch, ticket, bank, and address
must all match before an accepted physical read can retire. A wrong reply is
ignored with ready low and the owner retained; a later matching reply can retire
it. Tickets wrap from 0xffffffff to 1 only after a matching acknowledgment.

Reset/cancel suppress new acceptance and physical commands, and drain any
accepted physical line before returning an outer error. An offered outer reply
is immutable until acknowledged, even through reset/cancel or publication lease
changes. Error payload bytes are not meaningful and may contain a completed
prefix. `power_on_reset` is cold initialization only, with assertions excluding
owned work; the reset/cancel ports are the supported in-flight controls.

`reader_client_mux` arbitrates display (owner 1) and reference (owner 2) once
per 16B transaction, round robin between eligible clients. Ownership lasts
through downstream acceptance, physical drain, held reply, and downstream busy
release. An accepted gate prevents duplicate acceptance during reply release.
Only the current owner's reset/cancel reaches the physical reader. Ungranted
client cancellation cannot affect an owned transaction. Reply identity is
validated before routing and acknowledgment.

`reference_shared_timed` preserves every old `shared_sdram_timed` port and adds
the reference endpoint, accepted lease, status, captured `ref_source_bank`, and
`ref_line_*` telemetry. Its old `rd_*` request/reply pins are the display client;
old `rd_busy` and physical counters still describe the shared physical bridge.
The frozen shared service, controller, and timed pin model are instantiated
unchanged. Their original JSON receipts remain in the transcript. New timestamped
JSON receipts identify reference outer offers/ACKs, physical line requests/ACKs,
and client mux arbitration, ownership, requests, and replies.

Run `python3 scripts/cu66-v91l-reference-reader/run.py`. The runner snapshots all
sources and hashes into unique immutable attempt directories, including failures,
and builds inside `gamebub-cu66-v69-build` with Verilator 5.020, timing/assertions,
strict `-Wall`, C++20 `-Wall -Wextra -Werror`, and two build jobs. Unit simulation
has a 2ms watchdog; actual-pin simulations have 5ms watchdogs and test tAC 2ns
and 7ns with the frozen #2.75 read phase / 4ns flight model. Physical test data
is seeded by explicit logical writer transactions, never memory backdoor preload.

The abstract reader test injects wrong epoch/ticket/bank/address responses and
tests all planes at both tile edges, valid fid0, high64 generation and unequal
high32/equal low32 rejection, invalid bounds/IDs, held responses and lease changes,
and reset/cancel before acceptance, before line acceptance, and during each of
the four reads. The pin test independently computes seeded bytes and checks
line/outer responses, contention, held display replies with ungranted reference
cancellation, and cancellation/reset during each physical line. Verdicts are
simulation evidence only; no fit, hardware, or 30fps claim follows.
