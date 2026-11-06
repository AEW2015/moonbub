# V88: a measured entropy tradeoff and addressed COPY aliases

V88 adds an actual alternative entropy format and measures physical tile and
descriptor traffic for the alias layout. Existing quantized 720×480 pixels,
HUD and content commitments are preserved. The two studies remain separate:
their savings are not combined into an unmeasured decoder latency.

## Application-specific entropy coding

The new BR88 chunk format keeps bounded Rice run/level coding while bypassing
adaptive probability updates, interval multiplication and renormalization.
CS88 packets can mix AB38 and BR88 chunks. The host chooses complete packets
under an explicit byte budget and minimizes remaining adaptive feedback.

**457 sources × five policies = 2,285 actual packets** pass native coefficient,
canonical/HUD/display/root/seal parity. Independent reconstruction matches
**all 3,656 candidate packets** and all 35 retained fixtures exactly.

| Policy | Complete corpus bytes | Change versus CS87 | Adaptive decisions removed | Frames within 49,152 B |
|---|---:|---:|---:|---:|
| AB38 control | 7,784,499 | 0 | 0% | 457/457 |
| Minimum bytes | 7,781,672 | −0.04% | 0.47% | 457/457 |
| Up to 5% overhead per frame | 7,877,561 | +1.20% overall | 26.15% | 457/457 |
| Up to 15% overhead per frame | 8,273,629 | +6.28% overall | 96.16% | 457/457 |
| All BR88 diagnostic | 8,323,868 | +6.93% overall | 100% | 456/457 |

This is a concrete application-specific tradeoff: a modest corpus byte increase
can replace most adaptive feedback with simpler bounded parsing, without
additional picture loss. It is not a clock-speed result. The 15% policy still
reads 36,211,863 plain Rice bits; bit extraction, runs, scattering and memory
service remain real work. The encodings are prepared offline, so live host
encoding and ESP32 execution are not benchmarked here.

See [complete packets, policies and FPGA implications](wire.md) and the
[BR88 grammar/component experiment](entropy.md). Thirty-five grammar checks
and 20 actual native protocol checks pass, including recovery, replay and a
validly encoded coefficient mutation rejected at the reconstructed content root.

## Addressed alias traffic

The alias experiment now traces actual three-slot data addresses, packed
descriptor addresses/values, reference reads, provisional stores, HUD traffic
and complete base-YUV gathers across all 457 sources. Descriptor banks rotate
physically; no implicit map copy is omitted. Native tile and gather bytes match.

| Descriptor placement | Maximum decoder memory-busy work | Maximum including base gather | Sources regressing versus frozen decoder memory work |
|---|---:|---:|---:|
| On-chip | 9.99088 ms | 15.82288 ms | 18/457 |
| Small word cache | 10.07724 ms | 15.93210 ms | 73/457 |
| Uncached external | 15.68120 ms | 22.97120 ms | 450/457 |

These numbers price service work at assumed 100 MHz, 18-cycle read BL8 and
16-cycle write BL8. **Memory-busy work is not decoder completion latency.**
On-chip descriptor-port cycles are separate; causal stalls and other engines
still matter. The gather follows validated publication and is not continuous
LCD timing or RGB565/HUD composition.

The layout uses 1,555,200 logical pixel bytes and 6,075 packed descriptor bytes;
the three maps reserve 2,048 bytes each after alignment. Physical RAM ports,
rounding and target fit remain unqualified. Non-COPY stores are restored where
the old bank layout could elide them, explaining some regressions. Uncached
descriptors erase most of the traffic benefit.

## Selected causal checks

Ten schedules on four sources preserve the actual fixed-CS86 frontend work
and add alias data stores, descriptor ports and post-publication gathers.
All ten pass an independent timeline, resource, context-order, credit and
publication audit. Twelve descriptor-value/drain contract tests also pass.

| Source / assumed costs | Frozen decoder model | Alias decoder model |
|---|---:|---:|
| Key, LOW two lanes | 7.22181 ms | 7.30283 ms |
| C0/f1, LOW two lanes | 12.10858 ms | 8.83972 ms |
| C0/f3, LOW two lanes | 8.89402 ms | 7.94219 ms |
| C3/f50, LOW two lanes | 12.82457 ms | 11.27666 ms |
| C3/f50, HIGH two lanes | 18.58340 ms | 17.14844 ms |

C0/f3 explicitly exercises 294 added non-COPY stores previously elided by the
old layout. The key's descriptor initialization causes a small regression.
These are selected-source conditional timings, not a full-corpus latency
claim. They retain AB38 frontend work and cannot be assigned to BR88 packets.

See [the addressed layout and evidence](alias.md),
[independent full-trace accounting](../../experiments/python-gamebub-v88/alias-audit.json)
and [all ten independent DAG audits](../../experiments/python-gamebub-v88/alias-probe-audit.json).

## Next milestone

Observe actual BR88 bit/symbol arrivals and join them with alias addressing,
descriptor storage and display deadlines in one bounded schedule. Then calibrate
the simpler entropy parser and DSP transform pipeline in RTL. The current
grammar, fixtures and native oracle support that implementation work.

**Sustained hardware 30 fps and complete validated decoding under 10 ms remain
open.** There is no new FPGA RTL or ESP32 firmware in this iteration. All
content comes from one 457-source walkthrough family in four reset histories;
encodings, replays and selected probes do not extend distinct gameplay coverage
or establish HEVC/AV1 superiority.

- [Next experiment and implementation plan](next-steps.md)
- [Audited combined results](../../experiments/python-gamebub-v88/summary.json)
- [Independent full-packet reconstruction](../../experiments/python-gamebub-v88/packet-audit.json)
- [Independent policy/byte audit](../../experiments/python-gamebub-v88/wire-audit.json)
