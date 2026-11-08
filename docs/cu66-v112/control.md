# V112 local control and admission geometry

Status: **focused Verilator PASS and read-only source/artifact audit PASS**. This is a
bounded, original-edge timing experiment composed onto the retained **V110
Count** sources. It does not compose the rejected V111 header candidate and does
not implement the full PCTL1 latency-changing ownership protocol.

The routed controls are Count at 100 MHz (WNS −1.022 ns) and the fresh V111
Count at 125 MHz (WNS −3.264 ns). The latter's worst path launches from scratch
`read_segment_reg[1]` and ends at `busy_owned_reg/D`, with 11.211 ns data delay
and 15 logic levels. Admission's tile-to-`group_visible` population family was
also observed in the Count route. These findings motivate the two local changes;
they do not establish that either candidate meets timing.

The complete production sources and reversible recipe are in
[`fpga/experiments/cu66-v112-control`](../../fpga/experiments/cu66-v112-control/).
[`prepare.py`](../../scripts/cu66-v112/control/prepare.py) pins the frozen Count
origins, requires every edit anchor exactly once, reconstructs each candidate,
and reverses all edits byte-for-byte. No frozen source or prior proof is edited.
`packaging.json` records a lossless admission main/scale/mode split for Verilator;
native synthesis reads the entire production file.

The admission change prepares sixteen visibility bits on the existing edge
before `GROUP_BEGIN`. Initial header admission prepares plane 0/tile 0.
`GROUP_NEXT` prepares its successor plane/tile when changing planes, and the
current plane/tile otherwise. A balanced, five-bit population count is extended
to the original 32-bit `group_visible` on the unchanged consuming edge. The
mask registers are private payload with no reset/cancel fanout. Cancellation
prevents consumption, and every new admitted owner prepares its initial key
before use. An assertion compares the consumed value against the unchanged
original scalar function. No fixed-profile ROM, narrowed tile domain, p3 alias,
or replacement of an out-of-domain result with zero is used. The original
unsigned 32-bit `t+k` wrap remains part of both paths.

The scratch change validates each physical cache bank's selected word/position
before `read_segment` selects a one-bit invalid result. This removes the late
bank selector from the wide word/position selection followed by rank, signed
value, block-limit and monotonicity checks feeding failure/state/busy. The
original selected word/position remain the payload and diagnostic sources.
Only the existing `AC_EXTRACT` hit branch consumes the new flag; cache miss,
response matching, physical write/read drain, final output and cancellation
priority remain the original code. An assertion compares the new flag against
the complete old predicate at consumption. No additional transfer or clock
latency is introduced; physical ownership and all public invalid-cycle outputs,
states, counters and error priorities retain their prior meaning.

Run the preparation check with:

```sh
python3 scripts/cu66-v112/control/prepare.py
python3 scripts/cu66-v112/control/qualify.py
```

The explicit `--run` option performs the focused bounded Verilator suite. The
runner uses the pinned existing tool image, assertions, strict warnings, one
compiler job, two CPUs, 8 GiB RAM and the same 8 GiB memory-plus-swap ceiling.
Each attempt retains a separate source snapshot, compiler/simulator transcripts,
complete commands, source and artifact hashes, binary identities and compressed
traces. Failures are retained before a later attempt is made.

The complete original Count scratch and admission bodies are the references.
The inherited scratch miter retains every public/invalid/debug/counter/memory
comparison and the independent sparse coefficient, memory service, corruption,
stall, bank and owner oracles. The inherited admission miter retains public
invalid-cycle checks and the packet, mode, coordinate, active-bit, quantization
and RAM-port oracles. Its original side now uses the same frozen TABLES source
as Count; four C++ hierarchy paths are translated from the preceding inline mode
array to the frozen mode-store helper. Only observation paths change; checker
conditions and expected values remain unchanged. Both admission helpers are
compiled once with identical complete main-module bodies.

A separate combinational probe extracts the candidate's actual visibility
functions and compares them with an independent C++ integer oracle. All 65,536
intermediate masks exhaust the balanced population-count identity. Every tile
0..65,535 and the final sixteen wrapping uint32 tile values are checked for all
four plane values. For the remaining mathematical domain
`65,536 <= t <= UINT32_MAX-15`, every `t+k` is nonwrapping and exceeds both tile
counts, so every predicate is false. Random full-width values provide an
additional check of that domain argument. Whole-packet execution and the
consumption assertion check the predecessor/successor ownership alignment;
the combinational test alone does not establish state reachability.

The selected [focused receipt](../../experiments/python-gamebub-v112/control/attempts/20261108T193449002942Z/results.json)
(SHA-256 `0f501ce57eeb2a4f33994ec2a7e3c94bf2f558d1018383bcf0e583cbdcb821b5`)
records Verilator 5.020 and six successful seeded runs after three strict
compiles. Each scratch seed covers 72 full transactions, 128 corrupt-response
cases, four read-owner cases and all four cache banks/sixteen byte offsets.
Each admission seed covers 86 packets (52 positive, 34 negative), 44 directed
checks, 348,673 quant prepared edges, 738,933 header prepared edges, 40,585 scale
prepared edges and 158,230 mode prepared edges. Its independent replay oracles
also pass. Each geometry seed covers 65,536 population masks, 262,208 exhaustive
low/wrap tile-plane rows and 100,000 random full-width rows.

The [read-only audit](../../experiments/python-gamebub-v112/control/audit.json)
rehashes 28 source inputs and 48 retained artifacts, binds the references to the
actual Count source origins, checks the complete strict commands and production
packaging, and verifies the scratch predicate's bank-distribution identity after
normalizing only bank-word/position names. Run it with
`python3 scripts/cu66-v112/control/audit.py`.

The first [attempt](../../experiments/python-gamebub-v112/control/attempts/20261108T193302716067Z/results.json)
remains **FAIL**: both full-body scratch and admission seed pairs passed, then
the independent geometry probe failed strict `VARHIDDEN` warnings because its
top-level `p/t` ports shadowed the unchanged extracted function arguments.
Renaming the probe ports fixed that verification-only issue. Assertions and
warning severity stayed enabled, production RTL hashes stayed unchanged, and
the entire focused suite was freshly rebuilt and rerun in the selected attempt.

Full canonical composition, fresh 100/125-MHz route, whole-parent CDC/I/O/memory
integration, synchronized harness timing, device calibration and hardware
qualification remain separate gates. This local source experiment cannot close
those gates or the broader PCTL1 contract by itself.
