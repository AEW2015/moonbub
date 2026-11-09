# Reproducing V116 measurements

Use the recorded source revisions and local pinned Docker images. The runners
require Python, Docker access, the Verilator 5.020 tools image, and (for native
runs) the existing Vivado 2026.1 container/tool mount with Artix-7 support and a
legitimate license. Image IDs and exact commands are retained in every receipt.
Build workspaces use `/home/lori/gamebub-build/cu66-v69`; native tools use
`/home/lori/acorn-nexys4-ddr/tools`. Port machine paths explicitly and regenerate
receipts/audits when running on another system. Never copy license contents into
a report, command line, or repository.

The simulation image's build recipe is the existing
[V69 tools Dockerfile](../../fpga/experiments/cu66-v69/build-env/Dockerfile).
Its package repositories are not a historical package lock: rebuilding it may
produce different tool versions and an image ID that the frozen runners reject.
Use the recorded image for an exact replay, or create a separately reviewed
port with newly recorded tool versions, image pins and receipts.

Root serialized dispatch and allowed at most two heavy jobs at a time. Each job
uses two CPUs, one compiler job, 8 GiB memory and no additional container swap.
Host available-RAM, memory-pressure and combined-use gates remain active.
Do not start all commands below together.

## Initial A source

Run the independent focused suites first:

```sh
python3 scripts/cu66-v116/rice/qualify.py --run --suite all
python3 scripts/cu66-v116/admission/qualify.py --run --root-grant ROOT_GRANTED_ADMISSION
python3 scripts/cu66-v116/rowjoin/qualify.py --run
```

Then run the body and peer proof. They can occupy the two study slots. The body
runner defaults to sequential seeds; Root's archived paired-slot grant was
issued only after the peer receipt passed and its containers exited.

```sh
python3 scripts/cu66-v116/peer.py --run
python3 scripts/cu66-v116/spatial.py --run
python3 scripts/cu66-v116/live/qualify.py --run --root-grant ROOT_GRANTED_LIVE
```

The LIVE default runs both byte and row variants, each with fast/stalled service.
Its original byte checks remain the control. A chosen `--variant byte` or
`--variant row` diagnostic records precisely which variant was qualified.

## Combined B source

B retains A's Rice, admission, row join, fixtures and original oracles. Its
additional two focused suites validate selected abort-target feedback and the
held-payload domain predicate, including the original exhaustive metadata tests:

```sh
python3 scripts/cu66-v116/control-b/qualify.py --run --suite all
python3 scripts/cu66-v116/domain-b/qualify.py --run --root-grant ROOT_GRANTED_DOMAIN --legacy-exhaustive
python3 scripts/cu66-v116/peer_b.py --run
python3 scripts/cu66-v116/spatial_b.py --run
python3 scripts/cu66-v116/live-b/qualify.py --run --root-grant ROOT_GRANTED_B_LIVE
```

LIVE-B runs the actual new source map and additionally requires its case,
fence, service and verdict records to match the immutable selected A controls.
It reruns the physical-owner/value/hash models; it does not reuse A's execution.

## Final C source: current checkpoint and commands

At this documentation checkpoint, C's focused, main/body, transport and peer
proofs and all four C LIVE cases are **PASS**. C125 native completed with
**setup FAIL**, WNS −1.847 ns; hold/pulse/routing checks pass. A partial
simulation or provisional attempt receipt is not a final PASS. In particular,
the main/peer runners initialize their mutable receipts with a pessimistic
`FAIL` status; terminal evidence and final selectors distinguish a completed
failure from an attempt still executing.

| C qualification | Evidence/status at this checkpoint |
| --- | --- |
| Focused generic and actual-caller pairs | `PASS`, two seeds each; [selector](../../experiments/python-gamebub-v116/record-c/results.json), [receipt](../../experiments/python-gamebub-v116/record-c/attempts/20261109T074445819704Z/receipt.json) |
| Main/body plus custom transport | `PASS`, attempt `20261109T075531068137Z`; [selector](../../experiments/python-gamebub-v116/control-c-study/spatial/results.json) |
| Full-top peer faults, physical debt and retries | `PASS`, attempt `20261109T075522748891Z`; [selector](../../experiments/python-gamebub-v116/control-c-study/control-peer/results.json) |
| C125 native route | Completed attempt `20261109T081825861048Z`; [receipt](../../experiments/python-gamebub-v116/control-c-study/native/20261109T081825861048Z/receipt.json), setup FAIL, −1.847 ns WNS |
| C LIVE byte/row parent | `PASS`, attempt `20261109T081648108920Z`; [selector](../../experiments/python-gamebub-v116/control-c-study/live-parent/results.json), all four fresh byte/row fast/stalled cases match A records |

