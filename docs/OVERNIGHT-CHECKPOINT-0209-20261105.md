# Coordinated MoonBub checkpoint, approximately02:09 Denver

November5 overnight work follows Sunshine plan commit16c290bc. The final baseline repeat is reconciled. **No firmware/FPGA installation, device query or new hardware sender occurred during development.** Game Bub can remain powered off. Installed control was last verified as v30-sequence-window-20261105, retained build50, overlap and32 slots; future readiness requires fresh identity/network checks.

## Ready and unfinished paths

| Path | Current evidence | Readiness |
|---|---|---|
| Existing JPEG/AV with v31 diagnostic app | Target check/release, production app-only UF2 parser, portable host checks and one clean relocated release pass | Candidate ready for a separately coordinated regression; not installed or physically measured |
| CP23 exact one-frame KEY + HUD | Complete byte ingress, outer/component integrity, decoded tags, real modeled physical storage and native composite scanout pass | Functional simulation; whole timing, board image and physical checks incomplete |
| CP23 fixed local ROM loader | Exact17,412-byte ROM through the actual composite; positive consumer release and held cancel/reset quarantine tests | Local RTL loader/composition passes simulation; no CSR/firmware hook, routed board image or physical result |
| Two distinct independent CP23 KEY frames | Both exact base/HUD pairs, disjoint storage, safe joint native handoff and four refreshes pass | Finite two-slot simulation; negative second-candidate test still running; no general bank reuse/reference allocator |
| Custom network fixture | No live carriage/port/capability assigned | Not ready; do not send custom data through JPEG/MSV1 or H.264 identifiers |
|720x480 at30 unique physical presentations/s | Not measured | Not ready for acceptance; simulations and encoding results do not establish physical FPS |

The selected first-fixture profile stays **CP23 / HC22 / HD22**. Current RTL supports the explicitly restricted independent KEY, HC22 mode0 and HR01 INDEX_RUNS2 subset. HD22 histories, P prediction and general reference/recovery semantics are not implemented. CP25 remains unselected.

## ESP32 and baseline diagnosis

The final unchanged-pacing baseline encoded600, sent526 complete and replaced74;522 accepted,3 rejected,1 unmatched(2014108). Receiver added522 received/decoded/presented and3 drops, with zero packet-queue drops and cumulative high15/32. STOP restored power saving. Epoch3 exported completely but lost2085 diagnostic records. The partial outbound Npcap capture positively observed2013780/10240 and2013900/SOF; it ended before the final boundary/STOP. It does not locate the transition to receiver assembly or prove RF delivery. No streaming fix was selected from those unknowns.

V31 removes full phase-max collection from the hot trace-record mutex and adds eight per-kind loss counters, not a packet-identity journal. Actual static SRAM130436B(+32), Trace8272B(+32), record entry frame320→192B; summary-page frame816→896B. USB trace v2 and its collector preserve v1 replay support. Physical stack/heap, trace-loss and delivery improvement remain unmeasured.

Published branch: `feature/overnight-30fps-20261105`, checkpoint commit `25b03c6`. The portable v31 package contains all568 selected inputs/602 files and the original app-only UF2; its manifest is `5aac54272fcfd15f7d440dc58c669620626d37243da46d2d2b6d162960ce0607`. The supplied UF2 is `380bf1c894744cc38e3b7988c8d1aaa4c10faefd499cca937eb27548a639024b`. One clean relocated build completes without another GameBub checkout; external pinned toolchain/IDF/Cargo/component caches remain required. Its new ELF is unselected; the supplied UF2 is unchanged.

## FPGA results and active timing work

- First exact CP23 fixture:518400 canonical bytes,21120 HUD words,259200 real modeled physical words,691200 composite pixels and1440 native latches; zero mismatches/misses/underruns.
- Distinct second fixture:17700bytes, epoch1/frame1, packetSHA `14cf325480e324dc1a5c6ab8bf64b1e4df4e1d5bb1ead61f0ff4162549c805ca`. Two independent generations and reference validations agree. Both complete displayed images differ in296801 pixels. Concurrent second decode/store qualification takes2774374 nominal100MHz cycles,27.74374ms; this is one functional simulation latency, not sustained FPS.
- Local ROM feeder: guarded unreset ROM data, stable held bytes, fresh consumer-release fence. Reset or a timeout does not prove drain; after accepted work the wrapper quarantines logical reset rather than claiming warm release. Loader held abort is explicitly adapted to one consumer cancel pulse while its byte/ownership fence remains asserted.
- Synchronous gather cache: matched standalone22950→1113LUT,12398→736FF, using18RAMB36. Native unit/static/concurrent tests pass; measured line-service increase is one clock, not an assumed deadline margin.
- Explicit registered transpose byte read:16→8RAMB36 without an acceptance/service-cycle increase; directed/full/final-flush-abort pass against the original leaf every cycle. Its component synthesis estimate is positive; its board timing is not established.
- Combined cache/transpose exact CP23 composition:44912→25638LUT,33525→21939FF,101/135 total BRAM tiles. Full native and cancellation/privacy tests pass. Setup estimate still FAILS at-4.829ns; unresolved CDC and board/routed/I/O gates remain. No exceptions were added to make the result pass.
- Next isolated timing composition adds a canonical-byte metadata stage, registered request addresses on existing FSM prepare edges, and already-validated fixed HUD geometry arithmetic. Native/abort/unit checks are running before its whole synthesis result. Previous failed launch/inference/handshake attempts remain preserved and are not selected readiness evidence.

New local component experiments and full raw evidence are being sealed; only the named portable publications above should be assumed present in a remote checkout. Further source exports will bind exact consumed inputs and licenses rather than depend on undeclared local repositories.

## Next coordinated physical gate

Keep Windows installed Sunshine and sender behavior unchanged during overnight software work. Do not combine the first v31 diagnostic comparison with the Windows pacing candidate. After a separate installation window, the proposed legacy regression is the same Xonotic clip/hash/offsetzero,20fps/4Mbps/Q25,input-only AV,audio/injectionoff, build50/overlap/32slots. Use unused IDs2014200 or newer, fresh starting counters/identity, full camera coverage and outbound packet capture through STOP. Reconcile every outcome, trace loss and power-save restoration before another soak.

A custom local hardware fixture is separate: require a compatible source-bound decoder/loader image, positive routed setup/hold/pulse and memory/CDC/I/O/reset evidence before programming. No date or30fps outcome is promised by the functional simulations. Development continues toward the morning handoff, approximately06:09 Denver.
