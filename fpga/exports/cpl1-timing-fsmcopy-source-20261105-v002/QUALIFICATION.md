# Qualified offline candidate

Selected source: cp23-timing-raster-reservation-20261105; physical result: route-qspi06. Setup +0.017 ns, hold +0.032 ns, pulse +2.000 ns; zero violations. All four bus-skew constraints meet (minimum +3.450 ns). All 49,960 nets route without errors. Timing margins are small and reported exactly.

The canonical flow is the source build, AlternateReplication, AggressiveExplore, AlternateReplication, then the recorded equivalent FSM-bit copy/local placement. The final copy has the exact original FDRE D/C/CE/R nets, INIT and available inversion parameters. The image writer rechecks this equality against the final checkpoint. No frequency, delay budget, pin or timing exception was relaxed. Failed reset-distribution and IRQ-bank-placement trials are excluded from this recipe.

Full digital-board model: 139 checks, 40 native QSPI reads, CRC 4c5725e5, 259,200 modeled pad writes, all 1,440 line latches; minimum modeled line lead 2,818.878 ns. The source/asset execution bindings are included. Two held scans of one image are not a unique-frame throughput test. Fresh portable smoke passes 16 checks. Focused cancellation, base-CRC and late-HUD rejection records are included with their copied test inputs. The alternate replay suite's qualifying extended02 records are retained; failed earlier harness attempts remain in the development workspace.

This is a fixed-ROM, independent-KEY CP23/HC22 diagnostic, CAPS=0. There is no new network receive port or claim of full-profile/P-frame decoding. Installed v30/build50 is unchanged. Neither physical playback nor 30 unique displayed fps is established by these artifacts.

Retained timing coverage gaps: 17 inputs without delay, two outputs without delay and one partial input-delay declaration. External QSPI hold and unbudgeted/asynchronous I/O remain outside board signoff. Native DRC warnings are retained and counted in HANDOFF.json; no severity waivers were introduced. The supplied BIT is generated but has not been programmed. The local routed checkpoint is referenced with its hash; the portable source recipe regenerates it. A second complete P&R rebuild was not executed during packaging.
