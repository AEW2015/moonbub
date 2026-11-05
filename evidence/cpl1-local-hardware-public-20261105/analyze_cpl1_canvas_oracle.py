"""Offline oracle visualization/transform checks; never changes expectations."""
import pathlib,zlib,json,numpy as np
from PIL import Image
R=pathlib.Path(__file__).resolve().parents[1];E=R/'evidence/hardware-cpl1-timing-20261105T195529Z';P=R/'fpga/exports/cpl1-timing-fsmcopy-source-20261105-v002/sim-assets'
v=np.array([int(x,16)for x in(P/'composite.hex').read_text().split()],dtype=np.uint16).reshape(480,720)
crc=lambda a:format(zlib.crc32(np.ascontiguousarray(a.T,dtype='<u2').tobytes()),'08x')
assert crc(v)=='4c5725e5'
rgb=np.stack([((v>>11)&31)*255//31,((v>>5)&63)*255//63,(v&31)*255//31],axis=2).astype(np.uint8)
Image.fromarray(rgb).save(E/'expected-composite.png')
actual=json.loads((E/'second-snapshot.json').read_text())['fields']['canvas_crc32_hex']
variants={'unmodified':crc(v),'byte_swap':crc(v.byteswap()),'BGR565':crc(((v&31)<<11)|(v&0x7e0)|(v>>11)),'flip_horizontal':crc(v[:,::-1]),'flip_vertical':crc(v[::-1,:])}
for axis in [0,1]:
 for n in [-2,-1,1,2]:variants[f'roll_axis{axis}_{n}']=crc(np.roll(v,n,axis))
linear=v.T.copy().ravel()
for n in [-2,-1,1,2]:variants[f'continuous_word_roll_{n}']=format(zlib.crc32(np.roll(linear,n).astype('<u2').tobytes()),'08x')
(E/'oracle-transform-comparison.json').write_text(json.dumps(dict(scope='Offline deterministic transform comparisons only; no hardware pixel capture and no changed oracle',expected='4c5725e5',observed=actual,variants=variants,matches=[n for n,c in variants.items()if c==actual]),indent=2)+'\n');print('ORACLE_CHECK',actual,'matches',[n for n,c in variants.items()if c==actual])
