import importlib.util
import io
from pathlib import Path
import socket
import struct
import threading
import unittest
import zlib

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('sender', ROOT/'tools/dy71_fixture_sender.py')
sender = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sender)
BODY = (ROOT/'handheld/src/cu66/fixtures/packet0.cu66').read_bytes()


class SenderTests(unittest.TestCase):
    def test_original_fixture_validation(self):
        sender.validate(BODY)
        for index in (0, 4, 16, 68, len(BODY)-1):
            altered = bytearray(BODY)
            altered[index] ^= 1
            with self.assertRaises(ValueError):
                sender.validate(altered)

    def test_data_vector(self):
        b = sender.datagram(BODY, 7, 11, 1024)
        self.assertEqual(len(b), 1076)
        h = sender.HEADER.unpack(b[:48])
        self.assertEqual(h[:5], (b'DYN1', 1, 0, 48, 7))
        self.assertEqual(h[8], 1024)
        self.assertEqual(b[48:-4], BODY[1024:2048])
        self.assertEqual(zlib.crc32(b[:-4]), struct.unpack('<I', b[-4:])[0])

    def test_presentation_without_final_staging_ack(self):
        errors = []
        received = bytearray()
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as server:
            server.bind(('127.0.0.1', 0))
            server.settimeout(5)
            def receive():
                try:
                    while len(received) < len(BODY):
                        b, peer = server.recvfrom(2048)
                        h = list(sender.HEADER.unpack(b[:48]))
                        self.assertEqual(h[8], len(received))
                        received.extend(b[48:-4])
                        h[0] = b'DYA1'
                        h[2] = 2 if len(received) == len(BODY) else 0
                        h[8] = len(received)
                        h[11] = 0
                        reply = sender.HEADER.pack(*h)
                        server.sendto(reply + struct.pack('<I', zlib.crc32(reply)), peer)
                except BaseException as e:
                    errors.append(e)
            worker = threading.Thread(target=receive)
            worker.start()
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client:
                client.bind(('127.0.0.1', 0))
                client.settimeout(0.05)
                result = sender.send_frame(client, server.getsockname(), BODY, 9, io.StringIO())
            worker.join(6)
            self.assertFalse(worker.is_alive())
        self.assertFalse(errors, errors)
        self.assertEqual(received, BODY)
        self.assertEqual(result['status'], 'presented')


if __name__ == '__main__':
    unittest.main()
