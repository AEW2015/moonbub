# V114 native SR14 syntax audit

Read-only audit of the selected native helper run, its runner, source/artifact pins, host completion, and the original Python-only result. Machine-readable details are in [`syntax-native-review.json`](../../experiments/python-gamebub-v114/audit/syntax-native-review.json). No code, tests, or builds were run for this audit.

Selected attempt `20261108T231821585595Z` completed with exit 0 and no resource stop. Its C++ helper compiled with C++17, `-O2`, `-Wall`, `-Wextra`, and `-Werror`. All 13 pinned source files match the working tree and attempt snapshots; all 17 attempt artifacts and three host-completion artifacts match their recorded hashes. The 48-row CSV matches the receipt. The earlier Python-only result also revalidates: its summary matches its receipt, all 12 source and 16 artifact pins match, and its host-completion and CSV pins pass.

Across six canonical packet fixtures, two SR14 versions, and four chunk sizes, all 48 native result rows exactly equal the previously selected Python proof rows. The helper executed the native SR14 packetizer and decoder, compared native BR88 chunk encoding bytes against Python, and round-tripped coefficients through both implementations. The run also covered eight synthetic profiles, 784 malformed-input checks, 392 recovery checks, and both BR88 flag values. This is container/chunk byte parity and coefficient validation; it does not validate pixels or a full published frame.

Projected parent-byte fits among the six fixtures at a 49,152-byte limit are V1: 4/6, 5/6, 5/6, 6/6 and V2: 5/6, 5/6, 6/6, 6/6 for chunk sizes 32, 64, 128, 256 respectively. For `actual_031`, the largest container is V1 at 32 blocks: 45,474 bytes, projecting to 62,510 parent bytes. V2 at 32 blocks is 37,754 bytes, projecting to 54,790 parent bytes. The projection replaces old BR88 bytes with SR14 bytes while retaining the other existing packet bytes.

The run used no FPGA RTL, ESP32, Sunshine integration, full-frame publication, or hardware timing. Three- and four-lane Rice-bit-work values are hypothetical balancing calculations, not measured cycles or hardware throughput.
