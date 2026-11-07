# V43 DY71 bounded bulk HUD candidate

V43 is paired with FPGA V025, not the installed V023. It keeps V42's original two-frame DYN1 lab transport and native C++ endpoint, and batches the actual HUD AUX writes and full readback into blocks of up to 256 16-bit words. It refuses V023 before writes. It is not a continuous encoder/video player or a 30 fps release.

The final candidate image is `release-bulk-hud-v002`: ELF `efd0a8650853f8d996dd22bfa4fb33d0d1b4da8678f453cb8304ac9579880fb9`, UF2 `476520418833411a5f712bda2193ec17ea2132cbced7804627cd494e564fd33c`. Earlier v001 packaging uses a superseded CSR map and must not be installed. The exact source snapshot is `evidence/source-snapshot-v002.json`; final packaging checks are in `evidence/package-v002`.

HBU1 status lives at CSR `0x600..0x618`; payload is `0x400..0x5fc`. The LD14 LCD observer is preserved. Required profile: DY71 magic `44593731`, ABI `00020000`, caps `1f`, HBU1 `48425531` / version `00010000`. Sequence, generation/frame/reference/bank/ticket, count and memory equality checks remain mandatory. No reset or image change is allowed under a retained owner.

Host test counts: local 18, network driver 15, native loopback 20, batch adapter 17, wire 6; total 76 passing. Target build, effective SDK SRAM guard and production UF2 parser pass. Static SRAM checks are not proof against every runtime stack/heap failure.

See `docs/cu66-v71/V43-BULK-HUD-DEVELOPMENT-20261107.md` at the repository root for executed FPGA simulation scope, the preserved inferred-RAM failure and the remaining implementation/hardware gates. Keep Windows stopped until exact app and FPGA identity, memory readiness and an explicit receiver START are confirmed. The unchanged uploader is `host/dy71-lab/dy71_fixture_sender.py` at `cbbd85fda` with original adjacent KEY/P fixtures and `--initial-wait-seconds 600`.
