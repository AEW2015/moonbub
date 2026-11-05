# First complete hardware fixture: CP23 baseline

Receiver target decision: **CP23 / HC22 / HD22**. Windows should retain its
tested CP23 baseline. The incompatible CP25 / GM25 / HD25 profile is not selected.
This is a development target, not an implemented or installed capability.

| Path | Decoder image | Local payload loader | Current scope |
| --- | --- | --- | --- |
| Complete CP23 / HC22 / HD22 | Does not exist yet | Does not exist yet | First complete-fixture target |
| Complete CP25 / GM25 / HD25 | Does not exist yet | Does not exist yet | Incompatible, not selected |
| Private AKD1 | Guarded-ROM BIT exists | v26 USB accessor starts its embedded ROM fixture only | Earlier AR03 / GM01 / CP02 KEY/hash diagnostic, pre-HUD |
| Retained build50 | Legacy JPEG/AV BIT exists | Existing legacy streaming path | MSV1/JPEG and AV; no CP23/CP25 support |

The CP23 Python reference is commit
`507ceb54c97e6a19b8bb21f5ab416dd3eb671e18` on
`study/gamebub-integrated-codec-v23-20261104`.
`experiments/python-game-hd22-joint-study/model.py` has SHA-256
`4aa1090904518483b2c621861067974c0626f47fbda7fac3140844c2243be665`.
These are reference/model artifacts, not an FPGA decoder image.

The incompatible CP25 reference is commit
`3d881382f022e95808f72cea2f2842a73343544f` on
`study/gamebub-motion-codec-v25-20261104`; its combined-motion model has SHA-256
`01056ea6d32b2986411e77f5e56ab3466639ae2799cbc93502bb217cc62fa8d6`.
Its existence does not switch the hardware target.

## Available diagnostic artifacts

- AKD1 BIT: `fpga/candidates/akd1-compute-rom-guard-20261104/bitgen/akd1-compute-rev4.1.bit`,
  SHA-256 `b1ca685e457446838b9d6c78b86f02c4b793dad42eccb3b5c50075d17e20e260`.
  Its manifest is `bfbd37e4b2899d68c815f45b07efcfc69d6a782ed08dbe791275c607b5d2cafb`.
  The fixture controller uses `$readmemh` on its fixed `fixture.hex`; it has no
  arbitrary CP23/CP25 payload loading path, P/HUD implementation or decoded LCD
  presentation. Native bars are independent of its computed samples.
- v26 app-only UF2:
  `firmware/experiments/v26-key-diag-access-20261104/release-key-resource/moonshine-rev4.uf2`,
  SHA-256 `80003d79887976d8a49889a0e0bcda2905cb58763ff21d720169c3a87432bc63`.
  USB `d/a/b/y` accesses only the restricted AKD1 job contract. This is a local
  diagnostic accessor, not a complete-profile payload loader.
- Retained build50 BIT: `fpga/candidates/v21-audio/build/moonshine-rev4.1.bit`,
  SHA-256 `a1ca6ce6b2c333a7c2ad4d29b94a7adf683dc49669d7f87fe3f80e63ef9ef3f9`.

**No custom network endpoint, port or capability has been allocated. Do not send
CP23 or CP25 packets to AKD1.** A separate installation log must establish the
current device image; this source audit cannot establish installed identity.

## Next coordinated gate

Freeze one complete CP23 fixture and its expected outputs with Windows. Bind the
pair parser, exact HC22/HD22 HUD behavior, candidate/reference ownership,
validation/publication, ACK and recovery semantics to that reference. Implement
an explicit local fixture loader and matching complete decoder before scheduling
the first complete-profile hardware trial. Preserve the earlier private compute
and memory experiments as component evidence; they do not close this gate.
