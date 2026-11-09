# V115 selected evidence status

Generated from selected receipts and completed routed reports. A component pass does not qualify the complete operational parent.

| Evidence | Selected status |
| --- | --- |
| Initial decoder/transport | [PASS_V115_SPATIAL_CANONICAL](../../experiments/python-gamebub-v115/spatial/results.json) |
| Initial peer faults | [PASS](../../experiments/python-gamebub-v115/control-peer/results.json) |
| Refined ingress | [PASS](../../experiments/python-gamebub-v115/refined/ingress/results.json) |
| Refined scratch | [PASS](../../experiments/python-gamebub-v115/refined/scratch/results.json) |
| Refined decoder/transport | [PASS_V115_REFINED_SPATIAL_CANONICAL](../../experiments/python-gamebub-v115/refined/spatial/results.json) |
| Refined peer faults | [PASS](../../experiments/python-gamebub-v115/refined/control-peer/results.json) |
| Actual QSPI/JPEG boundary | [PASS](../../experiments/python-gamebub-v115/jpeg-wire/results.json) |
| Initial-component C2/HUD/seal partition | [PASS_V115_SELECTED_COMPONENT_ACK_C2_HUD_ABSTRACT_PUBLICATION](../../experiments/python-gamebub-v115/live-parent/results.json) |
| Refined-component C2/HUD/seal partition | [PASS_V115_SELECTED_COMPONENT_ACK_C2_HUD_ABSTRACT_PUBLICATION](../../experiments/python-gamebub-v115/refined/live-parent/results.json) |
| Final request-bounds focus | [PASS](../../experiments/python-gamebub-v115/final/ingress/results.json) |
| Final owner-certificate focus | [PASS](../../experiments/python-gamebub-v115/owner-cut-focus/results.json) |
| Final decoder/transport | [PASS_V115_FINAL_SPATIAL_CANONICAL](../../experiments/python-gamebub-v115/final/spatial/results.json) |
| Final peer faults | [PASS](../../experiments/python-gamebub-v115/final/control-peer/results.json) |
| Final-component C2/HUD/seal partition | [PASS_V115_SELECTED_COMPONENT_ACK_C2_HUD_ABSTRACT_PUBLICATION](../../experiments/python-gamebub-v115/final/live-parent/results.json) |

| Composition | Clock | Setup WNS | Setup failures | Hold / pulse / routing errors | Internal OOC target |
| --- | ---: | ---: | ---: | --- | --- |
| initial-five-body | 125 MHz | -2.688 ns | 33790 | 0 / 0 / 0 | FAIL |
| initial-five-body | 100 MHz | -0.645 ns | 481 | 0 / 0 / 0 | FAIL |
| refined-header-tile-write | 125 MHz | -3.228 ns | 33633 | 0 / 0 / 0 | FAIL |
| refined-header-tile-write | 100 MHz | -0.777 ns | 1077 | 0 / 0 / 0 | FAIL |
| final | 125 MHz | -2.974 ns | 24606 | 0 / 0 / 0 | FAIL |
| final | 100 MHz | -0.263 ns | 3 | 0 / 0 / 0 | FAIL |

Final bounded keyframe validation: last required byte to validated abstract commit (125-MHz conversions remain conditional).

| Service profile | Actual cycles | Conditional time at125 MHz | Strict<10 ms |
| --- | ---: | ---: | --- |
| 0 | 3,062,014 | 24.496112 ms | FAIL |
| 1 | 5,732,576 | 45.860608 ms | FAIL |

One distinct keyframe fixture, two service profiles; not a sustained distinct-frame campaign.

Fresh positive repeat: 100 MHz = False, 125 MHz = False.

Complete parent timing/CDC/I/O and SDRAM/LCD integration, sustained hardware 30 fps, and validated full decoding below 10 ms remain open. See [cycle ledger](performance.md), [refined implementation](refined.md), [final cuts](final.md), [parent gaps](full-parent-gap.md), and [machine-readable results](../../experiments/python-gamebub-v115/results.json).
