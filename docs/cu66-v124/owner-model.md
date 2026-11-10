# V124 owner-equation model

This standard-library model compares two finite two-state equations motivated by the V123 routed owner cone and V123's next-timing proposal. It is algebraic software evidence only; it is not an RTL equivalence proof, formal proof, timing estimate, throughput result, or FPS claim.

## Compared owner identities

For tile mode, the scalar reference first selects `bank_epoch[selector]` and `bank_block[selector]`, then compares those full-width values with the current child epoch and expected uint16 block. The per-bank form computes a full 32-bit epoch and full 16-bit block match for each bank, then indexes that match vector with the same selector. The selector is never replaced by a first-match priority. For non-tile mode, both forms preserve the original scalar child epoch/block fallback equation.

The model treats owner identity independently of `bank_ready` and `child_valid`; those remain separate ready/valid context gates. It also compares ready, valid, and bad-owner error-67 behavior across boolean contexts. Priority is modeled as reset/abort, accepted start, refill error, child error, then normal DISPATCH owner checking, following the selected V119 wrapper source. This exercises the proposed Boolean factoring and does not prove its actual Verilog integration.

## Coverage and hashes

The run covers both selector values, tile and fallback modes, full-width epoch and block boundary/equality-adjacent values, opposite-bank poison, selected-bank mismatch with opposite-bank match, duplicate tags, and 100,000 deterministic random tuples over the full 32/16-bit spaces. It also checks 2,048 ready/valid/error-67 gate contexts and 16 bank-ready/child-valid independence contexts. No claim is made to exhaust all 2^32 × 2^16 tags.

The model output binds its own source SHA and the V123 frozen producer alias SHA. If the V124 candidate source exists when the model is run, its path and SHA are also captured; otherwise these fields remain null until the candidate is frozen and the model is rerun. Model output lives in `experiments/python-gamebub-v124/python-model/`, outside functional proof selectors.

Run:

```sh
python3 scripts/cu66-v124/owner_model.py
```

## Pre-run implementation plan (historical)

The following plan was written before the V124 RTL and native runs. The owner change and functional gates have since executed; routed 125 MHz setup failed. The broader endpoint and hardware gates below remain open.

The planned implementation step was the narrowly scoped V124 owner-equation change in the coefficients wrapper: source both child-bank epoch/block fields, compute two full-width match bits, select the matching bit with the existing emit-bank selector in tile mode, and keep the original scalar equation in fallback mode. Use exactly that owner result for child ready, output valid, and DISPATCH error 67. Preserve ready/valid evaluation when the selected bank is unready or child-valid is low; do not gate owner identity with bank-ready or child-valid.

Freeze the producer candidate and add focused generic and actual-caller RTL comparisons against V123. Retain reset/abort, accepted-start, refill error, child error, malformed/poisoned owner, arbitrary stall, both-bank, and opposite-bank cases. Then run the existing full-parent functional gates with unchanged source order/oracles and exact cycle checks before any native timing trial. V123's local Python harness and aggregate row fixtures do not model the real endpoint service or prove a CPU/Wi-Fi/memory calibration. Endpoint integration, full-board clocks/CDC/I/O constraints, actual memory service, sustained hardware 30 fps, and validated hardware decode below 10 ms remain separate milestones.
