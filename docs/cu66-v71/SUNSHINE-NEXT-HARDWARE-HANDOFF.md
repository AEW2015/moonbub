# Morning hardware order and host coordination

Current development branch: `feature/cu66-board-v71-20261105`, derived from
CU66 v70 `fcc02c58d46f96a26790ce02826a0bf937c2478b`. This is a development
handoff, not a streaming release or a new wire contract.

## First: the separate existing JPEG 25 fps test

Keep the established MSV1/MSF1 JPEG and AV paths and the already coordinated
sender settings. Last physically verified handheld image is ESP32
`v32-cpl1-observe-20261105` plus FPGA build50. The older CP23/CPL1 timing
diagnostic was tested locally and build50 was restored; it is not the new
CU66 decoder. No new ESP32 application has been installed overnight.

Do not infer present readiness from historical IP `192.168.0.157` accepting
`192.168.0.47`. Before transmission the receiver agent must freshly confirm
installed identities, configured sender, port/mode, baseline video/queue/core
counters, recorder and full-display camera coverage. Use new frame IDs and
retain the existing source/hash/start position and host logs for that test.
Ingress ACKs remain distinct from decoded/presented counters.

## Then: the new local CU66 fixture

The next app is **v36**, built and packaged but not installed. Its local USB
commands explicitly select a profile; there is no automatic compatibility
guess:

| Command | Profile | Magic | ABI | Capabilities |
|---|---|---|---|---|
| `G` | CU71 RGB diagnostic | `43553731` | `00010000` | `7` |
| `Y` | DY71 direct-YUV diagnostic | `44593731` | `00010000` | `f` |

The selected DY71 source includes the actual CU66 parser/entropy/inverse/hash
and owner, native HUD service, canonical SDRAM references, direct YUV/HUD
scanout, bounded grouped arbitration, SYNCsafe LCD crossings and split CSR
read addressing. Its full-board implementation is running; no qualified BIT
or physical CU66 playback is claimed. A clean three-frame simulation still
has a 46.10029 ms presentation interval, so it does not qualify 30 fps.

First hardware fixture will be USB-driven KEY/P with host senders stopped.
It requires complete exact-source firmware/FPGA functional and board timing
gates, final BIT/ELF/BIN/UF2 hashes, the known app-only UF2 physical button
step, post-boot identity check, CPU exception probe and guarded local test.
Keep the native endpoint/maintenance lease held after accepted mutation as
designed; recovery uses the qualified paired reset/reconfiguration procedure,
not a guessed command. Preserve the build50 rollback and settings/SD files.

**No CU66 network capability, UDP port, Sunshine sender profile or custom
streaming test is offered yet.** Physical local playback and final board
qualification come first. Windows can continue its existing localhost work
without changing the tested JPEG/AV contract or transmitting to the handheld.

## Evidence to reconcile after local testing

Record the exact app ELF identity and FPGA USERID/USR_ACCESS, fixture/profile,
source manifests and image hashes; actual accepted/front generation/frame/tag,
canonical/HUD checks and real presentation acknowledgments; LCD underruns,
memory/QSPI/bridge faults; task stack high-water and free/largest heap before
and after; camera observations and rollback identity. Keep simulation clocks,
CPU benchmark times, physical playback and sustained unique display rate
separate. Audio/controller coexistence and a new CU66 network contract remain
later coordinated steps.
