# V112 local-control 125 MHz native route audit

Status: **PASS_V112_NATIVE_FINAL_AUDIT** for independent evidence consistency.
The actual component **fails the 125 MHz setup target**.

The [receipt](../../experiments/python-gamebub-v112/native/20261108T195810929250Z/receipt.json)
(SHA-256 `a72bb8c5cdd61549e13a8e7e1db6563122400b6a660823154d53b6956ea797ef`) binds fresh RTL synthesis of
`cs88_pipeline_v91k` for `xc7a100tcsg324-1`, Vivado 2026.1 build 6511674,
8.000 ns loaded as a synthesis input, default synthesis by omission,
Default optimization/route and ExtraNetDelay_high placement. No physical
optimization, retiming, timing exception or guessed I/O delay was added.
The run used two CPUs/threads, 8 GiB RAM with an equal memory-plus-swap ceiling,
and the 3600-second limit. The actual wall duration was 1664.667 s.

All 72 external artifacts, 97 retained files, 18 source snapshots, four recipe
files and five driver/tool pins rehash. Preflight, independent preflight audit,
policy, dispatch and focused/full-canonical proof pins match. Source composition
is retained Count plus exactly the admission and scratch changes; the rejected
V111 header source is absent. Prior generic-context and unowned-private-state
scope qualifications remain unchanged.

| Actual routed 125 MHz result | Value |
| --- | ---: |
| WNS / TNS | −2.844 ns / −32490.680 ns |
| Failing setup endpoints | 33,323 / 88,865 |
| WHS / failing hold endpoints | +0.080 ns / 0 |
| WPWS / failing pulse endpoints | +2.750 ns / 0 |
| Fully routed / routable nets | 66,201 / 66,201 |
| Routing errors | 0 |
| Unconstrained internal endpoints / no-clock / loop failures | 0 / 0 / 0 |

The first setup path is
`coefficients/child/packet_decoder/synchronous.ingress/context_decoder/sel_rep[1]/C` →
`coefficients/child/packet_decoder/synchronous.ingress/context_decoder/out_block_reg[15]/D`.
Its data delay is 10.792 ns across 16 logic levels: 3.504 ns logic (32.469%)
and 7.288 ns routing (67.531%). Its requirement is 8.000 ns, clock skew −0.049 ns
and uncertainty 0.035 ns. The complete first setup and first hold paths are
retained verbatim in the [machine-readable audit](../../experiments/python-gamebub-v112/audit/control-125-final.json)
and the [raw setup report](../../experiments/python-gamebub-v112/native/20261108T195810929250Z/reports/route-setup-paths.rpt).
The next setup path remains in scratch: `phase_reg[1]/C` →
`write_slot_valid_reg/D`, slack −2.781 ns and 10.728 ns data delay.

Against the actual fresh Count 125 MHz route (WNS −3.264 ns,
TNS −40607.203 ns and 34,864 failing setup endpoints), this initial run improves
WNS by 0.420 ns and TNS by 8116.523 ns, with 1,541 fewer failing setup endpoints.
It remains a setup failure. The separate Count 100 MHz result (WNS −1.022 ns) is
not a 125 MHz result. There is no positive result or independent fresh-repeat
qualification to claim here.

The final methodology report retains 2,021 warnings: SYNTH-6 × 20 (RAM output
register use), TIMING-16 × 1,000 (large setup violations), TIMING-18 × 1,000
(missing I/O delays), and ULMTCS-1 × 1 (1,222 control sets, 7.71% of the report's
reference limit). The 1,000-entry methodology lists do not replace the exact
33,323 setup-failure and I/O-coverage counts. Final DRC retains 49 warnings:
CFGBVS-1 × 1, DPIP-1 × 6, DPOP-1 × 27, DPOP-2 × 14 and RTSTAT-10 × 1.
The latter reports 1,027 nets without routable loads; it is distinct from zero
routing errors. No finding was fixed, waived or hidden by this audit.

The route has 1,101 inputs without input delay and 12,856 outputs without output
delay. Effective XDC still contains only the 8 ns component clock; the exception
report has no valid timing exceptions. The single-clock CDC report's “safely
timed” result does not establish the proposed 125 MHz decoder crossing into the
current 100 MHz memory and existing pixel-clock domains. Full custom-parent fit, real
board I/O/clocks/CDC, memory service, publication ownership, bitstream,
hardware 30 fps and complete validated decode under 10 ms gates remain open.
