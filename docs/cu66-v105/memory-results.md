# V105 mode-store template experiment

The isolated mode-store candidate passes **316,440 clocked comparison cases across two seeds** and independent Python replay of every recorded event. It preserves all 8,100 two-bit entries and the existing one-clock FINISHED lookup. Native mapping/timing and complete packet qualification are separate root-owned lanes; this result establishes bounded behavioral equivalence for explicitly prepared states.

## Change and composition

Original: `fpga/experiments/cu66-v102-memory/cs88_admission_v91i2a.sv`, SHA-256 `c300f1bd819a906bfebd64e47648fe08d71f072d88d25cccc15c9a197d305187`.

Candidate: `fpga/experiments/cu66-v105-memory/cs88_admission_v91i2a.sv`, SHA-256 `cf4a21871436284fa542911b17c0f1f82dea133b01705529e3f748f68e6ad3de`.

The seven-edit recipe is `fpga/experiments/cu66-v105-memory/edit-proof.json`, SHA-256 `e83013f017ac22467c3a46144bf12df6912dd393f45bd616c33823d06c4c58e5`. It inserts the mode write mux/read process before `assign replay_ready`, extracts exactly five old write statements and moves only `lookup_mode` from the original compound lookup. The `lookup_scale` access remains in its original process. All tile assignments and the entire `residual_tile` task remain byte-identical. The recipe deliberately retains old whitespace around removed statements so exact replacements remain independently composable with the coordinate-cache experiment.

Write priority is clear, key, mixed, then group; state exclusivity means priority does not change legitimate transaction behavior. ACTIVE_CLEAR keeps `active_index!=8100`, KEY_TILE keeps `tile!=tile_count(plane)`, and all address additions retain full 32-bit `tile` arithmetic before the original 13-bit cast. Reset/start/abort suppress every write and lookup, while `lookup_mode` retains its previous value. No RAM reset, device attribute, capacity change, latency change, invalid-address guard or external SDRAM timing assumption is introduced.

## Focused clocked results

Final receipt: `experiments/python-gamebub-v105/memory/attempts/20261107T233727102520Z/receipt.json` (SHA-256 `0418df38c68b8cfc0fddef0a1425ae3624cdd1e9b033ef436b9ca22956e992b6`). The pointer is `memory/probe-results.json`; the independent replay is `memory/trace-audit.json` under that experiment area.

| Seed | Clocked cases | Clock edges | Mode reads | Mode writes | Guarded cases |
| --- | ---: | ---: | ---: | ---: | ---: |
| 105401 | 158,220 | 158,221 | 81,089 | 49,686 | 10,816 |
| 105402 | 158,220 | 158,221 | 81,094 | 49,633 | 10,886 |
| Total | **316,440** | **316,442** | **162,183** | **99,319** | **21,702** |

Both seeds cover every valid mode address during initial-state lookup, full clear, key writes, mixed zero/one writes, hidden/copy group writes and final complete-store comparison. The group-residual branch writes all **7,806** non-hidden full-grid tile positions; hidden positions correctly take the earlier hidden branch. Directed guards cover all 33 defined states and all eight reset/start/abort combinations, plus tile/group boundaries, empty/nonempty mode-bit cache and mixed-bit enable conditions. Random cases add 8,192 prepared trials per seed. A post-edge check validates the potentially touched word even when a write is suppressed, in addition to enabled-write, registered-read, held-output and final-array oracles.

The generated wrapper instantiates both **complete production modules** with only their module names changed. All **42 output names across 64 public port names**, including unpacked output arrays, are compared before and after every tested edge. The Python auditor reverses module renames and requires exact equality with pinned production sources; replays the mode-store oracle independently; verifies all trace artifact hashes, every event, all final 8,100 entries and the seven-edit recipe; and verifies preserved tile statements, residual task and declaration.

Reproduce from repository root:

```sh
python3 scripts/cu66-v105/memory.py
python3 fpga/experiments/cu66-v105-memory/audit_trace.py
```

The explicit existing backend is Verilator 5.020, `--assert -Wall`, with the existing `DECLFILENAME` exception required by module-renamed adapters. C++ uses `-Wall -Wextra -Werror`. Compilation uses two jobs, a 300-second watchdog; each simulation has a 120-second watchdog and an internal 300,000-case bound. The shared resource gate requires at least 8 GiB available RAM and memory PSI full avg10 below 1; swap alone is not the gate. Final compilation took about 5.1 seconds and simulations about 0.21/0.26 seconds. These are host test runtimes, **not FPGA decode latency**.

## Attempt ledger

All attempts are retained. The first runner bootstrap had incorrectly generated input/bench paths and stopped before tool execution (`20261107T233515307074Z`). The first actual strict compile (`20261107T233524217800Z`) rejected misleading C++ loop indentation; the harness was braced/formatted without relaxing warnings or changing RTL. `20261107T233539673683Z` passed; the final selected rerun added the immediate suppressed-write retention assertion. The offline auditor initially mistyped the non-hidden count; `audit-failures.json` records that failed expectation, now replaced by an independently computed sum over all valid coordinates. No RTL test failure is hidden or promoted to a pass.

## Native status and limits

The root-owned native memory build `native/20261107T233717813389Z` completed **synthesis only**, exit 0, with signoff open. Its completed primitive ledger verifies **one RAMB18E1 named `coefficients/admission/modes_reg`**, in addition to the unchanged 32 RAMB36E1 packet-store primitives. Admission LUTRAM use falls from 1,524 to zero. The full component changes from 49,040 to **47,482 LUTs**, 3,854 to **2,330 LUTRAMs**, and 34,689 to **34,672 FFs**, with DSP count unchanged at 28. It uses one additional RAMB18 and no additional RAMB36.

Same-stage synthesis WNS improves from −12.181 ns to **−11.728 ns** at 10 ns, so timing still fails the comparison target. No candidate placement or routing was performed. Primitive mapping, source-inference attribution, complete hierarchy rows and report/receipt hashes are recorded in `memory-inventory.md` and `memory/memory-inventory.json`. Treat these as synthesis-stage area/inference gains; select production sources only alongside the root-owned full-pipeline and composition evidence.

The focused test initializes backing storage and prepares internal parser states through verification-only `--public-flat-rw` access. It does **not** establish valid-packet reachability of every case, four-state equivalence, formal all-state equivalence, physical collision semantics, actual external-memory service, board 30 fps, or complete under-10-ms decode. Mode writes and FINISHED reads are exclusive in qualified source states; no physical read/write collision is claimed. Invalid lookup addresses 8,100–8,191 remain undefined and unqualified. Full fresh/canonical packet transactions, candidate composition, primitive mapping and routed clocks belong to the separate integration lanes.


## Follow-up composed route

The later locality variant completed component routing in `native/20261108T001325640117Z`, exit 0. The named mode RAM remains **one RAMB18E1 after route**, with admission LUTRAM usage still zero; exact primitive properties, source manifest and report pins are added to the memory inventory. Locality includes the coordinate/control/DSP edits as well, so its 47,966 LUTs, 34,827 FFs, 32 RAMB36 + one RAMB18, 28 DSPs and **−13.956 ns routed WNS** are composed-component measurements, not an isolated memory performance result. Timing and board service remain open.
