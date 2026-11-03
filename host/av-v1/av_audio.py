"""@brief Bounded audio sources for the experimental MoonBub AV companion.

PyAV supplies the standard FFmpeg IMA WAV encoder and resampler. WASAPI uses
PyAudioWPatch loopback, not a microphone. Optional imports happen on source use.
"""

import math
import queue
import threading
import time

from av_protocol import FRAMES, RATE, validate_adpcm


class EncodedAudio:
    """@brief Capture/resample audio on a worker with four encoded blocks maximum."""

    def __init__(self, source, *, gain=0.25, path=None, device=None):
        """@brief Select tone, file or default/explicit WASAPI loopback source."""
        if source not in ("tone", "file", "loopback") or not 0 <= gain <= 1:
            raise ValueError("Invalid audio source or gain")
        self.source, self.gain, self.path, self.device = source, gain, path, device
        self.blocks = queue.Queue(maxsize=4)
        self.stop = threading.Event()
        self.thread = None
        self.error = None
        self.dropped = self.encoded = self.capture_errors = 0
        self.info = {}

    def start(self):
        """@brief Start exactly one audio producer; imports remain off module load."""
        if self.thread is not None:
            raise RuntimeError("Audio worker already started")
        self.thread = threading.Thread(target=self._run, name="moonbub-audio", daemon=True)
        self.thread.start()

    def _publish(self, block, stamp):
        validate_adpcm(block)
        item = (self.encoded & 0xFFFFFFFF, stamp, block)
        self.encoded += 1
        try:
            self.blocks.put_nowait(item)
        except queue.Full:
            try:
                self.blocks.get_nowait()
            except queue.Empty:
                pass
            self.dropped += 1
            self.blocks.put_nowait(item)

    def _run(self):
        try:
            import av
            import numpy as np

            codec = av.CodecContext.create("adpcm_ima_wav", "w")
            codec.sample_rate, codec.layout, codec.format = RATE, "stereo", "s16p"
            codec.options = {"block_size": "512"}
            codec.open()
            if codec.frame_size != FRAMES:
                raise RuntimeError("FFmpeg encoder block size disagrees with wire contract")
            resampler = av.AudioResampler(format="s16p", layout="stereo", rate=RATE)
            fifo = av.AudioFifo()
            for frame in self._frames(av, np):
                if self.stop.is_set():
                    break
                for resampled in resampler.resample(frame):
                    # Per-frame timestamps are deliberately reset: this FIFO is
                    # an audio sample stream, not an A/V synchronization clock.
                    resampled.pts = None
                    samples = resampled.to_ndarray()
                    scaled = np.rint(samples.astype(np.float64) * self.gain).clip(-32768, 32767).astype(np.int16)
                    output = av.AudioFrame.from_ndarray(scaled, format="s16p", layout="stereo")
                    output.sample_rate = RATE
                    fifo.write(output)
                    while fifo.samples >= FRAMES:
                        chunk = fifo.read(FRAMES)
                        for packet in codec.encode(chunk):
                            self._publish(bytes(packet), time.monotonic_ns())
            # Do not pad or flush partial/stale tail audio on stop.
        except Exception as error:  # noqa: BLE001 - propagate worker failure to owning session
            self.error = f"{type(error).__name__}: {error}"
        finally:
            self.stop.set()

    def _frames(self, av, np):
        if self.source == "loopback":
            yield from self._loopback(av, np)
            return
        if self.source == "file":
            with av.open(str(self.path)) as container:
                origin, samples = time.monotonic(), 0.0
                for frame in container.decode(audio=0):
                    if self.stop.wait(max(0, origin + samples - time.monotonic())):
                        return
                    samples += frame.samples / frame.sample_rate
                    yield frame
            return
        origin, number = time.monotonic(), 0
        while not self.stop.is_set():
            if self.stop.wait(max(0, origin + number / RATE - time.monotonic())):
                return
            t = (np.arange(FRAMES, dtype=np.float64) + number) / RATE
            data = np.array([np.sin(t * 2 * math.pi * 440), np.sin(t * 2 * math.pi * 660)])
            frame = av.AudioFrame.from_ndarray(np.rint(data * 12000).astype(np.int16), format="s16p", layout="stereo")
            frame.sample_rate = RATE
            number += FRAMES
            yield frame

    def _loopback(self, av, np):
        import pyaudiowpatch as pyaudio

        with pyaudio.PyAudio() as manager:
            info = (manager.get_default_wasapi_loopback() if self.device is None
                    else manager.get_device_info_by_index(self.device))
            if not info.get("isLoopbackDevice"):
                raise ValueError("Selected device is not a WASAPI loopback device")
            channels, rate = int(info["maxInputChannels"]), int(info["defaultSampleRate"])
            if channels not in (1, 2):
                raise ValueError("Select a mono/stereo Windows loopback endpoint for this prototype")
            self.info = {"device": info["name"], "index": info["index"], "channels": channels, "rate": rate}
            with manager.open(format=pyaudio.paInt16, channels=channels, rate=rate, input=True,
                              input_device_index=info["index"], frames_per_buffer=512) as stream:
                while not self.stop.is_set():
                    # Overflow is a reported capture error, never silently treated
                    # as intact audio. The independent ADPCM block can recover.
                    try:
                        raw = stream.read(512, exception_on_overflow=True)
                    except OSError:
                        self.capture_errors += 1
                        if self.capture_errors >= 5:
                            raise
                        continue
                    data = np.frombuffer(raw, dtype=np.int16).reshape(1, -1)
                    frame = av.AudioFrame.from_ndarray(data, format="s16", layout="mono" if channels == 1 else "stereo")
                    frame.sample_rate = rate
                    yield frame

    def close(self):
        """@brief Stop and bound worker cleanup; report a stuck capture thread."""
        self.stop.set()
        if self.thread is not None:
            self.thread.join(timeout=2)
            if self.thread.is_alive():
                raise RuntimeError("Audio capture did not stop within2seconds")
