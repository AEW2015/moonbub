# MoonBub six-hour development window

Latest status: see [morning handoff](OVERNIGHT-MORNING-HANDOFF-20261105.md) for the final actual-board setup failure, newer address-strength component, current source packages and proposed next hardware gate. Earlier checkpoints below retain their original scope.

Window: November 5, 2026, approximately 00:09–06:09 America/Denver. Coordinated with Sunshine plan commit `16c290bc`; the exact downloaded plan and hash are under `evidence/overnight-coordinated-20261105`. No unattended physical sender, firmware installation, FPGA programming or pacing change is part of this window. Preserve installed v30/build50, overlap and 32 slots.

## Closed baseline and unresolved evidence

The final unchanged-pacing repeat is complete: 600 encoded, 526 complete, 74 replaced; 522 accepted, 3 rejected, 1 unmatched (2014108). Receiver increased522 received/decoded/presented,3 dropped; packet queue drops0, cumulative high15/32, core faults/overflows/underruns0. STOP restored power saving. Full-panel camera covered START through STOP. Epoch3 is completely exported but lost2085 trace records. Npcap independently observed first-failure offset10240 and the later SOF at2013900; last9seconds/STOP were not captured. These observations do not locate the loss/reordering stage. See `evidence/hardware-v30-sequence-20261105/run-2013600/packet-audit-e732dbd7/CORRELATION.md`.

## Parallel ownership

| Track | Owner | Concrete next deliverable |
|---|---|---|
| ESP32 M1 | gm01_timing | Isolated v31 trace critical-section reduction, bounded per-kind loss counters, versioned USB export/collector, host+target memory/build checks |
| FPGA concurrent storage | io_cdc_review | Full second candidate decoded/stored while prior immutable front scans, exact memory/pixel/latch comparisons; no forced promotion |
| Contract/fixture/repository inventory | overnight_inventory (Luna) | Source-bound selected CP23/HC22/HD22 assets, repository/branch state, local-loader and unfinished-stage inventory |
| Integration and FPGA feasibility | root | Cross-review, safe publication/rekey seam and bounded timing-cost repair, coherent reproducible readiness handoff |

Independent source successors must not edit sealed parent artifacts. Heavy builds are coordinated to avoid benchmark interference. Simulation correctness, synthesis estimates, routed timing and physical playback remain separate gates.

## Order of work and gates

1. Archive both v30 epochs and host correlations; select CP23/HC22/HD22 static independent KEY plus restricted full legacy HUD fixture. Do not advertise HD22/P/reference paths not implemented.
2. Remove measured tracing work from hot mutex scope; quantify bounded SRAM and tests before target packaging. Trace gaps must be observable without making packet absence into evidence of RF loss.
3. Finish concurrent storage/scanout test and bind exact RTL, fixture, memory model and commands. Advance owner/cache handoff only when real drain and line-service invariants are checked.
4. Quantify FPGA storage resource/timing constraints in isolated OOC work. A synthesis estimate is not a routed board image or hardware-ready decoder.
5. Integrate exact CP23 base/HUD ownership and presentation only against actual implemented interfaces. Preserve unsupported modes and missing local-loader/network gates explicitly.
6. Publish source-bound results and next-test recommendation. No new custom port/profile is allocated without coordinated agreement. No custom payloads on JPEG/MSV1 ports.

## Handoff checklist

- Exact candidate source/artifact hashes, Git branch/commit where available, parent manifests and reproduction commands.
- Executed tests and preserved failures, static SRAM/stack observations, resource/timing estimates and unresolved gates.
- Local custom decoder, local loader, live endpoint and measured30fps readiness stated independently.
- One proposed controlled next physical test with a single changed variable, fresh camera coverage, counters, STOP restoration and unused IDs (next range starts2014200 or later).
- Windows precise-pacing development remains owned by the Sunshine agent; MoonBub does not change the installed service or remotely transmit during this work.

## Checkpoint at approximately01:25 Denver

- Published branch `feature/overnight-30fps-20261105`, latest commit `25b03c6`: complete portablev31 source/UF2 plus exact-input fixes, clean relocated target-build evidence and portable transpose read-index component. A Git-archive replay verified all602v31 files/all568 inputs after inherited ignores initially excluded four paths; the correction is a separate commit.
- V31 original target check/release and one clean relocated release pass. Static SRAM130436B(+32), Trace8272B(+32), record frame192B versus320B. No physicalv31 result; installedv30/build50 unchanged.
- Exact17,412-byte CP23 restricted KEY composition v006 passes every canonical byte,21,120HUD words,259,200 modeled physical words and two full composite refreshes/1440latches, with zero pixel/latch/underrun faults. v006 removes a real coordinator READY→VALID loop found in v005synthesis; no automatic timing exception is accepted. Whole-component estimated timing remains negative, so it is not a board image.
- Independent full-concurrent storage and safe same-image descriptor/cache rekey simulations pass. Distinct-frame composition is now separate work; the bank-release/network contract remains unimplemented.
- Synchronous BRAM gather passes native-oracle units and static scanout: maxline1702clocks(+1), matched standalone resource reduction22950→1113LUT /12398→736FF, using18RAMB36. Concurrent memory contention check is still running.
- Local17,412-byte fixed ROM loader passes234checks with fresh consumer-release fencing; actual composite integration is pending.
- A second CP23 epoch1/frame1 fixture is being verified without changing the selected profile. Its distinct composite will support the next finite two-owner publication test.
- Further isolated work: registered shared transpose byte read, bounded canonical-byte pipeline and exact negative/abort lifecycle tests. Any incomplete result remains a gate; no candidate is installed overnight.
