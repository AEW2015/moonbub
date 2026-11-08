# STB1 post-place margin experiment v003

PREPARED, HELD. No Vivado process has been started. Other agent owns current query/export; root must explicitly release the launch hold.

Source is exact immutable V001 placed.dcp; V001 routed checkpoint and selected BIT remain preserved. prepared-bindings.json pins both checkpoints,79-input source manifest and scripts. No RTL, XDC, clock or exception edits.

query.tcl derives the actual CE net from semantic endpoint control_plane/hud_ticket_reg[4]/CE, instead of guessing E[0] from the routed netlist. It must have one actualLUT4 driver. It records exact net/pin/cell/INIT/loadcount, through/endpoint timing, installed help, clocks and exceptions. If the post-place mapping differs, root reviews the actual evidence before any physical call.

After root releases the query hold, set allow_query true in review-approval.json and run:

`python C:/moon/builds/stb1-margin-v003/run-phase.py query`

Then review target-review.tsv and both actual timing reports, and pin its SHA256 in review-approval.json as target_review_sha256. Root must set allow_optimize true before:

`python C:/moon/builds/stb1-margin-v003/run-phase.py optimize`

Physical script re-derives and compares every query field before calling force_replication_on_nets on the exact matchedLUT4CE driver net, now in POST-PLACE context. It stops on unsupported option/no-op and retains evidence. It does not replicate the low-fanout generation register.

After successful replication: baseline-identical route_design NoTimingRelaxation, phys_opt_design AggressiveExplore, route_design Explore -tns_cleanup; then new routed checkpoint and all timing(setup/hold/pulse/unconstrained), route, DRC(no waivers), CDC, exceptions, clocks, skew, check_timing and LCD-output reports. No BIT/hardware. A positive result is only selected after root compares all gates and source hashes; V001 stays the fallback if this regresses.

A negative launch test confirms the default HOLD approval rejects before creating a launch receipt or starting Vivado. Python syntax is checked. VivadoTcl is prepared but not executed/qualified yet. Native post-route error4-265 from the separatev002 trial is retained there; this experiment intentionally starts at a different, documented supported optimization stage and requires a full reroute.
