"""Compare modeled burst/packing signatures; not a hardware fault locator."""
import pathlib,json,zlib,numpy as np
R=pathlib.Path(__file__).resolve().parents[1];E=R/'evidence/hardware-cpl1-timing-20261105T195529Z';P=R/'fpga/exports/cpl1-timing-fsmcopy-source-20261105-v002/sim-assets'
memory=np.array([int(x,16)for x in(P/'column.hex').read_text().split()],dtype='<u2');gold=np.array([int(x,16)for x in(P/'composite.hex').read_text().split()],dtype='<u2').reshape(480,720)
rects=[(22,54,160,24),(22,82,160,24),(168,360,320,24),(168,390,240,24)]
def upsample(p):
 p=p.astype(np.int32);right=np.concatenate([p[:,1:],p[:,-1:]],axis=1)
 h=np.empty((240,720),dtype=np.int32);h[:,::2]=p;h[:,1::2]=(p+right+1)//2
 below=np.concatenate([h[1:,:],h[-1:,:]],axis=0);out=np.empty((480,720),dtype=np.int32);out[::2,:]=h;out[1::2,:]=(h+below+1)//2;return out-128
def render(m):
 y=m[:172800].view(np.uint8).reshape(720,480).T.astype(np.int32)
 cb=upsample(m[172800:216000].view(np.uint8).reshape(360,240).T)
 cr=upsample(m[216000:].view(np.uint8).reshape(360,240).T)
 red=np.clip(y+((359*cr+128)>>8),0,255);green=np.clip(y-((88*cb+183*cr+128)>>8),0,255);blue=np.clip(y+((454*cb+128)>>8),0,255)
 out=((red>>3)<<11)|((green>>2)<<5)|(blue>>3)
 for x,y,w,h in rects:out[y:y+h,x:x+w]=gold[y:y+h,x:x+w]
 return out.astype('<u2')
crc=lambda image:format(zlib.crc32(np.ascontiguousarray(image.T,dtype='<u2').tobytes()),'08x')
baseline=render(memory);assert np.array_equal(baseline,gold),'Independent reconstruction must match the complete unchanged oracle first'
assert crc(baseline)=='4c5725e5'
observed=json.loads((E/'second-snapshot.json').read_text())['fields']['canvas_crc32_hex'];results={'unmodified':crc(baseline),'YUV_word_byteswap':crc(render(memory.byteswap()))}
groups=memory.reshape(-1,8)
for delta in [-2,-1,1,2]:
 for fill in ['wrap','edge','zero','ffff']:
  out=np.empty_like(groups)
  for i in range(8):
   j=i+delta
   if 0<=j<8:out[:,i]=groups[:,j]
   elif fill=='wrap':out[:,i]=groups[:,j%8]
   elif fill=='edge':out[:,i]=groups[:,max(0,min(7,j))]
   elif fill=='zero':out[:,i]=0
   else:out[:,i]=65535
  results[f'burst8_shift{delta}_{fill}']=crc(render(out.ravel()))
(E/'burst-signature-comparison.json').write_text(json.dumps(dict(scope='Offline transformations of golden memory, not observations of hardware memory/read data',observed=observed,oracle='4c5725e5',baseline_exact_pixels=True,variants=results,matches=[name for name,value in results.items()if value==observed],limits='Even an exact signature does not distinguish write corruption from read capture or locate the physical stage without further evidence.'),indent=2)+'\n');print('BURST_SIGNATURE_MATCHES',[name for name,value in results.items()if value==observed])
