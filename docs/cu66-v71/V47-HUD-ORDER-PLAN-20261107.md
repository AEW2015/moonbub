# V47 bounded HUD allocation candidate

The V46 network trial failed an11,520-byte native malloc with35,284total free but7,680largest internal block. Its cold CPU-only12 test passed. The next experiment changes candidate allocation order, keeping V027 and sequence-v3 unchanged.

V47 parses all four bounded component slices, reserves four output descriptors once, then decodes larger fixed patches first: canonical indices2,3,0,1. Results remain in canonical output order; reference indices, reconstruction tags, native cap98,304, physical reserve8,192 and commit/abort authority remain unchanged. Accepted prediction data is not freed or overwritten early. If multiple components are invalid, the first reported component error may change.

Host verification checks exact HUD output and reference progression across twelve frames, broader retained semantic inputs, allocator rejection, late-component rollback and stale/newer-generation behavior. Fragmented-heap comparisons use the local ESP-IDF5.4.3 TLSF implementation with bounded backing and pinned holes. They are synthetic64-bit-host layouts, not the ESP32's exact live heap. Only runs with intact allocator metadata are eligible evidence. Exploratory invalid runs must remain identified separately.

This is a targeted candidate, not a guarantee for every fragmented layout. Fixed reusable output storage or a bounded pool remains a larger alternative if hardware still fails. Do not increase memory limits or change FPGA/wire behavior within this experiment.

Hardware ladder after offline qualification:

1. Preserve V46 failure and rollback artifacts. Stop Windows uploaders. Install only the exact app image through the existing physical updater and verify reboot ELF.
2. Run the cold CPU-only12 test once, checking all CRCs, allocation failures and measured stack/heap. Stop if it fails.
3. Reload unchanged qualified V027, verify DONE/USERCODE and pre-Wi-Fi memory, then coordinate the same pinned sequence-v3/count12 uploader.
4. Arm one cached12 trial. Require12 matching presentations,253,440 actual HUD comparisons, no native allocation failures, cap/reserve respected and complete retained diagnostics. On failure, retain/quarantine; do not retry automatically.
5. Reconcile host outcomes with receiver exports. Only after bounded success consider a longer distinct sequence; this diagnostic path still does not establish30fps or full120-second playback.

All physical V47 results remain pending. The current handheld is V46 with its failed endpoint retained until the coordinated update. Sources, builds and evidence remain underC:/moon.
