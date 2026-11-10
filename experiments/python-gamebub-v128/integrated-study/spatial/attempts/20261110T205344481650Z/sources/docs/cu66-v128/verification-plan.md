# V128 frozen-verification contract

This contract qualifies a cycle-preserving five-origin composition against the
published V127 index `d16589645d3824399a4df4559a84405051547a48e236dc0aa0e1841812f5ce39`.
The [selected composition](../../fpga/experiments/cu66-v128-raw/selected-composition.json)
retains separate component recipes: four raw-validation origins and one admission
padding origin. Thirteen other origins remain byte-identical. Core order remains
18 entries; byte/row parent order remains24. Original B100 files, prior proofs and
protected marker fixtures are immutable. Publication does not qualify hardware.

## Source and proof roles

The raw change exposes two complete72-bit tuple views and their actual ingress
selector, forwards them through capacity wrapper/child, evaluates complete
8-phase scratch validation per lane and selects Boolean decisions. Full32 epoch,
full16 block, signed16 coefficient,6-bit index and2-bit band are preserved. The
stored scratch raw-format bit remains independent of the ingress selector. All
original masks, casts, priorities and assertions remain. No raw production FF,
reset, attribute, public top port or cycle is added.

The padding change adds one unreset Boolean payload FF. Existing ordered
HEADER_BYTE116–127 writers compute the current header's padding conjunction,
forwarding byte127 on its actual edge. HEADER_CHECK consumes it under the existing
ordered error4–8 chain. Verification-only epoch/size/sequence ownership and literal
padding assertions remain active. Existing16 guarded blocks and both RAM-wrapper
module tails are byte-identical. No public-cycle change or reset removal occurs.

## Raw focused execution

The strict `raw_probe` executable contains two real scratch controllers: the exact
V127 module with only its module identifier renamed, and the actual V128 scratch.
A verification wrapper derives the baseline/old-public coefficient tuple from the
same selector and independently driven raw/context tuples. Every old output and
all8 current phase decisions, selected input_bad and full epoch classification
are compared on every evaluation. New input fields are driven through public
probe ports; there are no hierarchical state, owner, result or payload forces.

A separate source-extracted combinational submodule executes exact old implemented
rank-mask/phase expressions and the actual new lane expressions. Its independent
C++ reference preserves arbitrary64-bit rank masks,32-bit prior positions/counts,
original17-bit block storage with16-bit cast, all signed/range/band/index cases and
all8 phase encodings. The original mathematical-position oracle is checked as a
separate expression and equated to the implemented oracle only when the rank mask
has the coherent original threshold relation. This avoids assuming unowned mask
payloads have a valid threshold.

Wire seeds128501/128502 each execute196608 cases:131072 deterministic boundary
crossings plus65536 random full-width cases, with1572864 phase checks. Selector
and stored-format masks are3; phase mask is255. Coherent literal cases are16384;
arbitrary-mask cases are180224. Good/bad, selected-only bad, other-only bad and
high epoch/block observations must all be positive. Actual scratch pair evaluation
in this suite is reset-held with default registered metadata; the rich arbitrary
phase domain is the source-extracted scalar submodule. There are **zero DUT clock
edges** in this suite; it is not a natural controller-reachability proof.

Clock seeds128601/128602 each execute74 real public-interface contexts without
backdoors:60 malformed selected coefficients (10 epoch-first error2,50 format
error3),12 accepted-write/cancel/ACK/retry contexts and2 unready-APPEND/band-epoch
contexts. Natural phase mask is15; selector/format masks are3. The physical cases
retain4 pending coefficient faults,2 wrong-ACK priority/debt checks,4 reset/abort
cancellations,2 same-edge write-accept/fault cases and12 retries. Two unready offers
are not consumed; two band epoch faults retain error2. Requests and matching ACKs
must balance and be nonzero. Driver clocks/evaluations are measured; no packet
latency/FPS is inferred from these short contexts. Sealing, dense output and full
canonical publication are checked in the complete composition below.

`raw/qualify.py` requires `--run --root-grant ROOT_V128_RAW`. It rebuilds one strict
actual model and runs the four seeds. Source extraction, namespace-only adaptation,
archived source copies and actual external compiled-input copies are hashed before
and after execution; current original-source hashes alone are insufficient.

## Padding focused execution

