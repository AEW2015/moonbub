# V46 cold CPU-only twelve-frame hardware result

V46 was installed through the Rev4 app-only updater. Post-reboot USB query verified exact ELF `bd955c61ac3f23660b79edfcfdd79b1eb3f4c2fbe06ac5f916bdcd4da18ade10`, variant `v46-dy71-native-failure-20261107` and reset reason 4. No network uploader was armed for this check.

USB `I` ran once before Wi-Fi or custom FPGA programming. All twelve native HUD frames passed readback CRCs against their ROM golden values: 21,120 words each, 253,440 words total. The native arena stayed within 98,304 bytes, reached a 92,400-byte peak and reported zero normal-run allocation failures. Frame3 passed; the V45 network-run failure did not reproduce under these cold CPU-only conditions.

Elapsed time was 2,898,645 microseconds including readback and the negative check. Worker stack low-water was 3,084 bytes. A deliberately constrained 1,024-byte arena correctly rejected an allocation and the exception was caught. Before the probe, internal heap was 167,364 free / 83,968 largest; a later post-probe menu query reported 165,308 free / 83,968 largest. These are separate samples, not a measured allocation-leak attribution. Normal test teardown and other firmware activity occurred between them.

This is target-native correctness evidence, not FPGA or network playback, maximum stack proof, or a fix for V45's frame3 failure. The cold probe cannot reproduce Wi-Fi-time fragmentation, network ownership or FPGA interactions. Prepare times were approximately 88–153 ms per HUD; do not infer 30 fps capability from this result.

Evidence: `C:/moon/dev/evidence/v46-v027-network-20261107-run01/CPU12-RESULT.json`, corresponding raw USB capture and exact selected release. Next is one coordinated cached12 network trial on unchanged V027 using the new failure diagnostics. Windows remains stopped until its uploader-wait coordination.
