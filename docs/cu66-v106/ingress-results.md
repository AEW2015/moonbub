# V106 live ingress replay cache

The isolated candidate removes the full32 remaining subtraction and last-word addition from the live staging-to-Rice input-validation cone. The fifth native trial's [synthesis report](../../experiments/python-gamebub-v106/native/20261108T021556317071Z/reports/synth-setup-paths.rpt) measured `sizes_reg[0][1]` → parser `out_value_reg[0]/R`: WNS −3.581 ns, data 12.940 ns (6.823 logic / 6.117 estimated route), 28 levels including 18 CARRY4s. That trial later failed placement; these are synthesis estimates, not routed timing. [Pinned motivation](../../experiments/python-gamebub-v106/ingress/motivation.json) retains the exact report hash.

## Exact change and qualified invariant

One private 32-bit `cached_replay_remaining` initializes to `sizes[band]` on the original CONTEXT_START edge, where `replay_bits` becomes zero. It decrements only inside the original successful `ctx_valid && ctx_ready` replay branch. Reset, abort and replacement start set the private cache to zero. Original state transitions, word-valid and bounds checks, full32 replay counters, outer context-error/done priorities, accepted-word ownership and public ports remain unchanged. No public cycle or storage capacity changes.

While CONTEXT_RUN is live, `cache = sizes[band] - replay_bits` modulo 2³². The new clamp retains the original unsigned full32 subtraction result and 16/32 cap; last-word detection uses `cache == bits`, exactly equivalent to the original modular `replay_bits + bits == sizes[band]`. Successful replay updates preserve the identity by subtracting the same accepted width on the same edge. The selected band's size is unchanged during its live context.

Outside CONTEXT_RUN, only private `ctx_bits`/`ctx_last` may differ. Both `ctx_valid` and public `stage_word_valid` are then false. The unchanged child connects these to parser `in_valid`, and its `in_ready` does not depend on `in_bits` or `in_last`. The clocked wrapper asserts the inactive input fence. All public outputs and original clocked state continue to compare unconditionally; inactive private values are not silently claimed equivalent.

The [Python model](../../experiments/python-gamebub-v106/ingress/model.json) passes 200,450 numeric rows including 99,660 wrapped subtractions and records the universal modular-ring update/last-word identities. Numeric sampling does not enumerate all 2⁶⁴ size/replay pairs or constitute formal equivalence.

## Actual whole-production comparison

[Selected receipt](../../experiments/python-gamebub-v106/ingress/attempts/20261108T024251781215Z/receipt.json) SHA-256 `4bf37afab6fff48c4b23522de2af22cae1554f5f888aad9da16fa9c83d3d1d87` is `PASS_ACTUAL_INGRESS_CACHE_EQUIVALENCE`, process exit 0. Original and candidate full sync-ingress modules are embedded in duplicate **complete original production pipelines**, with module/type renames as the only adapter changes. The unchanged historical packet/memory bench has only class/main renames and pre/post-edge oracle hooks. All complete pipeline outputs and all **47 synchronous-ingress public outputs** compare before and after every clock, alongside original control/counter/staging fields and child Rice registers.

Strict Verilator 5.020 `--assert -Wall` and GCC `-Wall -Wextra -Werror` passed with j2, a 300-second compile watchdog and 180-second simulation watchdog per seed. The sole Verilator filename exception covers renamed test adapter modules. All production assertions remain enabled. Each command used the existing available-RAM/PSI gate without an override.

| Seed | Prepared cases / clocks | Prepared context starts / word accepts | Historical clocks | Historical word accepts | Historical trace checkpoints |
| --- | ---: | ---: | ---: | ---: | ---: |
| 106401 | 5,760 / 11,521 | 240 / 224 | 7,983,546 | 47,514 | 31,407 |
| 106402 | 5,760 / 11,521 | 240 / 224 | 7,981,974 | 47,514 | 31,401 |

