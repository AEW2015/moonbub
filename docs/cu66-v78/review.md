# Independent integration review

A separate scanout agent reviewed `cu78_system.sv`, `tb_system.cpp` and
`run_system.py` read-only after the two-frame paced and four-frame fixed-arrival
passes. It found no blocking functional defect in that demonstrated positive
path. The review is scoped to source inspection and retained simulation results,
not exhaustive RTL verification or hardware qualification.

The reviewer confirmed actual FPGA parser/base/hash writes, the real command-
level SDRAM model, full canonical plane/tag verification, HUD transfer/readback,
qualified presentation ACK, and at least one exact native raster per requested
source. Expected planes and reference pixels are confined to the oracle.

The following findings remain explicit in the handoff:

1. The serial 30-fps threshold ends at processor COMMIT ACK. It is not a display
   latency or sustained-cadence result. In the four-source run, first complete-
   raster latency reaches 58.68038 ms and the first source raster-start interval
   is 61.46706 ms. `analyze_system.py` reports those separate boundaries.
2. Fatal scanout/cache recovery is open. The scanout latches diagnostic stop;
   parent LCD errors are separate from receiver abort/error. Bad-candidate
   reference/front retention is a narrower, separately tested property.
3. Error monitoring should retain sticky observations during release/readiness
   waits and the final display drain, with full-raster progress deadlines. The
   current bench continuously checks native pixels and transaction errors, but
   it does not independently record every late diagnostic pulse in those waits.
4. The producer's queue estimate is sampled before its `start_ready` wait. It
   can under-report growth under future slower service. Primary latency retains
   admission-minus-original-release queue time; queue-capacity proof is open.
5. The model omits live ESP32 transport and target CPU HUD/control cost. Assumed
   clocks and finite samples do not prove hardware throughput or max-under-10-ms
   validation. Target fit, timing and CDC remain separate gates.

The directed fault extension subsequently checks a CRC reject, a physical
canonical-write abort, exact old-front rasters and an accepted retry with lost
COMMIT ACK. It does not close the fatal-display recovery finding.
