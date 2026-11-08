# V59 throughput probe: measured costs and a visual failure

V59 was built, reviewed, installed app-only with complete readback, and tested against unchanged V029. The network performance trial completed all40 original frames with matching presentation replies; its final camera image matched the expected scene. The faster flash-backed trial also counted40 starts but produced broad false colors: **that result fails visual qualification and cannot establish a usable maximum FPS**. No120-frame hardware run or higher-rate sweep followed.

## Physical results

All three trials used the identical40-packet manifest `76b37ca8245b8ed657c6caabbbd9d416de3dd4c775b1626ed466699559623034`, one frame in flight, and a fresh software restart plus volatile reload of the same FPGA. All reported40 accepted/40 presented/0 rejected/0 underruns,844,800 HUD words written and zero native allocation failures.

| Trial | Source / evidence | Receiver elapsed | Starts/s including startup | Between-start rate | HUD words read back | Final camera |
|---|---|---:|---:|---:|---:|---|
| 01 control | Network, full readback |25.583813s|1.563|1.622|844,800|Expected scene|
| 02 diagnostic | Flash40, Wi-Fi off, write completion only |14.547563s|2.750|2.755|0|**False colors**|
| 03 diagnostic | Network, write completion only |19.738250s|2.027|2.115|0|Expected scene|

These rates count owner-matched LCD front switches at frame boundaries. RTL ties the event to matching generation/frame/slot, `frame_boundary` and `scanout_drained`; repeated display refreshes are excluded. A complete physical raster/panel-observation counter is absent. Final camera samples support placement/color observations, not exhaustive freeze or per-frame pixel qualification. No cross-machine clock subtraction was used.

| Mean completed-frame stage | Network control | Flash diagnostic | Network diagnostic |
|---|---:|---:|---:|
| Header wait + ingress/staging |206.82ms|72.80ms|199.15ms|
| Admission to HUD request |1.33ms|1.34ms|1.31ms|
| Native HUD Prepare |123.08ms|121.32ms|122.89ms|
| HUD write path |151.93ms|151.13ms|152.08ms|
| HUD readback |137.52ms|omitted|omitted|
| Software commit ACK to scanout switch |6.18ms|4.75ms|5.27ms|

Admission-to-HUD-request is **not a complete FPGA decode-time measurement**: background decoding and memory work may overlap later stages. HUD write timing includes native READ/packing, command submission/status and payload transfer; it is not raw QSPI line utilization. Ingress includes source-header waits and stop-and-wait network timing. Aggregate maxima/means are retained; percentiles and individual lock/credit stalls are not measured by this version.

Native decoding and the command-heavy HUD write path each exceed a33.33ms30fps budget even with Wi-Fi/readback removed. The current diagnostic serialization therefore needs substantial work; these trials do not establish the production codec or FPGA maximum.

## Implemented changes

- Fixed-size all-completed-frame stage counts/totals/maxima/bytes and scanout-start intervals; last-three detailed records remain bounded. No per-packet/per-frame USB print is added during playback.
- Explicit HC70 op4 arg2 distinguishes externally completed writes from full-readback arg1. Status bit5 binds that evidence through ACK/commit. In performance mode verified-word counts, readback timestamps and readback aggregates remain zero. All HBU write completion/status, ownership, decoded tags and packet integrity checks remain required; malformed/error paths cannot manufacture completion.
- Flash-backed40 uses the exact existing packets in DROM, no packet-sized SRAM allocation and no Wi-Fi setup. USB `1` launches network performance40, `2` network performance120, `3` flash performance40. Existing `&` full-readback40 and original controls remain unchanged.
- A checksummed-export summarizer rejects missing stages, corruption, inconsistent interval counts and false verification claims. Independent120-frame fixtures and all-frame telemetry enable longer trials after the gates below.

## Verification and versions

Full host suite passed28 steps, including69 driver and39 telemetry tests. New native evidence-mode negatives/rollback tests and exact flash-source bounds/content tests passed. Actual V59 native40 passed844,800 words plus80 malformed/late-failure and40 recovery checks. Native120 passed2,534,400 words plus240 malformed/late-failure and120 recovery checks; independent C++ oracle matched all120 canonical/HUD/display hashes. The first native120 harness incorrectly zero-padded filenames above99; that harness failure and its corrected rerun are retained separately. Models/host execution are not physical heap or sustained-rate evidence.

