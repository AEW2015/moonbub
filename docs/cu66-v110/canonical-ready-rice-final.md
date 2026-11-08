# V110 READY + Rice full canonical audit

The selected actual full canonical run passed both V109 FETCH seeds. Its exact 18-source RTL closure (17 SystemVerilog files and one header) contains seven replacements: Rice, busy scratch, inverse fault, dequant, READY producer, reconstruction fault, and top-level fault handling. The 30-file source manifest, current inputs, selected attempt snapshot, and all 38 retained artifacts match their pinned hashes. The five focused receipts (busy, fault, dequant, READY, Rice) are all actual PASS and each receipt hash matches the source manifest used for this run.

Each seed passed 22 canonical cases and 21 directed checks: 44 newly executed case profiles and 42 directed checks total. Candidate canonical gzip files match V109 byte-for-byte and after decompression; events and simulation/stdout JSONL hashes also match for both seeds. The V109 FETCH actual RTL baseline was reused and not recompiled or rerun. The selected receipt hash is `7b3494c516182df3dd1fb4c64e5749814ab43906914e9a4dc0f2d3424a51132a`.

This establishes exact RTL canonical behavior for this candidate, not native timing or hardware performance. Machine-readable audit: [`canonical-ready-rice-final.json`](../../experiments/python-gamebub-v110/audit/canonical-ready-rice-final.json).
