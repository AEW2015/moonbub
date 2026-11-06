# Bounded aligned 128-bit reads behind the chroma cache

The frozen converter still requests 518,400 individual canonical bytes. An
adapter holds three separate 16-byte lines, one for Y, Cb and Cr. It aligns
physical read addresses to 16 bytes and retains plane tails while another plane
is consumed. Thus each canonical line is fetched once: 21,600 Y lines, 5,400 Cb
and 5,400 Cr, totaling 32,400 accepted 128-bit requests and 518,400 payload bytes.
The local hit count is 486,000 and the miss count is 32,400 per frame. Three line
slots add 48 logical payload bytes, plus byte response and control/tag registers.

Game Bub's documented external SDRAM bus is x16, not 128 bits:
[official interface reference](https://docs.gamebub.net/developing-cores/reference-interfaces/).
This experiment treats 128 bits as a gathered logical response over eight x16
payload beats. FAST prices eight data edges plus one registered response edge
per line ACK (nine edges after acceptance); SLOW prices the same eight data
edges and one through five response/stall edges (nine through thirteen).
The frozen byte-service control prices one x16 beat plus one through five
response/stall edges (FAST two; SLOW two through six). No command-accurate
SDRAM CAS, row-open, refresh or concurrent display model is implied. The local
100-MHz controller and one-chip mapping remain the separate frozen board scope.

Only one physical request and one inner byte lease can be outstanding. Cached
hits produce a registered one-edge byte response. Misses first accept a physical
line request, await its matching tagged response, then return the selected byte.
Physical responses populate a line slot only while its frame is active and
valid. Slots are invalidated on start/reset/cancel/fault, without bulk reset of
payload registers. All source/output bytes must match the existing exact
RGB565 contract and independently retained diagnostic vectors.

Cancellation can acknowledge/discard the inner byte lease while the physical
read still drains. New frames cannot start until both owners are released.
Wrong physical epoch fails the active frame but cannot release the genuine
pending physical read. A matching bus-error response retires that physical
request and fails the byte lease. A one-shot cancel retires the frozen core's
pending byte request; sticky adapter errors cannot prevent a clean later retry.

The wrapper reports adapter errors in 0x80|code: 1=physical epoch mismatch,
2=matching bus error, 3=zero start epoch, 4=invalid byte address/epoch. The frozen
core's own error remains visible when there is no adapter error. Complete `done`
waits for core completion and adapter frame-lease closure; all final closure
cycles are included in the measured fence.

The unchanged byte converter and line adapter are measured on the same captured
V91k canonical inputs and separate nonuniform edge fixture. FAST isolates a
fixed service rule. SLOW consumes seeded randomness differently after scheduling
changes; no identical absolute stall trace is claimed. Physical read count,
payload bytes, x16 beats, byte hit/miss count, pixel identities, request/ACK
ownership and recovery are checked. This is candidate-memory replay, not the
monolithic decode/HUD/content-validation/publication/display system.
