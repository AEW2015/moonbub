# V47 cold CPU12 physical result

V47's app-only installation was verified by post-reboot USB: exact ELF `592b8607c039e0d7d55c3eec046deef829ca464ade2ebe839cea55e70d859779`, variant `v47-dy71-hud-order-20261107`, reset reason3.

One USB `I` invocation passed all twelve native HUD frames before Wi-Fi or custom FPGA programming. All253,440words were read and their per-frame CRCs matched ROM golden values. The98,304-byte arena recorded peak88,830, maximum allocation15,360 and zero normal-run failures. V46's corresponding physical peak was92,400, a3,570-byte reduction. The deliberately restricted1,024-byte arena correctly rejected an allocation and caught the exception.

CPU12 elapsed2,894,706microseconds including readback and the negative test. Worker stack low-water was3,100bytes. Before the probe the menu query reported166,192free/83,968largest. After probe completion and entering Game view, the pre-programming query reported174,576free/83,968largest; different UI states make these unsuitable for leak subtraction.

Frame3 passed again in the cold CPU test. This does not establish that the network-time fragmented allocation failure is fixed. No network uploader was armed for CPU12 and no hardware presentation count is inferred from it. Next is one cached12 network trial with unchanged V027 and the pinned sequence-v3 uploader.

Evidence: `C:/moon/dev/evidence/v47-v027-network-20261107-run01/CPU12-RESULT.json` and raw USB capture. [Machine-readable result](V47-CPU12-HARDWARE-RESULT-20261107.json).
