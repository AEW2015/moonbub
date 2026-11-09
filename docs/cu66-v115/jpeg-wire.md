# V115 actual QSPI-to-JPEG boundary experiment

The selected strict run **passes**, using the real QSPI endpoint, CDC bridge,
Moonshine core and vendor JPEG decoder with the existing isolated SOF input
guard. [Selected result](../../experiments/python-gamebub-v115/jpeg-wire/results.json):
attempt `20261109T015808060797Z`, raw receipt SHA-256
`fb991064c205608ee8f1653535644a95ab8819f3a625f5088d6790828e98e3a4`.
No production RTL is edited. This JPEG baseline is separate from the custom
CS88 component whose timing is measured in V115.

## Executed checks

Each of two modeled clock alignments passes two complete good frames, one
bad-CRC rejection, and reset during an incomplete receive followed by a full
retry. Per alignment, 691,200 exact RGB565 pixels, 79,525 accepted ordered bus
writes and 183,575 held-pixel cycles are checked. The two alignments therefore
cover four good frames and 1,382,400 pixel comparisons. This repeats one pinned
image; it is not a distinct-frame or sustained-throughput campaign.

The C++ driver uses actual QSPI pins and the `begin`, `forward`, `commit` MMIO
sequence from `firmware/handheld/src/streaming/mod.rs`. Modeled rates are 200 MHz
endpoint, 100 MHz core, 40 MHz quad writes and 16 MHz quad reads. The read dummy
interval is 64 bits. Register `0x0c` reports remaining frame bytes. Every accepted
bus write is checked against an ordered address/data ledger; chip-select
release must revoke drive. CRC fault injection deliberately bypasses the
receiver's CRC rejection to check the FPGA core's downstream gate.

Preparation runs the actual production Python MSV1 parser/reassembler on the
original 26-datagram, 26,159-byte 720×480 q65 JPEG fixture and compares recovered
bytes with the original JPEG. The output sink has bounded frame storage,
coordinate uniqueness, bank ownership, finite backpressure and stable held
transfers. Publication waits for modeled sink drain and a frame-boundary pulse.

The related upstream C-model PPM is the frozen RGB565 oracle. It shares upstream
JPEG algorithms and is not an independent decoder implementation. The input
module is the existing research `jpeg_input_guarded.v`, rather than the original
vendor input module. Both choices are source-pinned and explicit in the receipt.

## Strict build and retained failures

The first attempt (`20261109T012546265917Z`) stopped on 102 lint diagnostics.
Ten owned wrapper empty-port connections were fixed and checked via an observed
sideband invariant. Root reviewed the 92 remaining inherited diagnostics, their
source hashes, exact lines and arithmetic/reset scope. The second attempt
(`20261109T012908937875Z`) still stopped on one already reviewed y-DC unused-bit
diagnostic despite its line rule. Both failed snapshots and logs remain; neither
ran RTL simulation.

The selected third attempt uses 84 exact file/rule/line entries and one exact
file/rule/message entry for that same y-DC diagnostic. Message-match syntax was
verified against the official [Verilator configuration reference](https://verilator.org/guide/latest/control.html),
and the installed 5.020 binary then accepted it in the actual run. Source hashes,
line text and full diagnostic remain pinned. This does not establish why the
older line rule failed. There is no blanket `-Wno-fatal`, global width waiver or
assertion downgrade. All remaining warnings are fatal. Owned C++ uses warnings
as errors; compilation uses one worker. Exact baseline-lint and Root review
files are retained with the selected source snapshots.

## Reproduce and limits

```sh
python3 scripts/cu66-v115/jpeg-wire/prepare.py
python3 scripts/cu66-v115/jpeg-wire/qualify.py
# After a shared heavy-job slot is granted:
python3 scripts/cu66-v115/jpeg-wire/qualify.py --run
```

The bounded runner limits each job to two CPUs and 8 GiB RAM with an equal
combined RAM/swap ceiling. RAM/PSI and wall-clock watchdogs remain active.

The C++ pin driver is an adapter, not ESP32 firmware, Rust CPU, Wi-Fi or Sunshine
capture execution. The sink models frame storage/ownership, not SDRAM pins or
LCD scanout. The older `qspi-study/tb_qspi_jpeg720.sv` additionally connects its
functional SDRAM and LCD models but used historical `-Wno-fatal`; it is separate
evidence. Mixed-reset lint scope does not qualify physical reset/CDC margins.
This pass establishes a bounded actual digital boundary, without proving the
complete CS88 parent, routed timing, hardware 30 fps or validated under-10-ms
decoding. No hardware, Windows Sunshine instance or relay was contacted.
