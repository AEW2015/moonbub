# Next causal ingress-control study after V119 A

Keep Source A and all consumed proofs frozen. Its two fresh 100 MHz implementations have now passed the internal component gates; the 125 MHz target failed. The following work is a proposal: no production B source or timing result exists yet. The separate standalone range probe is verification preparation, not a selected pipeline composition.

## Evidence from actual routed reports

The report headers identify the design state as `Routed`; these observations do not substitute for the final native audit/receipt. A125 remains a failing target. Both A100 implementations have only +0.024 ns setup margin; the separate fresh repeat passed at the same margin.

| Route | Actual family | Worst listed slack | First implication |
| --- | --- | ---: | --- |
| A125 | Base kill authorization → ingress prepared request address D | −2.105 ns | Initial fetch ownership and the global eligibility cone remain coupled. |
| A125 | Raw coefficient → scratch transfer payload CE | −1.852 ns | Two CARRY4s are now resolved as the signed positive upper-bound rejection chain; prototype the exact range prefix first. |
| A125 | Context emitted count → context error D | −1.808 ns | Full counter terminal checks and context control warrant a separate preparation study. |
| A125 | Base kill → parser consumed/reservoir/remaining control | −1.803 / −1.774 / −1.743 ns | Payload register enables inherit global cancellation/ready logic. |
| A125 | Admission qbuffer → admission state | −1.764 ns | One grammar-validation control path remains; preserve original error ordering. |
| A125 | Base kill → admission memory write enable | −1.761 ns | Shared staging eligibility crosses into physical memory control. |
| A100 | Raw mode → scratch state replicas | +0.024 / +0.082 ns | Even the passing frequency has a cross-module mode/control bottleneck. |
| A100 | Scratch request epoch → assembler reset | +0.115 ns | Physical payload reset ownership is still relevant after carry optimization. |

Input-agent mapping additionally identifies 19 retained output-plan FDREs on both cards: one `last_block`, 16 `next_block` and two `next_state` bits. No epoch/block-id/block-limit/raw certificate register is retained, and no output-plan endpoint appears in the bounded top 50. Further output-plan rewrites therefore have no current measured priority.

No producer nonce or reconstruction residual-writer family appears in either routed top-50 report. The old admission ACTIVE_SCAN family also does not appear there. This is bounded reporting evidence, not proof that those paths are absent elsewhere. It does not justify an owner-only B change now.

## Five experiments, each with its own decision gate

1. **Preserve the completed A endpoint.** Final A125/A100 timing, hold, methodology, utilization and top-path reports are retained with source and artifact hashes. The positive card was repeated from fresh synthesis with identical sources, tool and core recipes. Reconcile all selected 18-source hashes with the full and LIVE receipts. Record that a component OOC result does not establish a routed LIVE parent or board clock.

2. **Try exact signed-range logic before changing chronology.** The ingress raw acceptance predicate is signed 16-bit −2048 through +2048 inclusive. An exact alternative is: bits 15:11 are all zero, or all one, or the complete 16-bit value equals 0x0800. A Python enumeration of every 65,536 bit pattern matches the original signed comparisons, including −2049/−2048/−1/0/2047/2048/2049. The executable proof is `scripts/cu66-v119/raw_range_model.py`; its measured result is `experiments/python-gamebub-v119/prototypes/raw-range.json` (65,536 patterns, 4,097 accepted, zero mismatches; Python only). The [actual checkpoint diagnostic](checkpoint-diagnostic-results.md) now resolves the measured operands: `i_11/CO[3]` is `OR(raw[9:0])`, while `i_4/CO[2]` is signed `raw > 2048`. Fifteen actual LUT2 INIT functions plus both CARRY4s match these equations over all 65,536 inputs. This confirms that the proposed range rewrite targets the measured positive upper-bound rejection chain; the negative bound remains a separate part of complete validation. Nine repeated unresolved reset/abort alias rows remain outside these carry cones. No B RTL or improved mapping/timing result exists. Preserve the output-valid qualification, mode selection, invalid-value rejection reason and stall behavior exactly. Add an actual RTL full 16-bit truth-table test and real RAW-mode boundary packets with held output/reset/abort; only then run fresh whole-model and native mapping. Do not combine this with another change in its first experiment.

