# V120 unselected context terminal-predicate proposal

This independent proposal targets the V119 emitted-count-to-error and emitted-count-to-memory-enable path families. It does not address every global parser reset/enable path. Root may add it to a later composition only when the isolated range candidate's actual final route justifies that choice.

The current V119 `br88_context` is the complete V113 geometry body. Two places evaluate the same wrapped 32-bit condition, `(emitted + 1) == target`: the final-symbol consumed-bit/error-7 check and the accepted-output completion branch. The new source prepares that exact predicate in one private `terminal_last_event` payload bit at the existing request phase.

## Existing-edge ownership

The hardware writer is enabled by REQ_DC, REQ_RUN or REQ_LEVEL state alone. It has no reset, global ready, cancellation or error qualification. An update on a canceled or stalled request phase is unowned. The original controller can enter WAIT only through the actual `req_valid && req_ready` handshake at that same edge, when the phase writer also captures the coherent emitted/target predicate. The bit holds in every WAIT and HELD cycle.

The request's emitted count, target and epoch cannot change before the corresponding WAIT/HELD consumption. A run response changes position and advances to REQ_LEVEL; the subsequent level request owns the same emitted/target pair again. Emitted changes only on an accepted held coefficient, after the final predicate has been consumed. Start/reset/abort changes the logical state and invalidates the verification owner before any new consumption. A new accepted request replaces the retired payload.

Verification-only ownership is born on the actual request handshake, independently of the broader hardware preparation enable. Every WAIT_DC, WAIT_RUN, WAIT_LEVEL and HELD edge checks that owner and its complete 32-bit epoch/emitted/target key, plus the wrapped predicate identity. These ghost fields are excluded from synthesis. No original assertion, error priority, output clear, public counter, parser input, request or geometry stage is changed.

The source adds one payload bit. Actual synthesis may optimize or replicate its implementation; native mapping must report what remains. It adds no public cycle, tile buffer, memory port, queue capacity or pipeline acceptance capacity. In particular, it is not a claim of zero added storage.

## Verification contract

The reference adapter is rebuilt from the exact current V119-selected context, not an older scalar context. Both models use the current selected V116 Rice parser. The complete original natural context checker remains byte-for-byte, including 55 corpus cases in eight configurations, 172 directed checks, held final output, bad input metadata, missing data, out-of-range values, run overflow, trailing-bit priority, abort/reset/restart phases and epoch replacement. The existing 8,064 start-domain checks, earliest response-edge checks and 4,260,918 independent geometry checks remain active. All public values, including invalid/debug/counter values, remain paired every clock.

The additive actual-context predicate fixture covers all three actual accepted request kinds. It begins from a real valid start, reaches REQ_DC/REQ_RUN naturally or decodes a real run before REQ_LEVEL, and deposits a coherent full-width emitted/target/epoch tuple in all three verification instances before the real request edge. It never forces state or the candidate cached bit. The fixture is a prepared arithmetic/ownership context, not a reachable gameplay-frame claim. It resets before completing an artificial frame.

Each seed requests 99,216 prepared captures: 912 endpoint/near-boundary cases and 98,304 random full-32-bit pairs. Counts include wrap from emitted 0xffffffff to target 0. Each of DC, RUN and LEVEL has 33,072 actual request captures. DC/RUN additionally hold the real WAIT phase without input for 264,576 total edges while caller ports are poisoned. The original literal terminal expression, the new generic/specialized captured bits and an independent unsigned C++ modulo-32 oracle must agree. Natural old tests separately cover held coefficients and all original first-fault cases.

`--flatten` and `--public-flat-rw` are explicit simulation-only options so these declared count/epoch deposits use the generated verification hierarchy. They do not change the Vivado hierarchy method or add a production interface. New ownership assertions remain enabled with `--assert -Wall`; no warnings are suppressed. C++ uses `-std=c++17 -O2 -Wall -Wextra -Werror` and one build job.

## Preparation and Root dispatch

The [production candidate](../../fpga/experiments/cu66-v120-context-terminal/br88_context.sv) has SHA256 `79db0404c4561e853c7019c27f076f86c0b8a7171f56b68f5cfae94759619f05`. Its reversible [recipe](../../fpga/experiments/cu66-v120-context-terminal/edit-recipe.json) retains every original RTL assertion block and exact source/adapter hashes.

```bash
python3 scripts/cu66-v120/context_terminal/qualify.py --run \
  --root-grant ROOT_V120_CONTEXT_TERMINAL
```

Root alone dispatches. The runner prepares a fresh model, retains source/compile/log/artifact hashes and failed attempts, and records `actual_RTL_run` before model invocation. It uses the pinned Verilator 5.020 image with 2 CPUs, 8 GiB memory, an equal 8 GiB total memory/swap limit, and the campaign's available-RAM/PSI/combined-use gates. No new package or license is required for this simulation.

Preparation does not select a physical composition or claim a passing run. Measured outcomes must be recorded in a separate results document after dispatch so this source-bound proposal document remains frozen. Any selected combined source must subsequently pass fresh full-component, actual transport, peer, guarded-parent and native timing qualification. A unit result alone establishes no 125 MHz clock, sustained hardware 30 fps or validated hardware decoding under 10 ms.
