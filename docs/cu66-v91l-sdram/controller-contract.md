# CU66 v91L SDRAM bridge model contract

This note describes a bounded abstract model of the existing SDRAM controller
and the proposed eight-byte row bridge. The model is protocol and source-FSM
evidence only. It is not an RTL proof, pin-level simulation, timing-closure
result, or performance claim. Regenerate the machine-readable evidence with
`python3 experiments/python-gamebub-v91l-sdram/model.py`.

## Frozen controller interface

`fpga/rtl/moonshine_sdram.sv` accepts a 24-bit **word address** and 16-bit
request data. It has `request_valid/request_ready`; ready is true only in
`IDLE` while `refresh_count < REFRESH_CYCLES`. It returns read data through
`response_valid/response_data`. There is no write acknowledgement, write error,
or byte mask. The mode register value `13'h233` configures BL8 reads and
single-word writes. A read enters `READ_WAIT` with delay 5 and then presents
eight response beats. A write issues one word and waits with
`wait_cycles(3,IDLE)`. Refresh can take priority in `IDLE` at the 750-cycle
counter threshold.

The bounded controller model follows these source states, command placements,
and wait transitions. In its cold same-row write probe, first acceptance is
followed by ACTIVATE and a 10-edge interval to the next accepted write; later
open-row hits are 6 edges apart. The interval includes source FSM wait edges,
not elapsed time in the complete system.

## Eight-byte row mapping and ownership

One logical row request contains an eight-byte-aligned byte offset, 64-bit row
data, candidate bank 0..2, and epoch/token tags. It maps to four ordered x16 word
writes:

```text
controller_word = (candidate_bank << 22) | (byte_addr >> 1) | word_index
word_index = 0, 1, 2, 3
candidate_bank = 0, 1, or 2 (bank 3 is reserved)
```

The controller decodes bank from word-address bits `[23:22]`, row from
`[21:9]`, and column from `[8:0]`. The mapping is enumerated literally in the
results. Each controller bank has an 8 MiB word-address aperture, with only
the bottom 560640 byte offsets populated; three candidates use 1,681,920 bytes
within 24 MiB of reserved apertures. For example, candidate bank 1, byte
offset 0 maps to controller word 4194304, bank 1, row 0, column 0. The earlier
packed formula `(logical_bank*560640 + byte_addr)/2` was rejected because it
put every logical range in controller bank 0.

The bridge model allows one logical owner. For each physical write, the owner
waits for controller acceptance and then observes the controller become idle
before retiring that physical word. A warm cancel retains its epoch, token, and
logical eight-byte lease until the already accepted word drains. It then stops
issuing the remaining row words and holds a cancellation completion until the
caller accepts it. Do not alter accepted data or front metadata while physical
ownership is outstanding. A cold power reset requires external quiescence;
resetting while a physical word is accepted is illegal. These are abstract
protocol obligations, not properties proven in RTL by this model.

The physical controller exposes no write completion or error. Any wrapper ACK
or cancellation error is an abstract bridge protocol signal and must not be
described as a controller signal.

## Byte-control read-modify-write policy

A separate byte-write policy requires an actual BL8 read: collect all eight
16-bit response words, replace the selected byte in its containing 16-bit
word, and issue exactly one x16 write. This preserves the adjacent byte in
that word and the other bytes in the burst. The policy is represented by a
data-level model case, not claimed as part of the row-only bridge
implementation. The row path itself writes four x16 words from one packed
eight-byte row; it is a distinct operation.

## Limits

The model keeps controller response values and SDRAM contents abstract. It
does not model electrical behavior, the special read-clock phase, FPGA I/O
cells, reset recovery at pins, or system arbitration. Its bounded checks show
only that the model's stated request, command, wait, mapping, cancellation,
and neighbor-byte rules are internally consistent with selected source
fragments. They do not establish hardware correctness, throughput, or measured
concurrent bank service.
