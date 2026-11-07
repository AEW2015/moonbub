# V94 bounded rANS category kernel

This is a real, standalone RTL symbol-state kernel, checked using Verilator
5.020 and independent Python traces of native-generated streams. It is not the
complete EC94 packet receiver or FPGA video decoder.

The kernel validates ordered frequency/CDF configuration, initial lane states
and start bounds. It performs sixteen parallel CDF interval comparisons for
the selected model, a registered multiply/update, zero/one/two byte refills,
and held symbol output. Two or four interleaved state registers share **one**
physical update FSM. No parallel-lane throughput claim follows from the state
count. Abort/reset clears provisional ownership and requires fresh preload.
It also suppresses every advertised handshake and done while cancellation is
asserted, including the same edge as offered input/output/configuration.
The pre-fix failure and repaired regression are bound in `cancel-repair.json`.

| Fence | Included |
|---|---|
| Configuration | 16 frequency/CDF writes per model, one initial-state write per lane, one start clock |
| Start accepted → terminal | `4×symbols + refill bytes + observed input stalls + observed output stalls` |
| Symbol acceptance | Exact category, lane, normalized state and cumulative byte cursor |
| Terminal | Every active lane returns to `2^23`, exact declared byte consumption |
| Recovery | Invalid configuration/state/length rejection; cancellation during output hold, refill wait and pending update; exact retry |

The 24×11 unsigned multiply is within the operand widths suggested by
[AMD UG479's DSP48E1 description](https://docs.amd.com/api/khub/documents/gu4oRPFEh_Pm2uaAlfY6Kg/content),
with appropriate zero extension for signed DSP inputs. This is a width
feasibility observation, not verified DSP mapping, area or achieved clock.
The RTL uses a 35-bit product guard and checks the category/state path against
independent exact values.

Logical model payload is two models ×16 entries ×(11 frequency +11 cumulative)
bits = **704 bits**; four lane states add **128 bits**. These figures exclude
control, counters, multiplier registers, packet/literal storage and the rest
of the design. Sixteen parallel comparisons expose many simultaneous table
reads and associated fanout; this is not a free single-port BRAM lookup.
No block-RAM inference, complete device fit or physical timing is qualified.

Independent vectors cover precision 8/9/10, state count 2/4, one/two models,
empty/rare/extreme streams and actual source contexts. Three runs per vector
include no stalls and two deterministic stall seeds. The checker compares every
accepted category/state/cursor; a separate audit replays the math without
importing the encoder and deliberately corrupts expected category, state and
cursor to demonstrate that each oracle check fails.

Model-ID/table byte parsing, CRC, literal Rice reconstruction, coefficients,
mode/reference/quantizer state, pixels, HUD, physical memory/display and atomic
frame publication remain outside this RTL boundary. Symbol outputs are
provisional until terminal validation; a complete adapter must preserve that
distinction. The native whole-frame campaign does not execute this kernel.
Neither experiment establishes hardware 30 fps or under-10-ms full decoding.

Run `python3 scripts/cu66-v94/run_rtl.py --vectors-index
experiments/python-gamebub-v94/optimized-rtl-vectors/index.json`, then
`python3 scripts/cu66-v94/audit_rtl.py`. The selected receipts include exact
source/vector pins, compile/simulation logs and focused compressed VCD files.
See [V94 results](../../../docs/cu66-v94/results.md).
