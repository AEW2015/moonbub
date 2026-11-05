# V40 first-key CS37 cap probe

This bounded probe takes the **first archived frame** from each of the four
PTS-selected v40 clips, constructs actual lossless HU25 → HX32 → HX33 HUD
packets, and feeds the selected HX33 bytes to the frozen integrated v38 sender
with fast analysis v37. The independent implicit-v37 receiver decodes each
complete CS37 key packet and validates the exact HUD and displayed output.

| Source clip; frame PTS | ROI 8 / background | Complete bytes | HUD bytes | Base bytes | Fast analysis ms | Integrated encode ms | Active MSE |
|---|---:|---:|---:|---:|---:|---:|---:|
| mass-effect-10000; 72000 × 1/11952 (500/83 s) | 16 | 27,690 | 12,407 | 15,203 | 5.490 | 44.615 | 17.71257 |
| mass-effect-10000; 72000 × 1/11952 (500/83 s) | 32 | 23,568 | 12,407 | 11,081 | 5.490 | 36.350 | 27.54330 |
| mass-effect-4500; 72000 × 1/11952 (500/83 s) | 16 | 38,355 | 14,357 | 23,918 | 5.501 | 50.418 | 27.96809 |
| mass-effect-4500; 72000 × 1/11952 (500/83 s) | 32 | 31,854 | 14,357 | 17,417 | 5.501 | 43.685 | 41.63480 |
| mass-effect-1600; 72000 × 1/11952 (500/83 s) | 16 | 13,658 | 899 | 12,679 | 5.402 | 38.932 | 11.51753 |
| mass-effect-1600; 72000 × 1/11952 (500/83 s) | 32 | 9,213 | 899 | 8,234 | 5.402 | 33.514 | 21.30647 |
| mass-effect-combat; 500 × 1/25 (20 s) | 16 | 43,354 | 16,694 | 26,580 | 5.533 | 54.410 | 26.19019 |
| mass-effect-combat; 500 × 1/25 (20 s) | 32 | 35,624 | 16,694 | 18,850 | 5.533 | 45.682 | 39.80453 |

All eight actual complete packets fit the 49,152-byte CS37 cap. The largest is
43,354 bytes, leaving 5,798 bytes. The identical key HUD packet is charged in
both background configurations for each source frame. Base bytes are complete
bytes minus the 80-byte outer wrapper and actual HX33 HUD bytes. All decoded
HUDs contain the original 21,120 RGB565 words exactly; table quality is active
area MSE against the archived source RGB565 after adding that exact HUD.

The timing scope is one fast analysis and one integrated sender call per source
frame. Analysis is reported separately; integrated encode time includes the
prepared CS37 sender work, and excludes source/HUD preparation, archive I/O,
receiver, score calculation, transport and display. These are single key-frame
probes, not paired timing campaigns or a full-window sequence. They do not show
that P frames or every frame in the 457-frame archive fits the cap, establish
physical 30 fps, or compare against HEVC/AV1. The source clips have prior project
use; this is not a project-wide unseen-data claim.

The compressed packet objects and source canvas objects are content addressed.
`results.json` records RGB/YUV/RGB565 and external media hashes, exact PTS and
time base, per-stage HUD packet lengths, complete/base/HUD budgets, timings,
quality, receiver tags, and source-code SHA-256 pins. `verify.py` independently
replays all eight complete packets and checks source pins, hashes, exact HUD
pixels, cap arithmetic, normalized references and active MSE.

Reproduce in the project study environment:

```sh
python prepare.py > prepare.log 2>&1
python verify.py > verify.log 2>&1
```
