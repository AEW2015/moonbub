"""Deterministic RGB888 source fixtures; no media download or RNG needed."""
from pathlib import Path
import sys
import numpy as np

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
for folder in ('python-game-unified-codec-study','python-game-unified-ui-study','python-game-feedback-study'):
    sys.path.insert(0,str(HERE.parent/folder))
import unified_codec as codec
import ui_plugin
import transport


def image(kind,index,width,height):
    y,x=np.indices((height,width))
    if kind=='gradient':
        rgb=np.stack(((x*3+index*2)%130+40,(y*4+index*3)%120+50,(x+y+index)%140+30),axis=-1).astype(np.uint8)
    elif kind=='flat':
        rgb=np.full((height,width,3),128+index,np.uint8)
    else:raise ValueError('fixture source kind')
    if kind=='gradient' or width==720:
        rgb[:8,:16]=[190+index,30+index,75]
    return rgb


def specs():
    return [dict(name='gm-small-lifecycle',mode='gm',kind='gradient',width=64,height=48,ui=True,
                 frames=[dict(id=i,promote=i==2,force_key=i==4) for i in range(5)]),
            dict(name='sr-small-lifecycle',mode='exact',kind='flat',width=64,height=48,ui=False,
                 frames=[dict(id=i,promote=i==2,force_key=False) for i in range(4)]),
            dict(name='full720-ui',mode='exact',kind='flat',width=720,height=480,ui=True,
                 frames=[dict(id=0,promote=False,force_key=True)])]


def encoder(spec):
    selector=ui_plugin.PatchSelector(rectangles=((0,0,16,8),)) if spec['ui'] else None
    return codec.Encoder(epoch=16,mode=spec['mode'],patch_builder=selector)


def prepare(enc,spec,row):
    rgb=image(spec['kind'],row['id'],spec['width'],spec['height'])
    return rgb,enc.prepare(rgb,row['id'],quant_scale=16,promote=row['promote'],force_key=row['force_key'])
