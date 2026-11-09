> The shared bench and initial proof history are documented below. The current
> [final peer selection](../../experiments/python-gamebub-v115/final/control-peer/results.json)
> also passes both seeds with the final owner/address bodies and all 18 sources.
> [Independent final peer audit](../../experiments/python-gamebub-v115/audit/final-peer-runtime.json)
> verifies all 28 complete canonical retry payloads against frozen V113 bytes.

# V115 full-component peer and pending-reservation qualification

This campaign compiles the actual V115 18-source component. Relative to the
V114B125 source manifest, exactly five helpers change: dequant, IDCT, synchronous
ingress, Rice elastic parser, and packed scratch. The registered control top and
inverse wrapper are unchanged. The runner pins every source, all three selected
focused proofs, immutable inputs and original canonical goldens before compiling.

The eight V114 peer cases and eight full canonical retries remain. The complete
inverse/reconstruction `fail(reason)` fixture is unchanged, including physical
owner retention. The private local-cancel checker retains its existing narrow
scope and independent cancellation accounting; every other original value,
held-transfer, replay and physical-owner check stays active. A reversible
recipe proves the derivation from the frozen V114 bench. No shared ancestor or
original oracle is edited.

Six additional cases exercise public abort and public reset immediately after
each of the scratch reservation, plan and maturity edges. They feed a real
packet through the full parent, inspect the actual parent `store_abort` and
`store_epoch`, and never assign a child tag or scratch state. Before commitment,
the parent must see the reserved owner, no accepted physical/output owner may
exist, and the private anti-replay epoch must remain unchanged. Each kill must
cancel the pending descriptor, return the reservation, leave no physical debt,
and permit a complete canonical retry. All fourteen retries per seed retain
all 518,400 original pixel checks; their emitted pixel bytes are also compared
against the immutable canonical file.

Run `python3 scripts/cu66-v115/control-peer/qualify.py --run` for the bounded
standalone Verilator campaign. It uses Verilator 5.020, assertions, fatal SV
`-Wall`, owned C++ `-Werror`, one compiler worker, two CPUs and an 8-GiB memory
and combined RAM/swap ceiling. Host available-memory and PSI gates remain active.
The two sequential seeds are 115501 and 115502. All attempts are retained.

The selected pointer is
`experiments/python-gamebub-v115/control-peer/results.json`. Until the selected
raw receipt reports `PASS`, preparation or a partial log is not qualification.
This campaign establishes functional integration and cancel/retry behavior; it
adds no routed timing, sustained hardware frame-rate or silicon decode claim.

Selected attempt `20261109T010603696297Z` passed both seeds on the first
attempt. Clock totals were 19,490,916 and 19,491,449. Per seed, all eight original
peer cases and six new parent cases passed, with fourteen full canonical
retries, zero pending physical debt, eight original checked local kills and
three additional checked kills caused by the new public aborts. All 28 emitted
canonical rows matched the original 518,400-pixel golden exactly. Compilation
had zero warnings and assertions remained enabled. Peak host full-memory PSI
avg10 was 0.18; minimum available RAM was 23,429,955,584 bytes.

The raw receipt SHA-256 is
`24b4b8e681215a2056e706d81e54221f65baf193afa7a12282550250d2a492c6`;
the summary SHA-256 is
`513daae40be5e642772fd750847a52ffc4a8577776521cce7f71e8787c5efce4`.
`control-peer/source-review.json` verifies all 67 current/snapshot source pins,
75 artifact pins, the eighteen source origins, the five helper replacements,
the reversible bench derivation, both actual terminal verdicts and all 28
canonical output rows. It is a self-audit of retained bindings and data, not an
independent timing review. Production sources and verification files are frozen.
