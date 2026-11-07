# V91l packed scratch address and payload model

This standalone model pins the packed-scratch source contract and checks it
against the current scratch bridge/controller wiring. It does not qualify a
physical FPGA implementation.

## Address and storage contract

`packed_scratch_v91g2.sv` exposes an 18-bit byte address and 128-bit data
interface. Its request assertion requires 16-byte alignment and that the full
line end no later than `used_bytes`; allocation rejects layouts over 262,144
bytes. This model additionally requires a nonzero request epoch as a strict
interface contract. The model enforces the source's block limit (1–8192)
and per-block band-count limits (5/15/43) before allocating coded storage.
The bridge implements
`physical_word_address = (3 << 22) | (byte_address >> 1)`. The first line maps
to bank 3 word offset 0; the last valid aligned line starts at byte address
`0x3fff0` and maps to bank 3 word offset `0x1fff8`. The scratch aperture uses
131,072 x16 words (256 KiB) at the start of physical SDRAM bank 3. The
controller decodes four banks of 4,194,304 x16 words (8 MiB) each; video uses
banks 0, 1, and 2. The bank index proves that the scratch aperture cannot alias
video storage. This is an external address partition, not an on-chip RAM
allocation.

The transfer width is 128 bits = 16 bytes = eight x16 words. The actual
`moonshine_sdram` controller uses single-word writes and BL8 reads, so a full
line WRITE takes **eight controller WRITE commands** and a full line READ takes
**one BL8 READ command**. The final aligned line starts at word address
`0xc1fff8` and its last inclusive word is `0xc1ffff`. This is payload and
command accounting; activate/precharge, turnaround, refresh, arbitration, and
drain costs are not estimated.

The RTL lays out the coded header at byte offsets 0 and 16, then aligned DC and
three AC regions. `coded_layout()` mirrors its `aligned()` and `plan_*`
expressions. RAW starts its payload at byte 32 and reserves 128 bytes per block.
The 128-bit assembler in the RTL is a single transfer staging register. It is
not evidence that the full 262,144-byte scratch aperture is implemented as
on-chip SRAM.

## Historical control evidence boundary

The selected source is
`fpga/experiments/cu66-v91l-reference-live/tb_reference_live.cpp`; its
reference-live result manifest states `scratch_rtl: false` and
`scratch_service_rtl: false`. The archived live event stream contains transform,
canonical, and reference-tile events, but no packed-scratch request/response
records. Therefore native scratch request totals are unavailable and are
recorded as `null` in `model-results.json`. Counts from reference reads or
candidate writes are not substituted for scratch counts.
This null applies only to that retained finite-scratch control. The new
`cu66-v91l-scratch-live` campaign observes scratch requests and responses
directly; its measured per-frame counts and independent pin replay are in
`summary.json` and `docs/cu66-v91l-scratch-service/results.md`. This address
model does not substitute estimates for those measurements.

The required source and campaign context is in
`docs/cu66-v91l-reference-reader/README.md`: it reports reference-reader
traffic and expressly excludes scratch traffic from those totals. Its next-work
section identified moving packed scratch onto the shared controller as
the next work at that historical checkpoint. `fpga/experiments/cu66-v91g2/README.md` and its retained
`pipeline-attempts/*/vectors.jsonl.gz` / `results.json` cover the scratch
component contract, not the native reference-live physical scratch service.

## Reproduce

Run `python3 experiments/python-gamebub-v91l-scratch-service/scratch_model.py`
to refresh the deterministic result, or add `--check` to compare against the
checked-in `model-results.json`. The result records SHA-256 hashes of this
model, the three reviewed RTL modules, and the shared SDRAM controller and pin
model. The executable checks the address boundaries,
bank separation, rejection of zero epoch/misaligned/out-of-range lines, and
little-endian assembly of all 16 transfer bytes.

This is a source-derived address and payload model. It makes no measured
scratch request count, simulator-cycle estimate, latency, throughput, or
performance-gain claim.
