# V115 registered helper preparation and dequant visibility

The V114 125 MHz worst path ran from dequant output into an IDCT DSP input,
with 17 logic levels (12 CARRY4s/five LUTs), despite AREG=1. V115 changes the
source before that input and local dequant storage controls. It does not add
DSP lanes or assert a multiplication-speed improvement.

## IV115.1 contract

Two source aliases change: `cu66_dequant.sv` and `cu66_idct8x8.sv`, under
[`fpga/experiments/cu66-v115-inverse`](../../fpga/experiments/cu66-v115-inverse).
The V113 inverse-stream wrapper remains byte-for-byte unchanged. Both helpers
add one private `PREPARE` edge after actual input acceptance. Consequently an
ordinary inverse tile has two additional service cycles (one per helper).
Content, accepted input order, output order and ownership are preserved; exact
old public-cycle/invalid-diagnostic timing is not claimed. Public ready/valid
remain immediately suppressed on reset/abort, and held valid outputs retain
their entire value/error/id tuple.

IDCT captures eight local groups of range, nonzero and AC-nonzero flags with
the retained source tile. `PREPARE` reduces those registered flags and fills
first operands from retained data, replacing the live dequant→validation/
zero/DC/operand-selection cone. The signed20 range is exactly ±522,240.
A short sign/bit predicate is independently checked against the original signed
comparisons. No transform constants, signed sample widths, accumulation,
rounding, clipping or arithmetic scheduling changes.

Dequant similarly captures grouped coefficient-domain/zero flags and the scale
flag with its input. Its 64 local 20-bit payload words no longer have reset or
whole-tile-clear enables: eight group visibility bits preserve the existing
zero contents on reset, invalid and zero cases. A speculative write on a kill
edge is private; visibility clears and a future nonzero output cannot become
valid before all eight groups have been completely replaced. Other owned
state and fault behavior retain reset/cancel. This is a specific payload change,
not a blanket removal of resets.

Flags and source payload capture only while IDLE, where they are unowned.
Their consuming PREPARE state follows an accepted input edge; later live-input
changes cannot change the owner. Original operand assertions remain enabled,
and added assertions compare captured preparation against original predicates
and require a complete visible output before dequant validity.

## Executed evidence

The [selected result](../../experiments/python-gamebub-v115/inverse/results.json)
is PASS. Two seeds, 115101 and 115102, each execute:

| Campaign | Actual scope per seed |
| --- | --- |
| Unchanged V113 inverse oracle | 48 boundary cases and 25 directed checks; original coefficient/dequant/residual goldens, accepted E+2 commit ledger, finite result slots, held final output and abort/reset/retry |
| Direct helper probe | 58 dequant transactions and 116 IDCT transactions; accepted tuples poisoned immediately afterward, output stall/hold checks |
| Domain identity | All 1,048,576 signed20 bit patterns through the actual RTL range function, compared with independent signed integer bounds |
| New-state cancellation | 30 reset/abort phase cases and 30 clean retries, including PREPARE, all ten active/output IDCT phases and dequant preparation/early/middle/final-write/held-output phases |

The direct helper test uses an independent full two-pass integer matrix
reference. Its values first match all valid frozen boundary goldens, then test
zero/DC, signed limits, invalid limits and random full tiles. The original
inverse bench is not edited. The reversible
[edit recipe](../../fpga/experiments/cu66-v115-inverse/edit-recipe.json)
recovers both original helper sources exactly; source snapshots, strict compile
logs, completed verdicts, compiler binary hashes and all input files are retained.
No original assertion/check is removed or relaxed to obtain PASS.

Reproduce from the repository root, with a Root heavy-job grant:

```sh
python3 scripts/cu66-v115/inverse/prepare.py
python3 scripts/cu66-v115/inverse/qualify.py --run
```

The established standalone Verilator 5.020 backend is retained; this is not a
new Vivado-integrated simulator backend. Commands bind the tools image content
ID, `--assert -Wall`, owned C++ `-Werror`, one compiler worker, two CPUs and
8 GiB memory with the combined memory-plus-swap ceiling also 8 GiB. Host
available-RAM/PSI gates and finite compile/runtime watchdogs remain active.
There was no failed attempt in this campaign.

Native source-bound timing, physical primitive/control-set effects, full
canonical/transport composition, full-parent I/O/CDC/memory/display,
Sunshine/ESP32 execution, hardware 30 fps and validated under-10-ms decode are
separate gates. These helper tests do not establish any of them. In particular,
the added service cycles are a latency cost until routed timing and the complete
service ledger show a useful overall result.
