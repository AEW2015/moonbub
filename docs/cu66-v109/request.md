# V109 request address and bounds preparation

This isolated derivative targets the initial B native route's measured request-address/bounds cone: fetch_return[2] through stage_read_addr carry logic and stage_read_req comparison/control to ingress error CE, −1.737 ns, fifteen levels and seven CARRY4s. The initial A/B source and physical limitations are documented in [fetch-next-paths.md](fetch-next-paths.md). Neither initial route contains this candidate; no timing improvement is claimed from preparation or simulation.

The derivative starts from the frozen fetch response candidate SHA `4d6a16d0b89aa067fe3e7acc01351ea0bacac694cc63fb681a1471ee4683d044`. Its only production body is `fpga/experiments/cu66-v109-request/br88_packet_ingress_sync_v91h.sv`, SHA `ac7260e749ace036495a162882fdb30fdb129d2c7ddde8df67bc2a8957f8f4b1`. The historical native alias remains `fpga/experiments/cu66-v91h/br88_packet_ingress_sync_v91h.sv`. Existing FETCH production, tests and receipts remain frozen.

The first address and bounds are captured in the existing begin_fetch task. Every fetch starts with index zero, where all three original address forms equal the task's full-width base argument. The packet's owned size is already captured; the task computes the original unsigned `base<size_bytes && base<MAX_PACKET_BYTES` bound predicate on that edge.

For later bytes, a state-only speculative assignment executes at every FETCH_WAIT edge before the existing reset/start/error priority. It first forms the next six-bit index with exactly the original modulo-64 behavior, then applies the original full-32-bit address forms and bounds to that next index. Header index41→42 explicitly jumps to size_bytes−4. Descriptor index5→6 explicitly uses fetch_base+lengths[band]−1. Other addresses retain full-width base-plus-index arithmetic; no physical-RAM-width truncation is introduced.

A successful nonfinal WAIT edge also advances fetch_index and enters FETCH_REQ, so this private payload is exactly the next request's address and bounds with no added cycle. During a held WAIT it may be calculated repeatedly while the current response expectation remains unchanged. Final responses, response failures and cancellation leave the speculative value unowned. No such path can enter a fresh FETCH_REQ without begin_fetch replacing its initial payload. Both assignment sites belong to the same original sequential process, so each added register has one writer. The payload and bounds flag have no reset assignments; WAIT preparation does not inherit cancellation or bounds enables.

stage_read_req uses the owned prepared bounds with the original immediate cancellation and active-context error/done gates. The internal RAM read and ram_addr capture use the prepared full-width address. FETCH_REQ's out-of-bounds failure uses the complement of the same prepared predicate with the original error priority and code. Public stage_read_addr retains its original live expression in **every** state, including invalid/inactive cycles. All public response address/epoch views, request and response counts, error values, RAM acceptance edges, byte storage, metadata and output cycles remain subject to exact comparison.

The frozen fetch response expectation and its two response comparisons remain intact. Every original assertion remains. Added consuming-state assertions require prepared_request_addr to equal the original live fetch_address and prepared_request_in_bounds to equal its two original full-width comparisons whenever an uncancelled FETCH_REQ is reached. Out-of-bounds requests are included in these checks.

The complete-ingress focused miter uses the actual V108 capacity ingress SHA `6514a5f2e2c1b597dfb2cddffeb3e637034d5fe79cdb07861ecd1081034c83c6` as its original control, so it checks both the prior response-address cut and this request derivative against that qualified baseline. Every public port is compared, including invalid values, debug, counters and capacity outputs. The frozen FETCH capture oracle, all six original stale-response assertion rejection subprocesses, packet goldens, actual request/response scoreboard, full-width wrap/bounds fixtures, header/trailer and descriptor discontinuities, live external context noise, metadata holds, and 36 request/response-edge abort/reset/restart retries per seed are retained.

Only the NEW copy of the whole-ingress test initializes added prepared-request fields when it directly forces a synthetic FETCH_REQ. The initial values are computed from the original independent address and bounds formula, before evaluation; they are never copied from ram_addr, an injected response or candidate readiness. Existing forced-WAIT capture fixtures require no extra request initialization because their new WAIT edge prepares the next payload naturally. This is a verification fixture adjustment, not a production interface assumption.

Reproduction commands:

```sh
python3 scripts/cu66-v109/request/prepare.py
python3 scripts/cu66-v109/request/qualify.py
python3 scripts/cu66-v109/request/qualify.py --run
```

The explicit focused run uses two seeds, Verilator assertions and strict warnings, C++ `-Wall -Wextra -Werror`, a 4-GiB container memory limit with no additional swap, two CPUs and one build job. Its selected receipt is the authority for actual execution and status. Full canonical qualification and any native trial are separate gated work; no hardware operation is performed.

Actual focused RTL qualification completed: **PASS**. The strict complete-ingress compile produced zero Verilator warnings. Both unchanged capture-oracle seeds passed all 1,728 prepared cases, 128 high32 metadata owners, eight actual RAW header packets, capture/flush/commit cancellation cases and 2,312 held metadata edges. All six foreign epoch/address subprocesses stopped at the retained original `stale staging response` assertion with capture disabled.

The two complete-packet seeds compared 15496047 exact public cycles and 1509288 independent golden coefficients. Each completed 76 packets, 36 request/response abort/reset/restart retries, eight actual synthetic-context RAM requests, two full-width bounds rejections, every fetch purpose and every directed header/trailer/descriptor boundary. Speculative private preparation did not alter public cancellation, error or invalid-cycle views in those traces.

The [selected receipt](../../experiments/python-gamebub-v109/request/attempts/20261108T120623089944Z/results.json) has SHA-256 `1b044fd57747f4583e7e071505a0bc5d6033ea9b2aee844b2ad9508ef7da15f5`. The [current selection](../../experiments/python-gamebub-v109/request/results.json) records `status: PASS`, `actual_RTL_run: true`, frozen source hashes, commands and original negative assertion logs. Full canonical integration and native timing remain unqualified by this focused result.
