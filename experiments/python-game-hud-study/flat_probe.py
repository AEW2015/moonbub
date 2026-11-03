#!/usr/bin/env python3
"""Separate deliberately low-color HUD best-case fixtures; not game evidence."""
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform

import numpy as np
from PIL import Image,ImageDraw,ImageFont
import hud_codec as h

HERE=Path(__file__).resolve().parent
RECTS=((16,48,192,80),(160,352,400,80))


def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def fixture(colored):
    rgb=np.full((480,720,3),(25,30,40),np.uint8)
    for x,y,w,rh in RECTS:rgb[y:y+rh,x:x+w]=(12,16,20)
    # A 1-bit mask deliberately excludes antialias colors. This is the stated
    # low-color best case, not a measurement of a real game's UI renderer.
    mask=Image.new('1',(720,480),0);draw=ImageDraw.Draw(mask);font=ImageFont.load_default(size=18)
    draw.text((24,56),'HP 090 / 100',font=font,fill=1)
    draw.text((168,360),'MISSION 01: REACH THE EXIT',font=font,fill=1)
    draw.text((168,390),'AMMO 024',font=font,fill=1)
    rgb[np.asarray(mask,dtype=bool)]=(240,240,240)
    if colored:rgb[104:112,24:184]=(40,200,80)
    return rgb


def main():
    sources=[HERE/'flat_probe.py',HERE/'hud_codec.py',Path(h.gm.__file__),Path(h.gm.roi.__file__),Path(h.gm.ft.__file__),
             Path(h.gm.mt.__file__),Path(h.gm.token_coeff.__file__),Path(h.gm.word_coeff.__file__),
             Path(h.gm.word_coeff.frozen_codec.__file__),Path(h.corpus.__file__)]
    hashes={str(p):digest(p) for p in sources};cases=[]
    for colored in (False,True):
        rgb=fixture(colored);m=h.gm.roi.declared_map(720,480,RECTS,8,16)
        enc=h.gm.Encoder();base=enc.prepare(rgb,0,scale_map=m)
        wrapper=h.encode_frame(base,rgb,RECTS);actual,info=h.Receiver().receive(wrapper)
        assert info['base_rgb_sha256']==enc.expected_hash(0)
        original=h.corpus.rgb565(rgb);displayed=h.corpus.rgb565(actual)
        mask=np.zeros((480,720),bool)
        for x,y,w,rh in RECTS:mask[y:y+rh,x:x+w]=True
        errors=int(np.count_nonzero(original[mask]!=displayed[mask]));assert errors==0
        cases.append({'name':'flat-colored-3color-first-region' if colored else 'flat-monochrome-2color-regions',
                      'synthetic':True,'source_sha256':hashlib.sha256(rgb.tobytes()).hexdigest(),
                      'base_bytes':len(base),'wrapped_bytes':len(wrapper),'patch_increment_bytes':len(wrapper)-len(base),
                      'base_packet_sha256':hashlib.sha256(base).hexdigest(),'packet_sha256':hashlib.sha256(wrapper).hexdigest(),
                      'over_48k_cap':len(wrapper)>49152,'patches':info['patches'],
                      'roi_rgb565_word_mismatches':errors,'base_rgb_sha256':info['base_rgb_sha256'],
                      'display_rgb565_sha256':hashlib.sha256(displayed.astype('<u2').tobytes()).hexdigest(),
                      'scope':'Deliberately flat background and1-bit glyph mask; best-case palette1/2bit test, not real-game/HUD or performance proof'})
    assert hashes=={str(p):digest(p) for p in sources}
    result={'evidence':'Two separately labeled synthetic low-color functional HUD patch probes; no timing or realgame/generalization claim',
            'source_sha256':hashes,'versions':{'python':platform.python_version(),**{n:importlib.metadata.version(n) for n in ('numpy','Pillow','av')}},
            'rectangles':RECTS,'cases':cases,'pixels_in_declared_regions':47360,
            'comparison_scope':'Main18source campaign including36overcap wrappers remains unchanged; these are deliberately favorable newfixtures'}
    (HERE/'flat-results.json').write_text(json.dumps(result,indent=2)+'\n')
    for c in cases:print(c['name'],c['base_bytes'],c['wrapped_bytes'],[(p['mode'],p['colors']) for p in c['patches']],c['over_48k_cap'])


if __name__=='__main__':main()
