# V55 Xtensa optimization warning map

## Scope and compiler evidence

This read-only map is based on the preserved isolated object compile of the exact V55 `native/endpoint.cpp`. Xtensa ESP32-S3 GCC 14.2.0 is at `C:\Users\lavat\.espressif\tools\xtensa-esp-elf\esp-14.2.0_20250730\xtensa-esp-elf\bin`. Both failed attempts used `-std=c++17 -mlongcalls -ffunction-sections -fdata-sections -fexceptions -fstack-usage -Wall -Wextra -Werror -c`; the sole changed option was `-O2` or `-O3`. The preserved result reports `-Os` return code 0, `-O2` and `-O3` return code 1, and each failed with `-Werror=maybe-uninitialized`. See the publish audit result and raw logs listed in `bindings.json`.

## Diagnostic locations and common path

Both `O2/compile.stderr.log` and `O3/compile.stderr.log` contain the same three distinct promoted diagnostics:

| Reported location | Expression/function named | Inlined source path |
|---|---|---|
| GCC 14.2 `bits/basic_string.h:228:28` | `std::basic_string::_M_data()` pointer `_M_p` may be uninitialized | `std::basic_string::_M_is_local` → `_M_dispose` → destructor → `cu66_partition::Status::~Status()` (`hud_gate.hpp:45`) → `HudGate::~HudGate()` (`hud_gate.hpp:53`) → `std::optional<HudGate>` destruction/reset → `v34::Endpoint::~Endpoint()` (`endpoint.hpp:17`) → `v34_hud_destroy()` (`endpoint.cpp:15`) |
| GCC 14.2 `bits/basic_string.h:288:21` | `std::basic_string::_M_destroy()` capacity may be uninitialized | Same optional `Status.failure` string destruction chain |
| `bounded.hpp:32:40` | `cu66_port::Alloc<char>::deallocate()` reads `owner` which may be uninitialized | Same `Status.failure` string cleanup invokes the custom character allocator's deallocate; inlined through `std::allocator_traits`, `_M_destroy`, `_M_dispose`, string destructor, Status/HudGate/optional/Endpoint destruction and `v34_hud_destroy()` |

Thus the observed promoted warnings at both optimization levels converge on **one source ownership path**: the `Status::failure` custom-allocator string as `HudGate` is destroyed through `Endpoint` teardown. The standard-library reports identify string pointer/capacity fields; the project report identifies the allocator owner. The log does not show a distinct warning in another endpoint operation or an unrelated helper. This is a report-path classification, not a proof that the cause is one defect or that any emitted field is actually uninitialized at runtime.

## Relevant source ownership and lifetime branches

- `bounded.hpp:14-22`: `Arena` owns accounting and allocation/release operations. `Arena::release` calls `free` and subtracts live bytes.
- `bounded.hpp:24-25`: thread-local `active` arena and `Scope`, which saves/restores it.
- `bounded.hpp:26-34`: `Alloc<T>::owner` is declared at line 28; the default allocator constructor captures `active` and throws if absent (line 29); converting construction copies `a.owner` (line 30); `deallocate` dereferences owner (line 32).
- `hud_gate.hpp:45-52`: `Status` owns `cu66_port::String failure` at line 51. `HudGate` embeds `Status status_` at line 56 (inspect adjacent lines in exact source); status assignments include reset/defaulting and failure-message assignments in its prepare/failure branches.
- `endpoint.hpp:13-17`: `Endpoint` declares `arena` before `optional<HudGate>`; constructor creates the gate inside an arena `Scope`; destructor creates a `Scope` and explicitly calls `gate.reset()` before the `Endpoint` members undergo their automatic reverse-order destruction.
- `endpoint.cpp:14-15`: `v34_hud_create` constructs `Endpoint`, and `v34_hud_destroy` deletes it, the inlined call site in both diagnostics.

These facts are consistent with the preserved README's stated uncertainty. The constructor and explicit reset provide source context; neither alone settles the optimizer's dataflow analysis or the runtime behavior. The warning alone is not evidence of undefined behavior, and it is not evidence of a false positive.

## Finding

O2 and O3 failures all originate along the same optional `Status.failure` string cleanup path, with the library's string internals and `Alloc<char>::deallocate` represented in each warning chain. No independent warning site appeared. Cause remains unresolved; do not suppress `-Werror`, infer UB, or call the warning a false positive from this map. A future investigation should first use a minimal optional/custom-allocator lifetime reproducer and the already suggested sanitizer/fault tests, while retaining the current strict warning policy.

## Source identity

The exact eight native source files and hashes from the audit's `result.json` are repeated in `bindings.json`; their before/after hash sets were equal and `source_changed` was empty. This report is a read-only interpretation of those records and preserved compiler logs. No compilation or source change was made for this map.
