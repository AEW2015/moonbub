#!/usr/bin/env python3
"""Make deterministic, non-gameplay JPEG frames and independent RGB565 references."""
import argparse
from array import array
from io import BytesIO
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'host'))
from PIL import Image, __version__ as pillow_version
from make_fixture import pattern
from moonshine.encoding import encode, validate_jpeg


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path, help='new or empty output directory')
    parser.add_argument('--frames', type=int, default=10)
    args = parser.parse_args()
    if not 1 <= args.frames <= 1800:
        parser.error('--frames must be between 1 and 1800')
    if args.output.exists() and any(args.output.iterdir()):
        parser.error('output directory must be empty')
    args.output.mkdir(parents=True, exist_ok=True)
    manifest = {'format_version': 1, 'source': 'Moonbub synthetic moving bars and detail; not gameplay',
                'fps': 30, 'width': 720, 'height': 480, 'quality': 65,
                'jpeg': 'Moonbub baseline 4:2:0 fixed Huffman profile',
                'reference': 'Pillow RGB to little-endian RGB565; chroma/IDCT differs from RTL; no tolerance has been established',
                'pillow_version': pillow_version, 'frames': []}
    seen = set()
    for frame_id in range(args.frames):
        jpeg = encode(pattern(frame_id), quality=65, subsampling='420')
        validate_jpeg(jpeg)
        digest_jpeg = digest(jpeg)
        if digest_jpeg in seen:
            raise ValueError(f'duplicate JPEG at frame {frame_id}')
        seen.add(digest_jpeg)
        with Image.open(BytesIO(jpeg)) as image:
            pixels = image.convert('RGB').tobytes()
        words = array('H', (((pixels[i] >> 3) << 11) | ((pixels[i+1] >> 2) << 5) | (pixels[i+2] >> 3)
                            for i in range(0, len(pixels), 3)))
        if words.itemsize != 2: raise RuntimeError('16-bit reference type required')
        if sys.byteorder != 'little': words.byteswap()
        reference = words.tobytes()
        if len(reference) != 720 * 480 * 2: raise ValueError('wrong reference size')
        stem = f'{frame_id:04d}'
        (args.output / f'{stem}.jpg').write_bytes(jpeg)
        (args.output / f'{stem}.rgb565le').write_bytes(reference)
        manifest['frames'].append({'id': frame_id, 'presentation_time_numerator': frame_id,
                                   'presentation_time_denominator': 30,
                                   'jpeg_bytes': len(jpeg), 'jpeg_sha256': digest_jpeg,
                                   'rgb565le_sha256': digest(reference)})
    (args.output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(f'generated {len(manifest["frames"])} distinct, validated JPEG frames in {args.output}')


if __name__ == '__main__':
    main()
