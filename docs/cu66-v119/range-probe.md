# V119 standalone signed16 range probe

This experiment isolates the proposed replacement for the signed 16-bit range
predicate `-2048 <= raw <= 2048`. The combinational RTL in
[`range_probe.sv`](../../fpga/experiments/cu66-v119-range-probe/range_probe.sv)
accepts when `raw[15:11]` is all zero, `raw[15:11]` is all one, or `raw` is
`16'h0800`. The C++ bench independently converts each unsigned 16-bit pattern
to a signed integer and applies the original inclusive bounds. It checks all
65,536 patterns and then explicitly checks the nine signed endpoints.

The prior mathematical model in `scripts/cu66-v119/raw_range_model.py` and the
actual carry-cone interpretation in
[`checkpoint-diagnostic-results.md`](checkpoint-diagnostic-results.md) motivate
this candidate. Those records establish Boolean equivalence of the predicate;
they do not establish that this RTL maps or routes better.

## Run protocol

The Root coordinator owns dispatch. Preparation prints the exact command and
hashes without compiling:

```sh
python3 scripts/cu66-v119/range_probe.py
```

The coordinating agent dispatches the prepared run with the required label
`ROOT_V119_RANGE_PROBE` (a dispatch label, not an authorization secret):

```sh
python3 scripts/cu66-v119/range_probe.py --run --root-grant ROOT_V119_RANGE_PROBE
```

The runner uses the pinned Verilator 5.020 image
`sha256:b35d0961607ab885b8024ef37ebcac0c3a0d010af00fe6bbdbc63264079a49cf`,
`--assert -Wall` with no warning suppressions, C++17 with `-O2 -Wall -Wextra
-Werror`, one build job, and a container limit of two CPUs and 8 GiB RAM/swap.
Before each container it gates on at least 8 GiB available memory, PSI full
below 1, and combined memory use below 0.85. It stops on available memory below
4 GiB, PSI full at least 5 twice, combined use at least 0.90, or timeout. Each
attempt gets its own timestamped directory with source snapshots, source and
artifact SHA256s, commands, logs, resource samples, and a durable receipt.
Immediately before invoking the compiled RTL model, the receipt is persisted
with `actual_RTL_run: true`; failures remain recorded as `FAIL`.
Before each container, it also checks that fewer than two active Docker
containers have `gamebub-v11` in their names. It verifies the logged Verilator
version is 5.020 and rechecks all source hashes at attempt completion. The
terminal `experiments/python-gamebub-v119/range-probe/results.json` selector
points to the receipt and its SHA256. The dispatch label does not require OS
uid 0.

## Scope

This is only a standalone combinational predicate prototype. The existing
accepted/output qualifiers, mode selection, cancellation, owner, ready/stall,
packet rejection reason, and cycle chronology are outside the prototype and
remain explicit obligations for any later integrated candidate. This does not
select a source composition or define pipeline Source B. It makes no clock,
physical timing, resource improvement, latency, FPS, or hardware claim. No
production RTL or native flow input is modified by these files.

## Executed standalone result

The Root-dispatched attempt `20261109T180259520162Z` completed with status
`PASS`. Verilator reported `5.020` (`2024-01-01 rev (Debian 5.020-1)`); the
receipt records zero exit status for version, compile, and model invocation,
`--assert -Wall`, C++17 `-O2 -Wall -Wextra -Werror`, one build job, and no
assertion downgrade. The model reported
`TEST_PASS patterns=65536 endpoint_checks=9 mismatches=0`. The C++ oracle
interpreted each pattern as signed16 and compared against inclusive integer
bounds. It separately checked −32768, −2049, −2048, −1, 0, 2047, 2048, 2049,
and 32767.

The receipt pins the RTL, bench, and runner hashes and records matching final
source hashes. The results selector is `experiments/python-gamebub-v119/range-probe/results.json`;
the terminal audit at `experiments/python-gamebub-v119/audit/range-probe-terminal.json`
records the receipt, selector, logs, binary hash, exact commands, and review
checks. This is executable Boolean equivalence evidence for this isolated
prototype. The surrounding qualifiers and chronology remain outside scope;
the run makes no integration or implementation-improvement claim.
