#!/usr/bin/env python3
"""Insert the evidence-bound V107 checkpoint without replacing earlier history."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
AREA=ROOT/'experiments/python-gamebub-v107'


def main():
    summary=json.loads((AREA/'summary.json').read_text())
    selected=summary['selected']
    row=next(r for r in summary['native_decoder_trials'] if r['variant']==selected['variant'])
    timing=row['timing']
    assert not summary['sustained_hardware_30fps'] and not summary['complete_validated_under10ms']
    for rel in ('docs/gamebub-v91-v110-development-plan.md','docs/gamebub-application-specific-codec-plan.md','docs/literature-review-2026-11-06/README.md'):
        path=ROOT/rel;text=path.read_text()
        prefix='../' if path.parent.name=='literature-review-2026-11-06' else ''
        block=f'''<!-- V107-CHECKPOINT-START -->
**V107 partial checkpoint: clock/reset experiments and measured timing cuts.**
The [V107 report]({prefix}cu66-v107/README.md) retains 720×480 CS88
q16/all-BR88 and the 49,152-byte cap. Six cycle-exact lanes pass 336
case-profile runs and 408 directed checks. A complete coefficient tuple register
and done fence pass the separate latency-aware canonical pair (88 case-profile
runs / 84 directed checks), preserving exact pixels and ordered transactions.
HEADER and TABLES candidate-only extensions reuse the retained actual elastic
control; the control is not newly executed or recounted. These are behavioral
samples, not hardware FPS or formal equivalence.

The best source-qualified completed route is `{selected['variant']}`:
**WNS {timing['WNS_ns']:+.3f} ns**, {timing['setup_failing']:,} failing setup endpoints,
hold {timing['WHS_ns']:+.3f} ns and pulse {timing['WPWS_ns']:+.3f} ns.
The unchanged **10 ns / 100 MHz decoder target remains {'met for internal component paths only' if selected['component_internal_100MHz_pass'] else 'unmet'}**.
See the [full comparison]({prefix}cu66-v107/vendor-comparison.md) for every
completed/failed/deferred trial and exact source map. The fresh native watchdog
is explicitly 3,600 seconds versus V106’s 1,800; runtime is not matched.
No decoder clock relaxation, false path or invented I/O timing was added.
The separately labeled RuntimeOptimized probe changes synthesis only on the
same eighth source set, retaining Default placement/routing; it is not an
RTL-only matched comparison or a claimed QoR improvement.

The [CDC repair]({prefix}cu66-v107/cdc-sync.md) removes the measured shared-peer
synchronizer and asynchronous RAM-control hazards in its isolated experiment.
Its native WNS +2.078 ns does not qualify the decoder or production parent.
The repaired pixel FIFO sustains only 0.5 word/receiving-clock, so it cannot
replace the native display’s burst/line buffering directly. Real 143-bit
reference requests, 512-bit responses, transport framing and publication/display
adapters remain open; the production top still uses the legacy JPEG core.
Preserve the related phase-shifted memory clock relationship.

[Measured canonical cycles]({prefix}cu66-v107/latency-next.md) still exceed the
strict one-million-cycle budget in most cases. Next prototype a bounded two-entry
transform-result queue to overlap math with 64-sample emission, retaining abort,
identity, ownership and final publication fences. Its estimated 3,352 data bits
are not an implemented memory allocation or validated speedup. **Sustained
hardware 30 fps and complete validated decoding below 10 ms remain OPEN.**

The user-requested [AMD reset/fanout review]({prefix}cu66-v107/amd-control-guidance.md)
produced two isolated, source-qualified payload experiments: dequant1,027 bits
and IDCT1,280 bits. Actual component mapping grounds all2,307 private reset pins
and removes input/reset ports from their local state-based enables; IDCT control
sets change22→11, with17 DSPs retained. Full routed TABLES→PAYLOAD control
sets instead change1,137→1,160, while slices fall13,642→13,075 and WNS
improves−3.076→−2.735 ns; local set reduction is not a global guarantee.
Every public output/reset cycle remains
exact in their independent RTL/golden tests. Full canonical composition and native
results are listed in the V107 comparison; component mapping is not full-top timing.
The coefficient tuple and coefficient banks were already reset-free and are not
counted as new removals. A local ×43 control-product mapping candidate follows an actual routed DSP
violation at −2.497 ns. Its standalone native run was cancelled for scheduling;
its source is included in the completed META trial. Neither result establishes
a separate ×43 timing gain, and math DSPs were not globally disabled.

The [pure metadata/value checks with their owned tuple]({prefix}cu66-v107/metadata-control-next.md)
were implemented and pass exact canonical comparisons. The combined META route
is −3.146 ns and is not selected: the best completed PAYLOAD route is faster.
Keep live index/bank-owner/token checks,
error priority, immediate kill, ready/valid and publication timing downstream.
Use the [status-use inventory]({prefix}cu66-v107/status-pipeline-inventory.md)
to move host-only observations to coherent tagged snapshots only under an
explicit new status contract; debug-named ownership/launch nets are operational. [Other source-level targets]({prefix}cu66-v107/reset-fanout-plan.md)
include genuinely redundant payload resets, local high-fanout drivers and small
incompatible control sets. Require reset/abort/golden regression and a matched
routed comparison before promotion; a functional job-initialization reset is
not an expendable payload reset.

The header-owned prefix and count-threshold pipeline passes31,856,723 paired
controller edges across both SYNC modes/two seeds, independent arithmetic and
capture/deadline checks, and another44/42 fresh complete-pixel canonical
comparison against the retained actual control. It precomputes packet-only
arithmetic during existing header edges, retaining full-width live block/epoch/
error checks and adding no public cycles. The isolated extracted pipeline maps
469 reset-free data FFs,124 SRLs and16 DSPs; two DSPs retain no MREG/PREG,
and synthetic broadcast sharing prevents treating those resources as a parent
prediction. The selected decoder route remains the timing authority.

The [read-only routed fanout attribution]({prefix}cu66-v107/fanout-attribution.md)
locates7,125 telemetry-data FFs among7,128 reset-pin loads on the retained
PAYLOAD route’s largest
cancellation net, plus three operational allocation/done/seal FFs whose resets
must remain. Prioritize local per-counter/bin validity and zero-base first
feedback/capture; masking output alone leaves stale increments. The separate
[Python feasibility model]({prefix}../experiments/python-gamebub-v107/telemetry-model/README.md)
checks200,000 synthetic clocks and retains a failing stale-feedback negative
control; it does not prove current-source equivalence or resource/timing gains.
A new snapshot/read-port contract could later permit RAM-backed histograms,
with forwarding, collisions, epoch wrap and final-event coherence proved first.
Lazy reset alone cannot infer BRAM while every bin remains a parallel output.
Also assess a production wrapper exposing only required observations, so unused
telemetry can be trimmed; this changes the observed interface and needs its own
qualification. No production wrapper/status API is claimed implemented here.

The [next timing-cut analysis]({prefix}cu66-v107/next-timing-cuts.md) separates
measured runtime scratch read-segment/control routing from earlier Rice synthesis
and coefficient-CE placement cones. A separate modular-capacity Python model
precomputes packet-owned bounds before comparing live blocks; it preserves
32-bit wrap cases and raw capacity, but is not RTL or timing proof. The guarded
Rice mask simplification is source reasoning only. An explicit debug-output
counterexample rejects unqualified coefficient-bank prewrites under cancel.
One bounded post-route physical optimization probe crashed in Vivado with no
completed candidate result; its intermediate slack is excluded from selection.
Retain the [failure evidence]({prefix}cu66-v107/postroute-probe.md), and prioritize
measured RTL/locality changes before expanding implementation-strategy trials.

Continue V107 by closing the measured setup cones, implementing actual parent
protocol/clock adapters and proving bounded service/reset behavior. V108 keeps
the bounded placement/routing matrix and a clean winner repeat; it must not hide
remaining timing failures with broader clock exceptions. No new compression,
quality, HEVC or AV1 performance advantage is claimed here.
<!-- V107-CHECKPOINT-END -->
'''
        start='<!-- V107-CHECKPOINT-START -->';end='<!-- V107-CHECKPOINT-END -->'
        if start in text:
            a=text.index(start);b=text.index(end,a)+len(end)
            text=text[:a]+block.rstrip()+text[b:]
        else:
            anchor='<!-- V106-CHECKPOINT-START -->'
            assert anchor in text
            text=text.replace(anchor,block+'\n'+anchor,1)
        path.write_text(text)


if __name__=='__main__':main()
