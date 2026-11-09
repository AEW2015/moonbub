# V115 final functional integration audit

The retained **custom-codec functional qualification passes** its source,
snapshot, transcript and canonical-output binding checks. The separate JPEG-wire
probe remains **FAIL before simulation** and contributes no passing functional
coverage. Native timing and hardware milestones are outside this audit.

The machine-readable result is
[`functional-final.json`](../../experiments/python-gamebub-v115/audit/functional-final.json).
This audit was performed by `/root/v115_ingress`, which authored the V115
ingress/parser changes and native driver. It independently rechecks the other
workers' integration evidence, but **is not an externally independent review of
all implementation code**. No new RTL run, container job or hardware operation
was performed for this audit.

## Source and oracle binding

All six passing selections— inverse, ingress/parser, scratch, full spatial,
control peer and supplemental scratch metadata—have their selected raw receipt
and selector verified. All **165 current source bindings**, the corresponding
**165 snapshot bindings**, and **218 retained artifacts** match their recorded
SHA-256 hashes. These counts include repeated bindings across different proofs;
they are not unique source-file counts.

The main spatial selection is
`52697a476f23ec0c44c17fc80026daeb63755d5481f2c360c8af9b4f557fc907`,
and its raw receipt is
`fb381cd142dfb9c4712bf8dacb280b45555859591af264bde244fa8f4ccff573`.
The main and peer proofs bind the same 18 origins and source order. Exactly five
aliases differ from V114 B125: dequant, IDCT, synchronous ingress, Rice parser and
packed scratch. Each replacement also matches its focused proof directly.
The V114 control top and remaining 12 bodies/include origins are unchanged.
Actual component/peer compilation arguments use the selected snapshot sources
in order. The unchanged admission source's three compile fragments concatenate
back to its exact production bytes.

Eighteen production, wrapper and bench derivations were checked forward and in
reverse. The V114 shared admission API derives back to the unchanged V107 bench:
all **144 original `need()` call texts** remain, with one added pending-admission
check. The additive peer bench retains all **27 original `need()` call texts**
and adds checks. All original assertion lines in the five replacement bodies
remain present. This is source and executable-test evidence, not a formal proof
of all possible input sequences.

## Actual retained results

Terminal verdicts below were read from the actual raw stdout and compared to
the selected receipts. All passing Verilator builds retain `--assert -Wall`;
owned C++ builds retain `-Wall -Wextra -Werror`. The separately compiled V97 RTL
model has no owned C++ bench; its linked transport adapter is checked separately
with the strict C++ flags. No warning waiver was used by these passing custom
functional builds.

| Selection | Actual results |
| --- | --- |
| Inverse, seeds 115101/115102 | Per seed: 48 boundary cases, 25 directed checks, 3,904 residual samples; helper probe has 58 dequant and 116 IDCT cases, 30 cancel/retries, and 1,048,576 signed-domain arithmetic checks. |
| Parser, seeds 115201/115202 | Per seed: 6,096 parameter cases and 189,105 prepared-state edges; historical corpus has 1,520 cases across eight configurations and 104 directed checks. |
| Ingress, seeds 115301/115302 | Per seed: 160 normal corpus profiles, 54 cancel/retries, four malformed checks and 218 successful packets; 1,904,808 coefficients. 1,602,892 requests equal 1,602,874 responses plus 18 canceled private read owners. |
| Scratch, seeds 115401/115402 | Per seed: 72 full transactions, 128 corrupt responses, four read-owner cases, 48 DC line-boundary transactions; 12 pending cancellations, 12 stale-abort checks and 24 complete retries. 269 paired descriptor accepts have exactly 807 extra preparation edges and 269 poisoned tuples. |
| Main spatial, seeds 107601/107602 | 44 actual case/profiles and 42 directed checks; separately rebuilt candidate model and no candidate/canonical reuse. |
| Actual V97 transport, seeds 107601/107602 | 24 successful profiles and four abort/reset retries; each seed checks 16 accepted commands, 16 registered deliveries, 16 poisoned command tuples and wrong DMA/completion token cases. |
| Control peer, seeds 115501/115502 | Per seed: eight retained local checks, six real-parent pending abort/reset cases covering all three preparation edges, 14 complete canonical retries, four accepted-read and two accepted-write checks. Prepared child fault injections are explicit fixtures. |
| Scratch metadata supplement, seeds 115451/115452 | Per seed: 12 invalid geometries, three valid boundaries, four replay-priority cases and 34 accepted poisoned descriptors; zero physical requests. |

All **76 emitted complete canonical rows**—24 component, 24 normal transport and
28 peer retries—were independently decoded and compared byte for byte with the
frozen original canonical vectors: **39,398,400 samples**, 518,400 per row. This
counts complete emitted arrays rather than inflating coverage with rejected
frames' provisional prefixes. Private prepared-state probes and injected
post-fault states are not presented as naturally reachable packet scenarios.

## Latency contract and retained failures

IV115.1 keeps the registered E/E+1 parent command API. It adds two helper
preparation edges per normal inverse tile, eight ingress SELECT edges per
compressed packet, and scratch reservation at E with commit at E+3 plus read-tag
preparation. The parser retains historical cycle equivalence in its paired
suite; the integrated candidate makes **no old public-cycle equivalence claim**.
Scratch paired tests explicitly account for three candidate-only preparation
edges and preserve the old comparison checks at paired edges. New real-parent
abort/reset tests cover the pending ownership interval through the unchanged
parent wiring. Ingress commit remains distinct from decoder done.

Three retained attempts are correctly classified as compile failures with no
completed RTL simulation:

- Scratch `20261109T005407832512Z`: C++ helper-name compile error; superseded by
  the selected successful scratch attempt.
- JPEG wire `20261109T012546265917Z`: compilation stopped on 102 warnings.
- JPEG wire `20261109T012908937875Z`: compilation stopped on one unused-signal
  warning; this is the current failed JPEG selection.

The failed JPEG receipt and all its snapshots/artifacts remain hash-valid.
Subsequent authoring changed `baseline-lint-review.json`, `baseline-lint.vlt` and
`jpeg-wire/prepare.py`, so three current source hashes differ from that failed
receipt. The audit records both old and current hashes. Those edits have no
passing simulation evidence and require a fresh run; they do not alter the
frozen passing custom-codec composition.

Complete C2/HUD validation and PCTL1 parent publication, scanout integration,
ESP32 execution, achieved native clock, sustained hardware 30 fps and validated
complete decoding under 10 ms remain open. Even at an assumed 125 MHz, the
measured fast-service component maximum exceeds the 1.25-million-cycle 10-ms
budget; the separate cycle ledger does not claim that milestone.
