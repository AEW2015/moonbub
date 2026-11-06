# HUD expected-tag payload capture

Production candidate: `cu71_receiver_tagcapture_v001.sv`, SHA
`c17a9dbe93c92a88d5ee90f3c689e40845f56c8f3610e84e72f1dd39915f2d76`.
It derives from the **actual v005-selected** board-math receiver, SHA7991bfc5...
Only the128-bit hud_expected register moves to a separate synchronous-reset FF
block. Its data and capture clock remain unchanged; its enable uses the exact
non-HUD fatal predicates. Global fatal/code/state/error/first-fault/event producer,
event ring and diagnostics remain unchanged, with an exact source reversal.
No new false path or clock/reset/latency change is introduced.

Unbounded actual-control proof replaces only the three children with88 arbitrary
independent output inputs (all64 original inputs arbitrary). Actual owner initial
states are arbitrary: only a verification reset_seen bit is initialized, and the
property is enabled after an actual reset edge. It proves PARSER_START/METADATA
implies !hud_requested. Consequently meta_fire excludes abort and both HUD-fatal
predicates. A second temporal-induction proof checks the original-global-guard
capture enable against the new enable and compares every128-bit tag value to an
original-guard shadow on every edge after reset. All other original sequential,
fatal and diagnostic code is unchanged, giving the compositional reachable
owner-output equivalence argument. This is not arbitrary-SEU/X-state equivalence.

Generic optimized-FF inspection finds128 current-tag bits in the parent tag FF
CE cone and zero in the candidate cone. This is a structural cut, not a device
slack/fanout measurement. Actual selected validpipe receiver/base/controller and
qualified SDRAM pin-model runs pass KEY/P/P with native HUD and full canonical /
pixel/HUD checks. Parent/candidate control/failure and frame traces are byte
identical, including expected_hud_tag and all144 diagnostic words on each
state/event/error transition. Denied writes, abort drain, incomplete HUD failure71,
first-fault/event records, timestamps and presentation counters are preserved.
Native CPU time is outside the HDL model; no physical SPI/network/FW latency,
routed timing, BIT or hardware claim follows.
