# V112: local control and a bounded simulation bridge

Branch: `study/gamebub-v112-local-control-20261108`.
Base: `49ff9c65f67428382ca5616f9587289930b71afb`.
Status: **bounded V112 work executed; V112 exit gates remain partial**.
The functional tests passed; both native routes missed setup. Full registered
PCTL1 ownership and shared-time target firmware integration remain unimplemented.
This continues the [V111–V115 roadmap](../gamebub-v111-v115-simulation-spatial-plan.md).

## Two distinct codec paths

The production Game Bub parent and the integration harness still decode
JPEG/MJPEG. CU66/CS88/BR88 is a separate custom-codec research decoder, with
transform/residual and bounded reference-reuse work. Its component simulation
and implementation evidence does not establish a complete Sunshine-to-display
path. Ordinary NVENC HEVC/AV1 output is not a CS88 payload, and these experiments
do not implement a standards-compatible HEVC/AV1 decoder.

## Timing experiment

Retain the Count composition, rather than V111's rejected header pipeline.
The [baseline inventory](inventory.md) pins the actual source set, separate
100/125-MHz routed bottlenecks, broad controls and existing parent clocks.
Two local transformations target the measured admission and scratch cones:

- Prepare the generic visibility mask before its unchanged consumption edge,
  then use a balanced population count.
- Validate each scratch cache bank before selecting the one-bit validation
  result, rather than placing wide data selection ahead of validation.

The focused original/candidate checks and full canonical regression must pass
before native dispatch. Original assertions, error priorities, accepted
physical drains, public cycles and invalid-cycle observations remain part of
the contract. These changes do not implement the complete PCTL1 ownership,
registered command/kill/flush or diagnostic-snapshot interface.

The [focused proof](control.md) passed both scratch and admission seeds plus
the exhaustive generic geometry checks. The full 18-source composition passed
44 case profiles and 42 directed checks across two seeds, with exact reference
stdout, public events/cycles and canonical pixels. The source deltas from
Count are exactly two files; V111's rejected header source is excluded.
The [independent full-Q audit](../../experiments/python-gamebub-v112/audit/canonical-final.json)
also compares the outputs with the retained actual Count result. The reference
was reused, not newly recompiled. Fixed workloads and the earlier declared
generic/private scopes remain explicit; this is not formal equivalence over
all possible input histories.

[Simulation cost](simulation-cost.md) records the actual instrumented host
cost and separates conditional long-campaign estimates from target throughput.

The [bounded study policy](../../experiments/python-gamebub-v112/study-policy.json)
permits two initial fresh-RTL component routes, at 10 and 8 ns, and one fresh
repeat of a genuinely positive result. Sources, XDC, recipes, proofs, tool
image and actual report clocks are bound in receipts. The target part remains
`xc7a100tcsg324-1`, Vivado 2026.1 build 6511674, Default synthesis/opt/route and
ExtraNetDelay_high placement. No timing exceptions, guessed I/O delays,
retiming or strategy sweep are introduced.

