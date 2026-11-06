# V82 application-specific COPY execution and content commitments

V82 is a Python/native design study. It combines encoded-zero-residual COPY,
certified existing candidate-bank contents and an opt-in hierarchical content
commitment. It keeps the original quantized picture, geometry and residual
entropy coding as the data baseline. No RTL, deployed encoder, ESP32 firmware or
streaming wire format is changed.

All **457 native sources** pass original packet/canonical/HUD/display digest
checks. There are **2,216,647 safe visible COPY_REF tiles** across 437 deltas;
these are identified from encoded all-zero coefficients, not a host-trusted
skip hint. Hidden tiles are generated CONST128. The new commitment profile
passes **113 synthetic checks** and **3,656 full-tree/seal comparisons**.

| Tiles per hash leaf | Data + HUD command reduction | Tree + residency maps | Group buffer | Command reduction if tree metadata uses existing external bridge |
|---:|---:|---:|---:|---:|
| 1 | 43.11% | 1,029.87 KiB | 64 B | −111.61% (more commands) |
| 4 | 40.07% | 261.87 KiB | 256 B | −4.13% (more commands) |
| 16 | 34.85% | 69.87 KiB | 1,024 B | 22.36% |
| 64 | 29.83% | 37.87 KiB | 4,096 B | 24.96% |

The first reduction column excludes scanout and off-chip tree metadata; on-chip
metadata accesses are counted separately. The last column prices complete shadow
tree copies, digest comparisons, child reads and digest writes as aligned BL8
traffic, retaining masks on chip. It is an accounting scenario, not implemented
traffic or measured speed. SHA lanes, control, ports and target fit remain
unqualified. All byte counts are logical, before physical memory rounding.

**16 tiles/leaf is a balanced prototype candidate**, with 4 and 64 as explicit
comparators. Granularity 16 minimizes aggregate hash work, but granularity 4
saves more data traffic if its larger state fits; 64 uses less state and wins
this external-metadata scenario. There is no universally best configuration.

The original bridge still has a **conditional worst-case data-service floor of
11.70174 ms** for cold deltas, before scanout, refresh or compute. No 30-fps or
under-10-ms milestone is closed by this model.

- [Native data and conservative COPY classification](native.md)
- [Compact content commitment and protocol tests](commitment.md)
- [Execution accounting, metadata placement and limits](execution.md)
- [Application-specific profile and next implementation steps](application-profile.md)
- [Evidence and reproduction](evidence-scope.md)

The comparison uses four independently reset histories from one walkthrough
family. V81 and earlier sources/evidence are immutable. These results establish
semantic consistency and modeled work counts, not sender authentication,
physical performance, compression superiority over HEVC/AV1 or FPGA fit.
