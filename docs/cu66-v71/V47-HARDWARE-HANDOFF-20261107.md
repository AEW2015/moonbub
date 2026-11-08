# V47 hardware handoff: bounded allocation-order experiment

V47 is ready for a controlled CPU12/network cached12 comparison. It is not installed or physically qualified. The current V46 endpoint remains retained after its frame3 allocation failure.

Selected release: `firmware/experiments/v47-dy71-hud-order-20261107/release-hud-order-v001`.

- ELF SHA-256: `592b8607c039e0d7d55c3eec046deef829ca464ade2ebe839cea55e70d859779`.
- UF2 SHA-256: `0cc70fdb4ba5347b469cd9a5ec9570401f125369d224d4671ee4213866861f25`.
- Static SRAM132,060bytes, guard163,840. Effective SDK checked. Production DFU parser verified13,681blocks and application-only round trip.
- Exact target build completed with no source changes.77Rust host checks, actual-native first12goldens/253,440words, allocator negatives and late-component rollback tests passed.
- Broader457-frame semantic corpus passed at a1MiB cap; peak100,888 exceeds the target cap, so this is not target-fit evidence for that whole corpus.
- First12 allocation-model peak88,974 versus V46's92,544. Independent review found no correctness blocker.

The [change plan](V47-HUD-ORDER-PLAN-20261107.md) keeps canonical outputs, prediction references and tags while constructing larger patch outputs first. Cap/reserve, sequence-v3, V027 and commit/abort authority remain unchanged. The [real bounded TLSF comparison](V47-FRAGMENTATION-RESULT-20261107.md) qualifies60synthetic schedules:57both fail,2improve to complete12,1both pass. One candidate fails earlier among cases where both fail. This is not a universal fragmentation cure or a replay of the exact target heap. Invalid exploratory configurations are preserved and excluded.

Next physical trial:

1. Windows stopped; physical app-only USB update clears V46's failed lease. Verify exact V47 ELF/reset identity.
2. Run CPU-only USB `I` once before Wi-Fi or custom FPGA programming. Require12goldens/no normal allocator failures and measured stack/heap.
3. Re-load unchanged V027 BIT `9922aa617c21a03e8a31f932d45e22d905e91d4e263ef593692898d363d07dee`, DONE1/USERCODE4459373f, after ownership/memory/LCD checks.
4. Coordinate the same pinned `a52caa395` sequence-v3/count12 Windows uploader. Obtain its session/source line before arming `@` once. Original12packets only; no JPEG, audio, AV, long stream or automatic retry.
5. Preserve both complete checksummed exports and matching Windows presentation/failure results. A failure retains/quarantines the endpoint. Hardware success must be recorded separately; it cannot be inferred from this handoff.

Evidence index: candidate `evidence/readiness-v001/readiness.json`. Native function stack-usage output is retained, but full target stack safety still needs measured runtime evidence. No new FPGA implementation or V47 full-system RTL replay was performed; exact native HUD goldens and unchanged V027 qualification are distinct evidence. Formal handoff tool unavailable; manual hash/source gates used.
