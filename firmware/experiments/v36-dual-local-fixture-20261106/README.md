# V36 explicit local CU71 / DY71 fixture firmware

Development successor of sealed v35, not installed. `G` selects only CU71
magic43553731/cap7. New `Y` selects only DY71 magic44593731/cap15. Both require
ABI00010000, fresh typed owner/staging counters, real original HU/native decode,
all21120 HUD word writes/readbacks per frame and real COMMIT/presentation.
There is no profile autodetection, identity alias, new network transport or FPS
claim. Wrong profiles are refused before writes. The one-shot worker retains
accepted native cache and maintenance lease after completion/mutation exactly
as v35; confirmed paired reset/reconfiguration is required before reuse.

Native CPU W, JPEG/AV, settings/SD and default firmware features are retained.
The SDK/exception/PSRAM profile is unchanged. Shared G/Y worker stack12288bytes
and heap gate170000/largest24576 are unchanged. Target build, SRAM, source/image
review, real CSR integration and physical gates must finish before flashing.
