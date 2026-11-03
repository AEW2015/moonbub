"""@brief Local fake-firmware and audio-worker tests for the AV companion client."""

import argparse
import contextlib
import hashlib
import io
import json
import select
import shutil
import socket
import struct
import subprocess
import tempfile
import threading
import time
import unittest
from pathlib import Path

import av

from av_audio import EncodedAudio
from av_client import handshake, run
from av_protocol import BLOCK, FRAMES, INPUT, NONCE, RATE, Packet, decode

HERE = Path(__file__).resolve().parent
GOLDENS = HERE / "fixtures" / "av-v1"


def _status(cookie, seq, *, buttons=0, audio=False):
    state = 1 | (2 if audio else 0) | 4
    payload = INPUT.pack(buttons, 0, 0, 64, 128, 0, state, 0x4D424F50)
    return Packet(b"MSI1", 1, cookie, seq=seq, payload=payload).encode()


def _wav_with_block(block):
    average_bytes = round(RATE * BLOCK / FRAMES)
    fmt = struct.pack("<HHIIHHHH", 0x11, 2, RATE, average_bytes, BLOCK, 4, 2, FRAMES)
    body = b"WAVEfmt " + struct.pack("<I", len(fmt)) + fmt
    body += b"data" + struct.pack("<I", len(block)) + block
    return b"RIFF" + struct.pack("<I", len(body)) + body


class HandshakeStub:
    """@brief Emulate UDP replies in-process to exercise offer source/nonce checks."""

    def __init__(self, peer):
        self.peer = peer
        self.queue = []
        self.sent = []
        self.timeout = None

    def settimeout(self, value):
        self.timeout = value

    def send(self, wire):
        packet = decode(wire)
        self.sent.append(packet)
        if packet.magic == b"MSC1" and packet.kind == 1:
            nonce = packet.session
            flags = packet.flags
            self.queue.extend(
                [
                    (
                        Packet(
                            b"MSR1", 1, 0xBAD1, flags=flags ^ 1,
                            payload=NONCE.pack(nonce),
                        ).encode(),
                        self.peer,
                    ),
                    (
                        Packet(
                            b"MSR1", 1, 0xBAD2, flags=flags,
                            payload=NONCE.pack(nonce ^ 1),
                        ).encode(),
                        self.peer,
                    ),
                    (
                        Packet(
                            b"MSR1", 1, 0xBAD3, flags=flags,
                            payload=NONCE.pack(nonce),
                        ).encode(),
                        (self.peer[0], self.peer[1] + 1),
                    ),
                    (
                        Packet(
                            b"MSR1", 1, 0xCAFE, flags=flags,
                            payload=NONCE.pack(nonce),
                        ).encode(),
                        self.peer,
                    ),
                ]
            )
        elif packet.magic == b"MSC1" and packet.kind == 2:
            self.queue.extend(
                [
                    (_status(packet.session, 0, audio=not bool(packet.flags)), (self.peer[0], self.peer[1] + 1)),
                    (_status(packet.session, 0, audio=not bool(packet.flags)), self.peer),
                    (_status(packet.session, 1, audio=bool(packet.flags)), self.peer),
                ]
            )

    def recvfrom(self, _size):
        if self.queue:
            return self.queue.pop(0)
        raise TimeoutError()


