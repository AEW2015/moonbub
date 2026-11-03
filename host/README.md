# Moonshine PC test sender

Standalone video-only MJPEG transport for the prototype firmware/FPGA. This
does not connect to unmodified Sunshine. See [codec audit](CODEC_AUDIT.md) and
[wire protocol](PROTOCOL.md). No Sunshine service installation is performed.

From the repository root, using Python3.11 and FFmpeg7.1:

```powershell
python -m pip install -r host/requirements.txt
python host/make_fixture.py
python -m unittest discover -s host/tests -v
python host/loopback_probe.py --duration 10
```

Start Test MJPEG in the Streaming screen on firmware configured with Wi-Fi
credentials and the sender's IPv4 address. Run a representative gameplay clip:

```powershell
cd host
python -m moonshine.sender 192.168.1.50 --clip D:\clips\gameplay.mp4 --fps 30 --quality 65 --mbps 12 --duration 120 --metrics evidence/gameplay.json --input-jsonl evidence/input.jsonl
```

Use `--desktop` instead of `--clip` for desktop capture. `--image` is a repeated
diagnostic image source, useful for bring-up but not sustained gameplay evidence.
The sender automatically scales/letterboxes and constrains baseline420 JPEG.
`--mbps` is a pacing ceiling, not a claim of measured wireless capacity. Audio
is disabled at capture and absent from the protocol. Input masks are logged by
default. Add `--inject-keys` explicitly to send Windows keyboard events to the
currently focused game: D-pad=arrows,A=Z,B=X,X=A,Y=S,L=Q,R=E,Start=Enter,
Select=Space. Focus the game manually after starting the sender. Held injected
keys are released on500ms feedback silence, receiver disconnect, socket error,
and sender exit. Windows can reject SendInput across desktop/integrity boundaries;
the sender reports that error and attempts every outstanding release. No real
desktop injection was performed during development; cleanup is mock-tested.
Virtual gamepad injection is not implemented.

The current automated loopback uses a Python sink that checks transport CRC,
JPEG profile, and full Pillow decoding before ACK. Its rate and capture age
measure the PC path only. FPGA decode/display and Wi-Fi/QSPI measurements remain
separate. `evidence/loopback*.json` includes exact scope and observed counters.
The initial coarse-clock run is retained; `perf_counter` now schedules packets
with high-resolution timing on Windows. No test claims real-game footage when
the source is synthetic.

Recorded observations (not hardware results): the static-pattern run sent and
decoded294 frames in10.0035s of sender operation,29.39fps, at quality65 and
6.31Mbps MSV1 traffic; maximum same-PC capture-to-reference-decode age was
55.97ms. The final moving synthetic clip run completed273 frames in9.6347s,
28.34fps, and lowered quality65 to50 after four expired partial frames. Those
frames were dropped and the next SOF recovered; no malformed frame was accepted.
Its maximum capture-to-reference-decode age was55.38ms. The probe reports
`transport_lossless` separately from parser/decoder recovery checks.

No sustained GameBub rate, hardware latency, or real-gameplay qualification has
been demonstrated by these host-only observations.

To reproduce the moving synthetic clip test:

```powershell
ffmpeg -nostdin -f lavfi -i testsrc2=size=1280x720:rate=30 -t 10 -an -c:v mpeg4 -q:v 5 -y host/fixtures/motion-test.mp4
python host/loopback_probe.py --duration 10 --clip host/fixtures/motion-test.mp4 --output host/evidence/loopback-motion.json
```

`fixtures/pattern-msv1-packets.bin` is the cross-language parser fixture.
`pattern-reference.ppm` and `pattern-reference-rgb565.bin` are Pillow reference
decodes. The decoder's integer IDCT and chroma upsampling differ from Pillow;
compare using a documented tolerance or the core's C-model semantics rather
than claiming bit identity with a different software decoder.

For the recorded decoder comparison:

```powershell
python -m pip install -r host/requirements-verification.txt
python host/build_cmodel.py
python host/compare_decoder.py --require-fixed-exact
```

The comparison checks345600 unique pixel addresses and distinguishes three
references. Stock Pillow interpolation differs at420 chroma edges; the upstream
C-model's floating-point color rounding differs by at most one quantized code
per channel on this fixture. A separately labeled C-model variant changes only
the three color conversion expressions to the RTL's fixed coefficients; its
RGB565 output matches all345600 RTL pixels exactly. Vendor entropy/IDCT/block
addressing sources remain unchanged. Build manifests bind the original source,
generated patch, compiler, executable, reference pixels and simulation dump.
This verifies one known frame through the RTL decoder, not hardware scanout or
general malformed-JPEG behavior. The initial C-model Windows text-mode PPM
failure and its comparison are retained; binary stdio wrappers correct the
platform output without changing decoder arithmetic.
