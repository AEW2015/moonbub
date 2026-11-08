# DY71 finite sequence v3 host package

November7,2026, America/Denver. This package prepares a **finite, count-bound** CU66 diagnostic, not a live encoder, automatic negotiation or a30fps sender. It uses12 distinct retained `mass-effect-10000` frames. These belong to an older roughly-four-second corpus, **not the user's requested120-second Mass Effect clip**. Original frames0/1/2 are byte-identical to the qualified original pair/third-frame package.

## Contract

Profile `dy71-sequence-v3`; DYN1 data/DYA1 feedback, UDP5535. Same48-byte little-endian header plus datagram CRC32 as v2, with these explicit incompatible changes:

- Header byte4 is **3**. Old v1/v2 data/replies are rejected.
- The former reserved `u16` at offset46 is **sequence_count**, valid1..12000. It is included in datagram CRC and echoed unchanged in every reply. Peer/session/count remain consistent for the complete invocation. A mismatched count must be rejected by the receiver before staging.
- Reply matching includes session, frame, reference, complete packet length/CRC, capture timestamp **and sequence_count**. A valid-CRC reply with a different count cannot advance storage or presentation.
- One socket/session, one frame in flight. Manifest begins with an independent KEY; later frames are strictly increasing IDs and refer to the immediately previous accepted frame. No opportunistic skip, frame replacement, auto-KEY recovery or whole-run retry.

Other fields remain: magic0..3; version4; data flags/status5; header length48 at6; sessionu64 at8; frameu32 at16; referenceu32 at20; complete CU66 lengthu32 at24; chunk offset/completed prefixu32 at28; whole-packet CRC32 at32; capture timestampu64 at36; chunk lengthu16 at44; sequence countu16 at46. Data CRC32 follows48+chunk_length bytes. Data chunk maximum1024, total CU66 packet80..49152, HU payload<=20000. DYA1 replies are52bytes, chunk length0, CRC over first48bytes at48.

Status0 means completed stored prefix,1 all staged,2 actual presentation and3 failed/retained. Stored/staged feedback does not prove decode/display. Next dependent frame is sent only after matching status2. Per-chunk retries are identical/idempotent; the initial KEY can wait1..1800seconds (default600), later chunks retain10-second budgets and presentation90seconds. Any failure/unknown outcome stops. Final endpoint/lease retention and reset/reconfiguration are controlled by the receiver owner; this profile has no STOP or automatic session restart.

## Select the exact count, do not start unattended

`--count` explicitly selects a prefix of the qualified manifest and is carried on wire. The receiver must be armed for that same count/cache mode. Current firmware selectors are coordinated separately: `~` cached3, `@` cached12, `^` scalar3; this host does not issue USB controls or choose cache mode.

Prepare commands only; wait for an explicit coordinated hardware START:

```powershell
python test_sequence.py
python sequence_sender.py --profile dy71-sequence-v3 --count 3 --receiver 192.168.0.157 --bind 192.168.0.47 --initial-wait-seconds 600 --log fresh-v45-cache3.jsonl
# Only after the controlled 3-frame test and separate readiness for12:
python sequence_sender.py --profile dy71-sequence-v3 --count 12 --receiver 192.168.0.157 --bind 192.168.0.47 --initial-wait-seconds 600 --log fresh-v45-cache12.jsonl
```

No transmitter was run to hardware while preparing this package. Addresses are historical intended endpoints and need fresh confirmation. Print the first session/source/count/profile/manifest-hash line promptly while the single invocation waits. Do not reuse an old log or retry the whole invocation after failure. Keep JPEG, AV/audio and controller injection off for these diagnostic comparisons.

## Executed offline evidence

- Fresh Python CU66 reference decoded all12 chronological packets and checked canonical YUV/tag, HUD words and composed RGB565 hashes, zero base motion and dispatch5/6. All local tile-packed canonical/HUD/display oracles are indexed under `C:/moon/maintenance/v45-sequence/qualification`; only packets and hash manifest are duplicated here.
- Four missing-reference/stale/CRC fault controls rejected without publication changes. This is software-reference evidence, not full-system RTL or target playback.
- Eight pure fake-transport tests pass. They exercise all12 packets, exact prefix3, count-mismatched reply refusal, count/profile bounds, packet hash refusal, receiver-failure chain stop, valid-CRC v1/v2/invalid-count rejection and all24 published golden data/reply vectors. No socket is created by tests.
- Native allocation initially refused frame4 under V44's98,304-byte ceiling. The root's V45 in-place owned-motion prediction fix passes an independent actual-native12-frame check with **253,440 actual golden HUD words**, peak92,544 at the unchanged98,304cap/8,192reserve. The allocator/wire-lifetime model was run with114,688 and117,524 baselines; it excludes target allocator metadata, SDK activity, fragmentation and target stack. The conservative bound `114688-92544-12443=9701` excludes those costs and is not a target-free-heap guarantee. Target guards must remain active.

`native-fit-qualification.json` pins that exact V45 native header and logs; a later native change requires revalidation. Firmware target build/stack/SRAM, full-system canonical/scanout and physical gates belong to the receiver's final candidate report. Nothing in this package alone declares hardware readiness or12-frame sustained FPS.

## Two-minute encoder dependency

The reported Windows source is `YTDown.com_YouTube_Media__luGrl_3Ajc_Mass-Effect-Legendary-Edition-Combat_004_720p.mp4`, SHA256 `fb01977e41e649bfb9fd53d1ee0e6db436127fb86e4b3b7ec303158e0568aff5`. Its reported local path and the current Windows `C:/ai` checkouts are absent on this PC; do not infer the remote encoder's current capability from that absence.

There is a usable research encode chain: causal source preparation/`encode_prepared` -> arithmetic CS38 -> CU66 `protocol.convert` after canonical reference/output verification. The smallest new adapter should be **output-only** with explicit source SHA/offset0/no-loop/duration,720x405 content at(0,37) in720x480, dispatch5/6 and zero-motion receiver profile,49,152byte cap and defined oversize/re-encode/reference policy. It must advance references from accepted reconstruction, then independently decode every output and hash canonical/HUD/display results. Existing monolithic scripts write frozen cohorts and must not be rerun into them. JPEG Q30/Q35 does not map automatically to CU66 quantization policy. The retained12-frame package cannot substitute for the requested source or establish a2-minute playback rate.
