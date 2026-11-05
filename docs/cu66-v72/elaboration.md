# V72 generic elaboration preflight and strip-memory review

**Status: `UNAVAILABLE_FRONTEND`; none of the three requested leaves was
elaborated by the native Yosys 0.33 frontend.** No generic cell count, inferred
memory-port count, FPGA resource estimate or timing result was produced.

The requested direct flow was staged without editing or translating qualified
RTL:

```text
read_verilog -sv -I<fixed-memory-map-directory> <leaf>
hierarchy -check -top <leaf-top>
proc
opt
memory_collect
check -assert
stat -json
write_json
```

`read_verilog -sv` rejected `int'(...)` casts before hierarchy or process
conversion in each source:

| Leaf | Direct parser result |
| --- | --- |
| `cu72_word_bridge` | Line 101: `syntax error, unexpected TOK_INT` |
| `cu72_tile_memory` | Line 48: the same parser error |
| `cu72_painter_burst` | Line 72: the same parser error |

The [Yosys loading documentation](https://yosyshq.readthedocs.io/projects/yosys/en/latest/using_yosys/more_scripting/load_design.html)
distinguishes the native frontend's SystemVerilog support from more comprehensive
frontends. Its [Verilog-support notes](https://github.com/YosysHQ/yosys/blob/main/docs/source/using_yosys/verilog.rst)
also describe the supported language subset. These references explain why a
native-parser failure cannot be treated as a target RTL or memory-inference
result. The direct source simulations remain separately qualified; no source
lowering was used to manufacture elaboration statistics.

Reproduce the preflight with:

```sh
python3 scripts/cu66-v72/run_elaboration.py
```

It deliberately returns exit code 2 for this known unavailable-frontend outcome,
retaining tool/version information, exact commands, source hashes, `.ys` files,
parser logs and `memory/elaboration/results.json`. The record uses
`UNAVAILABLE_FRONTEND` and per-leaf `NOT_ELABORATED`; neither status is PASS.
All six source/script pins remained unchanged. An initial identical bridge
parser failure is retained as `bridge-first-unavailable.log`.

## Source-level strip access finding

The declaration is one logical array of 5,760 × 16 bits: **92,160 declared bits,
or 11,520 bytes**. This is source storage capacity, not inferred BRAM usage.

The frozen v70 strip writer has one `rgb_strip` read expression in its drain
state and sends one word per scalar transaction. V72 gathers eight words in one
clocked `STRIP_DRAIN` branch into its registered 128-bit write payload. Its eight
read expressions share `drain_x` and select row lanes 0 through 7. The pixel
producer writes one indexed 16-bit word at a time using `{x,y[2:0]}`.

This is an implementation gate for the exact FPGA flow. The source has eight
read expressions; **the number of inferred memory ports is unknown**. The
register on the gathered payload, address relationship, frontend transformations
and target memory lowering can affect the resulting implementation. Do not
assume a single ordinary dual-port RAM or infer a specific block count from the
array declaration or functional simulation.

Two candidate structures for a subsequent measured implementation iteration are:

- Eight logical row-lane banks of 720 × 16 bits, with one selected bank write per
  produced pixel and one read from each bank during a burst gather.
- A 720 × 128-bit logical packed store, with lane-selective writes and one wide
  read per drain group, if the target flow supports the required write enables.

Both preserve the 11,520-byte logical strip capacity and the exact lane order.
Neither is implemented or target-qualified here. First inspect exact-device
memory inference, replication, read/write ports, utilization and timing; then
bank or pack explicitly if required and re-run exact-output/abort tests. A
memory-inference improvement must not change accepted-burst drain behavior or
substitute a source-level capacity calculation for actual FPGA resources.

This preflight supplies no target fit/Fmax, BRAM/DSP mapping, CDC, physical
30-fps presentation or sub-10-ms decoding evidence.
