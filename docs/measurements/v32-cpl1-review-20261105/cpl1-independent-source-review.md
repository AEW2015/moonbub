# CPL1 independent source review

Reviewer root;2026-11-05, before board implementation. Reviewed the source draft, board top, retained CSR and rendered CRC modules. This note is outside the agent-owned candidate; its source gates and manifests remain authoritative for exact revisions.

The top keeps the pinned service/panel clock generators and actual dotclock forwarding polarity. It reserves a distinct CPL1 identity with zero advertised capabilities. The snapshot write has no data-plane control route. Observations use additive ports rather than hierarchy peeks or substituted fixture constants. Actual post-read canvas CRC simulation independently matched4c5725e5, across two completed native canvases; this is modeled data-path evidence, not device SDRAM readback.

The captured40-word layout agrees with the v32 observer. All fields latch together, and generation/cookie exhaustion fails closed. The queried diagnostic values remain historical. CRC input is LE16 column-major, with explicit coordinate continuity and sticky invalidation; idle cycles do not count as gaps. Held-image canvas sequence is deliberately separate from unique video-frame rate.

Post-issue lock loss quarantines the local job and prevents automatic replay. Paired service-domain bridge reset behavior is retained. Reference-domain lock synchronization and the added core job-reset chain are explicit; an interrupted accepted SDRAM operation is not described as safely drained or memory-retained. Bootstrap and writer retirement are separate from front-bank release.

One baseline source gate remains open: the inherited LCD line-bank pixel read and bridge queue read are unconditional through their reset intervals. The agent recorded this instead of claiming containment. A separate successor is approved to guard the LCD read when reset_n is high and the bridge read when core_reset is low, leaving RAM data unreset, with matched source/full/reset checks. It must retain its own provenance; the observer-only baseline cannot borrow those results.

External SDRAM/LCD budgets are unchanged. Existing QSPI maximum propagation constraints do not prove external hold. Current source/simulation review is not routed timing, CDC signoff, BRAM post-synthesis enable proof, pin/electrical qualification, a BIT release or hardware readiness. No exception or severity relaxation was selected in this review.
