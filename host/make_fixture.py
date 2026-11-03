"""Generate deterministic motion/detail test fixture, not representative gameplay."""
from io import BytesIO
from pathlib import Path
import json
import hashlib
import struct
from PIL import Image, ImageDraw
from moonshine.encoding import encode
from moonshine.protocol import packets


def pattern(frame=0):
    image = Image.new("RGB", (1280, 720))
    draw = ImageDraw.Draw(image)
    colors = [(255, 255, 255), (255, 255, 0), (0, 255, 255), (0, 255, 0), (255, 0, 255), (255, 0, 0), (0, 0, 255), (0, 0, 0)]
    for i, color in enumerate(colors):
        draw.rectangle((i * 160, 0, i * 160 + 159, 359), fill=color)
    for y in range(360, 720, 12):
        for x in range(0, 1280, 12):
            draw.rectangle((x, y, x + 11, y + 11), fill=((x + frame * 7) % 256, y % 256, (x ^ y) % 256))
    x = (frame * 17) % 1100
    draw.rectangle((x, 250, x + 179, 429), fill=(255, 255, 255), outline=(0, 0, 0), width=8)
    return image


def main():
    output = Path(__file__).parent / "fixtures"
    output.mkdir(exist_ok=True)
    jpeg = encode(pattern(), 65)
    (output / "pattern-720x480-420-q65.jpg").write_bytes(jpeg)
    decoded = Image.open(BytesIO(jpeg)).convert("RGB")
    decoded.save(output / "pattern-reference.ppm")
    pixels = decoded.tobytes()
    rgb565 = bytearray()
    for i in range(0, len(pixels), 3):
        r, g, b = pixels[i:i + 3]
        rgb565.extend(struct.pack("<H", ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3)))
    (output / "pattern-reference-rgb565.bin").write_bytes(rgb565)
    wire = b"".join(struct.pack("!H", len(packet)) + packet for packet in packets(jpeg, 0x12345678, 1234567890123))
    (output / "pattern-msv1-packets.bin").write_bytes(wire)
    manifest = {"source": "deterministic bars/detail pattern; not gameplay footage", "canvas": [720, 480],
                "content": [720, 405], "black_rows": [37, 38], "codec": "JPEG baseline 420 standard DHT",
                "quality": 65, "reference": "Pillow RGB decode; core integer IDCT/color rounding may differ", "files": {}}
    manifest["packet_fixture"] = {"framing": "u16 big-endian datagram length then exact MSV1 datagram, repeated to EOF",
                                  "frame_id": 0x12345678, "capture_us": 1234567890123, "payload_size": 1024}
    for path in output.iterdir():
        if path.suffix != ".json":
            manifest["files"][path.name] = {"bytes": path.stat().st_size, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest))


if __name__ == "__main__":
    main()