class LocalFirmware:
    """@brief Minimal localhost UDP peer implementing the v1 session handshake."""

    def __init__(self, *, inject_noise=True):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("127.0.0.1", 0))
        self.sock.setblocking(False)
        self.address = self.sock.getsockname()
        self.inject_noise = inject_noise
        self.stop = threading.Event()
        self.error = None
        self.cookie = 0x123456789ABCDEF
        self.peer = None
        self.nonce = None
        self.flags = 0
        self.active = False
        self.input_seq = 0
        self.next_input_ns = None
        self.offered_valid_inputs = 0
        self.offered_noise_packets = 0
        self.last_control_seq = 1
        self.keepalive_sequences = []
        self.stop_sequences = []
        self.handshake = []
        self.thread = threading.Thread(target=self._run, name="fake-av-firmware", daemon=True)
        self.thread.start()

    def _send(self, wire):
        if self.peer is not None:
            self.sock.sendto(wire, self.peer)

    def _emit_inputs(self):
        now = time.monotonic_ns()
        if not self.active or now < self.next_input_ns:
            return
        self.next_input_ns = now + 20_000_000
        valid = _status(self.cookie, self.input_seq, buttons=self.input_seq & 0xFFF, audio=bool(self.flags))
        self._send(valid)
        self.offered_valid_inputs += 1
        if self.inject_noise:
            # A duplicate and older snapshot carry differing masks. Neither may
            # override the fresh complete snapshot or refresh its lease.
            self._send(_status(self.cookie, self.input_seq, buttons=0, audio=bool(self.flags)))
            self.offered_noise_packets += 1
            if self.input_seq:
                self._send(_status(self.cookie, self.input_seq - 1, buttons=0xFFF, audio=bool(self.flags)))
                self.offered_noise_packets += 1
            corrupted = bytearray(_status(self.cookie, self.input_seq + 1, audio=bool(self.flags)))
            corrupted[40] ^= 1
            self._send(corrupted)
            self.offered_noise_packets += 1
        self.input_seq = (self.input_seq + 1) & 0xFFFFFFFF

    def _run(self):
        try:
            while not self.stop.is_set():
                self._emit_inputs()
                readable, _, _ = select.select([self.sock], [], [], 0.002)
                if not readable:
                    continue
                raw, source = self.sock.recvfrom(561)
                packet = decode(raw)
                if packet.magic != b"MSC1":
                    continue
                if packet.kind == 1:
                    self.peer = source
                    self.flags = packet.flags
                    nonce = packet.session
                    self.nonce = nonce
                    self.handshake.append("hello")
                    offer = Packet(
                        b"MSR1", 1, self.cookie, flags=self.flags, payload=NONCE.pack(nonce)
                    )
                    self._send(offer.encode())
                elif packet.kind == 2:
                    self.peer = source
                    if packet.session != self.cookie or NONCE.unpack(packet.payload)[0] != self.nonce:
                        raise AssertionError("START did not match active offer")
                    self.active = True
                    self.next_input_ns = time.monotonic_ns()
                    self.handshake.append("start")
                    self._send(_status(self.cookie, 0, audio=bool(self.flags)))
                elif packet.kind == 3:
                    self.keepalive_sequences.append(packet.seq)
                    if packet.seq <= self.last_control_seq:
                        raise AssertionError("KEEPALIVE was not strictly newer")
                    self.last_control_seq = packet.seq
                elif packet.kind == 4:
                    self.stop_sequences.append(packet.seq)
                    if packet.seq <= self.last_control_seq:
                        raise AssertionError("STOP was not newer than KEEPALIVE")
                    self.active = False
                    self.handshake.append("stop")
        except (OSError, ValueError, AssertionError) as error:
            if not self.stop.is_set():
                self.error = error

    def close(self):
        self.stop.set()
        self.thread.join(timeout=2)
        self.sock.close()
        if self.thread.is_alive():
            raise RuntimeError("Fake firmware thread did not stop")


class HandshakeTests(unittest.TestCase):
    """@brief Reject mismatched offer fields/source before accepting ACTIVE MSI1."""

    def test_handshake_filters_nonce_flags_and_source_before_starting(self):
        peer = ("127.0.0.1", 5534)
        stub = HandshakeStub(peer)
        cookie, initial = handshake(stub, peer, audio=True, timeout=1)
        self.assertEqual(cookie, 0xCAFE)
        self.assertEqual(decode(initial).seq, 1)
        self.assertEqual([(p.magic, p.kind) for p in stub.sent], [(b"MSC1", 1), (b"MSC1", 2)])
        self.assertEqual(stub.sent[1].seq, 1)
        self.assertEqual(NONCE.unpack(stub.sent[1].payload)[0], stub.sent[0].session)


