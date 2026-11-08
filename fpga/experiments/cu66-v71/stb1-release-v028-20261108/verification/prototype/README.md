# STB1 compressed-staging burst prototype

This is an isolated **ABI 3 functional prototype**, not an installed image or a 30 fps result. V027, its source tree, its constraints and the handheld are unchanged.

The prototype replaces per-u32 credit/write/count round trips with a descriptor-reserved 1 KiB upload window and a 256-word FIFO. It still uses the exact selected V027 QSPI endpoint, write-queue CDC, byte staging RAM, CRC logic, and packet read arbiter. The native stage remains the authority for committed bytes and CRC. No decoder, SDRAM, memory-clock or timing-constraint change is included.

## Qualification status

- `evidence/unit06`: 13 unit scenarios with actual selected native staging, byte/word scoreboards and RAM reads. Covers seeded backpressure, all three partial tails, stale and high 64-bit generations, skipped alias offsets, duplicate tickets, partial nonfinal descriptors, FIFO overflow, reset cancellation, scalar collision, transport failure and bad whole-frame CRC.
- `evidence/full256-unit02`: the default 256-word FIFO is filled while native acceptance is stalled. An extra word is rejected; all 256 previously accepted words drain intact, all 1,024 native RAM bytes and CRC match, and both pointers wrap. No activation is requested. Drain after releasing this forced full-FIFO stall measured 12.8 microseconds in the 100 MHz behavioral model.
- `evidence/pins08`: nine digital pin-level cases through the selected QSPI endpoint and CDC, prototype control/FIFO, and actual native byte RAM. Eight cases vary phase/rate or inject CDC overflow. The ninth transfers the full 49,152-byte staging limit in 48 descriptors, compares every byte through the native packet request/response port, checks whole CRC and all 12,288 accepted words, and exercises repeated default-depth pointer wrap.
- `evidence/driver-oracle01`: ten pure Python tests of the abstract batch driver, including multi-frame tickets, partial tails, old-ABI rejection, errors/timeouts, native fault checks and completion during a sequential CSR read.

The 1,031-byte pin cases retain the legacy scalar port for the first four bytes, then use descriptors of 1,024 and three bytes. The final three-byte descriptor is deliberately stalled: the first status beat reads busy, native drain completes, and later beats read the now-ready prefix/CRC. The driver must tolerate this legal mixed-time read.

The pin test uses a synthetic idle decoder/owner and no SDRAM. It verifies actual compressed packet storage and retrieval, not whole CU66 decoding, presentation, a routed netlist, pin analog margins or hardware operation.

## Version and address map

The selected old controller advertised ABI `0x00020000`, capabilities `0x1f`. This prototype advertises **ABI `0x00030000`, capabilities `0x3f`**, retaining magic `0x44593731`. The new bit identifies this local staging extension; it does not advertise UDP production support or 30 fps. Existing V48's exact ABI/capability check must refuse this image. A new firmware profile must select it explicitly.

The alias occupies **`0xc00..0xfff`**, which is unused in the selected V027 controller, HBU1 and LD14 maps. LD14 uses `0x380..0x3ac`; HBU1 uses `0x400..0x618`. The QSPI endpoint and CDC retain their existing 12-bit core addresses. The suggested `0x2000` aperture was deliberately avoided because it would wrap with those unchanged modules.

| CSR | Meaning |
|---|---|
| `0x700` | STB1 magic `0x53544231` |
| `0x704` | STB1 version `0x00010000` |
| `0x708` | Flags: bit 0 fault, bit 1 armed descriptor, bit 2 native-drain fence ready, bit 3 blocked, bit 4 transport fault |
| `0x70c` | 256 free payload-word credits only when fenced, idle and fault-free; otherwise zero. At most one descriptor may be reserved |
| `0x710` | Native committed byte prefix, zero unless the fence is ready |
| `0x714` | Native committed IEEE CRC-32, zero unless the fence is ready |
| `0x718` | Last accepted descriptor ticket |
| `0x71c` | Rejected alias/scalar-conflict word attempts |
| `0x720`, `0x724` | Descriptor generation low/high |
| `0x728` | Descriptor starting byte prefix |
| `0x72c` | Descriptor valid byte count |
| `0x730` write | Strictly newer nonzero ticket; descriptor doorbell |
| `0x730` read | Queued word count, diagnostic only |
| `0xc00..0xffc` | Sequential packed-u32 payload writes, starting at `0xc00` for every descriptor |

