# DY71 local CSR profile and CPU HUD compatibility

This is an explicit local diagnostic profile, not a network protocol or a rate
capability. Require **44593731 / 00010000 / 0000000f** at CSR000/004/008 before
any write. The new `dy71_local_control` retains all84ports and every control
statement of frozen `cu71_local_control`; only the module name, magic and
capability literal differ. ABI1 remains unchanged. Original CU71 firmware must
continue rejecting this identity; the v36caller selects `Profile::Dy71`
explicitly. There is no identity alias or automatic fallback.

The existing local ABI commands, sequence/idempotence rules, immutable staging
limit49,152bytes, four-byte packet reads and complete-error statuses remain.
The capability bits denote staging, CU66owner, typed HUD and the explicitly
versioned direct-YUV/cache-context profile. They do not advertise UDP or30fps.

| Location | Meaning, preserved for the CPU |
|---|---|
| CSR200 /204 | Owner diagnostic byte-address selector / actual diagnostic value |
| Owner01c /020 | Accepted/reference frame ID / displayed front frame ID |
| Owner098 /09c /0a0 /0a4 | Accepted tag words, low32tohigh32 |
| CSR300..328 | Ticketed HUD generation/frame/reference, original HU span, leased bank/key and expected tag |
| CSR31c..328 | Expected HUD tag words, high32tolow32; distinct from owner-tag word order |
| CSR330..344 | Actual software COMMIT/ABORT request snapshot |
| CSR350 | Busy bit0, complete stage bits8:1, error code bits16:9 |
| CSR354 /358 /35c /360 | Accepted / presented / rejected / underrun counters |

Fresh accepted/front IDs are **ffffffff**, as the unchanged bank controller
specifies; freshness uses ownership/counters/generation, not an assumed FID0.
After completion, compare01c/020 with the actual packet FID. The nested owner
diagnostic000 still contains its inherited43553730 identifier. That nested
diagnostic is not the local CSR profile identity; use CSR000/004/008 and the
system's actual profile outputs.

The old `front_rgb_slot` concept is now a **cache-context bit**, exposed as
`front_cache_slot`. It is not a physical RGB surface address. The direct owner
retains canonical/HUD leases and reads tile-major canonical storage into its
cache context for direct YUV output. CPU HUD code treats canonical physical
mapping as opaque. It uploads original CU66packet bytes and services only the
leased linear21,120-word HUD window. HUD bank bases and word offsets are
unchanged; the FPGA still enforces exact identity and contiguous completed
writes. No CPU-side tile-major reordering or RGB write is appropriate.

CPU semantic service is unchanged: actual native PREPARE, all21,120completed
HUD_WRITE operations, actual HUD_READ responses compared word-for-word to
native READ_CANDIDATE chunks, then verified drain and actual native COMMIT/ABORT
results. Ingress/command acknowledgments are not substitute semantic success.
Ambiguous post-mutation failures retain ownership and require reconciliation.

The wrapper sets the30-second owner watchdog only for scalar correctness
bring-up. It does not disable the watchdog or establish throughput. Its actual
PIPE owner and grouped memory backend come from the frozen three-frame proof.
The checked SDRAM pin model is copied byte-for-byte from that proof, including
its disclosed1ps Verilator monitor compatibility. The simulation supplies ideal
100MHz/read274.5°/panel clocks; power-up is shortened to20cycles as in component
tests. Physical SPI/QSPI CDC, vendor PLLs, jitter, FreeRTOS locking, target CPU
time and board electrical behavior are not modeled.