C retains B's caller, abort-owner feedback and held-domain flag, together with
A's Rice/admission sources. Its only additional production replacement is
`fpga/experiments/cu66-v116c-record/packed_scratch_v91g2.sv` (SHA256
`1ac70499489acbdb00e682696a5783cf178c3e703e3b16d2138f275f7de59839`).
It separates pending-record payload capture from publication control: two
RTL banks with no explicit reset assignments (nominally 67 bits each) capture a prospective complete tuple into the
inactive bank, while the original good-record branch alone switches the visible
bank. The logical pending capacity remains one. Ports, readiness, public cycles
and the old raw `pending_record`, `pending_bytes` and `pending_position` views
are unchanged. The focused generic and real-caller pairs prove those same-edge
views through invalid offers, stalls, reset/current/foreign abort, response
errors, EOF and retry, with all old assertions retained. They do not establish
new routed timing or complete-parent qualification. See [record-c.md](record-c.md)
for the representation, initial two-state scope and exact proof contract.
Completed synthesis retains 112 payload FFs after constant folding. Of these,
44 use format-derived reset pins to implement literal data zeroing; the other
68 have no set/reset net. Both banks use local selection enables. Thus "no
explicit RTL reset" does not mean every mapped reset pin is tied off.

The frozen C reproduction commands are:

```sh
python3 scripts/cu66-v116/record-c/qualify.py --run --suite all
python3 scripts/cu66-v116/peer_c.py --run
python3 scripts/cu66-v116/spatial_c.py --run
```

All three commands completed at the checkpoint above; these are reproduction
recipes, not requests to launch duplicates. Root owns
the two global heavy slots. Body seeds are sequential by default; any
`--pair-grant-file` must be a fresh source/runner-bound Root grant satisfying
the runner's completed-peer checks.

Successful C selectors will be written under:

```text
experiments/python-gamebub-v116/record-c/results.json
experiments/python-gamebub-v116/control-c-study/control-peer/results.json
experiments/python-gamebub-v116/control-c-study/spatial/results.json
```

The recorded C125 preparation recipe, executed after those actual proofs passed, was:

```sh
python3 scripts/cu66-v116/native_c.py --trial integrated-125
```

Preparation prints the exact fresh `preflight.json` path and SHA. After its
independent source-bound audit passes, Root dispatches with the actual paths:

```sh
python3 scripts/cu66-v116/native_c.py --run --preflight "$C_PREFLIGHT" --audit "$C_AUDIT"
```

Here `C_PREFLIGHT` is the path printed by that preparation and `C_AUDIT` is the
reviewer's audit for that exact card; neither is an archived audit or a guessed
future path. C125 is the **fourth and last allowed initial source/clock trial**:
A125, A100 and B125 have consumed the preceding three. The CLI offers no C100
trial. This is the existing global budget, not an additional trial or a
negative-reroute allowance. C125 has now completed negative, so all four initial
trials are consumed and no positive fresh repeat is eligible. These commands
document the executed recipe; the frozen campaign rejects another dispatch.
A separately authorized future study must retain this evidence and declare its
own new policy and provenance rather than erase reservations or reuse an audit.

Once the C composition is selected and Root grants a slot, C LIVE's exact
default command is:

```sh
python3 scripts/cu66-v116/live-c/qualify.py --run --root-grant ROOT_GRANTED_C_LIVE_SLOT
```

The default runs byte and row joins with fast/stalled profiles. A diagnostic
`--variant byte` or `--variant row` records its narrower scope. C LIVE requires
the actual C18-source map and reruns the accepted-byte, ACK ownership, C2/HUD,
root/seal, completion-fence and abstract-publication checks against the frozen
A controls. All four C cases completed and matched the A records exactly.
Its selector is `experiments/python-gamebub-v116/control-c-study/live-parent/results.json`.

## Native timing

A's 125/100 MHz, B's 125 MHz and C's 125 MHz routes are completed negative
measurements. Their routed WNS values are respectively −2.219, −0.108,
−2.238 and −1.847 ns. The global policy forbids unchanged negative reroutes and
strategy/constraint searches. No native trial remains eligible in this campaign.

An independent reviewer must validate the fresh preflight's source snapshots,
recipes/tooling, functional proofs, clock-before-synthesis, image ID, resource
and trial budget, unchanged constraints and hardware/bitstream scope. Supply
that source-bound audit and fresh preflight to `native_c.py --run --preflight
... --audit ...`. Do not reuse an archived audit for a newly prepared card.
The runner rechecks the card, audit, policy, source and budget before dispatch.

A native pass requires nonnegative routed setup/hold/pulse slack, zero failing
endpoints/routing errors, correct clock and internal coverage, plus the declared
fresh positive repeat. This is decoder-body OOC evidence; complete-parent I/O,
CDC/memory/display timing and sustained hardware presentation remain separate.

`python3 scripts/cu66-v116/collect.py` refreshes the measurement index. Retain
failed attempts and interpret only their actual terminal statuses. No container
exit code or compile result alone is a functional or physical milestone pass.
