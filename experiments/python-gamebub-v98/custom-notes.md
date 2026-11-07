# Historical custom control

`custom_controls.run(frames, parameter, fps=30, output_dir=None)` returns a
decoded RGB list and JSON-serializable instrumentation. Parameters 8, 16, 32
select actual uniform GM01 quantizers with zero motion. `global8`, `global16`,
and `global32` select its bounded even global translation search. These runs
encode each caller-supplied fresh RGB frame. They never use previously decoded
CU66 vectors as source images, precomputed coefficients, or a rate proxy.

This is explicitly the older GM01 executable control, not the newest CU66
wire, its mode selection, two-bank reference policy, HUD patches, entropy
extensions, filter, or physical decoder. Inspection found V66 `protocol.convert`
is an offline adapter requiring a frozen CS38 packet and verified canonical
planes. V95 `python/codec.py` is an independent palette record/plane reader
with opaque EC92 residuals. Neither is a standalone fresh-RGB encoder API.
Later AR02/AF02 encoders exist with bank and display-patch mechanisms, but are
also distinct from CU66. This bounded control deliberately uses the mature
GM01 encoder rather than claiming an unproved reconstruction of current CU66.
It cannot establish the rate/distortion gap of the current custom line.

Color uses the identical `fixed_codec.rgb_to_planes` and `planes_to_rgb`
functions called by the prior common-color standard study through `b.gm.ft`.
These are the frozen full-range integer BT.601 approximation, rounded 2x2
chroma average and specified bilinear display interpolation. Source/module
hashes are recorded, including `common_color.py`. No swscale color conversion
is introduced in this custom path.

Keys occur exactly at IDs 0, 30, 60, etc. Every other frame uses the immutable
reconstructed key; even an abrupt scene cut does not silently change this
schedule. Every receive is followed by an immediate in-process ACK, with one
pending credit. There is no packet byte cap, silent dropping, quantizer
adaptation, wire ACK traffic, loss, RF service model, or deadline enforcement.
The corpus and standard wrappers must apply their common pacing separately.

Every full packet includes the 46-byte GM01 outer header, quantizer map,
three complete CP02 planes (including their own headers and CRCs), and a
4-byte whole-packet CRC. Returned byte counts include these exact bytes. The
concatenated `.gm01` file is retained along with packet offsets/lengths/hashes
and a stream hash. If no output directory is supplied, a temporary directory
is created and its absolute path is returned. GM01 lengths delimit each packet;
no uncounted storage framing is added to the elementary stream.

Encoding timings cover analyze, quantize/packet candidate and commit (including
key reconstruction). Decoding timings cover the actual parser and receive.
Independent sender-side reconstruction from candidate coefficients and the
encoder prediction verifies every output hash, including P frames, outside
these measured calls; verification timing is recorded separately. File writes,
metadata hashing and ACK are excluded. These are Python wall times, not FPGA
cycles or evidence of target throughput. The logical reference memory is
1.5 bytes per pixel per endpoint for an 8-bit YUV420 key; the actual NumPy
reference uses int16 and is also recorded. Scratch, source/output arrays,
packets, allocator overhead and physical-memory lifetime are not included in
the retained-reference figure.

Bounded tests exercise fresh random RGB, an abrupt scene cut, all uniform
scales, exact sender reconstruction versus an independent receiver parse,
retained stream replay, frame-30 independent refresh, global motion and
input preservation. No large benchmark is run by this module's tests.
