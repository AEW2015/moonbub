# CU71 original-map tile-address microsteps

Integration module: `cu71_tile_memory_address_pipe`, same public ports as frozen
`memory/cu71_tile_memory.sv`. No PHY, controller, canonical/RGB map or wire/CSR
profile changes are selected. In particular this is not the DY71 tile-major map.

The measured implementation03 path starts at upstream command-state logic and
ends at the old tile_base DSP cascade:22levels,9CARRY4s and−9.606ns slack. The
original adapter computes selected-index division/modulo90or45 plus row-stride,
plane and bank additions on its acceptance edge.

The successor captures operation, generation, bank, plane, index and512pixels
first. Six bounded compare/subtract steps compute row/column for valid tile
indices. Subsequent registers separate row scaling, bank/plane addition and
column addition. A registered word cursor advances by1 within read rows, by
pitch−3 between read rows, or by pitch between write rows. The public request
address has no per-word multiply or division path.

Valid tile setup adds10clocks before the first word request. At100MHz that is
100ns per tile, or0.81ms for one full8,100-tile surface pass; combined read/write
passes can add1.62ms. These are protocol-cycle budgets, not measured frame time.
Invalid metadata retains its immediate error-result path. All response identity,
read pixel order, write masks and one-operation arbitration semantics remain.
Abort at every new address state emits no memory request; an already accepted
word remains owned until its actual response drains, as before.

`scripts/cu66-v71/tile-address/run.py` supports isolated `unit`, `pins`, `synth`
runs into a new unique output directory. Pin regressions derive the parent
memory wrapper by changing only the tile-module instance type; all actual SDR2
controller, bridge, primitive and checked-model sources are frozen unchanged.
Fast and slow model tuples remain the qualified original profile. The unit
test compares all canonical tile locations and physical word contents against
the old adapter and an independently written row-major address formula, then
exercises invalid metadata, every new abort/reset phase, accepted-word abort
drain, every error response position and simultaneous arbitration.

The exact-device synthesized OOC diagnostic uses `xc7a100tcsg324-1`,100MHz and
the same1nsmax/0nsmin IO budget as prior leaf diagnostics. Observed setup WNS
is+3.223ns/TNS0;1,431LUTs,752FFs,2DSPs. Worst setup is now word-index to burst
data output, three LUT levels. Unplaced hold WHS−0.274ns is not closed; Vivado
warns HD.CLK_SRC is unset. Full-board setup/hold, placement and routing remain
required. No clocks or external timing budgets were relaxed. No hardware is
programmed by this work.

## Executed qualification

`qualification.json` binds the frozen source and four completed runs. The
prelaunch-frozen unit repeat passed48,660checked operations:48,600full-tile
write/read operations covering every valid bank/plane/index,14invalid-metadata
cases,40backend error ordinals and6simultaneous arbitration operations. It also
passed92cancellations:52abort/reset address-phase cases and40accepted-word
abort/drain positions. Both peer word-addressed memories match over all777,600
canonical words. Accepted requests were checked independently against the
original row-major address formula, payloads and burst masks.

Separate fast and slow checked SDRAM pin-model suites each passed5,168checks,
235tile operations and42aborts using the unchanged actual controller. These
prove selected physical memory contents/masks/drain and concurrent clients;
they do not extend the full unit memory sweep into an electrical hardware claim.
Component suite clocks increased from124,922to127,444. The candidate is a timing
pipeline tradeoff, not evidence of higher displayed FPS. Full-board integration
and routed setup/hold remain outstanding.
