# Matched staging timing experiment

Exact `xc7a100tcsg324-1` synthesis OOC used identical Tcl with200MHz SPI,
100MHz core,1ns maximum IO budgets and the same scoped CDC commands. No placement,
routing, BIT generation or hardware operation was performed.

| Metric | Original split DY71 | Registered credit | Safe credit |
|---|---:|---:|---:|
| Worst held_count CE setup | −1.039ns | +4.046ns | +4.595ns |
| Admission-path logic levels | 22 | 4 | 3 |
| Global unplaced setup | −1.039ns | +0.445ns | +0.445ns |
| Global unplaced hold | −0.751ns | −0.751ns | −0.751ns |
| Minimum pulse-width slack | +2.000ns | +2.000ns | +2.000ns |
| LUTs | 1663 | 1647 | 1702 |
| FFs | 2245 | 2282 | 2285 |
| RAMB36 | 17 | 17 | 17 |

The original packet_bytes→held_count CE path contains14 CARRY4 cells. Both new
variants eliminate direct packet_bytes/written_bytes→held_count timing paths.
Their worst admission path now starts at the actual queued-write BRAM. Safe
credit-update setup remains+2.873ns; global setup moves to the unchanged SPI
FIFO-enable path. The safety variant intentionally changes malformed concurrent
discard/upload behavior; normal loader/control-cycle equivalence passed.

The source-bound comparison is `comparison-ooc-v001.json`; combined safe
functional/OOC binding is `safety-v002/qualification-ooc-v002.json`. The initial
`ooc-old01` failed after producing reports because an observer query requested
credit registers absent in the original. Its evidence remains retained; clean
`ooc-old02` is the comparison control.

These are unplaced timing estimates, with negative global hold. No invalid
startpoint warning appeared in these OOC scopes. The separate full-board legacy
bundle selector warning remains real and requires root's exact C→D successor
audit; this experiment does not qualify those whole-board constraints or CDC.
