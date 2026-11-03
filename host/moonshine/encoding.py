"""Restricted baseline JPEG encoder compatible with fixed-table core_jpeg."""
from io import BytesIO
from PIL import Image


def letterbox(image: Image.Image, size=(720, 480)) -> Image.Image:
    image = image.convert("RGB")
    scale = min(size[0] / image.width, size[1] / image.height)
    extent = (min(size[0], round(image.width * scale)), min(size[1], round(image.height * scale)))
    image = image.resize(extent, Image.Resampling.LANCZOS)
    result = Image.new("RGB", size, (0, 0, 0))
    result.paste(image, ((size[0] - extent[0]) // 2, (size[1] - extent[1]) // 2))
    return result


def segments(jpeg: bytes):
    """Yield JPEG marker bodies, checking entropy stuffing and unsupported RST."""
    if not jpeg.startswith(b"\xff\xd8"):
        raise ValueError("missing JPEG SOI")
    pos = 2
    entropy = False
    while pos < len(jpeg):
        if entropy:
            start = jpeg.find(b"\xff", pos)
            if start < 0:
                raise ValueError("truncated JPEG entropy stream")
            pos = start
        if jpeg[pos] != 255:
            raise ValueError("invalid JPEG marker")
        while pos < len(jpeg) and jpeg[pos] == 255:
            pos += 1
        if pos == len(jpeg):
            raise ValueError("truncated JPEG marker")
        marker = jpeg[pos]
        pos += 1
        if marker == 0 and entropy:
            continue
        if 0xd0 <= marker <= 0xd7:
            raise ValueError("restart markers are unsupported")
        if marker == 0xd9:
            if pos != len(jpeg):
                raise ValueError("bytes after EOI")
            yield marker, b""
            return
        entropy = False
        if pos + 2 > len(jpeg):
            raise ValueError("truncated marker length")
        length = int.from_bytes(jpeg[pos:pos + 2], "big")
        if length < 2 or pos + length > len(jpeg):
            raise ValueError("invalid JPEG marker length")
        body = jpeg[pos + 2:pos + length]
        pos += length
        yield marker, body
        if marker == 0xda:
            entropy = True
    raise ValueError("missing JPEG EOI")


def _dht_tables(body):
    while body:
        if len(body) < 17:
            raise ValueError("truncated Huffman table")
        length = 17 + sum(body[1:17])
        if length > len(body):
            raise ValueError("truncated Huffman symbols")
        yield body[:length]
        body = body[length:]


def _standard_huffman_tables():
    reference = BytesIO()
    Image.new("RGB", (8, 8)).save(reference, "JPEG", quality=50, optimize=False, progressive=False, subsampling=0)
    return {table for marker, body in segments(reference.getvalue()) if marker == 0xc4 for table in _dht_tables(body)}


STANDARD_DHT = _standard_huffman_tables()


def validate_jpeg(jpeg: bytes, expected=(720, 480), subsampling="420"):
    jpeg = bytes(jpeg)
    seen_sof = seen_sos = False
    tables = set()
    quantizers = set()
    for marker, body in segments(jpeg):
        if marker in (0xc1, 0xc2, 0xc3, 0xc5, 0xc6, 0xc7, 0xc9, 0xca, 0xcb, 0xcd, 0xce, 0xcf, 0xdd, 0xcc):
            raise ValueError("unsupported JPEG mode/restart interval")
        if marker == 0xc0:
            if seen_sof or len(body) != 15 or body[0] != 8 or body[5] != 3:
                raise ValueError("requires one 8-bit three-component SOF0")
            dimensions = (int.from_bytes(body[3:5], "big"), int.from_bytes(body[1:3], "big"))
            if dimensions != expected:
                raise ValueError("JPEG dimensions differ from transport")
            factors = tuple(body[i] for i in (7, 10, 13))
            if factors != ((0x11, 0x11, 0x11) if subsampling == "444" else (0x22, 0x11, 0x11)):
                raise ValueError("unsupported JPEG subsampling")
            if tuple(body[i] for i in (6, 9, 12)) != (1, 2, 3) or tuple(body[i] for i in (8, 11, 14)) != (0, 1, 1):
                raise ValueError("unsupported JPEG component IDs/quantizer mapping")
            seen_sof = True
        elif marker == 0xdb:
            while body:
                if len(body) < 65 or body[0] not in (0, 1):
                    raise ValueError("requires 8-bit quantization tables0 and1")
                quantizers.add(body[0])
                body = body[65:]
        elif marker == 0xc4:
            tables.update(_dht_tables(body))
        elif marker == 0xda:
            if seen_sos or not seen_sof or len(body) != 10 or body[0] != 3 or body[-3:] != b"\x00\x3f\x00":
                raise ValueError("requires one baseline interleaved scan")
            if body[1:7] != b"\x01\x00\x02\x11\x03\x11":
                raise ValueError("unsupported JPEG scan component/table mapping")
            seen_sos = True
    if not seen_sof or not seen_sos or tables != STANDARD_DHT or quantizers != {0, 1}:
        raise ValueError("missing baseline scan or nonstandard Huffman tables")


def encode(image: Image.Image, quality=65, subsampling="420") -> bytes:
    if not 1 <= quality <= 95 or subsampling not in ("444", "420"):
        raise ValueError("unsupported encoder setting")
    output = BytesIO()
    letterbox(image).save(output, "JPEG", quality=quality, subsampling=0 if subsampling == "444" else 2,
                         optimize=False, progressive=False)
    result = output.getvalue()
    validate_jpeg(result, subsampling=subsampling)
    return result
