# Experimental MoonBub audio and Xbox controls

This companion implements a new UDP5534 contract, separate from the existing
UDP5533 MSV1 video sender. **It requires the new AV receiver application and
audio-capable FPGA build50 for audio. With the new application, input-only
sessions can use build49; build49 cannot play this audio.** Simulation, routed build and hardware acceptance are tracked
separately. Do not interpret ingress ACKs or software tests as audible playback.

The wire contract is `protocol/av-v1.md`. Golden datagrams and an independent
FFmpeg-decoded stereo fixture are in `fixtures/av-v1/`.

Audio: stereo signed16 source, resampled to48293Hz, independent512-byte
IMA ADPCM WAV blocks/505 stereo frames. The FPGA emits the existing DSP format
at nominal176171875/3648Hz (48292.728893Hz), using the unchanged panel-derived
clock. No exact48k mode, Opus, mono transport or multichannel transport.
The host encoded queue is four blocks; ESP has one decoded block; FPGA has eight
512-frame slots (16KiB), starts/rebuffers after two blocks and outputs silence
on underrun. The nominal compressed payload rate is about392kbit/s, plus headers
and input/status traffic, **in addition to video**. No adaptive drift correction
or measured A/V synchronization is claimed in this first prototype.

Controls: MSI1 carries a session cookie and independent wrapping sequence every
20ms, even during a held video frame. Its12 buttons map to Xbox A/B/X/Y, D-pad,
LB/RB, Start/Back. There are no analog sticks or analog triggers in this wire
version. MSF1 button snapshots do not drive the virtual controller. Invalid,
stale, duplicate and wrong-session packets cannot refresh the500ms input lease.
Timeout, exception and shutdown release controls. Injection is opt-in.

## Windows environment

Use a dedicated Python3.12 environment. The locally exercised versions are
PyAV19.0.2, NumPy2.5.4 and PyAudioWPatch0.2.12.9. Install those Python packages
into that environment; the video sender's environment/settings need not change.
FFmpeg is needed for the independent decoder test, not for the live PyAV encoder.

```powershell
python -m venv .venv-av
& .venv-av/Scripts/python.exe -m pip install av==19.0.2 numpy==2.5.4 PyAudioWPatch==0.2.12.9
```

For Xbox output the PC must have a working ViGEmBus runtime. Check the existing
driver first. Installing `vgamepad` normally launches a driver installer; to
install only the Python adapter while preserving driver state:

```powershell
$env:VGAMEPAD_SKIP_VIGEMBUS_INSTALL = 'true'
& .venv-av/Scripts/python.exe -m pip install vgamepad
Remove-Item Env:VGAMEPAD_SKIP_VIGEMBUS_INSTALL
```

The adapter reports a clear error if the package/runtime is absent. No driver
is installed or service changed by this program. Use the official
[vgamepad installation/runtime documentation](https://github.com/yannbouteiller/vgamepad)
and [ViGEmBus releases](https://github.com/nefarius/ViGEmBus/releases) to qualify
the actual PC's driver/package combination before a physical game test.

## Test order after receiver deployment is confirmed

Run from `tools/gamebub`, keeping the existing video sender unchanged. Verify the
printed local socket IP is the configured sender192.168.0.47. UDP5534 is an
additional port; do not change or reuse video source port55534.

```powershell
# Ordered input only, no audio capture and no virtual input output:
python av_client.py --receiver 192.168.0.157 --seconds 20 --log input-observe.jsonl

# Opt-in Xbox device, initially test in Windows controller properties:
python av_client.py --receiver 192.168.0.157 --gamepad --seconds 30 --log xbox-check.jsonl

# Quiet deterministic left440Hz/right660Hz channel test:
python av_client.py --receiver 192.168.0.157 --tone --gain 0.25 --seconds 10 --log tone.jsonl

# Game sound from the default Windows output endpoint, with Xbox controls:
python av_client.py --receiver 192.168.0.157 --loopback --gamepad --gain 0.25 --seconds 30 --log game-av.jsonl
```

Use the chosen environment's Python for all commands. A `.wav` or other supported
file can be selected with `--file PATH`. WASAPI capture is output loopback, not
a microphone; `--device INDEX` must select an actual mono/stereo loopback device.
[PyAudioWPatch](https://github.com/s0d3s/PyAudioWPatch) documents endpoint listing
and default-output loopback. Gain0.25 scales digital source amplitude; saved
handheld DAC volume/routing is left intact.

The program records the actual local/remote socket endpoints, session, ordered
input masks and audio status in JSONL. MSI1 accepted-block counters are not
audible evidence; check FPGA played/underruns with valid-snapshot flag, hear the
channel test, and verify buttons/releases in the host's gamepad properties.
Start moving video at5fps before increasing load. Keep margin13 and timing0.

## Offline checks

```powershell
python -m unittest test_gamepad_backend test_av_protocol test_av_client test_av_audio -v
```

These tests use fake gamepads and localhost peers. They never inject real input
or transmit to the handheld. Independent FFmpeg decoding checks505 stereo
frames/2020 PCM bytes and exact frozen PCM output.
