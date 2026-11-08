# V53 latest qualification —2026-11-08

The target build and production updater parser/package checks passed after the earlier source-stage README was written. Selected images are in `release-hbu-status-v001/`; `hashes.json` binds exact ELF/BIN/UF2. `preservation.json` binds the byte-identical source and selected host/target evidence copies. No target/runtime/hardware installation is claimed.

ELF SHA256: `023158630c563e3619394b6efd70ac88a39ccd785720c35a82f6af1931e2b734`. UF2 SHA256: `9701ad4c20d5a50896cfe45c0066f7d8e595b15c7c7e6add5949e5116e55c20a`.

See [the candidate index](../../../docs/cu66-v71/OVERNIGHT-CANDIDATES-20261108.md) for FPGA compatibility, static stack limitations, test scope and next hardware ladder. V53 is ABI2/V027; V52/V54/V55 explicitly require ABI3/STB1/V028. Passing a target build or host model does not establish physical throughput, stack low-water, network timing or allocator fragmentation.
