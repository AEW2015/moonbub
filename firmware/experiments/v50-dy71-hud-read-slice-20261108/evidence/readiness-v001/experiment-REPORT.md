# V50 HUD READ slice experiment

**Offline host-qualified, isolated experiment only.** No published sources, target image, hardware or network changed. This is not a firmware release or a hardware performance claim. Control exactly copies frozen V48 native sources. Candidate differs only in endpoint.hpp READop3's copy loop; it does not include V49 Huffman changes. Scope/hash checks are retained.

## Candidate behavior

The existing READ loop visited every21120 canonical HUD words for each request, even a1-word or256-word read. The isolated replacement skips complete patch ranges before the requested offset, then copies only the requested words, continuing across canonical patch boundaries as needed. It retains explicit little-endian bytes and the existing header, identity, candidate gate, payload length, return code and final CRC path.

Canonical patch word counts are3840/3840/7680/5760; boundaries are0,3840,7680,15360,21120. Input gates are unchanged: READ requires argument0, matching actual candidate,8-byte payload, off<=21120, count<=21120-off, global minimum response capacity108 and enough response capacity for the requested data. Count0/off21120 remains a successful zero-payload READ only with a valid candidate and the unchanged global capacity prerequisite. Invalid candidate/identity/bounds still produce the original72-byte status payload/response code5; malformed framing/CRC/shape/capacity still follows the actual C ABI error path.

The loop allocates nothing. It holds only skip/remaining/destination/take indices and the existing shared candidate reference. It does not select, acknowledge, commit, abort or mutate words/references. All arithmetic remains bounded by21120 words/42240 payload bytes after the original bounds check.

## Actual native differential qualification

Both variants compiled with UCRT g++ C++17 -Os -Wall -Wextra -Werror and the actual endpoint.cpp C ABI. The harness executed262669 requests per variant across all12 original prepared frames:

- Every word offset0..21119 individually against independent golden HUD bytes for each frame.
- Full-frame reads, all83 actual256-word network burst commands, exact patch boundaries, lengths spanning boundaries and500 deterministic random valid slices per frame.
- Count0/off21120 and global extents, UINT32_MAX offsets/counts, wrong generation/frame/reference, no candidate before Prepare and after Commit.
- Every truncated request length0..43, bad outer CRC, READ payload sizes0/7/9, undersized global capacities and insufficient payload response capacity.
- Full golden read after invalid requests; accepted cache word CRC before/after the complete read sequence. Every request also checks accepted pointer/tag and exact Arena live/peak/allocation-count invariance, plus unchanged output canaries outside the response.

There are261852 valid READs,636 expected C ABI error returns and181 status rejections. Every valid READ payload equals its independent golden bytes. Full HR70 response bytes (including response status/error contents, identities and CRC) are aggregated with request identity into SHA256 and match exactly across control/candidate:

`f25f7de81c42bac44f6047e4fc6ca2e713d7ad9afda17e40665ed3cf0bd92678`

Qualification logs and command records: control-qualification.log, candidate-qualification.log, qualification-execution.json and QUALIFICATION.json. Hashes bind the actual native sources and harness. The twelve Prepare inputs and independent HUD goldens are preserved locally under fixtures/ with exact origin/hash bindings; total589947 bytes. They are replay data, not regenerated output from the candidate.

## Host CPU/work measurement

The benchmark prepares one original KEY candidate, then repeatedly sends the actual83 HC70 READ requests through v34_hud_transact, preserving parsing, framing/CRC, candidate identity checks, shared-reference handling and full response comparison. Requests use256 words except the final128. Preparation is outside the timed region. Five rounds alternate variant order; each round measures1000 complete bursts/83000 actual READ transactions.

| Internal host timing | V48 control | Slice candidate |
|---|---:|---:|
|Median1000-burst time|1500075us|123402us|
|Median per83-command burst|1500.075us|123.402us|
|Tracked READ allocations|0|0|

This host benchmark is approximately12.16x faster and all response checksums match. No QSPI, FPGA transport, SPI lock, target SDK, display, network or real hardware scheduling is present. It cannot project the measured291ms hardware HUD-write stage directly, nor establish30fps.

Theoretical per burst: old loop visits83*21120=1752960 words; the new inner copy loops visit21120 requested words total, with at most4*83=332 bounded patch-loop checks. This is an83x reduction in word-loop iterations, not an83x total CPU claim. Parser/CRC/copy/ABI costs remain.

## Stack and scope

GCC host .su reports Endpoint::transact336 bytes for both variants and C wrapper64 bytes for both variants. These are host stack figures, not an Xtensa bound. No target build or target stack proof was performed. Native control matches V48 and endpoint.hpp is the sole differing candidate file; hud.hpp remains identical to control, so no Huffman experiment is mixed in.

Recommended next gate: independent review of boundary/identity/capacity semantics, then a separately requested ESP32 build/stack/identity gate and controlled physical comparison using unchanged FPGA ABI/image. This experiment does not authorize a release, merge, flash or hardware trial.
