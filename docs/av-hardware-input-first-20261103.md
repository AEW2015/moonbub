# First AV v1 physical input result —2026-11-03

**Input transport passes; audio and Xbox injection are not yet verified.**
The host repeated a20-second input-only session from192.168.0.47 to receiver
192.168.0.157:5534, with audio and virtual-gamepad output disabled.

| Host-reported observation | Result |
|---|---|
|HELLO/OFFER/START|First attempt successful|
|MSI1 packets|954|
|Independent sequence range|0–953, no gaps|
|Invalid/stale/timeouts|0/0/0|
|Physical buttons|A0x800,Up0x080,Down0x040,Left0x020,Right0x010|
|Neutral releases|Observed|
|STOP|Sequence184 sent; successful exit|

The remote report is
`C:/ai/sunshine-gamebub/tools/gamebub/measurements/av-v1-input-first-20261103.md`
on the Windows sender computer. Its contents were supplied by the operator;
that filesystem is not available on the receiver computer. These are not
independently read host logs. Exact50Hz delivery and all12buttons are not claimed.

Receiver logs independently show the repeat active at01:27:20.019UTC and stopped
at01:27:40.025UTC on2026-11-04 (eveningNovember3 inAmerica/Denver). Wi-Fi power
save changed1→0 on valid START and restored0→1 afterSTOP; entry/restore errors0.
Post-run AV session inactive, malformed0/socket errors0, core faults0 and all
video/audio admission/decode/presentation/drop/play/underrun counters0 as
expected for input-only. AV worker stack low-water4548bytes; idle values do not
prove stack safety under audio load.

Installed application UF2 SHA256:
`d43b3137fde1d95358181b23c80d71d3ef908b074510c3d5ae0271d4b46e37d3`.
Selected FPGA build50/V4 SHA256:
`a1ca6ce6b2c333a7c2ad4d29b94a7adf683dc49669d7f87fe3f80e63ef9ef3f9`.
Runtime buildID0x4d424f50 and audio-online snapshots confirm communication.
Margin13/timing0, overlap,32-slot video queue and requested40MHzQSPI retained.

The next test is a10-second quiet stereo tone, video/injection off, using the
product-rounding-compatible encoder. Compare confirmed audio admission with
actual FPGA played/underrun counters and acoustic observation. Virtual Xbox
output still requires its Windows driver and a separate physical injection test.
