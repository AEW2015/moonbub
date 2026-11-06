# Explicit SYNCsafe/math + split DY71 CSR integration

This is a new simulation binding. It preserves the sealed original PIPE/grouped
CSR wrapper and evidence, the split component qualification, and frozen v36
firmware/native endpoint without editing them.

The selected system is `direct-system/syncsafe-math-v002/sources.json`, top
`cu71_system_direct_syncsafe`, manifest SHA
`8451653672247a3bad012c3bb90b0d76fdee4802768b5964d6a0a0bf61783b9f`.
Its actual SYNCsafe LCD owner, staged inverse math and grouped physical memory
backend are compiled from that manifest. The actual typed control is
`../dy71_local_control_split.sv`, SHA
`84757d07c3de49aa4c4bba49130b9b86a4d88e26f84f660e618ef989d0d7d716`.
The model is byte-identical to the prior qualified grouped SDRAM pin model.

The numeric CSR adapter drives `bus_read_address=bus_address`; this intentionally
does not instantiate the physical bridge or QSPI endpoint. The separate paired
bridge/QSPI suite proves the unchanged protocol's exercised behavior. This test
must not be described as a physical SPI or mailbox CDC timing measurement.

`evidence/control01` passes the same 83 actual staging/owner/abort/HUD/SDRAM
checks. It does not post invented native semantic results or software ACKs; its
final post-HUD abort remains held pending a real native ABORT response.
`evidence/v36-native01` is the separate actual frozen v36 Rust/native C++ HU
KEY/P algorithm gate. Only its completed result may establish native PREPARE,
all 42,240 completed HUD writes and word-for-word readbacks, and actual COMMIT
success for this specific binding.

Ideal clock generation, 8 virtual clocks per CSR call and the explicit 30-second
laboratory owner watchdog are retained. Native CPU work does not advance RTL
clocks. Neither virtual elapsed time nor zero native-CPU virtual timings measure
ESP32 performance. No target SPI, vendor PLL, FreeRTOS concurrency, physical
board timing, hardware or 30 fps qualification is provided.


## Completed native integration

Actual frozen v36/native KEY and P completed: accepted/presented 2/2, rejected and
LCD underruns 0; all 42,240 HUD words written and independently read back through
actual SDRAM/CSR responses. Actual native PREPARE/COMMIT completed.
Virtual RTL elapsed 583945 us and 787090 scalar RPC calls are not ESP32 performance.
The completed result and exact source/model/binary bindings are retained in
`evidence/v36-native01`; qualification-v001.json records the explicit selected
SYNCsafe/math plus split-control binding. No hardware or physical timing gate
is added by this functional proof.
