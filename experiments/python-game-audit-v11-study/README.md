# Python Game Bub v11 evidence audit

This independent standard-library audit reads the hybrid selector, block-motion, mixed GF02/GA01 transport, initial-key refresh probe, and decoder architecture artifacts. It does not rerun codecs, video, or timing workloads.

The audit recomputes source/policy counts, per-profile decoded frame counts and paired input hashes, whole packet caps, selected/requested pixel coverage, packet and forward-wire totals, presentation counts, and source pin/media manifest hashes before and after reading. It keeps captures, codec decodes, strict presentations, eventual presentations, policy evaluations, and probe runs as separate counts. Component measurements and counters are included only when the source result records them.

## Findings

- The hybrid study has 140 source records and 560 policy decisions across four policies. Two synthetic noisy source frames exceed the GM base cap, producing eight base-over-cap policy rejects with no selected hybrid format. All emitted complete hybrid packets fit the 49,152-byte cap. Candidate rejection and attempted-service counters are retained per policy; offline selector service measurements do not establish device execution time.
- The block study has 612 actual codec output records across seven scenes and three profiles. Per-profile IDs map to the same input hashes. The BM block motion profile is not a general compression win: mean bytes are about 3.8% higher than GM zero on combat, 2.1% lower on the second full-size clip, and 6.7% lower on its 512×288 version. Synthetic noise is a counterexample, with BM mean bytes above GM zero and lower mean PSNR. These are decoded results for the custom experimental format, not standard codec conformance.
- The mixed transport study has 12 independent 60-capture case runs (720 capture-policy decisions summed across runs), 670 packet events, 669 successful decodes, and 654 presentations in the stored metrics. Strict and eventual presentation counts differ; neither is a hardware 30 fps result. The separate initial-key-only refresh probe has 120 captures, 119 preparations/decodes, 117 strict presentations, and 119 eventual presentations. It is not added to baseline run counts.
- A serialized functional feedback check binds the outer feedback identity to the inner GM epoch/frame; unit tests include atomic rejection of an invalid nested patch. The run uses modeled virtual transport/service assumptions plus Python wall observations. It does not prove target-link latency or hardware decoding.
- The architecture file is a parameter model, not a synthesized implementation or resource fit. Resource inventory and traffic estimates are explicitly treated as external/reference inputs and modeled bounds.
- The audit rehashed 34 pinned local source files and two media manifests; before/after values match. Mutable external source claims and supplied hardware inventory are not independently reproduced by these local hash checks.

New custom packet formats are not established as installed or standard-conformant. Target hardware timing, live transport, display scanout, and sustained 30 fps presentation remain unproven.

Run `python3 audit.py` to regenerate `audit.json` and `audit-run.log`. Run `python3 -m unittest -v test_audit.py` for the lightweight helper and actual-artifact checks.