V59 SDK ELF `9ea80b4a4588925bd507477990a26e260ec6c116d358d06804b028fdf4cfc94f`; BIN `2db3f1bcdd635e76fb06a70e4430100a505f1737e99ff01b1abd1a40436f5035`; UF2 `a8d090eb7d656af90abbb63992c926e2fd4210f70595fba3e321213e0133e229`. BIN4,578,048 bytes fits factory5MiB with664,832 bytes spare. All40 packet byte strings plus pointer table were independently located in flash DROM. Static shared SRAM132,308 bytes passes163,840 guard. Native cap98,304, reserve8,192 and worker stack16,384 remain unchanged.

V029 BIT `59a2439488c529941661debcf3f3c75f8fd2f6e61418c3c63a45e377e971e7c3`, DONE1/USERCODE44593741. No FPGA rebuild. User-accepted setup0.000ns, hold+0.008ns and inherited bundled-status CDC caveats remain.

Native physical peak86,020/request maximum15,360/failures0 in every trial. Observed worker stack low values were884/1,588/860 bytes (trials01/02/03): **stack headroom needs improvement before longer or more instrumented hardware trials**. No stack-overflow proof is claimed. Minimum native free13,428/54,604/13,924; final largest blocks35,840/57,344/30,720. Each52-row export passed its indexed/checksummed validation; underlying USB transmit-loss count remains unknown. No all-core fault snapshot was collected.

App-only installation was backed up and readback verified; updater/table and SD files were preserved. The authorized WinUSB helper again returned a post-install description-check error; the error is retained, and independent PnP problem0/serviceWINUSB plus successful full backup/readback established access. This is not a claim that the helper returned success. No physical rail cycle or manual button press was required for this campaign after Windows UAC approval.

## Visual issue and next gates

The local flash trial's final frame39 is visibly different from the exact RGB565 oracle, despite matching IDs/tags and zero reported rejects/underruns. Full-readback network control and write-completion-only network trial both show the expected final scene. Thus **omitting readback alone did not reproduce the visual failure**; local source, no-Wi-Fi conditions and faster ingress are coupled factors. There is no selected fix or established mechanism. Exact V029 HBU/SDRAM/LCD sources were audited; no missing documented readback fence, direction reset or cache-refresh requirement was found. Readback changes traffic and delay and may hide another defect; do not assume that is the cause.

1. Reduce report/snapshot stack copies or otherwise establish safe stack headroom without weakening SRAM guards.
2. Add a local full-readback control and explicit flash chunk/inter-frame pacing controls; compare the same final frame and read-only memory evidence to separate source/rate/retirement effects. Keep the false-color mode unqualified.
3. Profile native Huffman/Rice decode costs, then optimize with identical-output/rollback checks; separately measure HUD write command/lock/payload time. Preserve V58/V029 as rollback and the exact JPEG V38/build50 recovery archive.
4. Improve HBU transfer efficiency/descriptor batching and overlap only after ownership/failure recovery and RTL timing verification. A higher QSPI clock or bitrate is not selected by these measurements.
5. Run the offline-qualified120-frame sequence, then longer source-backed sequences and rate sweeps, once stack/visual gates pass. Add isolated FPGA decode-throughput and complete-raster observation before claiming maximum displayed FPS. Audio/controller coexistence follows video qualification.

The120 fixture samples20seconds of the same local rendering clip at6fps; source sampling is not sender/display FPS. Original40 samples the interval at2fps. Both are RGB444/uniform codecq32, not Mass Effect/live Sunshine or JPEG Q32. No audio/controller/30fps claim.

[Source, installed artifacts and selected receipts](../../firmware/experiments/v59-throughput-probe-20261108/README.md). [Offline-qualified120-frame package](../../host/dy71-clip120-20261108/README.md). The final expected network image/endpoint remains held, senders/USB are stopped and bounded camera tails finish automatically. Raw flash and full Wi-Fi logs remain private under C:/moon.
