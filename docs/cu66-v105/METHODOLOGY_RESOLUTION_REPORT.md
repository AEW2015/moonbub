# V105 methodology resolution report

**Status: component evidence measured; methodology signoff OPEN.**

Constraint source: `component.xdc`, line 4. The command is `create_clock -name component_clk -period 10.000 [get_ports clk]`: clock component_clk, period 10 ns, target input port clk. It is loaded before synthesis. Default implementation directives and two tool threads are retained. No comparison clock, exception, waiver, I/O delay or parent clock-source location was fabricated to clear findings.

| Variant | Stage | WNS ns | No clock | Unconstrained internal endpoints | Missing input delays | Missing output delays |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| admission | synth | -11.108 | 0 | 0 | 1101 | 12885 |
| combined | synth | -12.014 | 0 | 0 | 1101 | 12885 |
| combined | place | -12.703 | 0 | 0 | 1101 | 12885 |
| combined | route | -13.653 | 0 | 0 | 1101 | 12885 |
| geometry | synth | -11.593 | 0 | 0 | 1101 | 12885 |
| geometry | place | -12.375 | 0 | 0 | 1101 | 12885 |
| geometry | route | -13.124 | 0 | 0 | 1101 | 12885 |
| locality | synth | -12.015 | 0 | 0 | 1101 | 12885 |
| locality | place | -12.599 | 0 | 0 | 1101 | 12885 |
| locality | route | -13.956 | 0 | 0 | 1101 | 12885 |
| memory | synth | -11.728 | 0 | 0 | 1101 | 12885 |

The endpoint numbers above come from check_timing. Methodology rule counts below are the tool-reported summary counts; per-rule enumeration limits have not been qualified.

