# Independent STB1 source review ? 2026-11-08

Conclusion: no blocking functional defect found in the reviewed ABI3/STB1 RTL for the selected DEPTH=256, exclusive single-owner protocol. This is permission to continue isolated verification, not hardware or full-system qualification. Sources and exact inspected evidence are pinned in bindings.json. Author is extending full-depth/max-packet coverage; append a separate binding when complete.

## Reviewed behavior

- The FIFO has a synchronous unconditional RAM read. Empty-to-nonempty and each pop insert a fetched bubble, so the consumer never uses a newly addressed RAM word before its clocked read completes. Pointer advancement is on native upload acceptance, not on valid alone. A push/pop pair keeps occupancy unchanged. Full rejects a concurrent new push conservatively even if a pop occurs that edge; the 256-word descriptor reservation makes that safe for the selected legal transfer.
- Each stored word carries its own 1?4-byte count. A partial word is admitted only for the packet's final descriptor; native staging, byte count and CRC remain authoritative. FENCE requires both no queued words and native written_bytes equal accepted bytes, covering the native staging module's byte-at-a-time drain after FIFO pop.
- Generation must be nonzero and match the staged packet. Descriptor offsets match the committed prefix, are aligned, are bounded by the 33-bit end sum and packet length, and tickets strictly increase. Alias offsets must match received bytes within the descriptor. Stale/skipped/extra writes latch fault; previously accepted words still drain. A generation mismatch blocks further FIFO delivery and latches fault.
- Reset clears pointer/count/fetched/control metadata, not bulk RAM. Old contents cannot become valid in the new epoch. Transport fault prohibits new alias acceptance and setup but deliberately drains already accepted same-generation words. Fault is reset-only; CLEAR_FAULT does not release burst quarantine. This is a retained-endpoint contract, not live recovery.
- Existing scalar writes pass through only when no burst is armed/queued and no burst fault is latched. A scalar/burst collision faults rather than interleaving data. The pin suite checks one legacy word followed by burst descriptors; it does not establish complete old-ABI behavioral equivalence. ABI and capability advertisement explicitly change to 3/0x3f, so old clients must not silently accept it.
- Register reads are live and sequential, not atomic. The corrected driver ignores all later data beats when the first flags beat was busy, confirms ready flags and then rechecks generation/ticket. Under the required exclusive owner, no next descriptor is issued during the snapshot, so a ready observation remains stable. Concurrent owners/reset are not a supported transactional snapshot mechanism. The directed pin transition explicitly has first flags busy and later prefix/CRC ready.
- Selected QSPI endpoint and CDC sources are unchanged from V027. The eight dummy-byte read contract is retained. Pin tests vary clock phase and QSPI/core rates; nominal 100 MHz core / 16 MHz QSPI is included. This checks digital protocol timing only, not metastability, analog setup/hold or routed constraints.

## Evidence inspected

- All seven reference copies hash-match both source-bindings.json and their exact selected V027 input files. The included memory-map hash matches. All nine pins06 freeze entries and three unit04 entries match current sources.
- pins06: eight cases passed, including delayed core, varied phases, forced CDC overflow/quarantine, real native staging RAM reads with request/response backpressure, partial tail and sequential-read completion crossing.
- unit04: seven cases passed with actual native staging and byte/CRC scoreboard: randomized stalls; stale generation; skipped alias; full small FIFO overflow with accepted prefix drain; reset; scalar collision; transport-fault drain.
- Nominal pin-test staging of 1,031 bytes took 173,900 ns in this synthetic owner, payload transactions 130,900 ns, two fence polls total 10,400 ns. These are simulation timings only and are not a measured MCU/QSPI/decoder frame rate.
- Earlier failed evidence remains retained. pins01?05 must not be presented as the final passing suite.

## Follow-up gates and limitations

1. Before synthesis promotion, add default DEPTH256 full/pointer-wrap coverage and a maximum 49,152-byte multi-descriptor pin transfer; current full test uses DEPTH8 and current pin packet is only 1,031 bytes. Test RTL partial tails 1 and 2 as well as 3, stale/replayed ticket, setup-while-blocked and seal-while-queued rejection.
2. DEPTH is effectively restricted to powers of two no greater than 256: pointer wrap assumes power-of-two, queued status is only 9 bits, and the alias aperture supports 256 words. The selected value satisfies this; add an elaboration guard or narrow the advertised parameter before making this reusable IP.
3. Full decoder/SDRAM/HUD coexistence, real firmware driver integration, target constraints/CDC report, inferred BRAM mode and full routed setup/hold closure remain untested. Actual transport fault is inherited across selected CDC boundaries; no new physical CDC proof is supplied by RTL simulation.
4. Credit is a whole-empty reservation, not continuously available FIFO space. The driver must issue one bounded descriptor, then wait for final native fence before reusing aliases or attempting seal/start. A partially sent descriptor faults/quarantines or remains blocked; no automatic retry/reset is qualified.

Review was read-only except this separate report/bindings folder. No Vivado, device enumeration, programming, reset or hardware run was performed.
