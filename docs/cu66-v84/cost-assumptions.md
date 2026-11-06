# V84 cost assumptions

This note separates observed frontend primitive counts from the cycle costs assumed by the conditional schedule model. The retained frame audit and source details are in [frontend-audit.json](../../experiments/python-gamebub-v84/frontend-audit.json); finite credit lifetimes and logical storage are described in [credits.md](credits.md).

## Entropy primitive weights

The runner applies the following independent cycle weights to each observed counter for a tile. LOW and HIGH are scenario assumptions, not calibrated bounds:

| Primitive counter | LOW cycles/count | HIGH cycles/count |
|---|---:|---:|
| `decisions` | 2 | 4 |
| `renorm` | 2 | 4 |
| `stream_bytes` | 2 | 4 |
| `rice_values` | 1 | 1 |
| `events` | 1 | 1 |
| `raw_bytes` | 2 | 4 |
| `header_bytes` | 2 | 4 |
| `crc_bytes` | 2 | 4 |
| `emits` | 1 | 1 |
| `raw_bits` | 1 | 2 |
| `prob_init` | 1 | 1 |

The schedule assumes 100 MHz to convert modeled cycles to milliseconds. It also assigns 64 cycles to each inverse task, each reconstruction task, and each SHA-256 compression block, using one hash lane. These values are inputs to the model, not measured implementation timing. Because the primitive weights are independent and not calibrated, LOW and HIGH must not be read as lower and upper bounds on physical latency.

## Existing scheduled work

The V84 wrapper retains V83's metadata, map, hashing, and memory jobs. The metadata assumptions are one 32-bit read and one 32-bit write per clock on independent ports, with map access on separate ports. Hash jobs use the modeled SHA-256 compression cost above. Four output groups, each covering 16 tiles of 64 bytes, form a 4,096-byte group ring.

BL8 memory service is modeled as 18 cycles per read and 16 cycles per write in the baseline scenarios. The service scenario changes these gaps to 12 cycles per read and 12 per write. These are modeled service gaps; they do not include a measured controller or row timing model.

The reserved-window scenario uses a 10,000-cycle period with cycles 0 through 1,999 blocked (20% of the period), restarting at phase zero for each source. It does not model continuous display refresh or an end-to-end display deadline.

## Finite credits and storage accounting

The model uses equal capacities of 64, 8, or 2 slots for each of three staging classes: 64 bytes per reference input, 192 bytes per signed 24-bit inverse result, and 128 bytes per coefficient/mode record. Four output groups add 4,096 bytes. Total logical allocation is therefore `4096 + slots × (64 + 192 + 128)` bytes: 28,672 bytes at 64 slots, 7,168 bytes at 8 slots, and 4,864 bytes at 2 slots.

For a fair comparison with V83's reference-plus-inverse accounting, omit the new 128-byte coefficient reservation per slot. That comparison is `4096 + slots × (64 + 192)` bytes: 20,480, 6,144, and 4,608 bytes at 64, 8, and 2 slots respectively. The additional coefficient reservation is 8,192, 1,024, and 256 bytes. These are logical capacities; they do not include RAM rounding, ports, or physical implementation overhead.

## Scope and omissions

The compressed packet is assumed fully available at the start of each modeled source. The observed counter set includes plane CRC byte counts and the runner applies the listed CRC weights. Outer CU/GU/HUD semantics, dequantization, ESP32 forwarding, and related control costs are not fully priced. COPY transfer-port work is also unpriced; the existing software graph does not assign a separate duration to moving or aliasing reference data into group output.

The weighted isolated frontend work and the finite-DAG schedules remain conditional software-model results. They are not measured hardware latency, physical throughput, sustained 30-fps evidence, or an end-to-end under-10-ms result. No final campaign performance conclusion is stated here.
