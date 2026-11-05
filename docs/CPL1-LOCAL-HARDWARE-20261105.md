# CPL1 local hardware test — 2026-11-05

**Result: FAIL_RENDERED_CRC. Custom network testing remains blocked.**
Programming and the read-only observer worked. Two fresh physical snapshots
reported successful decode/tag verification and matching counts, but the rendered
canvas CRC was `dec6d87d`, versus the frozen oracle `4c5725e5`.

## Exact installation and recovery

The application-only v32 observer was installed over USB UF2. Its installed
runtime ELF identity matched
`5bbb988144eeee7fcd96fb442573171f25912168fa94586a6a6fb2ce36e3e8fd`.
The UF2 SHA-256 is
`13c27ca9a919dd7d40b7ff7aa4d55e5d97e00ad79e596d5aeee732966e9c3d4d`.

The selected CPL1 BIT SHA-256 is
`e11a193a8cfe51b90053c852bdbb3d9308225bc1d115564418a64e016d6df789`.
Volatile JTAG programming completed at approximately 20:06 UTC, with DONE=1,
USERCODE=`c2310001`, USR_ACCESS=`43505231`. The serial-numbered reserved
adapter and a single XC7A100T were checked before programming.

After preserving the failed results, **build50 was restored through volatile
JTAG at 20:25:56 UTC**. DONE=1, USERCODE=`b0100004`,
USR_ACCESS=`4d424f50` were verified. Restored BIT SHA-256:
`a1ca6ce6b2c333a7c2ad4d29b94a7adf683dc49669d7f87fe3f80e63ef9ef3f9`.
The recovery camera shows color bars. V32 remains installed; no network session
was started. This is not a network-ready announcement.

No persistent FPGA flash, SD files or settings were written. Exact retained
v30 rollback artifacts were copied before installation; these are retained
release files, not a readback of the previous installed application.

## Physical observations

| Field | Snapshot 1 | Snapshot 2 |
|---|---:|---:|
| Capture cookie / generation | 1 / 1 | 2 / 2 |
| ROM bytes | 17,412 | 17,412 |
| Canonical bytes | 518,400 | 518,400 |
| HUD words | 21,120 | 21,120 |
| Pad write beats launched / transpose words | 259,200 / 259,200 | 259,200 / 259,200 |
| Completed canvas words | 345,600 | 345,600 |
| Canvas sequence | 7,426 | 21,856 |
| Rendered CRC-32 | `dec6d87d` | `dec6d87d` |
| LCD underruns / lost bridge writes / coordinate errors | 0 / 0 / 0 | 0 / 0 / 0 |

Both snapshots had checked result stage/code 0/0, matching base tag
`b74b12e10009cfccbcb5363d13edc4ee` and HUD tag
`1026aab8b7df606614f560a966806641`. No quarantine was reported.
The repeated scanout counter advanced; this is one fixed fixture and does not
measure unique-frame throughput. Launch counts do not prove SDRAM write contents.

The camera showed a held colored-band image with four HUD rectangles. Visual
presence is not pixel-exact validation. No reboot or panic was observed during
the window. A post-snapshot runtime sample reported 177,200 free heap bytes,
90,112 largest allocation and 2,756 bytes USB-task stack headroom; these are
scenario observations, not a proof against every possible stack overflow.

## Failure localization and next experiment

An independent offline YUV-to-RGB reconstruction exactly matches the frozen
golden pixels and CRC. Advancing each eight-word golden memory burst by one
word, duplicating its final word, produces **exactly `dec6d87d`**. Simple byte,
channel, axis and image shifts did not reproduce that CRC.

An isolated exact-controller simulation also exposes timing sensitivity:
with model tAC=2 ns, clock-flight assumptions of 1–4 ns pass the burst test;
0–0.5 ns fail its first read beat (`1001` instead of `1000`). The qualified
functional model assumed 4 ns clock flight. These are model parameters, not
measurements of this board.

Together these give a concrete burst-alignment lead. They do **not** distinguish
physical write corruption from read-capture alignment, nor prove the external
timing values. No clock-phase or data-offset fix has been selected or loaded.

Next, create an isolated SDRAM diagnostic with known per-beat patterns and
bounded raw write/read-return observation. Reproduce the alignment signature
across timing assumptions, then measure/qualify a correction with exact readback
and the unchanged rendered oracle. Preserve the current frozen source and
timing evidence; any new image needs its own simulation and routed checks.
Only after the fixture CRC passes should a versioned network receiver be added
and coordinated with Sunshine. CAPS=0 currently provides no custom network port.

## Evidence

Local evidence is retained under
`evidence/hardware-cpl1-timing-20261105T195529Z/`: app/image bindings,
program/recovery logs, runtime identity, two complete paged snapshots, independent
oracle comparison, burst signature analysis and model-sensitivity results.
Selected structured results accompany this report under
`evidence/cpl1-local-hardware-public-20261105/`.
Camera footage, full device-property dumps and private raw recordings remain
local. Host/parser results, digital simulation and physical observations are
separate evidence classes.
