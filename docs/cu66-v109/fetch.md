# V109 request-edge fetch address ownership

The fault-only routed V109 report at `experiments/python-gamebub-v109/native/20261108T112057270069Z/reports/route-setup-paths.rpt` measures the new limiting path from ingress fetch_index[3] to fetch_bytes[8][0] CE: −1.589 ns slack, 11.300 ns data delay (3.541 ns logic, 7.759 ns routing), fourteen levels and four CARRY4s. The cone recomputes the request address and compares it with the registered RAM response before enabling byte storage.

The only production substitution is `fpga/experiments/cu66-v108-capacity/br88_packet_ingress_sync_v91h.sv`, SHA `6514a5f2e2c1b597dfb2cddffeb3e637034d5fe79cdb07861ecd1081034c83c6`, to `fpga/experiments/cu66-v109-fetch/br88_packet_ingress_sync_v91h.sv`, SHA `4d6a16d0b89aa067fe3e7acc01351ea0bacac694cc63fb681a1471ee4683d044`. Its historical native alias remains `fpga/experiments/cu66-v91h/br88_packet_ingress_sync_v91h.sv`.

A private unreset 32-bit register captures the original full-width fetch_address whenever state is FETCH_REQ, independently of current request acceptance or cancellation. The actual request still uses the original live address, bounds checks and cancellation fences. An accepted request enters FETCH_WAIT on this edge and the RAM registers its response on the same edge. Fetch base/index/kind, size and descriptor length cannot change between this accepted request and its response consumption. The cached address therefore belongs to that existing request and is available one edge before byte capture, with no new public cycle.

Only two production comparisons use the cached address: prefix_header_capture and the FETCH_WAIT mismatch branch. Public stage_read_addr, stage_rsp_addr, request bounds, RAM access, epoch checks, byte storage, counters and request order retain their original code. The original stale staging response assertion still compares ram_addr with the live original fetch_address. An additional assertion independently requires the cached expected address to equal that live expression on an owned response. Cancellation may write an unowned private address; no response or output can become owned through it.

The reversible edit recipe reconstructs both directions. Complete original/new ingress adapters rename only module declarations and the miter compares every public port, including V108 capacity outputs and invalid/debug/counter values. The existing capture oracle retains every check, expected count, flush/commit case, mutable external metadata hold and six expected negative subprocess rejections. Its manually forced WAIT fixtures initialize the added private expected address from their explicitly prepared prior request (`base0+index`); this initialization never copies the deliberately incorrect response address or epoch.

The additional whole-ingress driver uses actual RAM requests/responses and a separate address/epoch scoreboard. It decodes independent sparse/raw coefficient goldens from existing dense fixtures, covers header 41→42 and final trailer index45, descriptor index6, replay and RAW, full-width wrapped addresses and rejected high addresses, metadata holds, mutable live context ports and abort/reset/restart at request and response edges. Every public output is checked before and after each clock edge. No original oracle is weakened.

Reproduce source preparation and qualification:

```sh
python3 scripts/cu66-v109/fetch/prepare.py
python3 scripts/cu66-v109/fetch/qualify.py
python3 scripts/cu66-v109/fetch/qualify.py --run
```

The explicit run uses Verilator assertions and strict warnings, C++ `-Wall -Wextra -Werror`, two seeds, 8 GiB including swap, two CPUs and one build job. This document initially records preparation; actual qualification status is recorded by the selected receipt. No native timing success or hardware performance is claimed.

Actual focused RTL qualification completed: **PASS**. The strict complete-body ingress compile produced zero Verilator warnings. Both existing capture seeds passed all 1,728 prepared cases, 128 high32 metadata owners, eight actual RAW header packets, capture/flush/commit cancellation cases and 2,312 held metadata edges per seed. All six negative epoch/address subprocesses stopped at the retained original `stale staging response` assertion with capture disabled.

The two new whole-ingress seeds passed 15495499 exact public cycles and 1509288 independent coefficient comparisons. Each ran 76 complete packets, 36 request/response-edge cancellation retries, eight actual prepared address requests plus two bounds rejections, all four fetch purposes and every directed boundary. Request counts exceed consumed responses by eighteen per seed because eighteen accepted internal RAM reads were synchronously cancelled before their response was consumed; the independent scoreboard verifies those cancellations. All source hashes remained unchanged during qualification.

The [selected receipt](../../experiments/python-gamebub-v109/fetch/attempts/20261108T114928776297Z/results.json) has SHA-256 `5f2842b3c987b8b72b0b7b62bc5293829f005bb6b3647b0befab35ad94a0c862`. The [current selection](../../experiments/python-gamebub-v109/fetch/results.json) records `status: PASS`, `actual_RTL_run: true`, the complete frozen input hash map and the original assertion rejection logs. Full canonical integration and native timing remain separate qualification steps.
