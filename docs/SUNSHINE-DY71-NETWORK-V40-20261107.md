> November 7 current status: V43/V027 passed the original KEY/P network pair; the receiver is still a two-frame diagnostic, not a continuous streaming endpoint. Next work is tracked in the [continuous CU66 / Mass Effect plan](cu66-v71/CUSTOM-CODEC-STREAMING-PLAN-20261107.md). The V40/V41 readiness statements below are historical. Do not transmit without a fresh coordinated START.

## V41 follow-up: physical SRAM admission

V40 installed and connected to.157, then cleanly refused its140000-byte guard with118116free/largest37888, before any FPGA writes. No START or network payload transmission occurred.

[V41 receiver fix](../firmware/experiments/v41-dy71-memory-reserve-20261107/README.md) is built/packaged and host-tested, installation pending. It caps the native arena at98304 and checks actual internal heap before each native allocation against8192reserve. Initial free-heap admission is114688 with largest24576. Forced physical-low-memory rejection is tested. Runtime stack/heap and actual network KEY/P remain untested. Same V023,16KiB worker and exact DYN1 wire/KEY/P/uploader. Windows can keep its pinned5e4013ec uploader ready and stopped; no refetch is required to send.

# Sunshine / DY71 next integration gate

V40 implements an explicit two-frame CU66 network lab endpoint for the color-verified V023 FPGA. It is built and tested offline, not installed. No live Windows CU66 encoder or production network agreement is established.

[Complete DYN1 v1 contract, port5535, credits, integrity, presentation and recovery](../firmware/experiments/v40-dy71-network-lab-20261107/docs/SUNSHINE-DY71-NETWORK-LAB-v1.md).

[Reference uploader](../firmware/experiments/v40-dy71-network-lab-20261107/tools/dy71_fixture_sender.py) and [golden vectors](../firmware/experiments/v40-dy71-network-lab-20261107/docs/golden-vectors/).

Windows branch `gamebub/cu66-v70-windows-20261105`, commit `15ca3422`, was reported to qualify the exact retained key/P fixtures offline. First adapt/test the uploader against this lab contract, wait for installed-app and heap/identity readiness, then transmit the exact original pair on request. Do not send JPEG/MSV1 to5535 or start a sustained stream. No network run has been started by this handoff.

Next after KEY/P: bulk HUD service and continuous ownership, live host encoder, stage timing and sustained-rate tests; audio/controller coexistence follows video. V023 scalar diagnostics took about54seconds for two frames, so this is correctness bring-up, not interactive or30fps readiness.
