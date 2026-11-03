"""Actual-packet diagnostic for a known synthetic horizontal pan, not gameplay."""
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image

import motion_codec as mc

HERE = Path(__file__).resolve().parent


def frames(height, width, count=10):
    rng = np.random.default_rng(5)
    small = rng.integers(30, 220, (10, 12), dtype=np.uint8)
    base = np.asarray(Image.fromarray(small).resize((width, height), Image.Resampling.BILINEAR))
    rgb = np.repeat(base[..., None], 3, axis=2)
    for i in range(count):
        offset = i*4
        columns = np.maximum(np.arange(width)-offset, 0)
        yield rgb[:, columns].copy()


def main():
    rows = []
    for height, width in ((80, 96), (480, 720)):
        source = list(frames(height, width))
        for mode in ('zero', 'global'):
            enc, dec = mc.Encoder(), mc.Receiver()
            records = []
            mse = []
            for i, rgb in enumerate(source):
                packet = enc.prepare(rgb, i, quant_scale=8, mode=mode)
                actual, info = dec.receive(packet)
                if not np.array_equal(actual, enc.prepared_rgb()):
                    raise AssertionError('diagnostic reconstructed reference mismatch')
                enc.ack(info['frame_id'], epoch=info['epoch'])
                error = rgb.astype(np.float64)-actual
                mse.append(float(np.mean(error*error)))
                records.append({'id': i, 'bytes': len(packet), 'dx': info['dx'], 'dy': info['dy'],
                                'input_sha256': hashlib.sha256(rgb.tobytes()).hexdigest(),
                                'output_rgb_sha256': hashlib.sha256(actual.tobytes()).hexdigest()})
            rows.append({'width': width, 'height': height, 'mode': mode, 'records': records,
                         'total_packet_bytes': sum(x['bytes'] for x in records),
                         'mean_delta_packet_bytes': float(np.mean([x['bytes'] for x in records[1:]])),
                         'rgb_psnr_db': float(10*np.log10(65025/np.mean(mse))),
                         'scope': 'synthetic pan, immediate ACK, raw RGB error before RGB565; not game quality or timing'})
    result = {'evidence': 'actual MT02 packets over deterministic synthetic4pixelpan; no FPS claim',
              'source_sha256': {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in
                                (HERE/'synthetic_motion.py', HERE/'motion_codec.py', Path(mc.cc.__file__), Path(mc.ft.__file__))},
              'seed': 5, 'profiles': rows}
    (HERE/'synthetic-results.json').write_text(json.dumps(result, indent=2)+'\n')
    for row in rows:
        print(row['width'], row['mode'], row['total_packet_bytes'], row['mean_delta_packet_bytes'],
              row['rgb_psnr_db'], [(x['dx'], x['dy']) for x in row['records'][1:]])


if __name__ == '__main__':
    main()