Together the runs checked **15,988,562 actual clock edges**. The 5,760 prepared cases per seed cross 15 size boundaries (including high/full32 values), all four bands, 16/32-bit and serial modes, all eight reset/start/abort combinations, and context-start/accepted-word/fetch branches. These are cache-consistent verification-only states, not proof that each is reachable through a valid encoded packet.

Each real protocol run passes the original 20 packet fixtures × two memory profiles, 56 directed checks and nine synchronous-staging checks, with 4,501,888 dense golden comparisons per seed. The real pipeline interface uses its existing 32-bit replay configuration; prepared states additionally exercise the 16-bit/serial controls. Directed coverage includes malformed/padding rejection, queued and registered fetch cancellation, replacement start, context-failure cancellation of in-flight fetches, held sparse coefficients and raw pairs, memory backpressure and ownership/drain cases.

An independent C++ oracle checks ingress replay/cache and four counters every edge. A separate child-Rice oracle checks full32 loaded/consumed caches, reservoir/availability and six counters on every edge. Parser word validation and the selected prefix operations are independently recomputed. The common frozen V106 context/SUFFIX dependencies are identical in both pipelines; this probe isolates ingress changes rather than attributing other candidates' behavior to them.

[Independent offline audit](../../experiments/python-gamebub-v106/ingress/trace-audit.json), SHA-256 `c45ae433246f9b34de7841559aa3d33d4104f433fa452e35c5e983d3147145fb`, rehashes all source/artifacts, reconstructs the exact edit recipe/adapters, repeats the arithmetic model and replays every prepared transition plus recorded historical checkpoints. Prepared traces log all clocks; historical traces sample every 256 edges plus guards. The offline audit does not replay omitted historical transitions; the compiled independent oracle checks those transitions during simulation.

## Frozen source and retained failures

- Original SHA-256: `771447e0f7516448f47ea1e47f56474e424662a8bbe2b3c32a1f489d2d2b2b27`.
- Candidate [br88_packet_ingress_sync_v91h.sv](../../fpga/experiments/cu66-v106-ingress/br88_packet_ingress_sync_v91h.sv) SHA-256: `4342972a6cf42cebf4f01a82841c0bc7c1850292ca23362817f7f071af126093`.
- Seven-edit [recipe](../../fpga/experiments/cu66-v106-ingress/edit-recipe.json) SHA-256: `7a85248baf1c8de6095b9d7225aafd04f5eb1045a646fe4423a37b88fc2981d2`; schema `v106-edit-recipe-v1`.
- Independent auditor SHA-256: `9f571c4263fda595da0c09ac0526fe6fd3fe26746df9884abec58105e8204585`.

[Attempt ledger](../../experiments/python-gamebub-v106/ingress/attempt-ledger.json) retains three adapter/bench compile failures (unqualified monitor band, generated context-class hierarchy, automatic root-pointer substitution) and a post-run source-freeze failure caused by strengthening the offline auditor during a compile. That earlier attempt's two simulation verdicts passed, but its process exited 1; its prematurely assigned receipt status remains immutable and a failure note marks it unqualified. The corrected runner assigns PASS only after all source hashes are stable, and the selected frozen rerun passed every gate. No RTL/public equivalence or production assertion failure was observed, and no warning was waived to recover a pass.

## Reproduce and remaining gates

```sh
python3 scripts/cu66-v106/ingress.py --model-only
python3 scripts/cu66-v106/ingress.py
python3 fpga/experiments/cu66-v106-ingress/audit_trace.py
```

Two-state whole-module simulation and modular identities do not establish four-state behavior, complete arbitrary-state formal equivalence or mapped-netlist timing. Integrated strict production lint/regression, resource fit, legal routing and the unchanged 100 MHz target are separate gates. Parent boundary/I/O/CDC and memory service, sustained hardware 30 fps and validated complete decoding under 10 ms remain open. No hardware was accessed by this probe.
