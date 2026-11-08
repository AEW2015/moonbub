# V51 probe cost and new-source CU66 progress

V48/V027 remains the physical reference: twelve presentations and 253,440 verified HUD words in 21.923482 seconds. Software reboot passed. Software DFU currently needs a separate Windows driver binding; no vendor-client flash write has occurred. The following results are offline, not new physical playback results.

## V51: preserve reserve checks, remove unintended heap walks

The existing free-memory callback calls a helper that queries both total free memory and the largest free block, then uses only the free result. Inspection of the exact V48 ELF confirms both calls survived compilation. In the actual ESP-IDF source, total free size uses cached per-heap counts; the largest-block query walks allocated and free blocks under heap locks.

The physical twelve-frame run recorded 2,260 native allocations. Its two free samples per successful allocation imply 4,520 unnecessary largest-block queries on that path. This is a call-count finding; their elapsed cost and share of the 21.92-second run are unmeasured.

V51 splits the callbacks. Every pre-allocation reserve check, post-allocation free sample and minimum-free update remains. Failure diagnostics still query the largest block. Initial admission and final health still query both. The native allocator/decoder, 98,304-byte arena, 8,192-byte reserve, worker stacks, wire contract and V027 are unchanged.

Source: `firmware/experiments/v51-dy71-free-probe-20261108`.

- ELF: `83799f1197eaf8b1aedd449313204a356e509f277c4459e7ab5a96d6a69eaa82`.
- UF2: `c02da2dc55520fb6a156b6882fb38ce0c852b5b5aec2ec1a23eed114058de80b`.
- Target build, 104 Rust host tests, native golden/rollback checks, four source-extracted callback tests, production UF2 parser and static SRAM guard pass. Static SRAM is 132,076 bytes.
- Independent inspection of the new ELF confirms one intended IDF call in each callback. Native sources are byte-identical to V48; only the expected Rust callback/helper code differs.
- Runtime stack, heap fragmentation, elapsed time and display cadence remain unmeasured. This candidate is not installed.

After driver/read-only backup qualification, V51 is a useful first same-fixture comparison. Test V50 READ slicing and V49 Huffman changes separately before combining changes; preserve V48 as the control.

## New source frames can now be encoded offline

The [preserved bridge experiment](../../experiments/cu66-source-bridge-20261108/REPORT.md) produces new CU66 packets from prepared RGB frames, rather than merely exporting old packets. It composes the retained causal encoder, arithmetic coefficient encoder and canonical CU66 wrapper, with independent Python and native decoding checks.

The selected package contains twelve distinct frames from the local `motion-test.mp4`, scaled to 720×405 in a black 720×480 canvas at (0,37). It covers about 0.367 seconds of source motion. It is not the original two-minute Mass Effect clip, which was not located on this PC.

All twelve complete canonical/HUD/display hashes pass the exact native-v69 decoder. The exact V48 HUD endpoint passes 253,440 word comparisons at its original arena cap, peaking at 95,053 bytes with zero allocation failures. Native fault/rollback/recovery checks pass. These host results do not establish physical SRAM fragmentation or target stack headroom.

Packets range from 10,091 to 18,757 bytes. The KEY0 → P1 … P11 chain and adjacent manifest pass the unchanged sequence-v3 loader. [The manifest](../../experiments/cu66-source-bridge-20261108/package12/manifest.json) records every packet/source/output hash and the source preparation. Seventy-eight imported Python dependencies and the exact prepared source array are preserved; a replay from the dependency snapshot reproduces the synthetic control KEY hash. No sockets were opened or packets transmitted.

This is a research offline encoder and a short correctness package. Live capture/encoding, two-minute custom streaming and 30 unique displayed frames per second remain unqualified.

## FPGA work

An isolated STB1 prototype batches compressed ingress through a 1 KiB alias aperture, with explicit generation/ticket/prefix/CRC fences. It changes the ABI and must be rejected by V48–V51. Initial pin-level tests include the selected QSPI endpoint, CDC and native staging RAM; an independent review requested full default-FIFO and maximum-packet coverage before synthesis. Selected-source simulation, full-system behavior, implementation timing and hardware qualification remain separate gates. V027 has not been changed or reprogrammed for this work.
