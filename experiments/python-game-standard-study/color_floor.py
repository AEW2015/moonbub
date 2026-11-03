#!/usr/bin/env python3
"""Separate no-compression color-conversion probes for RD interpretation."""
import hashlib
import json
import os
from pathlib import Path
import numpy as np
import av
import benchmark as b

HERE=Path(__file__).resolve().parent


def main():
    media=Path(os.environ.get('GAMEBUB_MEDIA_DIR',str(HERE.parents[3]/'media')))
    paths=[HERE/'color_floor.py',HERE/'benchmark.py',Path(b.gm.ft.__file__),Path(b.corpus.__file__)]
    pins={str(p):b.sha(p) for p in paths};cases=[]
    for clip in ('mass-effect-combat','mass-effect-2600'):
        frames,manifest=b.corpus.load_video(media/(clip+'.mp4'),max_frames=60,start_seconds=1)
        for method in ('pyav_yuv420_roundtrip','gm_integer_yuv420_roundtrip'):
            records=[]
            for i,rgb in enumerate(frames):
                if method.startswith('pyav'):
                    actual=av.VideoFrame.from_ndarray(rgb,format='rgb24').reformat(format='yuv420p').to_ndarray(format='rgb24')
                else:actual=b.gm.ft.planes_to_rgb(b.gm.ft.rgb_to_planes(rgb))
                records.append({'id':i,'quality':b.quality(rgb,actual,manifest['active_rects'][i]),'bytes':0,
                                'rgb565_sha256':hashlib.sha256(b.corpus.rgb565(actual).astype('<u2').tobytes()).hexdigest()})
            summary=b.summarize(records)
            cases.append({'source':clip,'method':method,'manifest':manifest,
                'distinct_input_rgb_hashes':len(set(manifest['frame_sha256'])),'records':records,'summary':summary})
    assert pins=={str(p):b.sha(p) for p in paths}
    result={'evidence':'Separate no-compressioncolorconversion probes, not RDcurves ordecoderfloors forother matrices/rangechoices.',
            'source_sha256':pins,'cases':cases,'scope':'ActualroundtripCPUarrays. RGB565displayquantizationincluded; GMandnativecolorarithmetic differ. Doesnotnormalizeorcorrect maincodecresults; nottargettiming.'}
    (HERE/'color-floor.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    for c in cases:print(c['source'],c['method'],c['distinct_input_rgb_hashes'],c['summary']['pooled'])


if __name__=='__main__':main()
