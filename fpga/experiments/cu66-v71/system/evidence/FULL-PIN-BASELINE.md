# Actual-controller v71 KEY/P baseline

Source-bound run: `full-pin02`; separate verdicts: `full-pin02-cadence.json`.
This is the old-storage hierarchy before the new BRAM-oriented RTL work.

**Full reconstruction/readback passes; clean scanout cadence fails.**

The normal build, bounded control process and chronological KEY/P process all
exited zero. Each frame's complete 518,400 canonical bytes, 384,000 portrait
RGB565 words and 21,120 HUD functional readback words matched. The dependent
P frame retried a deliberately lost irreversible COMMIT acknowledgment and
retained consistent accepted processor/FPGA state.

| Modeled transaction | Memory clocks | Time at modeled100MHz | Painter clocks | LCD underruns during transaction | ACT / PRE |
|---|---:|---:|---:|---:|---:|
| KEY0 | 13,609,626 | 136.09626ms | 11,238,092 | 0 | 118,791 /119,273 |
| P1 with concurrent scanout | 32,112,310 | 321.12310ms | 23,877,598 | 9,123 | 593,080 /570,449 |

Final accounting after the additional drain/scanout tail contains 9,124
underruns, 9,278 exact lines and 9,124 whole-black replacement lines. The
pixel checker permits whole-black replacement lines to distinguish safe
underrun behavior from mixed/corrupted lines; those lines still fail cadence.
Descriptor ACKs and two matching stored buffers are not clean physical frames.

Each transaction launched 3,759,360 physical SDRAM write beats:

- RGB: 384,000 scalar writes ×8maskedBL8 beats =3,072,000 beats.
- Canonical: 8,100 tiles ×8four-wordrows ×8beats =518,400 beats.
- HUD: 21,120 scalar writes ×8beats =168,960 beats.

This is physical bus work including masked beats, not useful payload bytes.
Canonical row bursts reduced that client's request overhead, but scalar
RGB/HUD APIs remain expensive. Combining future scalar requests would require
changing acknowledgment/fence semantics; an explicit burst-capable producer
interface is the safer next integration boundary.

The large P-frame ACT/PRE increase also motivates isolating same-bank RGB
contention. Both RGB slots occupy physical SDRAM bank3. Earlier clean LCD
component stress used concurrent canonical/HUD traffic in other banks, so it
did not establish clean service during writes to the other RGB slot. A
separate controlled test must establish that cause before selecting arbitration
or memory-map changes.

The two system transactions are not directly comparable with archived v70
throughput measurements: the controller, masks, phase/model and arbitration
differ. Preserve both baselines. No achieved device clock, target fit, live
QSPI/ESP32 CPU time, network path, physical playback or30fps is established.
See `SIMULATION-SCOPE.md` for model and host-harness compatibility limits.
