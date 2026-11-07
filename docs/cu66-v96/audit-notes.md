# V96 contract audit notes

This is a bounded contract audit for V96/E6, based on the active plan, the E6
experiment proposal, and the retained V91k/V91l RTL evidence. It is not a new
measurement or a promotion decision. V96 must charge actual addresses and
service, and must not infer hardware fit or speedup from a smaller request
count, a source-level map, or a standalone write replay.

## Geometry and address contract

The canonical image is planar 4:2:0: Y is 720×480 = 345,600 bytes; Cb and Cr
are each 360×240 = 86,400 bytes. Canonical storage totals 518,400 bytes. Each
plane divides evenly into 8×8 tiles: Y has 90×60 = 5,400 tiles, and each
chroma plane has 45×30 = 1,350 tiles. A tile contains exactly 64 bytes, so the
three planes contain 8,100 canonical tiles. There is no tile padding.

The full candidate writer also allocates 42,240 linear HUD bytes at offsets
518,400..560,639, for a 560,640-byte candidate extent. Do not conflate that
with the canonical-only 518,400-byte consumer/storage extent. The reference
tile reader is canonical-only and rejects HUD addresses.

For candidate video bank `b` (0..2), the physical x16 word address is
`(b << 22) | (byte_address >> 1)`. The bank field therefore selects 2^22
16-bit words, or an 8-MiB byte aperture per SDRAM bank. This is physical
capacity, not the software allocation: candidate logical byte offsets remain
bounded at 560,639. In global byte-address terms, bank `b` starts at `b<<23`.
Bank 3 is reserved for packed scratch; the current scratch service uses only
its first 262,144 bytes (word addresses `0xc00000..0xc1ffff`).

The candidate tile-major map changes only canonical-plane placement. It keeps
plane bases 0, 345,600 and 432,000; within a plane it lays out tile rows, then
tile columns, then row/column within the tile. HUD remains linear. The
addressing math must retain these plane boundaries and byte/word conventions.
The map is generated with literal plane widths and tile-row multipliers; this
source fact does not establish the synthesized divider/multiplier cost.

## Pixel modes and reuse limits

The current reconstruction modes have distinct meanings:

| Mode | Pixel prediction | Reference read | Current contract |
|---|---|---:|---|
| COPY (mode 0) | Copy the same-position tile from the accepted reference frame | Yes | Full zero-motion COPY only |
| Hidden CONST128 (mode 1) | Emit the fixed hidden value 128 | No | Hidden-mask rule; hidden residual coefficients are zero |
| RESIDUAL (mode 2) | Add signed residual to key prediction 128 or same-position accepted reference, then clamp to U8 | For delta tiles | Zero residual is still RESIDUAL mode |

Thus an all-zero residual is not a COPY command and is not a constant
sentinel. CONST128 is a fixed hidden-tile semantic; it is not a general
compressible constant-color mode. COPY avoids coefficient/IDCT work, but
materialized output still has to be written, hashed/validated, and later read
for display as required. The E6 dictionary may count exact 64-byte matches,
but a count alone neither creates a new wire mode nor proves an address alias.

The qualified reference lifecycle is a frame-to-frame lifecycle: snapshot the
accepted bank, fid and complete 64-bit publication generation at request
acceptance; read only that immutable accepted reference; write the candidate
to a bank with a provisional lease; hash/validate; drain all physical writes;
publish atomically; then make that commit eligible as a later frame's
reference. No same-frame dependency is qualified. Do not let candidate reads
observe a partially written current frame.

Materialization is the safe E6 default: read the source tile, copy its exact
64 bytes into the destination candidate bank, and keep ordinary destination
ownership and hash/display behavior. An alias would require explicit source
bank+generation+tile descriptors and lifetime/reference-count proof through
abort, retry, publication, held scanout, and reuse. Arbitrary cross-position
aliases do not fit the current three-slots-per-position reference model by
assumption. Do not add a cache or alias lifetime without charging descriptor
storage, lookup/read ports, tags/generations, invalidation, and conflict policy.

## Bank protection and transaction identity

The allocator and display overlap guard have distinct protected roles:

- **accepted/reference** is the last atomically committed source that delta
  reconstruction may read;
