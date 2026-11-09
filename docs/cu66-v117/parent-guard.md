# V117 LIVE parent public observation guard

The isolated guard candidate fixes a LIVE wrapper boundary mismatch without changing the decoder's private one-edge registered cancellation schedule. The first guarded byte/fast RTL run passed every bench check, but its caller failed on a JSON type mismatch; a fresh full byte/row retry is active. Full guarded qualification remains pending. No existing A/B wrapper, test, selector or source was changed.

## Actual evidence and decision

The original B LIVE byte/fast attempt [20261109T115949823661Z](../../experiments/python-gamebub-v117/throughput-study/live-parent/attempts/20261109T115949823661Z/receipt.json) strictly compiled and executed actual RTL, then failed the original `cancel leaked local traffic` check. Its failed receipt remains preserved with `actual_RTL_run=true`.

The independent diagnostic-only exact replay [20261109T120816086878Z](../../experiments/python-gamebub-v117/throughput-study/live-diagnostic/attempts/20261109T120816086878Z/receipt.json) retained the byte-identical wrapper and original assertion, adding only a flushed observation before the failure. At cycle 195383, the actual wrong-token candidate ACK raised `join_error=129`, `fault_cancel=1`, `producer_fault_cancel=0`, `parent_transfer_enable=0`. Exported `residual_valid=1`, `residual_ready=1`, plane0/tile1/index3 matched the expected residual position. Raw transform valid was1, the older canonical owner was READY and the younger owner FILL. `frame_read_req=0`; external input/cache/memory/reference grants were all0. The join retained its real physical debt. The diagnostic also failed honestly and remains preserved.

This is the first edge between immediate parent revocation and the existing registered producer cancellation. External new-request masking already worked. The exported residual observation still exposed a private transfer during that edge. The original wrapper exported both residual-valid and local replay-request views directly, although it already masked external request grants.

The first actual guarded attempt [20261109T123151283675Z](../../experiments/python-gamebub-v117/throughput-study/live-guard/attempts/20261109T123151283675Z/receipt.json) is preserved as `FAIL`, `actual_RTL_run=true`. Its strict byte/fast simulation emitted `parent_guard_verdict: TEST_PASS`: 3,938,290 checked edges, exactly one parent-fault gap edge and one independently validated private residual handshake, 33,384 raw replay requests matched by 33,384 exact responses, and no remaining raw replay lease. All original byte/ACK/hash/C2/HUD assertions and the actual II1/spatial-overlap checks also passed in that simulation. The caller then compared the emitted numeric JSON `raw_local_pending: 0` with Python `is False`; this is a caller type bug, not an accepted-debt relaxation or an RTL failure. The failed receipt and its raw terminal success remain retained rather than relabeled.

The new independent [final B runner](../../scripts/cu66-v117/live_guard_final/qualify_b.py) requires `type(value) is int and value == 0`, matching the actual C++ ostream representation while still rejecting nonzero debt and Boolean/type substitutions. Its source closure pins its own runner file, avoiding an unused C runner edit invalidating B evidence. The [final C runner](../../scripts/cu66-v117/live_guard_final/qualify_c.py) applies the same correction with the C composition. RTL, benches, assertions, original runners and physical-response semantics remain unchanged. A fresh final B retry has started; no aggregate guard PASS is claimed until its required variants and finite-service profiles complete.

## Exact candidate scope

[Guard wrapper](../../fpga/experiments/cu66-v117-live-guard/cs88_live_v91l.sv) separates `producer_residual_valid` and `producer_frame_read_req` from the two exported observations, then applies the existing `parent_transfer_enable` mask to those exported views. It does not feed those masks back into the producer, inverse, reconstruction, local replay RAM, or response paths. It does **not** stop the one permitted private work edge. Physical memory, reference and candidate ACKs remain uncensored so accepted leases can drain.

