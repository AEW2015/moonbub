# V45 driver: HU ingress cache and bounded finite sequence

November 7, 2026 (America/Denver). No hardware access or physical network transmission by this workstream. V44 source/images and the held V44 hardware endpoint were not modified.

## Implementation

`network_driver::run` and `run_sequence` remain explicit scalar command21 controls. New `run_cached_sequence` selects the cached path. The cache uses one `Vec` of exactly HU length plus36 HC70 framing bytes, allocated earlier instead of allocating a second payload buffer. It copies only the checked HU interval from each validated-length source chunk while forwarding the same chunk to FPGA storage.

Before native use the driver still checks exact received/staged length and CRC, FPGA storage error state, seal/admission completion, stable HUD request identity/generation/reference/offset/length/bank/key/tag, native output identity and actual HUD write/readback/drain/commit/presentation. Cached mode also requires the first source chunk's76-byte prefix to equal the advertised prefix. Copy coverage must be contiguous/exact; arithmetic/range failures fail closed. The cache cannot cause native preparation before full staging integrity and live request checks. Full pixel readback remains enabled.

HU length is bounded to1..20,000 bytes; packet limit remains49,152 bytes. Sequence count is explicitly bounded1..12,000 independently of diagnostics. Only the last three records are retained using ordinal modulo3, with actual ordinal/frame/generation identifiers; arrays and stack use do not scale with sequence count. Failed native/transport operations still return an error to the existing fail-held owner workflow.

Small default `Source::active` observations identify HEADER, STAGING, STAGED, ADMITTED, HUD_REQUEST, NATIVE, HUD_WRITE, HUD_READBACK, COMMIT and observed PRESENTED phases. These do not fabricate completion or mutate FPGA ownership. Detailed partial arrays are not returned on an error; the telemetry wrapper retains only the explicitly observed active progress.

## Executed host evidence

Final actual-source run: `evidence/host-20261108-015913-496148Z`, with31driver +19batch +9wire tests passing (**59 total**). `source-check.json` confirms48 driver/native/test/fixture files unchanged during compilation/execution. `run-host.py` records before/after hashes and exact commands. Production C++ HUD and production Rust driver/parser are executed; FPGA MMIO is a test model.

Added tests include:

- Actual three-frame cached versus scalar equality,63,360 native HUD words, zero command21 operations on cached mode versus real scalar fetches on control.
- Actual four-frame turnover under98,304-byte native cap:84,480 words, fixed last-three ordinals `[3,1,2]`.
- Actual twelve-frame sequence with the separately selected native in-place prediction fix:253,440 words, last-three ordinals/frame IDs `[9,10,11]`, generations `[10,11,12]`, no native arena failures and no command21 operations.
- Prefix/body disagreement, HU corruption, FPGA staging CRC disagreement and bad live HUD reference fail before native preparation/HUD publication as appropriate.
- Actual phase hook identity/order and finite-count rejection before writes.
- Production cache-helper boundaries at HU offsets76/1023/1024/1025/2048 and lengths1/1024/1025/20,000; no HC70 header/trailer overwrite. Skipped/replayed overlap and arithmetic overflow fail closed.

The selected native header SHA is `d00896be1bdbd3df174f41895b98d321f45017cf45c704a4cb63fae303b15b92`. Root owns its independent broad-corpus/reserve proof. Inspection confirms owned motion prediction is moved into output, and each channel reads its original component before masking/replacing only that component. Plain co-located prediction remains a read-only accepted-cache borrow. Current candidate output is independently owned; failure does not mutate accepted state. This review does not replace the separate native golden tests.

## Timing and remaining boundaries

Cached `hu_extract_start/done` fields describe the ingress HU-copy span, which may include packet/staging waits **before** admission. They are not the old post-admission scalar-fetch interval. `cache_mode` distinguishes the meanings and `hu_extract_commands` is zero for cached retained records. Fake-MMIO and RTL virtual timings do not measure ESP32 copy/compute time or physical QSPI bandwidth.

The cache reuses the same logical HC70 input allocation, but its lifetime begins earlier. Physical largest-block availability, fragmentation, worker stack and the unchanged8,192-byte native reserve still need actual target measurements. The real target receiver and all metadata/version/count changes are owned by root/telemetry workstreams and must be included in final build/source gates. No general continuous-session recovery or120-second/30fps readiness is established by these finite tests.

The fresh exact V027 cached-five system replay is tracked separately under `C:/moon/maintenance/v45-system-cached5`; only its final result receipt can establish that gate.
