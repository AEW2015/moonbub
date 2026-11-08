# V55 latest qualification —2026-11-08

The target build and production updater parser/package checks passed after the earlier source-stage README was written. Selected images are in `release-stb1-performance-v001/`; `hashes.json` binds exact ELF/BIN/UF2. `preservation.json` binds the byte-identical source and selected host/target evidence copies. No target/runtime/hardware installation is claimed.

ELF SHA256: `ef005e82d795b3ea1bdb6248901b821a7b5e78ad753de5fe0b6d2766a663976b`. UF2 SHA256: `5278b95b1ac8b73454c5f0f76771beac606ecdd135ebeca1a0a6395601b0d28d`.

See [the candidate index](../../../docs/cu66-v71/OVERNIGHT-CANDIDATES-20261108.md) for FPGA compatibility, static stack limitations, test scope and next hardware ladder. V53 is ABI2/V027; V52/V54/V55 explicitly require ABI3/STB1/V028. Passing a target build or host model does not establish physical throughput, stack low-water, network timing or allocator fragmentation.
