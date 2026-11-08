# Independent V50 HUD READ slicing review

November8,2026. Read-only source/evidence review; no candidate edits, target rebuild, hardware action or driver installation.

**No blocking correctness or bounds defect found.** The slice loop preserves the READ/CABI contract and is suitable for a separate target build and bounded physical comparison. Host performance is not target/display evidence.

## Exact source identity

I independently compared all eight native files: the control exactly matches published V48, and the isolated candidate exactly matches published`v50-dy71-hud-read-slice-20261108`. Only`endpoint.hpp` differs; its prefix beforecase3 and suffix fromcase4are identical. Candidate endpoint SHA256:`0b8635d9c9483f6a15068cfda966902d84dcc42122524401d86107d2f1d418c0`. HUD decoding/Huffman remains V48; no V49 mix-in.

All16native initial pins remain identical in the final manifest. Final manifest adds two harness files, so initial/final whole dictionaries are not identical in domain; all18final hashes match current files. All24retained Prepare/golden fixture copies match their original paths, byte counts and hashes. Thus the executed source and replay inputs remain available. The harnesses have final hash bindings; they were not included in the initial native-only manifest.

## Bounds, zero-length and crossings

Unchanged input gates first require argument0, a matching valid candidate, eight-byte payload and the global108-byte response-capacity floor. The short-circuit`off<=21120 && count<=21120-off` prevents subtraction underflow, rejectsUINT32_MAXinputs, and bounds count*2to42240on both32/64-bit targets. The payload-capacity check precedes all output writes.

`skip` begins as the bounded canonical offset. A complete patch is subtracted only when`skip>=patch.words.size()`. Otherwise subtraction for`patch.words.size()-skip` is safe; `take=min(remaining,available)` cannot exceed either. For every iteration`skip+i` is inside that patch, `destination+i` is below requestedcount, and output byteindices32+2*(destination+i)and+1stay inside the checked response area. Resetting skipto0after a partial patch preserves canonical order across boundaries3840/7680/15360.

Count0immediately skips copying and returns the same zero-payload success, including off21120, only with a valid candidate and the unchanged globalcapacityfloor. Full-frame reads and final-word slices are bounded identically. Like the original loop, correctness assumes the valid immutable candidate contains the fixed21120words. HudGate publishes a candidate only after successful fixed-rectangle/tag-validated decoding; this patch neither changes nor relaxes that invariant.

## ABI, state and allocation

Explicit low/high-byte writes preserve little-endian output. Header fields, returnedpayloadlength, identity echoes, status/error72-bytepayload, responseCRC and C-wrapper handling are unchanged. Invalid identity/argument/bounds still produce code5/status; invalid framing/CRC/shape/capacity still throws through the existingCABIerrorpath. No acknowledgement, commit, abort, candidate/accepted mutation or new allocation was introduced. The local shared reference keeps the candidate alive; existing exclusive-owner assumptions are unchanged.

## Evidence and limits

The actual-native harness runs262669requests per variant: every one-word offset across12goldens, full and83-command bursts, explicit patch crossings, random slices, zero/extreme bounds, identities, truncations, CRC/shape/capacity errors and post-commit absence. It checks full response bytes/CRC, outside-response canaries, acceptedpointer/tag/CRC and exact Arena live/peak/allocation invariance. Control/candidate aggregate hashes match`f25f7de81c42bac44f6047e4fc6ca2e713d7ad9afda17e40665ed3cf0bd92678`. Qualification counts reconcile:261852valid READs,636CABIerrors,181status rejections.

Host benchmark preserves the actual CABI/parsing/CRC path and compares outputs; its median83-command burst1500.075→123.402us is useful CPU-work evidence. It contains no target/QSPI/lock/FPGA/network/display timing. The83×word-loop reduction is not an83×total-speed claim; the measured host ratio is about12.16×. Host Endpointframe336/wrapper64are unchanged, but Xtensa stack/SRAM and runtime low-water remain separate gates.

No V027 change is required by this read-only CPU optimization. Next is exact target build/source identity and measured coldCPU12/networkcached12stage timing, preserving the current hardware control and complete diagnostic export.