The driver writes the five descriptor words at `0x720` in one contiguous operation, then writes the packed payload in one auto-increment operation. A descriptor must reserve between one and 1,024 valid bytes, match the current native staged generation and committed prefix, fit the native packet, and start on a four-byte boundary. A partial final word is allowed only at the packet end. Its unused high bytes are ignored using the descriptor's exact byte count.

Payload bytes are packed little-endian within each numeric u32: byte zero occupies bits 7:0. The existing SPI driver serializes numeric words MSB-first (`to_be_bytes`), and the native stage consumes the low byte first. No per-word credit/count polling remains in this profile.

Ticket is 32-bit, strictly increasing, and persists across native BEGIN operations. One driver instance carries it across frames. Wrap is refused; no automatic reset or takeover of a retained endpoint is allowed. BEGIN, descriptor generation, native prefix and whole packet CRC remain bound. The existing scalar `0x100` path remains usable when no burst descriptor owns the stage; mixed scalar/burst writes fail closed.


## Mandatory supported-driver transaction limit

Every raw alias SPI transaction must contain **at most 1,024 bytes / 256 u32**. Both the STB1 staging driver and its concrete adapter must reject a larger request **before descriptor or SPI writes**. DYN1 must not bypass those guards.

The frozen hardware cannot identify arbitrary transaction overruns: after the valid last address `0xffc`, a 257th auto-increment word wraps through the unchanged 12-bit endpoint address to read-only CSR `0x000`, where it is ignored without an STB fault. Longer malformed raw bursts can reach writable legacy CSRs. This is outside the supported driver contract, not a hardware fail-closed guarantee.

`integration-v001/wrap-limit-v001` is an actual pin-level LIMITATION diagnostic. It observes one decoded wrapped CSR-0 write, no STB/quarantine fault, the extra word ignored, and the correct 1,024-byte supported prefix. It is explicitly **not** counted as a passing fail-closed gate. The unit full-FIFO extra-word test repeats an address inside the alias window; it proves that distinct case only. A later hardened ABI revision can add transaction-boundary visibility or write protection. The current frozen RTL and board overlay were not changed.

## Read-fence contract: sequential, not atomic

The existing eight dummy bytes and QSPI read pipeline are unchanged. A read **does not wait an unbounded time for the new FIFO to drain**. The fence is explicit: it is ready only when the FIFO is empty and every accepted byte has actually committed to the selected native staging RAM. Credits and prefix/CRC are masked while that condition is false.

Each CSR is sampled separately. A six-word auto-increment read can begin with busy flags and finish with ready data. Therefore:

1. If the first flags beat is busy or armed, ignore all later fields and poll again. Do not call later ready fields a publication violation.
2. For a ready snapshot, confirm ready/fault flags, exact staged generation at `0x114/0x118`, and the expected ticket again around the data read.
3. Require the exact expected end prefix and CRC. A drained but incomplete descriptor can have the fence bit set while `armed` remains set; that is not descriptor completion.
4. Before SEAL, retain the original native `0x104..0x110` check: written length, intended length, whole CRC and zero native faults. A FIFO receipt is not a decoder/presentation ACK.

The abstract oracle implements this protocol. Its bus methods are not hardware bindings; the separate Rust prototype is owned by another agent. Neither oracle changes network behavior or the current firmware.

## Observed digital timings

For the full-size pin case at nominal 16 MHz quad SPI, 200 MHz endpoint and 100 MHz core:

| Scope | Simulated time |
|---|---:|
| 48 payload transactions, including their headers and CS gaps | 6.202 ms |
| Descriptor/status work plus complete packet staging | 6.642 ms |
| Full pin test, additionally reading all 49,152 RAM bytes through the native packet port | 10.120 ms |
| Longest normal fence-poll transaction in this case | 5.2 microseconds |

These are behavioral bus test timings with no ESP/IDF transaction cost, network round trips, HU decode, full FPGA decoder or SDRAM arbitration. They are not a physical throughput promise. The 1,031-byte test includes a separate forced sequential-read transition and therefore has extra test-only polling.

The seeded native-backpressure unit measured a 400 ns maximum drain wait after its payload stimulus, with ten injected stall events. The separate forced full-depth test measured 12.8 microseconds after releasing native acceptance. Those are different stress cases; neither is an exhaustive worst-case guarantee.

