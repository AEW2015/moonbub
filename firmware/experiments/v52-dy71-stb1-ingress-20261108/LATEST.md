# V52 latest qualification —2026-11-08

The target build and production updater parser/package checks passed after the earlier source-stage README was written. Selected images are in `release-stb1-ingress-v001/`; `hashes.json` binds exact ELF/BIN/UF2. `preservation.json` binds the byte-identical source and selected host/target evidence copies. No target/runtime/hardware installation is claimed.

ELF SHA256: `285bc4953afd5c2dffc220bf512c33105642f18ed1f3ed4a1afa2080d7c48473`. UF2 SHA256: `06f568056eadcb4c7d1ed239d7c4fe767b5fc184b6008664bc9b32950f235464`.

See [the candidate index](../../../docs/cu66-v71/OVERNIGHT-CANDIDATES-20261108.md) for FPGA compatibility, static stack limitations, test scope and next hardware ladder. V53 is ABI2/V027; V52/V54/V55 explicitly require ABI3/STB1/V028. Passing a target build or host model does not establish physical throughput, stack low-water, network timing or allocator fragmentation.