3. **Split initial fetch payload preparation from transaction revocation.** The current ingress already speculates next-request address at FETCH_WAIT without reset/global CE. However, `begin_fetch()` also writes the same address/bounds registers from the reset/start/error-gated main FSM. The routed worst path still reaches those D pins. Enumerate every actual `begin_fetch` callsite and derive a complete initial descriptor owner: fetch kind, full 32-bit base, count, continuation, context epoch and descriptor tail. Seek a phase-local payload writer or earlier owned preparation at an existing edge, while leaving logical state, first-fault handling, public requests and physical synchronous response ownership unchanged. Preserve reset/start values where observable. Speculative unowned payload values require an explicit validity invariant and cannot be silently exempted from existing exact comparisons. Do not just register `base_abort` again: that changes cancellation chronology and may expose an extra transfer.

4. **Reduce parser/context payload CE depth with local phase ownership.** Trace the actual base-kill → parser consumed/reservoir/remaining CE and emitted → context error/memory-enable cones. Separate payload captures and local arithmetic preparation from unrelated running/error/ready terms only when a reachable phase invariant proves the original suppression redundant. Keep all 32-bit emitted/target/position domains and the original six-bit fetch-index wrap behavior. A terminal-count lookahead is eligible only if initialized and updated with the real accepted output edge and owned epoch, and all original zero/full-range/overflow cases retain their order. Do not narrow counters to the normal gameplay corpus or add memory read ports. Measure CE/D fanout and reset/control-set mapping after synthesis; lower logical depth can still route worse.

5. **Isolate scratch/public ready dependencies, then qualify the combined winner.** After input/control mapping is understood, consider a local accepted-tuple payload writer for the actual raw-mode/raw-valid → scratch input/transfer path. The output plan itself is not currently a measured critical family. Keep whole owner/descriptor checks before physical request acceptance, retain physical pending debt through cancel/reset, and do not alter synchronous RAM collision behavior. Any extra acceptance buffer or registered ready boundary changes capacity or visible cycles unless proved otherwise; treat that as a separate architecture variant with an explicit schedule, rather than calling it exact A equivalence. Run focused strict simulation, full-component transport/peer tests, guarded LIVE, and fresh A125/A100 routes for the final selected combination.

## Required evidence for every source experiment

Retain asserted fatal-warning Verilator and strict C++ warnings, independent canonical/transform/packet goldens, and every old oracle. For a chronology-preserving variant, require exact public bytes/events/cycles against A and compare all physical owner/debt ledgers. Directed cases must use actual accepted leases and exercise start, reset, abort and first fault at the relevant phase boundaries; impossible pending-state deposits are not a substitute.

The LIVE parent must continue to account for its actual one-edge private residual gap while revoking external grants immediately. Retain raw synchronous replay conservation and unsuppressed physical responses. The existing four LIVE fixtures do not contain private gap-local reads or revoked responses; new claims about those cases require new reachable tests. Preserve declaration-owned anti-replay lifetime, error priorities, qualified owner capture, every payload clear promised by the interface, and complete ACK-before-hash/seal/publication fences.

Use no false/multicycle paths, fanout directives or period relaxation to label 125 MHz closed. Prefer one causal candidate and a measured netlist comparison over a collection of unmeasured rewrites. Keep the old A source and failed attempts immutable.

## Relation to the frame-rate/latency milestone

V119's row fast/stalled LIVE profiles remain 1,145,104/1,553,197 cycles from final outer byte to validated commit, exactly A's V118 controls. At a demonstrated 125 MHz parent clock these would be 9.161/12.426 ms; at 100 MHz they are 11.451/15.532 ms. Faster routing can improve the clock conversion, but cannot make the stalled profile under 10 ms without reducing its work/service cycles. Sustained distinct-frame 30 fps and measured under 10 ms decoding require a complete parent/memory implementation and hardware evidence beyond this study.

## Pinned routed input reports

- A125: `experiments/python-gamebub-v119/integrated-study/native/20261109T171305710307Z/reports/route-setup-paths.rpt`; SHA256 `b21b7b440dbc4c172233f3e68b95a326d453283325a28602ad110ae8d35d02b2`.
- A100: `experiments/python-gamebub-v119/integrated-study/native/20261109T171312690398Z/reports/route-setup-paths.rpt`; SHA256 `b61701e9b4b39426ca925ec140e849eafa28f2b543648fcf65216659d843394d`.
