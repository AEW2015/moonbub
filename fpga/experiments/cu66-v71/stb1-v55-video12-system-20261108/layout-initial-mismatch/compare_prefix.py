"""Independent canonical bytes and every composed scanout pixel for NEW localvideo12."""
from pathlib import Path
import array,hashlib,json,re,sys
p=Path(__file__).resolve().parent;oracle=p/'goldens';sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
log=(p/'native-run.log').read_text(errors='replace');banks={int(f):int(b)for f,b in re.findall(r'ACTUAL_FRAME_PRESENTED frame=(\d+) bank=(\d+)',log)};assert banks and set(banks)==set(range(len(banks)))
rows=[]
for frame in sorted(banks):
 actual=p/f'frame{frame}-bank{banks[frame]}.u16';gold=oracle/f'frame{frame}.canonical.u16';a=actual.read_bytes();b=gold.read_bytes();assert len(a)==len(b)==518400
 canonical_bad=sum(x!=y for x,y in zip(a,b));raster=array.array('I');raster.frombytes((p/f'frame{frame}-raster.u32').read_bytes());pixels=array.array('H');pixels.frombytes((oracle/f'frame{frame}.rgb565').read_bytes())
 if sys.byteorder!='little':raster.byteswap();pixels.byteswap()
 assert len(raster)==384000 and len(pixels)==345600 and 0xffffffff not in raster
 bad=border=0;first=None
 for y in range(480):
  for x in range(800):
   actual_rgb=raster[y*800+x]
   if 40<=x<760:
    w=pixels[y*720+x-40];r=(w>>11)&31;g=(w>>5)&63;bl=w&31;want=(((r<<3)|(r>>2))<<16)|(((g<<2)|(g>>4))<<8)|((bl<<3)|(bl>>2))
    if actual_rgb!=want:
     bad+=1
     if first is None:first=[y,x]
   elif actual_rgb!=0:border+=1
 hud_actual=bytearray()
 for left,top,width,height in [(22,54,160,24),(22,82,160,24),(168,360,320,24),(168,390,240,24)]:
  for yy in range(top,top+height):
   for xx in range(left,left+width):
    rgb=raster[yy*800+xx+40];word=(((rgb>>19)&31)<<11)|(((rgb>>10)&63)<<5)|((rgb>>3)&31);hud_actual.extend(word.to_bytes(2,'little'))
 hud_golden=(oracle/f'frame{frame}.hud').read_bytes();assert len(hud_actual)==len(hud_golden)==42240
 hud_bad=sum(hud_actual[i:i+2]!=hud_golden[i:i+2]for i in range(0,42240,2))
 rows.append({'displayed_HUD_words':21120,'displayed_HUD_mismatched_words':hud_bad,'frame':frame,'front_bank':banks[frame],'canonical_mismatched_bytes':canonical_bad,'canonical_actual_sha256':sha(actual),'canonical_expected_sha256':sha(gold),'composed_pixels':345600,'composed_mismatched_pixels':bad,'black_border_mismatches':border,'first_mismatched_yx':first})
result={'status':'PASS_COMPLETED_PREFIX_ONLY_CANONICAL_HUD_RASTER'if all(not x['canonical_mismatched_bytes']and not x['composed_mismatched_pixels']and not x['black_border_mismatches']and not x['displayed_HUD_mismatched_words']for x in rows)else'FAIL_CANONICAL_OR_RASTER','frames':rows,'scope':'actual selected decoder/memory/SDRAM model/native HUD and composed scanout; direct CSR RPC plus separate pin-level proof, no physical throughput claim'}
(p/'prefix-comparison.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2));assert result['status'].startswith('PASS_')
