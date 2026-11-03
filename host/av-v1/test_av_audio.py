"""@brief Offline audio geometry, decoder golden and bounded-worker checks."""

import hashlib
import json
import subprocess
import time
import unittest
from pathlib import Path

from av_audio import EncodedAudio
from av_protocol import Packet, decode, validate_adpcm

FIXTURES = Path(__file__).parent / "fixtures" / "av-v1"


class AudioTests(unittest.TestCase):
    """@brief Exercise real encoding/decoding without a microphone or speaker."""

    def test_wire_golden_vectors(self):
        """@brief Every frozen packet reserializes byte-for-byte including CRC."""
        data = json.loads((FIXTURES / "vectors.json").read_text())
        for name, vector in data["vectors"].items():
            with self.subTest(name=name):
                raw = bytes.fromhex(vector["hex"])
                self.assertEqual(decode(raw).encode(), raw)
                self.assertEqual(hashlib.sha256(raw).hexdigest(), vector["sha256"])

    def test_ffmpeg_decodes_fixed_stereo_block(self):
        """@brief An independent decoder reproduces the exact505-frame PCM fixture."""
        result = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-i",
                                 str(FIXTURES / "stereo-505.wav"), "-f", "s16le", "pipe:1"],
                                capture_output=True, check=True)
        self.assertEqual(result.stdout, (FIXTURES / "stereo-505-decoded.s16le").read_bytes())
        self.assertEqual(len(result.stdout), 505 * 4)

    def test_tone_encoder_real_blocks_and_bounded_queue(self):
        """@brief Real FFmpeg encoder emits valid blocks, bounded backlog and stops."""
        source = EncodedAudio("tone")
        try:
            source.start()
            sequence, stamp, block = source.blocks.get(timeout=5)
            self.assertEqual(sequence, 0)
            self.assertLessEqual(stamp, time.monotonic_ns())
            validate_adpcm(block)
            self.assertEqual(len(Packet(b"MSA1", 1, 123, payload=block).encode()), 560)
            time.sleep(0.15)
            self.assertLessEqual(source.blocks.qsize(), 4)
            self.assertGreater(source.dropped, 0)
            self.assertIsNone(source.error)
        finally:
            source.close()
        self.assertFalse(source.thread.is_alive())

    def test_reject_bad_source_gain_and_adpcm_header(self):
        """@brief Invalid settings and independent-block predictor indices fail closed."""
        for source, gain in (("microphone", 0.25), ("tone", -1), ("tone", 2)):
            with self.assertRaises(ValueError):
                EncodedAudio(source, gain=gain)
        block = bytearray((FIXTURES / "stereo-505.ima").read_bytes())
        for offset, value in ((2, 89), (3, 1), (6, 255), (7, 1)):
            malformed = block.copy()
            malformed[offset] = value
            with self.assertRaises(ValueError):
                validate_adpcm(malformed)


if __name__ == "__main__":
    unittest.main()