The intended contract is explicit: public parent observations revoke immediately; private work can continue at most on the first parent-fault edge before the registered kill is visible, and is subsequently discarded. After registered or external reset/abort cancellation, raw residual offers and raw replay requests must be absent. This change must not be described as preventing all internal work immediately.

## Independent verification

The original functional `need` statements and original RTL assertions are retained exactly, including the original cancellation check. Reversible derivation and whole source snapshots bind the candidate to its frozen B verification ancestor. The added checker reads actual raw producer wires independently of the masked observations.

- While enabled, both public observation views must match actual raw traffic. During revocation they must be zero; all external grants remain zero, and parent faults expose no new candidate write, hash delivery, HUD acceptance or start grant.
- A raw private residual handshake is allowed only on the first parent-fault edge with registered kill still false and no external reset/abort. It must match independent arithmetic golden, complete frame/child/token/plane/block/tile/qcell/scale/index ownership and current stream order. At most one such sample is permitted; actual gap/sample counts are recorded. Different finite-service variants can legally have no sample on this edge.
- A separate raw local-read ledger runs every edge, including revoked edges. Every actual raw replay request owns its address, frame epoch and expected received byte. The following preedge must return exactly that response address/epoch/data. Unsolicited responses fail, each response releases precisely one lease, and accepted requests equal responses plus the current lease. The ledger never clears merely because parent fault/reset is asserted: the prior edge's actual registered RAM response remains observable before the reset/abort edge clears the producer registers. Responses observed during revocation and responses for private-gap reads are separately counted.
- Terminal success requires an empty raw read lease, exact request/response conservation and complete private-gap response accounting. Original byte/row request/ACK/hash/C2/HUD and whole canonical independent goldens, physical drain, wrong-ACK retention and clean retry checks remain active.

[Original guarded B runner](../../scripts/cu66-v117/live_guard/qualify_b.py) selects the exact frozen B eighteen-source composition; [original guarded C runner](../../scripts/cu66-v117/live_guard/qualify_c.py) selects the eventual C ingress-repair composition. They write independent `live-guard` areas and do not replace failed original B evidence. Both retain byte/row and fast/stalled finite-service controls, strict warnings/assertions, source-bound commands/artifacts, terminal records and resource/watchdog limits. C prerequisites must independently qualify before C is runnable.

## Limits

The guard wrapper is outside the routed producer component. No achieved full-parent clock, hardware 30fps, physical SDRAM behavior, ESP32 execution or validated under-10-ms decoding is implied. Current proof covers simulation of the declared observation boundary, independent raw private work and accepted debt under the stated finite-service model; actual guarded results must be cited once available.

## Frozen candidate pins

- `fpga/experiments/cu66-v117-live-guard/cs88_live_v91l.sv` — `0f649831a4143d6afd8983b8f4b72eb1b6caeeee7a26ad5b8ec0d4545046ff4d`
- `fpga/experiments/cu66-v117-live-guard/tb_keyframe.cpp` — `cad383becd5a9d20a8722a4ec78b0cb5ae86d7967abdbfac0a4857c6b1da4b18`
- `fpga/experiments/cu66-v117-live-guard/derivation.json` — `f5eee585b212dd475a0dc0b17dc254d24fdffaf88b2e73e5482bc4da1943da60`
- `scripts/cu66-v117/live_guard/qualify_b.py` — `8313512ecd5367a241ff8574e807998f4656835c95b3b48efcc0678ea0bc63b6`
- `scripts/cu66-v117/live_guard/qualify_c.py` — `176fb5ba1a6503c33527c7f990b497c21d36f46b9aa7a9a7e0f9b3da87a052a8`
- `scripts/cu66-v117/live_guard_final/qualify_b.py` — `c4f84c3a4ed6eac8c0b42c5e3924b641745cb899dda9a5f7f71ad495065cb93c`
- `scripts/cu66-v117/live_guard_final/qualify_c.py` — `849af0e0d105045577c967664503d894fbe96226b43ee201a53ba325ae913525`
