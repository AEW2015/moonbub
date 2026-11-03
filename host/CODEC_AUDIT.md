# Codec and Moonlight integration decision

Use FPGA baseline JPEG for the first standalone color prototype. This is an
engineering risk decision; hardware fit, timing, Wi-Fi throughput and sustained
display rate still require measurement on the delivered design.

| Path | Existing implementation | Compatibility and remaining proof |
|---|---|---|
| JPEG | Apache2 `ultraembedded/core_jpeg`, pinned by the FPGA tree | Baseline420/444; block-ordered RGB output. Constrain encoder features, add framebuffer addressing and fault recovery, then prove resource/timing fit. |
| H.264 | `freecores/nova` historical Baseline RTL candidate | Its project evidence is QCIF and Virtex4; neither720x480 throughput nor Artix7 fit follows. The overview has no clear license grant. Profile, references, slices, entropy support and current source licensing need investigation before reuse. |
| Software H.264 | Moonlight is a transport/control library, not an FPGA decoder | Moving a desktop decoder onto ESP32 conflicts with the primary acceleration architecture and has no measured performance evidence here. |

The selected JPEG core excludes restart markers and422. Its standard-table
configuration avoids dynamic Huffman loading. Upstream peak420 throughput is
137 cycles per64 pixels; at75MHz that calculates to about9.86ms for720x480,
before stalls and system overhead. This is an external reference plus
arithmetic, not a benchmark of this GameBub. [Decoder source documentation](https://github.com/ultraembedded/core_jpeg/tree/bb03cce45d0b7459d395486e9e1db3de1b416bd2).

Nova is useful as a comparison candidate rather than a committed integration.
Baseline-only support does not establish acceptance of the normal Moonlight
H.264 High-profile stream. No H.264 IP was added to the prototype.
[Nova project overview](https://opencores.org/projects/nova),
[pinned source tree](https://github.com/freecores/nova/tree/0fd3481a32c8478c856b803af039e80941df4ec9).

## Actual Moonlight dependency audit

The reference checkout is `references/moonlight-common-c`, revision
`f050b13b6a3d61e132ba10ab611cf1949aa0fca7`. It is audit material and is not linked
into the firmware. Its GPL3 license is retained. The CMake build requires its
modified ENet submodule; the nanors submodule supplies FEC routines. Their exact
gitlink revisions are in `references/audit_sources.json`. They have not been
initialized because the standalone transport does not build Moonlight.
[Upstream dependency warning](https://github.com/moonlight-stream/moonlight-common-c/tree/f050b13b6a3d61e132ba10ab611cf1949aa0fca7).

Porting requires bounding video/FEC allocations and queues, mapping threading,
mutexes, condition variables and interruptible waits onto ESP-IDF, and checking
lwIP BSD socket `poll`, timeouts, options and error behavior. The POSIX platform
backend uses pthreads and monotonic clocks. These interfaces must be verified
on the actual IDF configuration rather than assumed from header compatibility.
[Platform implementation](https://github.com/moonlight-stream/moonlight-common-c/blob/f050b13b6a3d61e132ba10ab611cf1949aa0fca7/src/Platform.c),
[socket implementation](https://github.com/moonlight-stream/moonlight-common-c/blob/f050b13b6a3d61e132ba10ab611cf1949aa0fca7/src/PlatformSockets.c).

Crypto defaults to OpenSSL. `USE_MBEDTLS` selects the PSA Crypto backend in this
revision, including authenticated AES-GCM, AES-CBC and random generation.
ESP-IDF's bundled crypto build must expose the required PSA API and algorithms;
simply defining `USE_MBEDTLS` is insufficient evidence of an interoperable port.
This library also does not supply the complete UI, discovery and HTTP/TLS
pairing frontend. No pairing implementation is advertised in Test MJPEG mode.
[Build configuration](https://github.com/moonlight-stream/moonlight-common-c/blob/f050b13b6a3d61e132ba10ab611cf1949aa0fca7/CMakeLists.txt),
[crypto implementation](https://github.com/moonlight-stream/moonlight-common-c/blob/f050b13b6a3d61e132ba10ab611cf1949aa0fca7/src/PlatformCrypto.c).

## Sunshine boundary

The audited Sunshine source is revision
`c10125088da1f61e72fe1c65faa996a297490d36`; selected files, license and hashes are
retained under `references/Sunshine`. The video format selector exposes H.264,
HEVC and AV1. Moonlight's codec masks likewise have no JPEG capability. The
prototype therefore uses its own MSV1 test sender and does not masquerade as a
standard H.264 stream. [Sunshine format definition](https://github.com/LizardByte/Sunshine/blob/c10125088da1f61e72fe1c65faa996a297490d36/src/video.h),
[Moonlight codec masks](https://github.com/moonlight-stream/moonlight-common-c/blob/f050b13b6a3d61e132ba10ab611cf1949aa0fca7/src/Limelight.h).

After the standalone hardware path is proven, a separate Sunshine fork needs an
explicitly named experimental JPEG capability, matching client negotiation,
restricted encoder output, video packetization, disabled audio transmission,
and negative tests proving existing clients retain their normal codec path.
This milestone does not install/modify a Sunshine service or claim that extension
exists. Pairing, application listing, virtual gamepad injection and audio remain
unimplemented host integration work. The standalone sender has an explicit
`--inject-keys` Windows keyboard mapping; it is separate from GameStream's
authenticated controller transport and defaults to logging only.
