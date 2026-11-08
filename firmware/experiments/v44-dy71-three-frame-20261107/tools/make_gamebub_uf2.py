"""Package a Rev4 application binary for the Game Bub USB updater."""
import argparse
import hashlib
import json
import pathlib
import struct

APP_START = 0x100000
APP_END = 0x600000
FAMILY = 0xC47E5767
# Official gamebub-rev4_v1.0.1.uf2: variant, minor, major, product.
DEVICE = b"bub!\x00\x00\x04\x01"


def package(data):
    if not data or data[0] != 0xE9:
        raise ValueError("Expected an ESP application image")
    padded = data + b"\xff" * (-len(data) % 256)
    if APP_START + len(padded) > APP_END:
        raise ValueError("Image exceeds the application partition")
    count = len(padded) // 256
    blocks = []
    for index in range(count):
        block = bytearray(512)
        struct.pack_into("<8I", block, 0, 0x0A324655, 0x9E5D5157,
                         0xA000, APP_START + index * 256, 256,
                         index, count, FAMILY)
        block[32:288] = padded[index * 256:(index + 1) * 256]
        struct.pack_into("<I", block, 288, (0xC8A729 << 8) | 12)
        block[292:300] = DEVICE
        struct.pack_into("<I", block, 508, 0x0AB16F30)
        blocks.append(block)
    return b"".join(blocks)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("binary", type=pathlib.Path)
    parser.add_argument("output", type=pathlib.Path)
    args = parser.parse_args()
    data = args.binary.read_bytes()
    uf2 = package(data)
    args.output.write_bytes(uf2)
    manifest = {
        "board": "Game Bub Rev4 (product 1)",
        "application_address": hex(APP_START),
        "binary_bytes": len(data),
        "uf2_blocks": len(uf2) // 512,
        "uf2_bytes": len(uf2),
        "binary_sha256": hashlib.sha256(data).hexdigest(),
        "uf2_sha256": hashlib.sha256(uf2).hexdigest(),
        "hardware_tested": False,
    }
    args.output.with_suffix(".json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
