# V54 latest qualification —2026-11-08

The target build and production updater parser/package checks passed after the earlier source-stage README was written. Selected images are in `release-stb1-failure-diag-v001/`; `hashes.json` binds exact ELF/BIN/UF2. `preservation.json` binds the byte-identical source and selected host/target evidence copies. No target/runtime/hardware installation is claimed.

ELF SHA256: `c7506ed07f791338fce41f2903e75081d4c7cef58b6bde6f7bae52aa6b1f19a6`. UF2 SHA256: `1f3bd4ce4a8221b57da3ac82acdbee6c5eddddb1adc66e101a8cc0e4c494fa6f`.

See [the candidate index](../../../docs/cu66-v71/OVERNIGHT-CANDIDATES-20261108.md) for FPGA compatibility, static stack limitations, test scope and next hardware ladder. V53 is ABI2/V027; V52/V54/V55 explicitly require ABI3/STB1/V028. Passing a target build or host model does not establish physical throughput, stack low-water, network timing or allocator fragmentation.
