# V102-A packet-memory read-template experiment

The isolated candidate makes admission's packet-memory read enable and address
selection explicit before one registered read. The control/metadata branches
retain stage-fetch priority over replay. The historical admission source is
unchanged. This experiment initially uses no RAM inference attribute.

## Frozen source change

- Original: [V91i2a admission](../../fpga/experiments/cu66-v91i2/cs88_admission_v91i2a.sv), SHA-256 `9c26be0c1fd8ec996c2bc94a97468b5f29a25b98f97f2a6e80b29be470a8243c`.
- Candidate: [V102-A admission](../../fpga/experiments/cu66-v102-memory/cs88_admission_v91i2a.sv), SHA-256 `c300f1bd819a906bfebd64e47648fe08d71f072d88d25cccc15c9a197d305187`.
- [Change manifest](../../experiments/python-gamebub-v102/memory/change.json) and [exact diff](../../experiments/python-gamebub-v102/memory/candidate.diff).

The only design change is the packet RAM's access template. Its existing byte
write and new single enabled read are in a separate `always_ff @(posedge clk)`.
Address selection remains `stage_read_req ? fetch_addr[15:0] : replay_addr[15:0]`;
the read enable remains stage fetch or accepted replay. Metadata latching
continues in the original branches, retaining the full 32-bit address and
receipt epoch. Logical depth/cap remains 49,152 bytes. Backing RAM, output data
and RAM address/epoch gain no new reset or initialization. Modes, scales,
CRC/parser state, validation, all 64 public port names and counters are unchanged.

Nonblocking read and write assignments retain old-data/read-first semantics
for a same-edge same-address RAM collision. Native synthesis must still be
checked for the actual primitive mode; behavioral parity alone does not prove
the configured FPGA primitive's collision behavior or device fit.

## Clocked actual-RTL comparison

**PASS:** both complete original and candidate admission modules are compiled
in one verification wrapper. Seeds `102401` and `102402` each pass **9,536
prepared-state cases and 9,537 rising clock edges**, including initialization:
**19,072 cases / 19,074 edges** total. All **42 public output names** match
before and after every tested edge; array outputs are compared as arrays.
RAM data, latched address and latched epoch also match an independent byte-array
model. At the end of each seed every one of the 49,152 backing bytes agrees
with that model in both DUTs.

| Per seed | Cases | Contract exercised |
| --- | ---: | --- |
| Five states × eight reset/start/abort masks × eight boundary addresses × four input/replay combinations | 1,280 | Ordinary guards, stage/replay selection and held output/metadata |
| Four out-of-range replay addresses × eight guard masks | 32 | Replay suppression without disturbing held RAM outputs |
| Same-address read/write collisions, explicitly verification-forced | 32 | Actual old-data/read-first edge behavior |
| Deterministic seeded mixed states, requests, addresses and guards | 8,192 | Mixed reads/writes, suppression, address/epoch latch and hold |
| Total | 9,536 | |

Observed accepted reads/writes are 381/152 for seed 102401 and 401/145 for
seed 102402. Each seed exercises exactly 32 same-address read-first collisions.
The probe checks first/last addresses, 16-byte boundaries, cache-line-style
boundaries and disabled/canceled controls. It prepares internal state and
initial memory explicitly, then advances the actual RTL clocks.

**Reachability boundary:** ordinary admission states fence accepted receive
writes from stage/replay reads. The collision cases therefore use clearly
marked verification-only `force` controls on `stage_write` and
`stage_read_req` in both DUTs while holding state IDLE. These are actual RAM
operations but not reachable packet-interface transactions. The other cases
also prepare states directly; this probe is not a complete legal packet
admission sequence. The separate root-owned fresh/historical pipeline
regressions provide the transaction-level lane.

Backend: retained Verilator 5.020, two-state behavioral RTL with `--assert
-Wall --public-flat-rw`, GCC C++17 `-O2 -Wall -Wextra -Werror`, and build `-j 2`.
Only `DECLFILENAME` is disabled for the verification-only module renames. No
functional assertion, candidate warning or checker is disabled to obtain PASS.
The wrapper adds output comparisons and collision overrides, without changing
candidate production code.

The [selected probe](../../experiments/python-gamebub-v102/memory/probe-results.json)
binds an immutable attempt with the executed runner, generated wrapper, actual
original/candidate source copies, bench, strict compile transcript, two terminal
`TEST_PASS` records, binary hash and complete compressed traces. The
[independent trace audit](../../experiments/python-gamebub-v102/memory/trace-audit.json)
replays all **19,072 rows** through a separate standard-library Python RAM model,
checking old-data ordering, held data/address/epoch and guard suppression. Its
[reader](../../fpga/experiments/cu66-v102-memory/audit_trace.py) imports no producer
code and launches no FPGA tools.

## Retained verification failures

[Three failed attempts](../../experiments/python-gamebub-v102/memory/failed-attempts.json)
remain bound to their original receipts/transcripts:

1. The first compile rejected four `MULTIDRIVEN` warnings from using
   `always_comb` around verification `force/release` assignments. The wrapper
   was corrected to the event process `always @(probe_force_collision)`.
2. The next run found a pre-edge public-output mismatch because the bench's
   `BOTH(name, rng())` macro evaluated the random expression twice, preparing
   different receipt epochs in the two DUTs.
3. A diagnostic run retained the exact case-zero mismatch: old epoch
   `2700538554`, new epoch `2050733699`. The macro was corrected to evaluate its
   argument once before assigning both DUTs.

Only verification code changed. Candidate SHA-256 remained frozen throughout;
there was no candidate functional failure or warning-severity workaround.
The final strict compile and both complete runs pass.

## Reproduce and physical boundary

```sh
python3 scripts/cu66-v102/memory.py
python3 fpga/experiments/cu66-v102-memory/audit_trace.py
```

The runner uses `gamebub-cu66-v69-build`, repository mounted at its absolute
host path, and `/home/lori/gamebub-build/cu66-v69` mounted as `/build`. Every
attempt is new; external compiler binaries stay outside Git. Before each
command it requires at least 8 GiB available host RAM and memory PSI full avg10
below 1. Compile/run watchdogs are 300/120 seconds. No native Vivado or Yosys
job was launched by this focused runner.

Native inference/resource/timing and combined-candidate measurements belong
to the root-owned V102 physical experiment. This focused result establishes
bounded behavioral memory equivalence; it does not establish BRAM inference,
placement, routing, hardware frame rate or complete decode under 10 ms.
