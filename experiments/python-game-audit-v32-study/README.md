# V32 independent Python codec audit

This audit independently checks all six causal cohorts (two 48-frame scenes × `band_control`, `shrink_strict`, and `shrink_budget`), every retained packet and candidate attempt, each cohort's own accepted-reference chain, source-pixel replay bindings, and the strict-control baseline. It recomputes sampled HEVC/AV1 comparisons with the same per-frame HU32 byte vector and 60-byte binding used for custom base accounting.

## Audited result

The audit verified 288 accepted frames, 1,504 attempts, 6,082,560 exact HUD words, 3,023 archived objects, 96 exact full-packet/ACK matches to v30's strict baseline, and 288 deep replay rows. All accepted CP27 packets fit the 49,152-byte cap. The replay is pinned to the exact results and verifier source and reports pixel reconstruction, candidate guards, and work replayed.

The three cohorts preserve separate causal histories. Per-frame strict or 1% RGB error guards are measured against each frame's v30 strict winner. Those local guards do not guarantee a better aggregate MSE across a complete cohort: the complex-scene strict cohort is slightly worse globally than its control because the policies build different references over time.

The HU32 component reduces the 96-frame sidecar from 310,961 to 310,685 bytes for the primary window and from 623,615 to 562,316 bytes for the complex window. Applying each actual HU32 frame size plus 60 bytes to both custom base and sampled native operating points yields these ranges across the three cohorts:

| Window | Custom MSE | Custom complete bytes | Lowest-byte sampled AV1 point meeting MSE and cap | Lowest-byte sampled HEVC point meeting MSE and cap |
| --- | ---: | ---: | --- | --- |
| Primary | 14.3854–14.3958 | 551,764–552,343 | q48, MSE 12.2482, 333,570 bytes | q32, MSE 11.2109, 349,857 bytes |
| Complex | 26.3039–26.5020 | 1,164,275–1,168,835 | q38, MSE 19.7675, 701,183 bytes | q28, MSE 22.1619, 706,328 bytes |

At these sampled points, HEVC and AV1 use about 36.6–40.0% fewer complete bytes than the corresponding custom case while meeting or beating its mean MSE. Every selected point fits the per-frame cap after adding HU32 and 60 bytes. This is a sampled operating-point comparison, not a matched-quality curve or a native endpoint result.

The existing v32 CP27 packets still carry HU25. The comparison accounts for the independently replayed HU32 component prospectively alongside each base; an HX32/CP32 combined full receiver is not implemented. The audit therefore does not claim that these prospective totals have been transmitted by an integrated custom endpoint. It also makes no native ESP32, RF, display, or physical 30-fps claim.

## Reproduce

From the repository root:

```sh
/home/lori/gamebub-streaming-prototype/.venv/bin/python -m unittest discover -s experiments/python-game-audit-v32-study -v
/home/lori/gamebub-streaming-prototype/.venv/bin/python experiments/python-game-audit-v32-study/audit.py
/home/lori/gamebub-streaming-prototype/.venv/bin/python experiments/python-game-audit-v32-study/audit.py --check
```

`audit.json` records sorted repository-relative SHA-256 pins, the full sampled standard points, and the exact accounting. It omits its own hash to avoid a self-reference.
