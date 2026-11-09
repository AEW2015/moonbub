# V120 A: 100-MHz result and fallback

Prefix-only A completed fresh routing at 100 MHz but **failed setup timing by 0.045 ns** on one endpoint. It is not a qualified 100-MHz handoff and is not eligible for a positive repeat.

The independent terminal audit passed **759 evidence checks**. It verified all 110 retained artifacts, 83 external artifact pins, 18 consumed/current source origins, functional proof pins, frozen implementation settings and 450 bounded path records.

Evidence:

- Native receipt: `experiments/python-gamebub-v120/integrated-study/native/20261109T200300378785Z/receipt.json`
- Audit: `experiments/python-gamebub-v120/audit/native100-terminal.json`
- Audit SHA-256: `bcf8dee4519f9290f569e00f56939aa5d37eab7324935913d5e42e97b511658f`

| Metric | Actual result |
| --- | ---: |
| Clock period | 10.000 ns |
| WNS / TNS | −0.045 / −0.045 ns |
| Failing setup endpoints | 1 |
| Hold slack / failing endpoints | +0.072 ns / 0 |
| Pulse-width slack / failing endpoints | +3.750 ns / 0 |
| Routing errors | 0 |

The same prefix-only A source map was used as in the passing functional tests. The run used the frozen Vivado 2026.1 recipe: fresh RTL, Default synthesis/optimization/routing, `ExtraNetDelay_high` placement and the 10-ns clock loaded before synthesis. No timing exceptions, guessed I/O delays or strategy sweep were introduced.

## Actual failing cone

The failing path is `scratch/prepared_raw_line[8]` to `scratch/state[0]/D`. Its data delay is 9.992 ns: 2.208 ns logic and **7.784 ns routing**. It crosses two CARRY4 stages and eight LUTs; both carry instances match the routed inventory. The launching net has fanout three.

The source is the prepared address of the next RAW cache line. The combinational cache-address mismatch decides whether to launch a prefetch. At an accepted RAW output, this launch decision joins current prefetch ownership to select `PREFETCH_DRAIN` versus `RAW_FETCH`. The measured path therefore crosses scratch prefetch/control logic, rather than the ingress range predicate or admission header-total equality.

Only this path is negative in both the normal 50 and extended 200 setup samples. The retained source-family samples have positive worst slacks:

| Family | Worst reported slack |
| --- | ---: |
| Kill | +0.141 ns |
| RAW mode | +0.098 ns |
| RAW coefficient | +0.143 ns |
| Context emitted | +0.446 ns |

These samples overlap and are bounded; positive family samples do not prove universal path coverage.

## Remaining trials and handoff

B changes the admission header-total equality payload and retains the same scratch source. It has no direct logical cut on this A100 failure. A B100 timing change would be an implementation result that must be measured, rather than inferred from B’s unit PASS. B100 and B125 remain separate declared trials after their functional and parent gates; this audit does not select either result or introduce another composition.

If B100 also fails, retain the stable V118100 source handoff at `experiments/python-gamebub-v118/handoff.json`. Its initial route `20261109T151440332481Z` and clean repeat `20261109T154034767493Z` both have +0.061-ns setup and +0.078-ns hold slack with zero setup, hold and pulse-width failures. Their receipt hashes and timing reports were independently checked here.

That fallback qualifies an OOC internal component clock, not a complete board bitstream or hardware FPS/latency. V120 research remains unqualified if its remaining 100-MHz candidate fails. Sustained hardware 30 fps and validated under-10-ms decoding remain open.
