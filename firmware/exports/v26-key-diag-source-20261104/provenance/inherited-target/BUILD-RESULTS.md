# v26 offline build result ? KeyDiag resource-meter candidate

The current bundle is `release-key-resource/`, built from prebuild03 with
`esp193`, rev4, ESP-IDF5.4.3 and the exact v26 source directory. Typecheck and
release build pass. The app-only UF2 passes every12419 blocks through the
production updater parser, including Rev4/product identity, application-only
addresses, binary round trip and final padding. It is **not installed**.

| Current image | SHA-256 |
| --- | --- |
| moonshine-rev4.elf | `521f529ed99e587cfbd47e63be0de99f4a5f9a13fbf099752a24065655ed49e6` |
| moonshine-rev4.bin | `40cd845d6fb4cd6c4e0e5a7761d8bef776b931f78bac76eb2a9c4c29561e2d30` |
| moonshine-rev4.uf2 | `80003d79887976d8a49889a0e0bcda2905cb58763ff21d720169c3a87432bc63` |

The SDK application descriptor's embedded ELF digest exactly matches the ELF
above; this is the primary exact runtime identity. The variant reports
`v26-key-diag-access-20261104`. There is no self-BIN hash or circular source-hash
claim. Prebuild03 freezes575 inputs at SHA
`6530279c0655723183e53c95877b534c8e69a386d923b9fb2cd500926c03eb97`.

Static shared SRAM is122124 bytes,344 above sealed v24, below the163840 build
guardrail. This is not free-heap/largest-block evidence. Generated SDK config
and bindings are byte-identical to v24; bindings SHA
`c721d4d5940dcd68b8e54cdc266224773fc221af2b3c3624862b24afa33de991`
defines `StackType_t=u8`. Watermark units in this SDK are therefore bytes.
Existing USB4096/AV8192 and all other stack/priority/SDK/default settings stay
unchanged. No ESP compiler source fix was needed.

The updated host evidence passes39 model tests,66 SDK host tests and24 expected
compiler rejections. Meter tests use the exact production worker with fake
Device/SPI/clock/sys/logger, checking current KeyDiag task/NULL handle, zero
CONTROL/Device depth, report-before-resource routing, exact fields and180-byte
worst-width host payload (244 with64-byte framing reserve). Fake sys values are
not actual heap or stack measurements.

## Actual selected frames and open stack gate

| Actual ELF function | Entry frame bytes |
| --- | ---: |
| USB worker body (usb_test command inlined) |512|
| key_diag_usb::command / start |64 /80|
| diag_dispatch::launch |80|
| SdkLauncher::spawn_empty / Builder::spawn |144 /128|
| KeyDiag worker |720|
| KeyDiag report / key page formatter |528 /496|
| KeyDiag resource_sample / resource formatter |480 /288|
| DiagnosticCore complete / read |48 /96|
| FPGA driver program |192|
| SDK logger |128|
| AV run |2480|

These are selected prologues, not independent maxima to subtract from a task
allocation. Page and report frames can nest; indirect SDK/FFI/formatter/logger,
thread-runtime and interrupt/context overhead remain open. The new KeyDiag4096
allocation remains **PROVISIONAL**. Host layout figures in the source README are
host figures; release ELF has no usable DiagnosticCore DWARF type entry, so no
target object-layout claim is inferred from that query.

Each report is followed by separate inline-never `resource_sample` on KeyDiag,
outside Device/CONTROL. `USB_D24 v=2 p=key_resource` reports its own raw stack
minimum in bytes, declared4096, internal free heap and largest internal block.
This follows the earlier report/SPI path and precedes its own formatting/logging;
a later sample can include that path. These values are sampled separately.
The existing `?` continues to measure the USB task.

The model has one active I/O job, one capacity-one channel handoff and no frame
buffer, PCM buffer, Vec or boxed Core. Channel receiver allocation metadata
persists until the closure returns. OS task/stack reclamation is detached and
may overlap a later job after exit proof; there is no measured hard total heap
or reclamation bound. Runtime meters make the required later checks observable,
not satisfied. Stack minima, actual logger framing, query-cadence overhead,
internal heap peak/largest block, synchronous SPI WCET and physical admission/
drain behavior all remain **NOT_RUN**. No reboot fix, hardware qualification or
physical throughput claim is made.

## Preserved history and verification

The first build without the own-worker meter remains unchanged in `release/`
and `evidence/build-01/` (ELF9887ada690a8e23357cdaa930a53f42ee91ba78ff6146915c8583c6b4e29656a).
All1473 original bound artifacts, metadata, prebuild02 sources and selected-frame
evidence were copied before the resource change. Prebuild01/02/03 have raw input
and reviewed host-evidence copies. A postbuild helper's missing inherited
size-tool metadata key was corrected in appended `postbuild_finalize.py`;
original frozen helper and first-build history remain preserved. No SDK source
change was involved in that helper correction.

`evidence/build-manifest.json` binds the current bundle, SDK/config evidence,
selected ELF frames, resource-observability record and historical artifacts.
`python verify.py` checks current inputs, all artifact hashes, historical raw
snapshots and sealed v25/v24 parents. The separate read-only recursive audit
also passes all five sealed v24 parent guards,2652 hashes; its record is
`evidence/recursive-parent-guards.json`. Sealed v24/v25 and installed v22 are not
modified. No hardware, COM, USB-device, JTAG, flash or SD action was performed.