The old V48 path required at least 131,463 staging SPI transactions for the twelve fixtures. The new driver needs two writes per 1 KiB descriptor plus bounded status/generation/ticket reads, rather than three transactions per u32. SDK overhead and actual completion latency still need measurement.

## Unsupported clock envelope is retained, not relabeled

`evidence/negative-clock01` deliberately reproduces failure at **16 MHz SPI with a 10 MHz core**: the selected fixed-dummy read/CDC path cannot return correct identity at that ratio. It is an expected failure, not part of the passing set. Testing the slow core with 4 MHz SPI separately does not repair or qualify the failed ratio.

The selected V027 top proves the intended production clocks: 50 MHz input, PLL feedback multiply 20, endpoint divide 5 = 200 MHz, core divide 10 = 100 MHz; both the CDC and controller use that 100 MHz core (`reset-bufg-v027/moonshine_top_dy71.sv`, lines 16–19, 47, 75–77). The passing 16 MHz/100 MHz case matches that digital envelope. Physical timing, jitter, external input/output delays and final routed constraints still require signoff on the new full design.

## Reproduce without hardware

Run from `tools`:

```powershell
python run_unit.py
python run_full256.py
python -m unittest -v test_batch_driver
python run_pins.py
python run_negative_clock.py
```

Each simulator runner uses owned `C:/moon/tmp` compiler temporaries, explicit tool paths, source hashes, commands, return codes and unambiguous pass markers. The max packet case has a 300-second simulator timeout. Earlier failed testbench/launch iterations remain under their evidence directories. The initial BOM/temporary-path launch problems, the unsupported slow-core read, and a testbench that forced native readiness before descriptor setup completed are not counted as passing coverage.

## Board overlay prepared for root review

`C:/moon/builds/stb1-v001` contains a separate roughly 1 MiB source overlay, no checkpoint or bitstream. `overlay-binding.json` and prototype `evidence/overlay-delta-proof.json` show:

- The selected V027 top, clock/reset implementation and every XDC/Tcl constraint file are byte-identical.
- The original controller source is replaced with the prototype controller and the new FIFO source is added.
- The board copy changes only the prototype controller's module identifier back to `dy71_local_control_bulk_v025`, preserving the exact selected top and hierarchy. Normalizing that one module identifier reproduces the tested prototype source byte-for-byte.
- The synthesis script reads those replacement sources. Implementation steps and constraint source files are unchanged apart from completion-marker naming. No false/multicycle exception or clock change was added.
- The new runner uses `C:/moon/tmp`, never the original script's forbidden `C:/vtmp` path.
- ABI is 3/caps `0x3f`; a new bitstream USERCODE is intentionally **unassigned**. No BIT command or hardware operation exists in these phase scripts.

The runner refuses to execute without a root-reviewed receipt binding both the frozen source hash and overlay/script binding hash. Root can create `review-approval.json` after reviewing this evidence:

```json
{
  "source_freeze_sha256": "dec6bfe052d58b11478bfca566edcdc22973f25be9681dd8e281ee1055b9baf9",
  "overlay_binding_sha256": "26a19d929a3f85faee57d6bb391dc1306737d4028ad67717bdefb204dbbc2e41",
  "allow_synth": true,
  "allow_implementation": false
}
```

Then, only after root approval:

```powershell
python C:/moon/builds/stb1-v001/run-phase.py synth
```

A later implementation launch requires its own approval and a successful fresh synthesis receipt:

```powershell
python C:/moon/builds/stb1-v001/run-phase.py implementation
```

No Vivado phase has been launched by this prototype task. The recorded V027 synthesis took 17.1 minutes and implementation 47.8 minutes. Budget about 15–25 minutes synthesis and 45–75 minutes implementation/reporting for the new candidate; timing closure is not guaranteed. V027 had only +0.019 ns setup/+0.012 ns hold margin. The new FIFO data RAM has no reset, but its metadata, identity comparison, status mux and quarantine fanout must be checked in synthesis, CDC and routed timing. Preserve all existing constraints and address real paths with pipelining/placement if needed.

Before a bitstream or hardware test, root must assign a new exact image identity, validate selected full-system decode/presentation and fault behavior, sign off timing/DRC/CDC, build an explicitly ABI-3 firmware profile, and preserve the V027/V48 recovery artifacts. Nothing in this prototype authorizes changing the installed handheld.
