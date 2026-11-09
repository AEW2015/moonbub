# V120 Source B: 100 MHz component hardware-development handoff

Source B is repeat-qualified internally at **100 MHz** for `xc7a100tcsg324-1` / `cs88_pipeline_v91k`. Two separate fresh RTL synthesis/place/route runs passed all component setup, hold, pulse-width, internal clock-coverage and routing gates. This is an OOC component qualification, not a complete Game Bub board bitstream.

**The selected 18 source/include files are byte-identical to commit `69c0f145d1e3969f5418645a79647634b312214b`.** The board team's pinned experimental Source B remains the same RTL; the new commit adds qualification evidence, this manifest and export checks. No decoder interface or ordinary public cycle changed during qualification.

| Component metric | Initial fresh route | Separate fresh repeat |
| --- | ---: | ---: |
| Clock | 100 MHz / 10 ns | 100 MHz / 10 ns |
| Setup WNS / failing endpoints | +0.174 ns / 0 | +0.174 ns / 0 |
| Hold WHS / failing endpoints | +0.028 ns / 0 | +0.028 ns / 0 |
| Pulse-width slack / failures | +3.750 ns / 0 | +3.750 ns / 0 |
| Internal unconstrained endpoints | 0 | 0 |
| Routing errors | 0 | 0 |

The [machine handoff manifest](../../experiments/python-gamebub-v120/handoff.json) binds the selected source paths, all 18 hashes, compilation order, default parameters, part/top, tool image, core recipe, functional proof selectors and both native receipts. It identifies the same-source repeat lineage explicitly. The [export QA](../../experiments/python-gamebub-v120/audit/handoff-export-qa.json) and [actual source preparation](../../experiments/python-gamebub-v120/audit/handoff-preparation.json) verify the export without running vendor tools or contacting hardware.

- [Initial 100 MHz receipt](../../experiments/python-gamebub-v120/repair-study/native/20261109T205145534717Z/receipt.json)
- [Fresh 100 MHz repeat](../../experiments/python-gamebub-v120/repair-study/native/20261109T211623143358Z/receipt.json)
- [Failed 125 MHz route](../../experiments/python-gamebub-v120/repair-study/native/20261109T205145239583Z/receipt.json)
- [Measured results](../../experiments/python-gamebub-v120/results.json)
- [Remote hardware bring-up instructions](remote-hardware-test.md)

## Prepare the exact component sources

From this checkout, with Git and Python 3.10 or newer:

```bash
python3 scripts/cu66-v120/prepare_handoff.py \
  --output /absolute/new/v120-component
```

Use a new output directory. The exporter validates declared part/top/clock/default parameters, image identity, both positive native receipts, their retained evidence hashes, distinct fresh-build identity, source/recipe lineage and current source hashes. It copies the exact alias tree and the original 10 ns component flow. It rejects existing output directories and inconsistent metadata. No Docker installation, AMD license, Vivado invocation or board access is needed for this preparation step; a new implementation or board build needs its own licensed tool environment.

The source is V119 plus the signed16 ingress range prefix and one phase-local full35 admission equality payload bit. Address-writer and context-terminal prototypes are not selected. Preserve the independently qualified [V118 100 MHz control](../cu66-v118/handoff.md) for board comparisons. V120 Source A itself failed 100 MHz at -0.045 ns and is not this handoff.

## Functional evidence and hardware limits

The focused, complete decoder/actual transport, physical-debt peer/cancellation/retry and guarded byte/row parent suites passed. All tested V119 public values, event ordering and cycles remain exact; independent canonical, HUD, hash and seal oracles passed. The full suite's 48 canonical records are repetitions across six goldens/profiles, not 48 distinct gameplay frames. Prepared fault/header domains are explicitly separate from natural packet tests.

The board team still needs its full top, actual clocks/pins/I/O/CDC/reset constraints, memory service, CS88 transport/profile adapter, full validation/publication and display integration. The existing JPEG `moonshine_top` does not instantiate this decoder. Wide diagnostic outputs are internal debug interfaces, not a physical pin map. Full-board timing must pass before hardware tests; this component's unspecified external I/O timing is not a board waiver.

The row fixtures remain 1,145,104/1,553,197 model cycles from final input byte to validated commit, conditionally 11.45104/15.53197 ms at an assumed 100 MHz complete-parent clock. These exclude earlier delivery and use abstract memory/software HUD semantics. **Sustained hardware 30 fps, complete-parent routed frequency and validated hardware decoding below 10 ms remain open.** Follow the remote instructions for local golden playback, real contention and distinct-frame logs.

## Continuing 125 MHz

Source B's 125 MHz route fails at **-1.517 ns WNS**, with 10,524 failing setup endpoints and -3,931.934 ns TNS. Its new worst path is refill `offset + issued` request-address arithmetic followed by admission replay bounds/readiness and RAM enable. The header-total timing cut retains one predicate FDRE and three writer CARRY4s; arithmetic has not disappeared from the FPGA. The [next 125 MHz work plan](125mhz-next.md) targets that measured request-control cone while keeping this qualified 100 MHz Source B pinned.