| Variant | Stage | Report | Rule | Severity | Reported count |
| --- | --- | --- | --- | --- | ---: |
| admission | synth | methodology_reported | RTGT-1 | Advisory | 64 |
| admission | synth | methodology_reported | SYNTH-5 | Warning | 378 |
| admission | synth | methodology_reported | SYNTH-6 | Warning | 16 |
| admission | synth | methodology_reported | TIMING-16 | Warning | 1000 |
| admission | synth | methodology_reported | TIMING-18 | Warning | 1000 |
| admission | synth | DRC_reported | CFGBVS-1 | Warning | 1 |
| admission | synth | DRC_reported | DPIP-1 | Warning | 49 |
| admission | synth | DRC_reported | DPOP-1 | Warning | 26 |
| admission | synth | DRC_reported | DPOP-2 | Warning | 12 |
| combined | synth | methodology_reported | RTGT-1 | Advisory | 67 |
| combined | synth | methodology_reported | SYNTH-5 | Warning | 378 |
| combined | synth | methodology_reported | SYNTH-6 | Warning | 16 |
| combined | synth | methodology_reported | TIMING-16 | Warning | 1000 |
| combined | synth | methodology_reported | TIMING-18 | Warning | 1000 |
| combined | synth | DRC_reported | CFGBVS-1 | Warning | 1 |
| combined | synth | DRC_reported | DPIP-1 | Warning | 51 |
| combined | synth | DRC_reported | DPOP-1 | Warning | 20 |
| combined | synth | DRC_reported | DPOP-2 | Warning | 11 |
| combined | place | methodology_reported | RTGT-1 | Advisory | 67 |
| combined | place | methodology_reported | SYNTH-5 | Warning | 378 |
| combined | place | methodology_reported | SYNTH-6 | Warning | 16 |
| combined | place | methodology_reported | TIMING-16 | Warning | 1000 |
| combined | place | methodology_reported | TIMING-18 | Warning | 1000 |
| combined | place | DRC_reported | CFGBVS-1 | Warning | 1 |
| combined | place | DRC_reported | DPIP-1 | Warning | 51 |
| combined | place | DRC_reported | DPOP-1 | Warning | 20 |
| combined | place | DRC_reported | DPOP-2 | Warning | 11 |
| combined | route | methodology_reported | RTGT-1 | Advisory | 67 |
| combined | route | methodology_reported | SYNTH-5 | Warning | 378 |
| combined | route | methodology_reported | SYNTH-6 | Warning | 16 |
| combined | route | methodology_reported | TIMING-16 | Warning | 1000 |
| combined | route | methodology_reported | TIMING-18 | Warning | 1000 |
| combined | route | DRC_reported | CFGBVS-1 | Warning | 1 |
| combined | route | DRC_reported | DPIP-1 | Warning | 51 |
| combined | route | DRC_reported | DPOP-1 | Warning | 20 |
| combined | route | DRC_reported | DPOP-2 | Warning | 11 |
| combined | route | DRC_reported | RTSTAT-10 | Warning | 1 |
| geometry | synth | methodology_reported | RTGT-1 | Advisory | 64 |
| geometry | synth | methodology_reported | SYNTH-5 | Warning | 378 |
| geometry | synth | methodology_reported | SYNTH-6 | Warning | 16 |
| geometry | synth | methodology_reported | TIMING-16 | Warning | 1000 |
| geometry | synth | methodology_reported | TIMING-18 | Warning | 1000 |
| geometry | synth | DRC_reported | CFGBVS-1 | Warning | 1 |
| geometry | synth | DRC_reported | DPIP-1 | Warning | 49 |
| geometry | synth | DRC_reported | DPOP-1 | Warning | 26 |
| geometry | synth | DRC_reported | DPOP-2 | Warning | 12 |
| geometry | place | methodology_reported | RTGT-1 | Advisory | 64 |
| geometry | place | methodology_reported | SYNTH-5 | Warning | 378 |
| geometry | place | methodology_reported | SYNTH-6 | Warning | 16 |
| geometry | place | methodology_reported | TIMING-16 | Warning | 1000 |
| geometry | place | methodology_reported | TIMING-18 | Warning | 1000 |
| geometry | place | DRC_reported | CFGBVS-1 | Warning | 1 |
| geometry | place | DRC_reported | DPIP-1 | Warning | 49 |
| geometry | place | DRC_reported | DPOP-1 | Warning | 26 |
| geometry | place | DRC_reported | DPOP-2 | Warning | 12 |
| geometry | route | methodology_reported | RTGT-1 | Advisory | 64 |
| geometry | route | methodology_reported | SYNTH-5 | Warning | 378 |
| geometry | route | methodology_reported | SYNTH-6 | Warning | 16 |
| geometry | route | methodology_reported | TIMING-16 | Warning | 1000 |
| geometry | route | methodology_reported | TIMING-18 | Warning | 1000 |
| geometry | route | DRC_reported | CFGBVS-1 | Warning | 1 |
| geometry | route | DRC_reported | DPIP-1 | Warning | 49 |
| geometry | route | DRC_reported | DPOP-1 | Warning | 26 |
| geometry | route | DRC_reported | DPOP-2 | Warning | 12 |
| geometry | route | DRC_reported | RTSTAT-10 | Warning | 1 |
| locality | synth | methodology_reported | RTGT-1 | Advisory | 67 |
| locality | synth | methodology_reported | SYNTH-6 | Warning | 17 |
| locality | synth | methodology_reported | TIMING-16 | Warning | 1000 |
| locality | synth | methodology_reported | TIMING-18 | Warning | 1000 |
| locality | synth | DRC_reported | CFGBVS-1 | Warning | 1 |
| locality | synth | DRC_reported | DPIP-1 | Warning | 51 |
| locality | synth | DRC_reported | DPOP-1 | Warning | 20 |
| locality | synth | DRC_reported | DPOP-2 | Warning | 11 |
| locality | place | methodology_reported | RTGT-1 | Advisory | 67 |
| locality | place | methodology_reported | SYNTH-6 | Warning | 17 |
| locality | place | methodology_reported | TIMING-16 | Warning | 1000 |
| locality | place | methodology_reported | TIMING-18 | Warning | 1000 |
| locality | place | DRC_reported | CFGBVS-1 | Warning | 1 |
| locality | place | DRC_reported | DPIP-1 | Warning | 51 |
| locality | place | DRC_reported | DPOP-1 | Warning | 20 |
| locality | place | DRC_reported | DPOP-2 | Warning | 11 |
| locality | route | methodology_reported | RTGT-1 | Advisory | 67 |
| locality | route | methodology_reported | SYNTH-6 | Warning | 17 |
| locality | route | methodology_reported | TIMING-16 | Warning | 1000 |
| locality | route | methodology_reported | TIMING-18 | Warning | 1000 |
| locality | route | DRC_reported | CFGBVS-1 | Warning | 1 |
| locality | route | DRC_reported | DPIP-1 | Warning | 51 |
| locality | route | DRC_reported | DPOP-1 | Warning | 20 |
| locality | route | DRC_reported | DPOP-2 | Warning | 11 |
| locality | route | DRC_reported | RTSTAT-10 | Warning | 1 |
| memory | synth | methodology_reported | RTGT-1 | Advisory | 64 |
| memory | synth | methodology_reported | SYNTH-6 | Warning | 17 |
| memory | synth | methodology_reported | TIMING-16 | Warning | 1000 |
| memory | synth | methodology_reported | TIMING-18 | Warning | 1000 |
| memory | synth | DRC_reported | CFGBVS-1 | Warning | 1 |
| memory | synth | DRC_reported | DPIP-1 | Warning | 51 |
| memory | synth | DRC_reported | DPOP-1 | Warning | 27 |
| memory | synth | DRC_reported | DPOP-2 | Warning | 13 |