The architecture follows AMD's guidance to [break long combinational
paths](https://docs.amd.com/r/en-US/ug949-vivado-design-methodology/Determine-Whether-Pipelining-is-Needed)
and [limit resets to state that requires them](https://docs.amd.com/r/en-US/ug949-vivado-design-methodology/When-and-Where-to-Use-a-Reset).
Those guidelines motivate experiments; only routed measurements establish
whether this particular placement improves.

## Simulation bridge

The [executed harness](harness.md) uses an explicitly labeled bounded replay
adapter and actual QSPI/JPEG/memory/display RTL. Ten presentations of one
fixture passed 3,456,000 exact decoder pixels and presented SDRAM words. It
checks actual credit/commit/abort responses, abort/reset/retry, corruption,
oversized records and six causal-trace rejection controls. One event of at
most 1,039 bytes is resident; transformed sequence/frame IDs and the original
guest trace hashes are explicit. This is separate from the custom-codec
timing experiment and does not force RTL FIFO-credit exhaustion.

The [clock-ratio CDC screen](cdc.md) freshly compiled the existing synchronous
five-channel experimental fabric and passed six strict, zero-warning runs at
nominal and detuned ratios around 200/125/100/29.36 MHz. Independent scoreboards
account for 104,610 accepted = 103,638 delivered + 972 reset-discarded words,
with at most nine owned words per channel. Reset discards in this isolated
transport are not PCTL1 physical-transaction retirement. Old physical CDC/reset
findings and full-parent integration remain separate obligations.

Concurrent adapter/RTL clocks do not imply a shared-time ESP32 guest, calibrated
CPU/Wi-Fi service, a production GP-SPI/DMA driver, or a native Sunshine encoder.
Ten repeated presentations of one fixture are not ten distinct gameplay
frames, nor a sustained 30-fps proof. Whole-parent 125-MHz integration, CDC,
memory and board-I/O qualification remain separate gates.

## Reproduction and limitations

### Routed custom-decoder measurements

| Source / role | Target | WNS ns | TNS ns | Setup-failing endpoints | Hold / pulse ns |
| --- | ---: | ---: | ---: | ---: | --- |
| V110 Count control, reused | 100 MHz | −1.022 | −1,125.069 | 4,620 | +0.085 / +3.750 |
| V112 local cuts, fresh | 100 MHz | −1.034 | −2,028.748 | 5,607 | +0.086 / +3.750 |
| V111 Count control, reused | 125 MHz | −3.264 | −40,607.203 | 34,864 | +0.080 / +2.750 |
| V112 local cuts, fresh | 125 MHz | −2.844 | −32,490.680 | 33,323 | +0.080 / +2.750 |

All routable nets are routed with zero routing errors, actual clock targets match,
and internal clock/constraint coverage checks pass. Both new runs have zero
hold/pulse failing endpoints but still fail setup. At 100 MHz, WNS worsens
0.012 ns, TNS magnitude grows and 987 more endpoints fail. At 125 MHz, WNS
improves 0.420 ns and 1,541 fewer endpoints fail, but a 2.844-ns setup deficit
remains. These are two source-bound OOC measurements, not board clock or
statistical route-quality qualifications. The old controls were reused rather
than remeasured.

The worst new 100-MHz path is `transform/fill_bank_reg/C` to coefficient-bank
word enable `value_reg[12]/CE`, 10 levels and 10.745-ns data delay. At 125 MHz
it is context `sel_rep[1]/C` to `out_block_reg[15]/D`, 16 levels and 10.792 ns.
The [next-control proposal](next-control-boundary.md) maps those actual paths
back to the source before proposing owned coefficient commits and prepared
context geometry. It also retains the earlier scratch/ownership obligations.

The terminal independent audits are [100 MHz](control-100-audit.md) and
[125 MHz](control-125-audit.md). Neither result qualifies for the positive-only
fresh repeat; zero repeats were used. Count remains the retained control,
and V112 is not promoted as a timing-qualified replacement. No production RTL
was changed. The [receipt summary](../../experiments/python-gamebub-v112/results.json)
and [comparison CSV](../../experiments/python-gamebub-v112/native-comparison.csv)
retain actual metrics and open system gates.

See [reproduce.md](reproduce.md) for runner commands and resource rules.
Vivado MCP returned `Transport closed`; native CLI execution is explicit.
Existing Verilator is the selected behavioral backend; there is no XSim,
post-route timing-simulation or hardware result implied by its checks.
The [attempt history](audit-history.md) separates repaired verification
failures and the pre-dispatch pressure rejection from the selected proofs and
actual negative native measurements. [Portable fixture preparation](portable-harness.md)
passed without changing the frozen harness; its optional complete rerun was
not executed.

No board bitstream is programmed. Sustained hardware 30 fps and validated
complete decoding below 10 ms remain open until their actual acceptance gates
are met.
