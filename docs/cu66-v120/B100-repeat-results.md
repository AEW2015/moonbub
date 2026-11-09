# V120 B100: fresh repeat verified

The initial and independent fresh-repeat implementations both pass **100-MHz internal OOC timing** with identical reported margins: +0.174-ns setup, +0.028-ns hold and +3.750-ns pulse-width slack. Both have zero failing setup, hold and pulse-width endpoints and zero routing errors.

The repeat terminal audit passed **359 checks**. It independently parsed the raw clock waveform, all 12 timing-summary fields, complete `check_timing` counts, route-net counts and worst path, then compared them with the sealed receipt. Source/current/snapshot pins, proof pins, tools, core recipes, initial lineage and distinct fresh build/log were verified.

Evidence:

- Initial: `experiments/python-gamebub-v120/repair-study/native/20261109T205145534717Z/receipt.json`
- Fresh repeat: `experiments/python-gamebub-v120/repair-study/native/20261109T211623143358Z/receipt.json`
- Independent audit: `experiments/python-gamebub-v120/audit/B100-repeat-terminal.json`
- Audit SHA-256: `c8b04ebdc468c6e6f179e1d64287f28efb22148ee2f8827efe5f378640ce6fd5`

All 18 selected source files are byte-identical between the two runs and hardware-team checkpoint `69c0f145`. The repeat starts from RTL with the 10-ns clock loaded before synthesis, uses the same fixed Vivado 2026.1 recipe and reads no checkpoint. One named predicate FDRE and three named writer CARRY4 cells remain after routing.

The global campaign contains four initial trials, two source compositions and one positive repeat. No negative-clock repeat was performed. Handoff generation and export QA remain Root’s separate steps.

This qualifies the selected component’s internal 100-MHz clock on `xc7a100tcsg324-1`. It does not qualify external I/O, complete-parent/board timing, a programmed bitstream, sustained hardware 30 fps or under-10-ms decoding. The 125-MHz target remains open.
