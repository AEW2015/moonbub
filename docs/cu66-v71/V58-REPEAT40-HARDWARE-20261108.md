# V58 / V029 unchanged forty-frame repeat

The second controlled trial passed: **40 accepted /40 presented /0 rejected /0 underruns**, with **844,800 HUD words written and verified**. Receiver elapsed **25.415006 seconds**, versus26.532393 seconds on the first trial. This is reproducibility evidence, not an isolated speedup or20/30fps acceptance.

No firmware, FPGA logic, fixture, transport, caps or intentional frame delays changed. A nonce-bearing software REBOOT was accepted by verified V58 before reloading the exact V029 volatile BIT; no firmware flash or physical rail cycle was needed. Cold CPU12 passed before programming. Initial memory175,120 free/largest83,968. The final image and successful endpoint/lease remain held; sender stopped with exit0, no whole-run retry.

Session15853432817710338057, source192.168.0.33:59488 to192.168.0.157:5535. All forty matching status2 replies arrived. The81.172-second sender invocation includes readiness waiting and must not be treated as playback time. Receiver QSPI transactions92,835, reads561,340, writes723,304; final free72,884/largest36,864, observed stack low2,772 and minimum native free13,632. These are local observations, not a proof of whole-stack bounds or all-core fault clearance.

Both read-only exports validated all43 rows with complete indexed/checksummed boundaries. Underlying USB transmit-loss count remains unknown. Camera coverage included the entire playback interval; sampled views show the decoded final scene with the full handheld display visible. No exhaustive freeze or full canonical-pixel verification is claimed. The bounded300-second camera tail completes automatically; raw recordings stay private under C:/moon.

Exact unchanged versions: V58 SDK ELF `c7d9452a123db12c9edeede96551a3bb6c1206da617ad431103656aba6f476c4`; V029 BIT `59a2439488c529941661debcf3f3c75f8fd2f6e61418c3c63a45e377e971e7c3`, DONE1/USERCODE44593741; fixture manifest `76b37ca8245b8ed657c6caabbbd9d416de3dd4c775b1626ed466699559623034`. Same user-accepted zero setup margin and inherited CDC caveats apply.

This is the same20-second rendering-clip interval sampled2fps, RGB444/uniform codecq32, not Mass Effect/live Sunshine, JPEG quality settings, audio or controller coexistence. Installed firmware only exposes up to40 frames per trial. Extending count/duration or changing performance instrumentation requires a separately verified candidate.

[Selected hardware evidence](evidence/v58-repeat40-20261108/preservation.json). [Source, images and first-trial report](V58-CLIP40-HARDWARE-20261108.md).