- **front** is the source currently presented;
- **pending** is a validated commit waiting for safe presentation;
- an active **display lease** snapshots source bank, fid, epoch and generation
  until RGB, reader/mux ownership, physical drain, and output acknowledgment
  have closed.

Allocation must keep every live role protected, even if two roles temporarily
name the same source. Candidate writes must be blocked against protected banks
and against a bank held by an active display lease. The existing isolated
overlap lease adds metadata/control, not payload RAM; it relies on the caller to
gate both physical request-valid and returned request-ready. Publication drain
must include the display lease and physical reader/mux drain, not just an
external vblank hint.

Outer reference requests carry epoch, fid and full 64-bit publication
generation. The V91l reference reader snapshots accepted bank/fid/generation,
checks exact identity and plane/tile bounds, and produces one 512-bit (64-byte)
tile response. It fetches that response as four aligned 16-byte requests. Each
physical request/response has the outer epoch, bank, address, and a separate
nonzero 32-bit monotonically advancing ticket; the ticket is not a truncated
publication generation. A response with the wrong identity does not retire
the owner. Cancel/reset suppresses new issue but drains an accepted line before
offering an error; a held offered reply is immutable. A lease cannot be
silently changed while reads are outstanding.

The reference/display mux grants per 16-byte transaction and retains ownership
through physical drain and a held logical response. The native overlap
allocator preserves accepted/front/pending banks while a display lease is
active. These identities and drains are functional contracts; they do not
make additional banks or payload storage appear for free.

## Measured service costs and experiment candidates

The retained V91l evidence gives useful comparison points, with narrow scopes:

- One reference tile is 4 aligned 16-byte reads, hence 4 BL8 read commands and
  32 returned x16 words. The V91l physical-reference delta workload adds
  31,224 BL8 reads / 249,792 x16 words. A COPY/read-elision claim must explain
  how this reference demand changes while preserving exact output.
- The unoptimized base RGB565 replay reads nine bytes per pixel, or 3,110,400
  acknowledged byte reads/frame. The qualified two-row chroma cache records
  518,400 acknowledged reads/frame; the aligned line reader records 32,400
  physical line requests/frame, each priced as eight x16 transfers plus
  response overhead. These are distinct conversion schedules; neither is a
  free display consumer for a new memory layout.
- The tiled candidate writer's matched replay has 70,080 logical eight-byte
  rows and 560,640 bytes/frame. Its standalone native write cycles are
  1,271,369 → 937,045 for key and 1,271,364 → 937,040 for delta, with ACT
  counts 42,441/42,450 → 1,786. This is 26.30% fewer write-replay cycles in
  that experiment, not a full-frame or shared-service speedup. The fixture
  replays decoded bytes; it does not include live reconstruction, display,
  complete validation, or hardware implementation.
- In native overlap, the matched serial/overlap ACTIVATE count changes
  28,571 → 47,459 with unchanged READ/WRITE counts; bank 0 accounts for
  18,000 additional activations without new unique rows. The bounded tile-grant
  follow-up lowers that case to 36,713 ACTIVATEs, but also changes credits up
  to 4:1 reference/display. It does not isolate locality. Compare balanced
  service, tile-grant, and per-line controls before assigning the gain to
  grouping.

Likely useful bounded experiments are (1) exact accepted-reference tile-match
counts and materialized COPY bytes, with measured avoided transform work and
added memory/hash/display service; (2) grouped/tile-major placement compared
against raster using identical clients and actual pin-level ACT/PRE/REF,
turnaround, refresh stalls, and full read/write/display completion; and (3)
scheduled CONST128 generation compared to explicit source bytes while charging
the generator and every write/hash/display consumer. Each should preserve
same-position accepted-reference semantics and include abort/replay and bank
reuse histories.

Likely negative or misleading experiments include treating zero-residual
RESIDUAL as COPY/CONST; using same-frame or arbitrary cross-position aliases
without descriptor/lifetime proof; reporting only request-count or ACT savings
without refresh, read/write turnaround and continuous display service; and
calling the tiled writer's standalone write replay a complete-frame latency or
physical-FPGA win. Constant generation may reduce source payload work, but
without actual generator cycles, destination writes, hashes and display reads
it is only a byte/work hypothesis.

## Promotion gates

