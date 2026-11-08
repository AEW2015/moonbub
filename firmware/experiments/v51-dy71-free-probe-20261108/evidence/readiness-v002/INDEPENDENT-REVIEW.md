# Independent V51 callback review ? 2026-11-08

PASS for the isolated source/build candidate. No blocking defect found. This does not establish physical speedup or authorize a device update.

Compared exact published V48 and V51 native and handheld/src trees: native is byte-identical; the only changed Rust file is cu66/network_usb.rs. Its diff replaces free_probe's heap().0 with internal_free(), replaces largest_probe's heap().1 with internal_largest(), and adds the two direct-IDF helpers plus a comment. Paired heap() snapshots, startup guard, caps INTERNAL|8BIT, MIN_FREE comparison/store/return, reset of the minimum, allocator callbacks,8192 reserve, all network behavior, endpoint retention and quarantine remain unchanged.

The actual allocator remains unchanged: the pre-malloc free/reserve guard and post-success low-water sample are both retained; failure paths still obtain largest-block diagnostics. The source-extracted Rust harness has two passing cases per variant and checks free values down to0, MIN_FREE and4520 callback invocations. It demonstrates the callback change, not the real IDF traversal time. Separate host suite execution records report successful commands. No candidate source was modified during this review.

Exact target build result is success with no source/native changes. Built ELF and published release-free-probe-v001 ELF are byte-identical, SHA25683799f1197eaf8b1aedd449313204a356e509f277c4459e7ab5a96d6a69eaa82.

Independent Xtensa disassembly confirms:

- free_probe at0x420ba770 contains exactly one callx8, targeting heap_caps_get_free_size0x42190da8, caps0x804; it retains the atomic-min load/comparison/store sequence. No largest-block call remains.
- largest_probe at0x420ba78c contains exactly one callx8, targeting heap_caps_get_largest_free_block0x42190e44, caps0x804; no unused free-size call remains.
- paired heap() at0x420ba79c retains both IDF calls for deliberate startup/final diagnostic snapshots.

Call targets are resolved from actual ELF L32R literals, rather than inferred from symbol names. Disassembly and independent source/ELF hashes are alongside this report. The V48 baseline had two calls in each callback, so compiled elimination of the redundant scans is established.

Release verification reports static shared SRAM132076bytes below163840guardrail, and the actual production DFU parser passes13691UF2blocks, app addresses, Rev4 identity and BIN roundtrip. These are build/package checks; they do not replace runtime heap/stack or updater-driver qualification.

Physical next comparison must keep V027, original12fixtures, network profile and all remaining settings unchanged, then report elapsed/Prepare timing, low-water/stack, accepted/presented and all failure counters. Saving4520 redundant scans on the historical2260-allocation sequence is a source/compiled call-count result; target saved microseconds, frame-rate benefit and bottleneck dominance remain unmeasured. V49/V50 are separate candidates and are not implicitly included here.

No hardware access, reset, driver install, Vivado or target rebuild was performed by the reviewer.
