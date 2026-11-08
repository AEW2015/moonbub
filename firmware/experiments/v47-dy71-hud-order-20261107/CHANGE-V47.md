# V47 HUD allocation-order candidate

This candidate changes only native HUD candidate construction and its firmware variant label. It addresses the V46 network trial's failed11,520-byte malloc when sampled total free was35,284 but largest block7,680. It does not raise arena98,304 or reserve8,192, change wire-v3 or FPGA V027, free the accepted prediction early, or fabricate commit authority.

All four component slices are bounded before decode. A four-slot descriptor vector is sized once; fixed output patches are decoded in descending output size (canonical indices2,3,0,1), then stored at their original index. Reference patch lookup and all output tags remain canonical. Accepted state remains immutable until the existing commit protocol. Partial candidate exceptions unwind before publication. With several invalid components, the first reported component error may differ.

Initial host gates passed all twelve golden HUD frames (253,440 words),77 Rust driver/wire/telemetry/diagnostic checks, allocator exception checks and457 retained corpus frames plus3malformed cases. The broader corpus runs with a1MiB semantic-only cap; its peak100,888 exceeds the target98,304 cap, so it does not qualify every retained corpus input for target fit. First12 model peak88,974, compared with V46's92,544; these host accounting numbers do not prove target contiguous allocation availability.

Further gates: bounded real TLSF fragmentation comparison, P-frame rollback/negative tests, frozen-source target build, ELF/SDK SRAM check, production UF2 parser and exact release hashes. Target stack/heap and physical cached12 are unverified. No device operation is part of these offline tests.

Inherited historical packaging/readiness scripts are not the selected V47 qualifier. Selected build/package commands use explicit candidate/build/release paths beneathC:/moon.
