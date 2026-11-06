# Actual v36 local fixture on prospective v005 components

New isolated numeric CSR wrapper and proof; prior PIPE, SYNCsafe/math, split CSR
and constraint-audit artifacts remain unchanged.

Explicit component selection:

- System manifest `validpipe-v003/sources.json`, SHA
  `8644b08e1aabda1254f28f30c11f2906e01dcb10d40770e0c07da33034939e7f`.
- Prospective board selection `syncsafe-math-v002/board-source-v005/selection.json`,
  SHA `84cc0f1e93f03f870207c68df2c33aac6a4a7a3cee8da87deab7900ec69daf76`.
- Actual DY71 safe CSR `dy71_local_control_safe.sv`, SHA
  `ef270c048922ab872de7eba15c26cba5b6e22dcc561d7a5b9101faab16cf4139`.
- Actual safe stager `cu71_packet_staging_safe.sv`, SHA
  `c45e3537db50ccbe2d1164fe72b00c81553d945305bf980d3eede32dc9f6d10b`.

The system module name remains `cu71_system_direct_syncsafe`; its actual selected
base pipeline now instantiates `cu71_idct_validpipe`. This has one additional
work cycle per accepted tile. The wrapper replaces the actual CSR and stager
implementations without changing scalar register offsets, explicit DY71 identity
or v36 firmware/native HU sources. `bus_read_address` remains tied to the numeric
CSR address. Physical QSPI/CDC behavior is a separate gate.

The scripts verify the selected manifests, child IDCT and safe-stager evidence,
and completed whole-system KEY/P/P proof before compiling. The control suite
uses real owner/stager/arbiter/SDRAM behavior and fabricates no native ACK. The
subsequent frozen v36 Rust/native C++ HU gate must independently complete KEY/P,
all 42,240 HUD writes and actual word-for-word readbacks, PREPARE and COMMIT.

Ideal clocks, eight virtual clocks per CSR access and the 30-second laboratory
watchdog remain correctness settings. Native CPU work does not advance HDL time.
No target CPU latency, physical SPI/PLL/board behavior, routed timing or 30 fps
claim follows from this simulation.

Host native allocator counters are retained for reproducibility. They do not
measure ESP32 heap fragmentation, stack headroom or target allocator layout;
those require target build analysis and physical runtime evidence.


## Completed native integration

Actual frozen v36/native KEY and P completed: accepted/presented 2/2, rejected and
LCD underruns 0; all 42,240 HUD words written and independently read back through
actual SDRAM/CSR responses. Actual native PREPARE/COMMIT completed.
Virtual RTL elapsed 583945 us and 787090 scalar RPC calls are not ESP32 performance.
The completed result and exact source/model/binary bindings are retained in
`evidence/v36-native01`; qualification-v001.json records the explicit selected
SYNCsafe/validpipe plus safe control/stager binding. No hardware or physical timing gate
is added by this functional proof.
