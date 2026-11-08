# V113 native-driver static review

Read-only review of `scripts/cu66-v113/native.py`, the current
`study-policy.json`, the V113 Tcl/XDC flow, IV113.1 and spatial harness
contracts, and the retained V112 native receipts. This review covers the
preparation/launch gates and component-only evidence contract; it is not a
Vivado execution or native proof result.

## Findings

The two provenance gaps from the prior review are fixed in the current
`native.py`. `qualify()` now verifies all five control reports it reparses
against each frozen receipt's `retained_artifact_sha256`. The canonical-reuse
branch now verifies every prior `sources/<path>` snapshot against the prior
receipt's `source_sha256`, in addition to the complete artifact map and the
current hashes for RTL/bench inputs. The existing reused-stage attempt has 38
source entries and 51 artifact entries; all hashes verify. No actionable
driver or policy defect remains in the static review.

The four comparison controls are explicit and each binds its receipt SHA-256,
target period and WNS: Count100 (10 ns, −1.022 ns), Count125 (8 ns,
−3.264 ns), V112100 (10 ns, −1.034 ns), and V112125 (8 ns, −2.844 ns). The
V112125 receipt remains the exact 18-origin source parent; the 10 ns
comparison is also retained independently.

Source hashes are resolved from repository root and attempt-artifact hashes
from the selected proof directory. I exercised `focused()` read-only against
the three current geometry, scratch and inverse PASS summaries; all passed.
An earlier concern that source pins were resolved relative to the attempt
directory was a false positive and is closed.

The spatial prerequisite fails closed until its full canonical PASS receipt is
present and meets the exact seed, run-count, directed-check, canonical-byte,
source and artifact-pin checks. The current selected spatial summary remains
`FAIL` while the adapter-only transport retry is running, so final spatial
qualification cannot yet be claimed. The native flow is limited to two initial
spatial trials and one qualifying fresh positive repeat, fresh RTL, a clock
loaded before synthesis, fixed Default/ExtraNetDelay_high/Default directives,
bounded resources, and an explicitly serialized Root dispatch assumption.
The XDCs define only the component clock. OOC timing does not claim complete
parent timing, board I/O qualification, bitstream, hardware frame rate, or
decode latency. These limits match the IV113.1 changed-latency contract and
the described retained scoreboards.

## Verification performed

Read and cross-checked source/policy/flow/docs and all four pinned control
receipts; re-parsed the four control report sets and confirmed their report
hashes match retained artifact hashes. Reviewed the updated reuse and control
report guards. Checked the failed spatial attempt's source/artifact pins, its
two component stdout-verdict bindings, PASS counters and canonical payload
hashes. All 38 source snapshots match their recorded source hashes, and all 51
artifact hashes verify. The prior
read-only V113 `focused()` validation passed for geometry, scratch and inverse.
No build, native tool, hardware, or source/policy modification was made.

Exact reviewed-file SHA-256 pins and the four control values are recorded in
`experiments/python-gamebub-v113/audit/native-driver-review.json`.