For each V96 candidate, record the descriptor and payload format, generated
addresses, all source/destination banks and generation IDs, and ownership
through acceptance, cancellation, drain, retry, commit and display release.
Use an independent address inverse and byte/hash checks. Compare identical
source frames and exact pixels/root/seal. Count actual addressed reads/writes,
ACT/PRE/REF, x16 beats, idle/refresh waits, read/write turnarounds, arbitration
wait and outstanding/held occupancy. Include continuous raster reads and
report display completion/underruns, not just decoder-side work or memory-busy
fraction. Account for descriptor/generator logic, storage and map ports and
the candidate's source/reference/display service. An improvement in memory
busy time is necessary service evidence, not a full-path completion-time
saving. Simulation does not demonstrate BRAM/DSP/LUT fit, routed timing,
hardware 30 fps, or validated decode below 10 ms; keep each of those gates
explicitly open until measured in its proper environment.

## Standalone materializer and service-model audit

Read-only review of `fpga/experiments/cu66-v96-materialize/tile_materializer.sv`
and `tb_materialize.sv` found the address conversion consistent with the
retained mapping: a canonical tile-base byte address identifies one contiguous
64-byte tile in tile-major storage; `raster_row` maps each of its eight
8-byte rows back to the canonical raster row address expected by the frozen
writer; the writer then maps that row to physical tile-major words. For valid
Y/Cb/Cr tile bases (0..518,336), the plane boundary and 720/360-wide row math
are consistent. Physical reads use four 16-byte aligned offsets from the
captured tile base. The test seeds and checks actual timed-controller memory
words at tile-major addresses, exercises Y/Cb/Cr edges, and observes pin writes,
read words and refresh. This supports the addressed materialization case, not a
full-frame raster inverse or display proof.

The module holds a one-tile payload, snapshots source/destination bank and
full 64-bit IDs, exposes both banks in `lease_mask`, matches physical epoch,
ticket/token, bank and address before retiring a pending transaction, and
keeps the lease through a held completion. Warm reset/cancel stops new issue;
accepted reads/writes remain pending until a matching response drains. The
module does not roll back already acknowledged destination rows, so the caller
must retain the destination lease and prevent publication/reuse until the
completion contract is satisfied.
The testbench stalls the response path and checks every one of four source lines
and eight destination rows under reset/cancel, wrong epoch tags, held replies,
and a changed source identity sharing the original low 32 bits. It also checks
generator cycles for the configured RTL lane widths and exact pin-memory bytes.
Destination legality uses the supplied protected-bank mask and the captured
accepted-bank identity. A follow-up adds dynamic destination protection during
a pending source read and pending first/last destination writes: no further
offers issue, accepted work drains, invalid completion retains its lease and
retry succeeds after protection clears. This tests the component input mask;
it does not integrate the real front/pending/display allocator or cover every
possible phase interleaving. The selected final campaign passes 867 checks per
configuration, 2,601 total.

The testbench's `raster` seed helper mirrors the RTL `raster_row` arithmetic.
Direct physical peeks confirm exact tile bytes at selected plane-edge
locations, but there is no independent whole-bank dump/inverse or canonical
full-frame hash in this RTL campaign. Its timed metrics include the retained
reader/writer/controller/refresh service for these isolated tile transactions;
they omit descriptor parsing/search, live decoder/HUD/hash integration and a
continuous RGB/display client. Generator-cycle counts are for `GEN_LANES` 1 or
4, not evidence for a 16-byte RTL generator.

The Python `service-model/model.py` schedules a fixed hidden mask over a
complete canonical tile list. Its 32,400 baseline 16-byte lines/frame and
31,224 visible-memory lines/frame reflect 1,176 generated 16-byte lines
(294 hidden 64-byte tiles); 18,816 generated bytes are payload work, not saved
candidate write traffic. Generator clocks are 18,816/4,704/1,176 for 1/4/16
bytes per clock, respectively, and are not aggregate controller latency. It
checks assembled canonical tile parity and SHA, but the
scheduled line scan is not the RGB raster reader, controller arbitration, or
display cadence. Generator widths 1/4/16 are behavioral accounting choices;
the RTL supports only widths 1 and 4 in this checkpoint. The bank model is a
directed behavioral lifecycle oracle with one outstanding write in its
campaign, not an implementation/formal proof. V96 inventory verifies
canonical tiles only; it does not rerun the retained V95 packet or RGB565 root
outputs. Keep that verification boundary explicit.
