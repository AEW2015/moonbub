# Prompt for the Sunshine agent: prepare the next network gate

Prepare offline for the next coordinated MoonBub network test. Do not transmit
to the handheld until the MoonBub agent explicitly announces network readiness.

The local test is complete: **FAIL_RENDERED_CRC; custom network gate blocked**.
Two fresh snapshots reported `dec6d87d` rather than the frozen `4c5725e5`, despite
matching decode tags/counts. Build50 has been restored; v32 remains installed.
See `docs/CPL1-LOCAL-HARDWARE-20261105.md`. Prepare offline only; do not transmit.

MoonBub performed a **local fixed-ROM CP23 fixture test**. The
selected CPL1 image has BIT SHA-256
`e11a193a8cfe51b90053c852bdbb3d9308225bc1d115564418a64e016d6df789`.
Its offline routed setup/hold are +0.017/+0.032 ns, and its native digital model
passes. Programming and observer readback worked, but complete physical fixture
acceptance failed. A timing-clean digital model is not physical acceptance.

Read the current MoonBub handoff on `feature/fpga-timing-cleanup-20261105`:

- `docs/FPGA-TIMING-CLEANUP-STATUS-20261105.md`
- `fpga/exports/cpl1-timing-fsmcopy-source-20261105-v002/QUALIFICATION.md`
- The versioned contract and capability records relevant to your selected path.

Important capability boundary: CPL1 has **CAPS=0**, an immutable 17,412-byte ROM
fixture and a read-only retained-snapshot observer. It does not implement a
network upload/decoder endpoint, predictive/reference modes, a complete HD22
history path or an advertised full profile. Selected local scope is independent
KEY, CP23/HC22 mode 0 with HR01 INDEX_RUNS2. Do not substitute incompatible
CP25/GM25/HD25 data or infer a custom UDP port. Existing UDP 5533 MSV1/JPEG and
5534 AV v1 remain separate legacy services; never send custom CP23 bytes to them.

Please prepare these items without changing the installed Sunshine service or
the established baseline sender behavior:

1. Report your exact repository branch/commit, encoder/sender build hashes and
   supported wire profiles. Identify any mismatch with the selected CP23 subset
   before proposing a live test.
2. Retrieve the exact local fixture assets from the selected MoonBub export.
   Convert the byte-entry `key.cp23.hex` to binary offline and report its length
   and SHA-256. Validate its envelope/component CRCs, tags and supported modes
   against independent golden/reference code. Keep expected and actual results
   distinct. The local rendered-frame oracle is CRC32 `4c5725e5` over 345,600
   RGB565 words, little-endian, column-major (x outer/y inner), including HUD.
3. Run serializer, packet reassembly, malformed/oversize input, duplicate/stale
   identity, timeout and recovery checks against a local emulator. State exactly
   which implemented or proposed carriage contract those tests cover. Localhost
   success does not establish Wi-Fi delivery or FPGA readiness.
4. Prepare a saved, hash-verified moving clip from a recorded start offset for
   later repeatable tests. Preserve the existing JPEG/AV recovery/control setup;
   keep codec, quality, bitrate, pacing and capture changes isolated and logged.
5. Prepare frame and packet logs with session/epoch/frame identity, capture
   timestamp, chunk offset/length, CRC, successful socket-send times, send gaps,
   deadlines, replacements, partials, feedback matches and logger-drop counts.
   Arrange outbound interface capture through START, STOP and drain; record the
   interface, capture point and capture-drop count. This is not RF-arrival proof.
6. Return a readiness report and unresolved contract questions. For custom
   networking, agree peer/port, version, bounds, packet layout, capabilities,
   real credits/admission, ownership lifetime, reset/rekey, acknowledgements,
   completion/publication/presentation meanings, timeouts and STOP/recovery with
   MoonBub before any transmission. An ingress ACK is not decoder readiness.

The next live test is conditional. MoonBub must first provide fresh local-test
results, installed ESP32/FPGA identities and hashes, current IPv4 address, the
implemented receive mode/port, supported profile and starting counters. Historical
receiver `.157` and sender `.47` are not current readiness evidence. Confirm the
actual route/source endpoint before sending, and allocate unused frame IDs in a
new or explicitly reset session.

If no custom network endpoint exists after the local test, report that gate as
blocked and continue offline preparation; propose a separate existing MSV1/JPEG
control only after MoonBub restores and verifies its compatible legacy image.
When a matched endpoint is implemented and both agents are ready, begin with
one agreed known-good fixture at an agreed conservative rate/deadline. Hold
audio and controller injection off initially. Require independent receiver
decode, publication and presentation evidence plus queue/core/drain counters
before advancing to moving-video rate tests. Keep 30 **unique displayed** fps
as the final objective, distinct from encoding speed, ingress ACKs, simulation
and repeated scans of the same image.
