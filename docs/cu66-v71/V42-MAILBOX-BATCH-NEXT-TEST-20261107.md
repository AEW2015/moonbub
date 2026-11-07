# Next test: V42 mailbox batching on unchanged V023

[Candidate source, checks and procedure](../../firmware/experiments/v42-dy71-mailbox-batch-20261107/README.md).

V41/V023 baseline: two presented frames with matching host status2, zero rejects/underruns,42240HUDwords verified; scalar58.043306s including49.982510s HUD writes/readback. V42 changes only bounded register transaction grouping and adds actual QSPI transaction counting. SDK, native allocation reserve, network wire, original fixtures, Windows cbbd85fda uploader and V023 BIT stay the same. Offline native, burst fault and exact-selected-pin/CDC tests pass; target build/UF2 parser/SRAM guard pass. No physical V42 pass yet.

Native HU CPU0.21?0.30s/frame is also a measured future limit. This candidate does not establish interactive video or30fps, and it does not implement the future bulk HUD endpoint.
