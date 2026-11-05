# CPL1 private local-ROM diagnostics — draft for review

This image runs exactly one original 17,412-byte frame0 ROM fixture after a positive loader bootstrap/idle certificate. It does not accept video/audio, advertise CP23 or restart a job. It is neither AKD1 nor MBV1. Reconfiguration is required for another job; post-start logical reset/PLL loss remains quarantined. No Windows sender changes are needed.

Keep the existing QSPI endpoint, ordered bus CDC, native button reads/control and IRQ behavior. Use only the existing bounded 16 MHz laboratory profile with at least eight dummy bytes. This is not maximum-QSPI or full external-hold qualification. Overlay writes are consumed/ignored without overlay RAM; DAC/vibration outputs are statically low. Fixed native LCD preset0/margin13; dynamic porch/margin/clock writes are unsupported and ignored.

## Identification and request

| Offset | Meaning |
|---|---|
| `000` | `0x314c5043` (`CPL1` little-endian byte spelling), distinct lab identity |
| `004` | CSR schema `0x00010000` |
| `008` | CAPS **zero**; no negotiated receiver capabilities |
| `184` | Distinct image `0x43505231`; never the MBK1 identifier |
| `500` write | Capture one atomic retained snapshot; written nonzero u32 is the caller's query cookie |
| `500` read | Echo of the retained snapshot cookie; zero means invalid/no snapshot |
| `504` read | Snapshot generation, increments only on accepted nonzero snapshot request |
| `508` read | Snapshot schema `0x00010000` |

All other writes are ignored and counted, including zero-cookie writes. Snapshot capture has no core/start/reset/abort or timing side effect. The bridge preserves request order; capture copies all fields on one core-clock edge. Data remains unchanged until another capture or reset. Within one ESP32 boot lifetime the SDK uses serialized queries and monotonically allocated nonzero cookies; FPGA reset/reconfiguration must not reset that allocator. Read generation before writing the new cookie, require a successful fresh capture with generation advancement, then read the group and recheck cookie+generation+LAB ID/schema. No cached old group is accepted without that successful fresh capture. On mismatch, reset/quarantine, or unexpected identity, reject the whole group. No claim is made that generations survive logical reset or configuration; the fresh query cookie guards such reuse. Within that SDK lifetime a query cookie is not reused across FPGA reset/reconfiguration. Across ESP32 reboot there is no globally persistent query/configuration identity: no NVS namespace, RNG proof or cross-reboot ownership/ACK/reference continuity is claimed. This is current-capture-only observation.

## Retained snapshot group

| Offset | u32 value |
|---|---|
| `50c` | State flags: bit0 bootstrap observed,1 autoSTART issued,2 consumer started once,3 configuration required,4 loader busy,5 load complete,6 core job active,7 base qualified,8 front valid,9 checked result retained,10 positive job release observed,11 snapshot-generation exhausted,12 ignored-write counter exhausted; remaining bits reserved zero |
| `510,514` | Captured core cycle counter, low/high |
| `518,51c` | Actual retained result owner64, low/high; valid only with checked/result-valid flag |
| `520,524,528` | Actual retained result epoch/frame/generation |
| `52c` | Actual ROM bytes sent |
| `530` | Actual canonical bytes accepted |
| `534` | Actual HUD words stored |
| `538` | Actual unmasked SDRAM write beats launched (not chip readback/ACK) |
| `53c` | Actual transpose output words accepted by the memory packer |
| `540..54c` | Actual computed base tag, numeric bits31:0 first |
| `550..55c` | Actual computed HUD tag, numeric bits31:0 first |
| `560` | Retained result stage in bits3:0, code in bits15:8; checked bit16; result-seen bit17 |
| `564` | Captured platform/drain flags: service LOCKED sync bit0, panel LOCKED sync bit1, raw physical idle bit2, joined idle bit3, child quiescent bit4, store-owner-clear bit5, transpose-owner-clear bit6; remaining zero |
| `568` | LCD underrun count |
| `56c` | Actual core-domain LCD frame-boundary count |
| `570` | Positive bootstrap releases observed |
| `574` | Positive consumer-job releases observed; **not front-bank lease release** |
| `578` | CDC bridge lost-write count, Gray-synchronized to core domain |
| `57c` | Ignored/unsupported core writes, saturating |
| `580` | Last completed canvas sequence, saturating; zero means no complete canvas |
| `584` | Last completed final RGB565 canvas CRC32: zlib/IEEE reflected polynomial, bytes low then high per word, column-major x0..719 outer/y0..479 inner |
| `588` | Last completed canvas word count; valid completion is exactly345,600 |
| `58c` | Canvas flags: bit0 retained digest valid,1 current canvas active,2 current coordinate gap,3 any coordinate gap since reset,4 canvas/error counter exhaustion; remaining zero |
| `590` | Saturating canvas coordinate sequence-error count |
| `594` | Current canvas word count |
| `598,59c` | Reserved zero |

Tags and result identity must come from the actual decoder result, latched before its handshake retires the leaf; never fixture constants. Failure results are retained too, with `checked=0`. Qualification/front flags distinguish a checked result from physical-drain/publication completion. Post-start reset clears this observational group while the wrapper's INIT-only quarantine persists; no retained-memory/reset-integrity claim follows.

The final-RGB observer consumes actual overlaid `line_data_valid/data` and x/y captured alongside the existing one-cycle overlay registers. It resets its running CRC/count only on observed(0,0), requires every subsequent coordinate in order and latches a completed digest only at(719,479) with345,600 words. Idle cycles/backpressure are not coordinate gaps. A missing/duplicate/out-of-range word increments a sequence error and permanently invalidates digest qualification until reset/reconfiguration; the old completed CRC is retained for diagnosis. A stopped partial canvas remains active with its partial count; no completion is invented. LCD underruns remain a separate field. This is downstream data-path evidence, not SDRAM electrical/readback-device qualification.

Snapshot generations never wrap: at exhaustion, subsequent requests invalidate the cookie, set flag11 and require reconfiguration; clients must reject generation`0xffffffff`. Canvas sequence/error and ignored-write counters saturate and expose exhaustion. The whole extended`500..59c` group is captured by the same cookie request, including all canvas fields. The caller reads40 words and rechecks the cookie/generation/identity pair; no field is a separate live page.

## Minimal observational source boundary

The sealed ROM wrapper/core lack output ports for computed tags, result identity and internal drain/count signals. Proposed additive copies expose these as read-only observation ports/registers; mechanically stripping additions and restoring module names must recover the exact sealed source. A separate read-only `write_beat_launched` port on the retained controller (propagated through its owned service) exposes the actual existing unmasked `write_cycle` pad-launch condition. It counts real launch attempts, not invented memory completion. Original functional statements, clocks, request ownership and accepted-burst drain remain unchanged. No hierarchical RTL references or golden-tag constants are used as status.

Additional observational x/y registers match the existing overlay enable/reset and do not alter its valid/data. A CRC unit test and actual-core full native-oracle comparison are separate gates; until executed they remain NOT_RUN. These ports do not change wire format or advertised capabilities.

Board source, clocks/pins and source-oriented simulations can proceed before whole-core timing adoption. No synthesis/route/bitstream/programming is authorized by this draft. Read/hold/CDC/BRAM reset-containment, actual SDRAM timing and all board signoff gates remain open.
