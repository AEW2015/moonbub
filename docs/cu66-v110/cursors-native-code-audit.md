# V110 cursor native code review

**Status: prospective code review passed; this is not a native preflight or timing result.** No preparation, preflight, Vivado invocation, or native work was performed.

The reviewed driver is `scripts/cu66-v110/native_cursors.py` (SHA-256 `2ad6557ebbbb9cd6e6329bc30f91ce38050465ab73bcb47247e2cf65493ac1c8`), policy `experiments/python-gamebub-v110/cursors-policy.json` (SHA-256 `ea4456d823c4b6279bc7f2b84d0157abc2342e60e2357b333efac79661c73de6`), and guard-test receipt `experiments/python-gamebub-v110/cursors-native-guard-tests.json` (SHA-256 `0735a6d183469c7e995be8f33304e598a6a9f9c8f782b33dfb5f05a77aa02574`). The receipt records 48 pure-validator checks: 17 accepted and 31 rejected. Its positive cases include synthetic terminal/parent fixtures and actual existing source/focused-proof closure; those mocks do not count as native results.

The driver binds the six focused proofs, cursor focus and adapter, exact full-canonical-cursors receipt, and the 18-alias source order. It permits only the scratch alias to differ from the PREFIX control. Public/invalid/debug/memory and noncursor observations remain in the exact contract; cursor payload must match whenever either side has a live owner, while retired private cursor payload may differ and is restored before new ownership. The contract explicitly avoids claiming all private state exact and specifies zero public latency change.

The new flow synthesizes fresh RTL with `RuntimeOptimized`, with the fixed 10 ns clock loaded before synthesis and no checkpoint clock inheritance. It keeps placement `ExtraNetDelay_high`, default opt/route, and no physical optimization. The run Tcl adds only directive metadata; report Tcl and XDC match the frozen ready flow byte for byte. The parent R5 runtime control receipt is hash-pinned and the observed directive check handles the actual lowercase log token `runtimeoptimized`. The earlier failed-Default null-result guard was also hardened.

The source-trial budget is one initial cursor attempt and at most one global positive fresh RTL repeat across the native, Default, and cursor namespaces. A positive Default result blocks cursor work so the authorized Default repeat takes priority. Resource controls preserve 8 GiB RAM/swap, 2 CPUs/threads, 2400 seconds, and the existing host memory/pressure/heavy-job gates. No clock exceptions or constraint changes are introduced.

**Preparation remains gated.** At review time the actual Default receipt was still `RUNNING`, and `canonical-cursors/combined/results.json` did not yet exist. Both a terminal negative/failed Default result and the full-Q cursor PASS are required before preflight. No preflight PASS has been issued.

Detailed source and receipt hashes are recorded in [`cursors-native-code.json`](../../experiments/python-gamebub-v110/audit/cursors-native-code.json).
