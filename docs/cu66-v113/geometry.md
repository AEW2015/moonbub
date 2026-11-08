# V113 private context geometry preparation

Status: **focused strict Verilator PASS; source and proof frozen**.
No routed V113 result is implied.
The source starts at the actual Count `br88_context.sv` used in V112's native
18-source composition. Its original generic count guard and the caller-owned
`PREVALIDATED_EVENT_COUNT` specialization remain unchanged. This experiment
addresses the measured V112 125-MHz context selector to output-block path
(16 levels, 10.792 ns; WNS −2.844 ns), without claiming that a source edit
establishes a new clock result.

The candidate adds two private stages. At an existing `REQ_LEVEL` edge, four
byte quotient/remainder contributions are captured from the current full
32-bit position and captured band, alongside the low 16 bits of the emitted
ordinal. At the first `WAIT_LEVEL` edge the contributions are reduced, the
remainder corrected, and the final block/index registered. `REQ_DC` and
`WAIT_DC` use the same key lifetime, with the complete eight-bit band deciding
the original default `{emitted[15:0], 6'd0}` behavior. All payloads are private;
only their validity needs reset. Start, reset and abort revoke both stages.

The actual retained Rice implementation is
`cu66-v110-prefix/br88_rice_elastic.sv`, SHA-256
`c07d936e807a09ee332b5df4c3f743f88f284784fbcf1e704d1a8db770c33eac`.
At request acceptance E it enters PREFIX. The earliest prefix operation is
E+1, which enters SUFFIX. Even a zero-bit suffix executes SUFFIX at E+2,
registering the response; the context first consumes that response at E+3.
A zero-length stream instead reports truncation in PREFIX and is consumed at
E+2. Input offers have priority over prefix/suffix execution and can delay
these edges. Request stalls repeat the same coherent preparation. No inserted
idle cycle is assumed. A response reporting an error takes the unchanged
error path without consuming prepared geometry. When start and abort coincide,
the existing context abort/reset branch wins; Rice resets and its stream-start
input is masked by abort. The private validity reset has the same priority.

Every successful DC or level parser consumption asserts that preparation is
valid, its complete key equals the consuming context/band/position/ordinal,
and its result equals the original independent scalar uint32 division/modulo
geometry. The original Count assertions remain byte-for-byte. Public request,
response, held coefficient, invalid output payload, debug, error and counters
retain their original edges. Public latency changes by zero cycles.

The reversible [edit recipe](../../fpga/experiments/cu66-v113-geometry/edit-recipe.json)
and [preparation script](../../scripts/cu66-v113/geometry/prepare.py) retain the
exact production original and candidate hashes. Preparation renames only the
complete context bodies for the proof and exposes the existing combinational
geometry to the inherited checker. The independent scalar assertion is inside
the production candidate under the existing nonsynthesis guard.

Run the focused proof with:

```sh
python3 scripts/cu66-v113/geometry/qualify.py
python3 scripts/cu66-v113/geometry/qualify.py --run
```

The selected behavioral backend is strict Verilator with assertions and
warnings fatal. The pinned tools container is limited to two CPUs and 8 GiB
of memory, with its memory-plus-swap limit also 8 GiB. Compilation uses one
build job; every command has an in-container and host watchdog and host memory
gate. This is not XSim, gate-level timing simulation or hardware evidence.
The original proof sources are never edited.

The complete actual original and candidate context bodies run the retained
55 contexts across eight serial/parallel, 16/32-bit and stall configurations,
with 84,265 expected outputs per configuration. The inherited independent
coefficient/error/held-output/counter checker and its 172 directed checks
remain byte-exact. A separate unchanged count-domain start checker exercises
8,064 generic/conditional configuration starts. A new edge test exercises the
fastest zero-suffix success and zero-stream truncation in all four parser
modes. The actual pair is compared on every public observation, including
invalid cycles. The inherited 4,260,918-case independent geometry checker
remains active.

The separate stage probe contains the exact production functions and stage
block. It drives full-width keys, all 256 band values including DC/defaults,
quotient wrap and emitted low16 truncation boundaries, every isolated byte
value in each lane, request stalls, abort/restart, and 131,072 random full32
positions per seed. Its expected result uses independent C++ uint32 division,
modulo and a zigzag table. This separates full-width private arithmetic from
the narrower legal operational contexts; it does not weaken generic behavior.

Receipts, source snapshots, failed attempts and compressed geometry traces
remain under `experiments/python-gamebub-v113/geometry/attempts/`. After a
focused PASS, source and proof inputs are frozen for the root's full
composition check and any native timing dispatch. Bounded seeded simulation
is not formal equivalence over every possible history; a fresh full-composition
route is needed before any timing conclusion.


The [selected focused receipt](../../experiments/python-gamebub-v113/geometry/attempts/20261108T205255315701Z/results.json)
is SHA-256 `b0664949960475afabfca70bc28ed3c24328eb0ec2becff0a3a9fa72f3f196ca`.
It passed on its first attempt in 394.14 seconds. Both builds had zero RTL
warnings, all seven commands exited zero, and the independent final read-only
hash check matched every pinned source. Candidate production SHA-256 is
`4eefd41198a0fcbfd80648e702a42f179315f7378969863c778bd06686ff6775`.
No source or proof edits followed this PASS.

| Check | Result per seed |
| --- | --- |
| Actual context seeds 113401 / 113402 | 55 contexts × 8 configurations; 84,265 expected outputs/configuration; 172 retained directed checks |
| Fast Rice edge checks | 8 checks; success E+3; zero-stream truncation E+2 |
| Count-domain starts | 8,064; 6,300 specialized-domain enabled and 1,764 excluded AC-count owners; generic pair always compared |
| Inherited scalar geometry | 4,260,918 cases, including 131,072 random full32 positions |
| Actual extracted stage seeds 113501 / 113502 | 157,184 cases; 131,072 random full32 positions; 14,290 abort cases; 22,456 request stalls |

The two inherited raw geometry traces both retain frozen SHA-256
`8254dd9da380dfbffb8446fc8d699e536314572f90c84ba9ef98c5e24353c33d`.
The [receipt summary](../../experiments/python-gamebub-v113/geometry/results.json)
links the selected source snapshot, commands, binaries, version and compressed
traces. The root's full V112-composition exact-cycle regression and subsequent
native measurements are separate gates, not results of this focused proof.
