# V129 codec boundary: actual firmware receiver

For otherwise structurally valid MSV1 packets, the production Rust receiver
rejects codec values other than `1` as `Format`; codec `1` alone does not make
a packet valid. It does not negotiate a CS88 profile or
inspect the payload to establish that it is JPEG. This matters before connecting
the experimental custom decoder to a production stream.

The [host test](../../scripts/cu66-v129/negotiation/receiver_guard.rs) compiles
the unchanged [firmware protocol module](../../firmware/handheld/src/streaming/protocol.rs)
and exercises its real `Header::parse`, `Receiver::accept` and CRC logic using
the 26-datagram, 26,159-byte JPEG fixture. The [passing receipt](../../experiments/python-gamebub-v129/negotiation/results.json)
records source, fixture, compiler-image, binary and log hashes. The binary was
temporary and was not retained for independent rehashing. Sources were mounted
read-only and checked before and after the run, not snapshotted for compilation.

| Control | Observed result |
| --- | --- |
| All 255 codec values other than `1` | `Format` rejection |
| Unsupported codec in the middle of a frame | Active frame aborted; a trailing continuation fails; all 255 subsequent newer-frame JPEG retries complete |
| Four-byte `CS88` payload labeled as codec `1` with a correct CRC | Accepted and marked complete by the protocol parser |

The last control deliberately uses a JPEG label on non-JPEG bytes. It shows the
parser's codec label and transport CRC do not establish payload type. It does
not run the downstream JPEG guard or show a decoder accepting those bytes.
The compiled Rust runs on this Linux host, not on the ESP32; it does not execute
the firmware session worker, Sunshine capture/encoder/session, Wi-Fi, QSPI,
FPGA or hardware.

The initial host-only compilation failed because this machine lacks the `cc`
linker; its [failure and exact runner snapshot](../../experiments/python-gamebub-v129/negotiation/repair-history/host-linker/repair.json)
are retained. The fresh successful build used the existing pinned toolchain
container, strict Rust warnings, read-only source mounts and no network.

For a future real integration, negotiate a versioned codec/profile, dimensions,
pixel layout, frame-size cap and recovery semantics **before** sending custom
payloads, and reject unknown or inconsistent selections at both endpoints.
Keep an explicit JPEG fallback, drain or cancel in-flight ownership on a
profile switch, and prove the selected FPGA decoder and firmware path agree.
The current MSV1 receiver must not be treated as a CS88 receiver merely because
it can carry arbitrary CRC-valid bytes under the JPEG label.

The repository also contains a separate [V97 portable session candidate](../../firmware/handheld/src/streaming/protocol97.rs)
with an explicit JPEG/research-profile setup and bounded gateway. The active
[network worker](../../firmware/handheld/src/streaming/mod.rs) still uses MSV1;
the existence of the candidate does not establish that the active Sunshine,
ESP32 firmware and selected FPGA decoder negotiate or execute a common profile.
