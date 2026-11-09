# V119 owned producer bounds and local reconstruction writer

These source changes address independently observed V118 A125 path families. They add no timing exceptions, fanout directives or primitive-preservation attributes. Their timing effect must be established by the coordinated V119 native runs.

The producer replaces its widened nonce-budget addition with an exact reduction of the three nonempty-plane predicates into a two-bit count and a three-bit low carry, gated by the high 30 nonce bits. All 32 nonce bits and all 32 plane-block fields remain in the domain. Entropy reason 64 retains priority over nonce reason 66, and ALLOCATE's independent last-nonce guard stays intact. Declaration-initialized nonce and last-frame anti-replay state retain their warm-reset lifetime. The CHECK_ENTROPY cache assignment is removed after establishing that accepted start and its unchanged ADMIT/CHECK sequence own plane/tile/cache zero; normal PREP_PLANE and positional cache updates remain.

Admission uses its existing captured `q_start` as the MODE_BIT/MODE_END extent. That field is captured together with `mode_bytes` from the same validated header. A new assertion certifies the full 32-bit identity throughout consumption. The original error-8 ordering, bit-cache check, cursor arithmetic and request schedule remain. Full-width synthetic predicate contexts bind both stored bound and count once; they do not continuously rewrite the DUT or claim those states are naturally reachable.

Reconstruction moves only physical residual-bank writes out of the reference-response-gated central FSM. The phase-local writer retains every reset/start/cancel and mode-lookup clear and the exact E+2 validated word commit. All logical state, output ownership, first-fault priority and physical reference descriptors remain in the existing controller. Assertions check the live reference phase and exclude an accepted reference failure from a live residual/mode payload edge. Every edge is additionally checked against the original writer's complete 1,536-bit expected poststate, including unchanged words. This is finite simulation evidence plus runtime invariants, not a formal all-trace or hardware proof.

The new source map is under `fpga/experiments/cu66-v119-owner`; production recipes are reversible, and `packaging.json` losslessly splits the admission source for Verilator while native Vivado reads the whole source. The original V118 and older files remain frozen.

Root dispatches the focused commands under the global two-job resource gate:

```bash
python3 scripts/cu66-v119/owner/reconstruct.py --run --root-grant ROOT_V119_R
python3 scripts/cu66-v119/owner/response.py --run --root-grant ROOT_V119_RESPONSE
python3 scripts/cu66-v119/owner/admission.py --run --root-grant ROOT_V119_ADMISSION
python3 scripts/cu66-v119/owner/producer.py --run --root-grant ROOT_V119_PRODUCER
```

All use asserted, fatal-warning Verilator and C++ `-Wall -Wextra -Werror`. Failed attempts and their snapshots remain; repaired verification adapters require fresh runs. The admission entry wrapper initially nested an inherited `main` macro incorrectly; its replacement embeds the exact old entry body with only its function name changed. The producer's first C++ adapter assumed a flattened admission hierarchy; it now uses the actual generated retained-module class and pointer fields. Neither repair changes production RTL or suppresses warnings. A later admission fixture repair initializes the existing selected tuple in both current V116/V119 sides; the older fixture initialized only its candidate because its original reference had been V112. The complete preparation is written once before the synthetic edge, with both reference assertions enabled; it does not repair state after evaluation or alter an expected result.

The whole original admission/cache/golden/physical-debt oracles remain. Added producer checks cover all eight plane masks and all entropy combinations at nonce endpoints plus full-width random RTL predicates. Added admission checks cover full-width mode extents/end±1/wrap and trailing bits. Reconstruction and response checks retain the complete V118 suite and require every original terminal field and cycle count to match after removing only the added ledger metrics.

Coordinated full-component, transport, peer, guarded-parent and fresh routed timing remain separate required gates. The active-cell scan and header/return-state families may require additional owned preparation if the actual new route still identifies them; they are not silently narrowed or replaced here.

## Focused evidence and remaining gates

The producer, reconstruction, and response selectors report actual-RTL PASS. Reconstruction checked the original 1,536-bit writer poststate on 4,098,658 clock edges across two seeds; response qualification checked 7,692,362 more edges including real reference-failure/drain/retry behavior. Their original terminal results and public cycle counts match exactly. Producer qualification retains the full cache/readiness suite and adds 9,216 prepared entropy/nonce cases and 250,000 real RTL predicate samples per seed. These are focused functional results, not routed timing or hardware frame-rate evidence.

The extra nonce-boundary runner uses the exact qualified producer model archive and generated headers to check FC/FD/FE/FF, every nonempty-plane mask, all 64 entropy combinations, and reset/abort priority. It hashes and names the parent PASS receipt and model artifacts and explicitly reports `model_reused=true`; its new C++ auxiliary is compiled with the same strict warning flags. It does not replace the fresh full-component compilation. Root dispatches it separately:

```bash
python3 scripts/cu66-v119/owner/nonce_boundary.py --run --root-grant ROOT_V119_NONCE_BOUNDARY
```

The nonce auxiliary reached actual-RTL PASS on both seeds: each checked 2,048 predicate cases (512 at FD), 693 simultaneous entropy/overflow cases preserving error-64 priority, and three reset/abort cases. The model was reused from the producer PASS and no natural-frame claim is made. Admission qualification also reached terminal actual-RTL PASS on both seeds. Each retained 86 packet cases, 44 directed checks, 25,344 chunk-boundary cases with 294 cancellations, and 540 new full-width mode-bound checks. All original independent packet-run/fill, mode-port, scale-port and geometry checks passed. The source-bound summary is `experiments/python-gamebub-v119/owner/focused-summary.json`. Full-component and routed A125 timing qualification remain required before claiming a V119 improvement.
