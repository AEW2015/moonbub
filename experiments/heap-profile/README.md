# Internal heap measurement helper (not integrated)

The current receiver allocates one 1,065-byte DMA-capable internal receive
buffer and forwards payloads to the FPGA. The protocol allows a JPEG up to
262,144 bytes. The simulated one-frame upstream queue and hypothetical five
packet slots are not present in this firmware, and no free-heap or largest-block
measurement proves that either fits when Wi-Fi and the rest of the application
are active. Five 1,064-byte packet slots alone require 5,320 bytes; the current
1,065-byte receive buffer, slot metadata and any alignment/allocator overhead
are additional. Actual allocation layout and lifetime must be decided and
measured; do not infer usable memory from an ELF file's disk size. External
PSRAM is disabled in the documented build and its physical presence has not
been established.

`heap_profile.rs` is an isolated, allocation-free diagnostic helper. A
caller passes an ESP-IDF capability mask, monotonic timestamp and phase to
`capture`, then can record values in a fixed-size `History`. It contains no
credentials, video, SSID, addresses or other packet data. The ESP-IDF calls
return free bytes, largest free block and minimum free bytes for the selected
capabilities. Queries happen sequentially, not atomically; asynchronous
allocations may change the heap between queries. ESP-IDF's minimum for multiple
regions is the sum of individual low-water marks, which need not have occurred
at the same instant. The helper makes no allocation-feasibility guarantee.

For a later **authorized board test**, integrate into an experimental firmware
build and pass the actual target binding's `MALLOC_CAP_DMA | MALLOC_CAP_INTERNAL`
mask (and separately a relevant internal byte-addressable mask). Record
snapshots before Wi-Fi, after connection, after socket/DMA allocation, during
sustained streaming, and after shutdown. Record free, minimum free and largest
block, sampling time and any dropped samples. A largest free block smaller than
the candidate allocation rules that allocation out at that instant; a larger
block alone does not prove allocation will succeed under concurrent load.
Perform a safe allocation/release test under representative workload only in
the dedicated diagnostic build, and measure low water over long runs. Never
print Wi-Fi credentials or packet contents. A mapped static memory report and
actual timing/heap trace are separate checks.

`run-host-tests.sh` compiles the no-std helper with a mock ESP-IDF FFI and runs
four logic tests. In this environment the helper also compiled to an Xtensa
ESP32-S3 rlib using the existing `esp193` compiler and matching previously
built `core`/`compiler_builtins` artifacts (see `test.log`). The rlib was not
linked into firmware, flashed or executed on an ESP32; toolchain compatibility
and FFI bindings must be verified when integrating. The helper stores no
persistent configuration and does not change the installed firmware.