`padding/qualify.py` requires `--run --root-grant ROOT_V128_PADDING`. One strict
source-extracted kernel model runs seeds128701/128702. It reproduces exact actual
HEADER_BYTE writer and HEADER_CHECK consumer/error-chain fragments and both old
and new owner guards. Its prepared state ports model contexts, not a complete
admission fetch/read FSM. The complete real admission is executed separately in
the fresh decoder/transport/peer/parent gate.

Each seed requires3072 exhaustive single-byte cases across all12 padding positions,
4096 random headers,84 canceled prefixes with84 observed unowned canceled payload
changes,12 incomplete-prefix checks,558 nonwriter holds,6 nonpadding-writer holds
and2 explicit last-byte forwarding cases. Completed headers and retained trace
rows are7268, with monotonic case IDs. Equality evaluations and public-view checks
both equal3×actual kernel clock edges. Payload captures exceed12×completed headers;
error classes0,4,5,6,7,8 all have positive coverage. No new payload or owner is forced.
Three matching-name module files reconstruct one source-bound kernel bundle
losslessly; strict filename warnings must not be suppressed.

## Focused aggregate and inherited proof

The focused selector is `experiments/python-gamebub-v128/focused/results.json`.
Its receipt composes **two separate actual executables**, with explicit raw4 and
padding1 proof roles, source/receipt/artifact closure and original command arrays.
It does not pretend that focused execution ran all five origins in one binary.
The actual simultaneous five-origin execution is the subsequent full gate.

Unchanged V127 focused and inherited scalar/producer/rank/bounds/tile/queue proofs
are rehashed and rechecked by the unchanged source-pinned V127 independent auditor,
with its output written under V128. These historical executions remain historical;
they do not certify modified V128 child dependencies. The actual new full benches
retain every old C++ check and all original RTL assertions, including producer
successor/owner identities. No assertion, counter, cycle, error, debt or golden
stream oracle is weakened to claim PASS.

## Full composition and independent audit

After independent focused PASS, Root may grant peer115501/115502 and decoder plus
actual V97 transport107601/107602. Exact V127 stdout and decompressed event and
canonical streams, including public cycles, remain mandatory. The actual V97
library/strict C++ adapter remains; no software transport is substituted.

Only after both peer and spatial terminal PASS may Root grant
`ROOT_V128_RAW_PARENT` for ordinary/stalled116701/116702 byte and row profiles.
Every HUD, C2, root/hash/seal, terminal, accepted write/ACK and canonical oracle
remains. Expected independent exact comparisons are4 spatial,2 peer,4 parent.
Byte/row first-input, last-input and start→commit boundaries remain separate.

The main index uses schema `v128-raw-functional-composition-v1` and status
`PASS_V128_RAW_FULL_FUNCTIONAL`; its four stages are focused/spatial/peer/parent.
The independent full audit is `PASS_INDEPENDENT_V128_FULL_FUNCTIONAL_AUDIT`.
It validates the exact five-source overlay, source18/parent24 orders, both focused
contracts and original qualified Source B hashes, then uses immutable V127 pure
raw-comparison helpers with explicit V128/V127 receipt arguments. No module-global
monkey-patching is permitted. A pre-freeze self-comparison of actual V127 receipts
must exercise all4/2/4 helper paths.

## Execution, freeze and limits

Backend is explicitly standalone Verilator5.020 in the pinned image, with
`--assert -Wall`, C++17/O2/Wall/Wextra/Werror and compilerj1. The V97 generated
library-only exception retains its original source-bound contract and strict host
adapter. At most two Root-granted study heavy jobs may run, each2CPU/8GiB RAM and
8GiB total RAM+swap/2048PIDs, with finite watchdogs. Launch gates are available
RAM≥8GiB, fullPSIavg10<1 and combined use<.85; stop at RAM<4GiB, PSI≥5 twice or
combined use≥.90. Do not stop unrelated work or change swap.

Freeze all current sources, recipes, fixtures, runners, seeds and independent
auditors before official execution. Preserve failures, inputs and logs; any repair
requires reviewed narrow changes and new affected builds. Root owns native timing,
which remains held until complete independent functional PASS. One fresh8ns trial
uses the fixed implementation recipe; a positive global result requires a second
fresh identical-source/tool/recipe implementation. Negative unchanged sources are
not rerouted to seek favorable placement. I/O/CDC/physical memory and complete
parent clocks, ESP32 CPU/Wi-Fi/QSPI service, custom host endpoint integration,
sustained720×48030fps and validated hardware decode<10ms remain separate open gates.