class LocalFirmwareSoakTests(unittest.TestCase):
    """@brief Exercise a five-second localhost session and ordered noisy MSI1 stream."""

    def test_localhost_handshake_newer_msi_soak_and_stop(self):
        firmware = LocalFirmware()
        args = argparse.Namespace(
            receiver="127.0.0.1",
            port=firmware.address[1],
            bind="127.0.0.1",
            source_port=0,
            seconds=5,
            gain=0.25,
            log=None,
            tone=False,
            loopback=False,
            file=None,
            gamepad=False,
            device=None,
        )
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                counts = run(args)
            self.assertEqual(counts["input_timeouts"], 0)
            # The fake firmware offers 50 Hz current snapshots plus intentional
            # duplicate/stale/bad-CRC traffic. Windows localhost UDP scheduling
            # may drop that burst; this asserts liveness, not 50 Hz throughput.
            self.assertGreater(firmware.offered_valid_inputs, 120)
            self.assertGreater(counts["input_packets"], 20)
            self.assertLessEqual(counts["input_packets"], firmware.offered_valid_inputs)
            self.assertGreater(counts["stale_packets"], 0)
            self.assertGreater(counts["invalid_packets"], 0)
            self.assertEqual(firmware.handshake[:2], ["hello", "start"])
            deadline = time.monotonic() + 1.0
            while "stop" not in firmware.handshake and time.monotonic() < deadline:
                time.sleep(0.005)
            self.assertEqual(firmware.handshake[-1], "stop")
            self.assertTrue(firmware.keepalive_sequences)
            self.assertEqual(firmware.keepalive_sequences[0], 2)
            self.assertEqual(firmware.stop_sequences[-1], firmware.keepalive_sequences[-1] + 1)
            self.assertIsNone(firmware.error)
            print(
                "localhost fake-firmware soak: "
                + json.dumps(
                    {
                        "duration_s": args.seconds,
                        "offered_new_msi": firmware.offered_valid_inputs,
                        "offered_duplicate_stale_crc_noise": firmware.offered_noise_packets,
                        "accepted_new_msi": counts["input_packets"],
                        "rejected_stale_or_wrong": counts["stale_packets"],
                        "rejected_crc": counts["invalid_packets"],
                        "keepalives": len(firmware.keepalive_sequences),
                        "stops": len(firmware.stop_sequences),
                        "input_timeouts": counts["input_timeouts"],
                    },
                    sort_keys=True,
                )
            )
        finally:
            firmware.close()


class AudioWorkerTests(unittest.TestCase):
    """@brief Decode complete tone packets and compare frozen FFmpeg WAV evidence."""

    def test_tone_worker_outputs_independent_512_byte_505_frame_blocks(self):
        worker = EncodedAudio("tone", gain=0.25)
        worker.start()
        try:
            seq, stamp, block = worker.blocks.get(timeout=5)
            self.assertEqual(seq, 0)
            self.assertGreater(stamp, 0)
            self.assertEqual(len(block), BLOCK)
            wire = Packet(b"MSA1", 1, 1, seq=seq, timestamp_us=stamp // 1000, payload=block).encode()
            packet = decode(wire)
            self.assertEqual(packet.payload, block)
            decoded = av.open(io.BytesIO(_wav_with_block(block)), format="wav")
            frames = list(decoded.decode(audio=0))
            self.assertEqual(sum(frame.samples for frame in frames), FRAMES)
            self.assertEqual({frame.sample_rate for frame in frames}, {RATE})
        finally:
            worker.close()

    def test_ffmpeg_golden_block_decodes_to_exact_retained_pcm(self):
        ffmpeg = shutil.which("ffmpeg")
        if not ffmpeg:
            self.skipTest("ffmpeg executable is not available")
        manifest = json.loads((GOLDENS / "vectors.json").read_text(encoding="utf-8"))
        block = (GOLDENS / "stereo-505.ima").read_bytes()
        expected_pcm = (GOLDENS / "stereo-505-decoded.s16le").read_bytes()
        self.assertEqual(len(block), BLOCK)
        self.assertEqual(len(expected_pcm), FRAMES * 2 * 2)
        self.assertEqual(hashlib.sha256(expected_pcm).hexdigest(), manifest["decoded_pcm_sha256"])
        with tempfile.TemporaryDirectory(prefix="av-v1-golden-") as temporary:
            output = Path(temporary) / "decoded.s16le"
            result = subprocess.run(
                [
                    ffmpeg,
                    "-v",
                    "error",
                    "-y",
                    "-i",
                    str(GOLDENS / "stereo-505.wav"),
                    "-f",
                    "s16le",
                    "-acodec",
                    "pcm_s16le",
                    str(output),
                ],
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr.decode(errors="replace"))
            actual_pcm = output.read_bytes()
        self.assertEqual(len(actual_pcm), FRAMES * 2 * 2)
        self.assertEqual(hashlib.sha256(actual_pcm).hexdigest(), manifest["decoded_pcm_sha256"])
        self.assertEqual(actual_pcm, expected_pcm)


if __name__ == "__main__":
    unittest.main()
