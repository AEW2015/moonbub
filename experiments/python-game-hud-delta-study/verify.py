"""Reconcile frozen HD21 controls with a separately written scalar decoder."""
from pathlib import Path
import hashlib
import json
import struct
import zlib

import numpy as np
import model

HERE = Path(__file__).resolve().parent


def sha(data):
    return hashlib.sha256(data).hexdigest()


def load_blob(desc):
    path = Path(desc["path"])
    assert not path.is_absolute() and ".." not in path.parts
    data = (HERE / path).read_bytes()
    assert sha(data) == desc["stored_sha256"]
    inflater = zlib.decompressobj()
    raw = inflater.decompress(data, desc["raw_bytes"] + 1)
    assert inflater.eof and not inflater.unused_data and not inflater.unconsumed_tail
    assert len(raw) == desc["raw_bytes"] and sha(raw) == desc["raw_sha256"]
    return raw


def independent_decode(packet, reference):
    """Fixture decoder intentionally does not invoke model's parser/tag logic."""
    magic, version, mode, width, height, length, ref_tag, out_tag = struct.unpack_from("<4sBBHHI16s16s", packet)
    assert magic == b"HD21" and version == 1 and mode in (0, 1, 2)
    assert 0 < width <= 720 and 0 < height <= 480 and width * height <= 21120
    assert length <= 42240 and len(packet) == 50 + length
    assert struct.unpack_from("<I", packet, len(packet) - 4)[0] == zlib.crc32(packet[:-4]) & 0xFFFFFFFF
    body = packet[46:-4]
    prefix = struct.pack("<HH", width, height)
    if mode == 0:
        assert ref_tag == bytes(16) and len(body) == width * height * 2
        words = list(struct.unpack("<" + "H" * (width * height), body))
    else:
        assert reference is not None and len(reference) == width * height * 2
        assert hashlib.sha256(prefix + reference).digest()[:16] == ref_tag
        words = list(struct.unpack("<" + "H" * (width * height), reference))
        if mode == 1:
            assert not body
        else:
            assert len(body) >= 2
            records = struct.unpack_from("<H", body)[0]
            offset, prior_row, prior_end = 2, -1, -1
            assert records > 0
            for _ in range(records):
                assert offset + 6 <= len(body)
                row, start, count = struct.unpack_from("<HHH", body, offset)
                offset += 6
                assert row < height and count and start + count <= width
                assert row > prior_row or (row == prior_row and start > prior_end)
                assert offset + 2 * count <= len(body)
                for j in range(count):
                    delta = struct.unpack_from("<H", body, offset)[0]
                    assert delta
                    words[row * width + start + j] ^= delta
                    offset += 2
                prior_row, prior_end = row, start + count
            assert offset == len(body)
    output = struct.pack("<" + "H" * len(words), *words)
    assert hashlib.sha256(prefix + output).digest()[:16] == out_tag
    return output


def main():
    data = json.loads((HERE / "results.json").read_text())
    assert data["schema"] == "gamebub-hud-delta-v21-1"
    for path, digest in data["source_sha256"].items():
        assert sha((HERE / path).read_bytes()) == digest, path
    words = packet_bytes = negatives = 0
    for vector in data["vectors"]:
        packet = load_blob(vector["packet"])
        current = load_blob(vector["current"])
        reference = None if vector["reference"] is None else load_blob(vector["reference"])
        assert independent_decode(packet, reference) == current
        assert model.inspect(packet) == vector["metadata"]
        ref_array = None if reference is None else np.frombuffer(reference, dtype="<u2").reshape(vector["shape"])
        assert model.decode(packet, ref_array).tobytes() == current
        assert model.encode(np.frombuffer(current, dtype="<u2").reshape(vector["shape"]), ref_array) == packet
        try:
            model.decode(packet[:-1] + bytes([packet[-1] ^ 1]), ref_array)
        except ValueError:
            negatives += 1
        else:
            raise AssertionError("CRC-negative accepted")
        words += len(current) // 2
        packet_bytes += len(packet)
    assert data["summary"] == dict(vectors=6, roundtrip_words=words, complete_packet_bytes=packet_bytes)
    print(json.dumps(dict(vectors=6, independent_scalar_words=words, crc_negatives=negatives,
                          complete_packet_bytes=packet_bytes, physical_30fps_proven=False), indent=2))


if __name__ == "__main__":
    main()
