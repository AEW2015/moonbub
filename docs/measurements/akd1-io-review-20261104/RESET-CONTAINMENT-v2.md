# RAM reset containment: source and routed-parent inspection

This is a follow-up to immutable `REVIEW.md`/`review.json`, not a replacement.
The current analysis is INCOMPLETE. It does not waive DRC or qualify warm reset,
PLL loss, AV playback, or physical memory retention. No RTL was changed.

## Applicable device rule

The Artix-7-specific [AMD/Xilinx UG473 v1.14, July 3, 2019, pp. 12–13](https://docs.amd.com/api/khub/documents/9gZGbqBxtlKXxBfkBt~lAg/content)
requires valid BRAM address/write-enable setup even for reads: disabling writes
alone does not rule out stored-content corruption. It separately explains that
asynchronous EN transitions can invalidate the first operation and recommends
holding EN inactive through reset or discarding an initial operation. On PLL
lock loss or a stopped free-running clock it requires immediate EN disable.
These are distinct failure mechanisms. RTL simulation models neither analog
setup/hold violation nor corruption during an unstable clock.

## Reset and startup scope

The top uses four-stage, async-assert/sync-release chains for raw100, raw200 and
pixel domains. They release after four destination edges with LOCK asserted.
Audio derives reset in the always-running 50 MHz reference domain from separately
synchronized PLL lock levels, followed by its own three-edge reset release.

Those intervals support logical state initialization and synchronized release.
They do not by themselves prove every BRAM enable is inactive while a PLL is
unlocked. The BUFG clock paths are not disabled with BUFGCE during lock acquisition.
Fresh volatile configuration reloads initialized memory once; a later logical
reset does not re-run `$readmemh` or restore corrupted ROM contents.

The proposed AKD1 lab scope is fresh volatile configuration followed by stable
PLL operation, no external reset during an owned job, and fresh configuration
after an unexpected reset. This is not warm-reset retention qualification.
Pre-LOCK enables must still be reviewed before treating that scope as sufficient.

## Known families

| Family | Source-level reset containment | Limit |
| --- | --- | --- |
| QSPI bridge queue | Reset clears both pointer/Gray chains, `fetched`, read state, response and pending tokens. `core_write` requires a newly fetched entry after the write pointer crosses; a fresh accepted write stores the word before that entry becomes visible. Previously corrupted contents are logically unreachable. | Raw async reset reaches BRAM WE. Pointer reset/source reasoning is not analog proof; confirm all uncapped warning pins and no non-reset metadata can publish old slots. |
| Audio sample slots | Common private reset disables playback/staging, clears pointers and online state. Rearming passes an offline/acknowledgment/four-cycle settle handshake. A new slot is committed only after all declared frames have been written and CRC verified; its last-frame sidebit prevents reading unused tail words. | Active-audio clock loss can have a finite reference-domain reset-detection interval. This lab has audio disabled; no AV reset/acoustic qualification follows. BRAM WE warnings still need review. |
| Fixture ROM | Read-only in RTL, initialized by `fixture.hex`; byte-valid and controller ownership/counters reset. v26 accepts success only with the expected count/tag and stable owner/result sequence. | No warm-reset reload. Read-only is not a corruption waiver. Its compiled EN/RSTRAM reset cone is the concrete pre-LOCK issue below. Expected-tag rejection is a diagnostic containment check, not proof the ROM survives. |
| Envelope / GM map / CP02 packet and DC scratch / raster stripes | Reset invalidates leases, pending responses, certificates, full-bank bits and output-valid state. A new packet/map is loaded before replay/certification; DC values are rebuilt for the new plane; a stripe is exposed only after its visible samples have filled that bank. | This is the reviewed source rationale, not a completed formal or analog proof. Uncapped netlist inventory must identify any additional control/address pins and whether all fresh-write-before-valid assumptions hold. |
| Overlay | Its memory write enable is a separate clocked `bank_write` stage without an async reset. Pixel outputs/valids reset; memory contents intentionally persist on logical reset and are initialized transparent by configuration. | Not among the first capped REQP cases. Persistent overlay/read-port behavior is not a generic proof of pre-LOCK BRAM safety. |

## Exact ROM cone in the routed parent

Read-only Vivado checkpoint inspection is preserved under `parent-ram-inspection`.
It opens the sealed routed parent only; it does not synthesize, place, route,
generate a bitstream, or program hardware. The parent checkpoint is not changed.

For `diagnostic/byte_data_reg_0_0`, DOA_REG and DOB_REG are zero, WEA/WEBWE are
constant zero, and RSTRAMARSTRAM is active through a reset/cancel LUT. ENARDEN
is **not** simply held low throughout reset. The inspected cone contains:

- base enable `byte_data_reg_0_0_i_1`, LUT5 `INIT=32'hFFFF0C20`;
- EN gate `byte_data_reg_0_0_ENARDEN_cooolgate_en_gate_82`, LUT3 `INIT=8'h70`;
- a delayed-enable flop with `INIT=0` and low initial `bytes_sent[15]`;
- reset/cancel RSTRAM LUT4 `INIT=16'hBAAA`.

The base-enable LUT is forced high by its reset/abort input. With address bit 15
initially zero, the LUT3 enables this ROM bank even while reset is active.
The separate high-bank `byte_data_reg_1_0` EN directly uses that base enable.
Thus the four-edge reset release does not establish that this initialized array
was never operated before LOCK. The source reset assignment `byte_data<=0`
maps onto the BRAM output-reset path; it is not merely clearing an independent
valid bit. This is a concrete missing startup-protection gate, not proof that
corruption actually occurred on this device.

A focused successor could leave ROM data unreset, mask it using the existing
`byte_valid` ownership, tie BRAM output resets inactive, and enforce EN low in
reset/unlocked conditions. It must retain byte/valid latency and pass the full
fixture plus reset/cancellation tests, then demonstrate the exact new EN/reset
netlist and routed timing. This review does not authorize editing the active
four-term cancellation candidate or claim that such a fix already exists.

Overall remains INCOMPLETE. The associated reset-inspection record binds the
netlist alias/truth derivation and unchanged parent checkpoint. The uncapped
successor warning inventory and a demonstrated startup-protection fix remain open.
