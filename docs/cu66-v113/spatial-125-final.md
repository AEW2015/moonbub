# V113 terminal 125 MHz review

**The route completed, but the 8 ns setup target failed.** The independent
[raw-pin audit](../../experiments/python-gamebub-v113/audit/spatial-125-final.json)
verifies the [terminal receipt](../../experiments/python-gamebub-v113/native/20261108T213919828839Z/receipt.json),
SHA-256 `713ddb73ab148bde242274406dd28a7399c9172fa735d75e55a07270ffd24a0b`.
All 97 retained-file pins, 72 external artifacts including checkpoints, 18
source bodies/snapshots, four recipe files, five tooling files and seven proof
pins match. No source change, new implementation or additional trial was made.

The actual run starts from fresh RTL, loads `component_clk` at 8.000 ns with
waveform `{0 4}` before synthesis, and uses `xc7a100tcsg324-1`. Default synthesis
is selected by omission, with no retiming option; opt/route are Default,
placement is ExtraNetDelay_high and physical optimization is omitted. Actual
commands, settings, clocks and before/after effective XDC agree. There are no
valid timing exceptions, false paths, multicycle paths, clock groups or guessed
I/O delays. The same 18 source bodies were used in the 100 MHz trial; only the
three documented V113 aliases differ from V112, with V111 header work excluded.

| Routed result | Value |
| --- | ---: |
| WNS / TNS | −3.303 ns / −48,746.754 ns |
| Failing setup endpoints | 44,277 / 96,321 |
| WHS / failing hold endpoints | +0.109 ns / 0 |
| WPWS / failing pulse checks | +2.750 ns / 0 |
| Fully routed / routable nets | 68,598 / 68,598 |
| Routing errors | 0 |

These values are reparsed from the raw reports, rather than accepted only from
the receipt. The worst routed path is
`transform/accept_state_reg[0]/C` →
`coefficients/child/packet_decoder/synchronous.ingress/prepared_request_addr_reg[16]/CE`:
11 levels and 11.013 ns data delay, comprising 1.820 ns logic and 9.193 ns net
routing (83.5%). Forty-two of the first 50 setup paths start at that accept-state
register. The endpoint families are predominantly ingress CEs; none of these
50 routed endpoints is a DSP datapath. The placed worst path instead starts
at `result_state_reg[1][1]`, with −3.244 ns WNS and 10.955 ns data delay. Those
origins feed the same broad ownership/busy/start/refill control network; the
placed source identity must not be reported as the terminal routed source.
See the [bounded next cut](next-control-cut.md).

| Same 8 ns control | WNS | V113 change |
| --- | ---: | ---: |
| Retained Count125 | −3.264 ns | −0.039 ns |
| V112125 | −2.844 ns | −0.459 ns |
| V113125 | −3.303 ns | — |

All remain negative. The separately audited V113100 run is also negative at
−1.686 ns; its fault-pending → ingress-CE worst path has 83.0% routing delay.
These are actual target-clock comparisons, not an inferred achieved frequency.
Neither initial V113 trial qualifies for the policy's positive fresh repeat.

The component fits its reported capacity: 36,976 LUTs, 39,225 flip-flops,
1,177 control sets, 42 DSP48E1, 32 RAMB36E1 and 12 RAMB18E1 (38 BRAM tiles).
The same-clock V112 control used 42 DSP, 32 RAMB36 and four RAMB18. The actual
IDCT mapping uses 17 DSPs, each with AREG/BREG/MREG/PREG = 1/1/1/0; an eight-lane
source description must not be equated with eight physical DSPs. The BRAM
inventory has DOA_REG/DOB_REG = 0/0 throughout. Adding DSP or BRAM output
registers changes latency/ownership and would need new qualification; it is not
a demonstrated remedy for the observed control-enable cone.

Methodology remains open: SYNTH-6 reports 28 unmerged BRAM output-register
instances; TIMING-16 and TIMING-18 each print 1,000 checks. These capped lists
are not the actual setup-failure or unconstrained-port counts. `check_timing`
reports zero unclocked/internal unconstrained endpoints, loops and latches,
but 1,101 inputs and 12,887 outputs lack external delays. DRC reports CFGBVS-1
(1), DPIP-1 (6), DPOP-1 (27), DPOP-2 (14) and RTSTAT-10 (1). The single-clock CDC
report says all paths are safely timed; this does not qualify board CDC or I/O.
No warnings are waived by this audit.

The functional binding retains 44 qualified canonical case/profile rows and
42 original directed checks, explicitly reused from their complete parent
certificates; the adapter-only retry newly executes zero canonical rows/checks.
Its two newly executed transport campaigns each pass 12 profiles and two
abort/reset canonical retries. The component route is still OOC: full custom
parent fit, PCTL1 supervisor/session integration, external memory/display
service, board timing, hardware 30 fps and validated decode under 10 ms remain
unqualified. The conclusion is **V113_TIMING_OPEN**.