## Resolution and remaining work

- **TIMING-16 / setup:** real architectural/route work remains. The 10 ns requirement is the fixed experiment target. Read the retained full setup paths and measured logic/route delays; the GEOMETRY route specifically identifies coefficient tile-to-cell validation feeding inverse coefficient-buffer write enable. The separate RTL review records exact source and guard/ownership obligations. Combined/locality path reports remain independent measurements.
- **TIMING-18 / parent boundaries:** check_timing still reports missing external delays. Integrate the actual parent clocks, interface timing and boundary locations before system timing signoff. This OOC component does not establish those contracts.
- **SYNTH-6 / RAM pipeline advisory:** native primitive ledgers retain optional output-register settings. The mode table maps to RAMB18 with the tested logical registered lookup. Any additional primitive output stage needs an explicit latency/ownership change and replay; it is not an attribute-only timing fix.
- **RTGT-1 / RAM retargeting advisory:** keep reported retarget opportunities separate from demonstrated mapping. Additional packet/table/intermediate banking requires actual port, latency and collision proofs plus matched native measurements.
- **DPIP/DPOP / DSP advisories:** report actual AREG/BREG/MREG/PREG settings per primitive and variant. V104 product prefetch is included only in the relevant variants; its local mapping does not qualify every DSP path or prove a system clock gain.
- **CFGBVS/configuration and OOC route/clock-source findings:** actual parent/board configuration and boundary contracts remain integration obligations. No board configuration value or HD.CLK_SRC/HD.PARTPIN_LOCS was guessed.

The scope is architectural RTL improvement with bounded behavioral evidence and component native measurements. No finding was waived, downgraded or hidden by a timing cut. The remaining setup/I/O/clock/CDC/configuration obligations prevent methodology, achieved-Fmax, board 30 fps and complete under-10-ms decode signoff.

Native evidence audit: `experiments/python-gamebub-v105/native-audit.json`, SHA-256 `9461759abde8a64317b20405797d7ff0fafe95519f7bc1337c0d4506103d42c1`.
It pins each source/constraint/recipe, full report and terminal outcome. PASS_EVIDENCE authenticates evidence, including failures; it does not clear the findings above.
