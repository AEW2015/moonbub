"""Validate exactly four complete STBF1 payload records; no hardware/network access."""
import argparse,json,re,struct,zlib
from pathlib import Path
class Invalid(ValueError):pass
def need(ok,message):
 if not ok:raise Invalid(message)
def number(value,bits,hex_width=None):
 if hex_width is None:need(re.fullmatch(r'0|[1-9][0-9]*',value) is not None,'decimal grammar');n=int(value)
 else:need(re.fullmatch('[0-9a-f]{'+str(hex_width)+'}',value) is not None,'hex grammar');n=int(value,16)
 need(n<1<<bits,'integer range');return n
def parse(payload):
 need(type(payload)is str and payload.isascii() and '\n'not in payload and '\r'not in payload and len(payload)<=192,'whole bounded ASCII payload required')
 tokens=payload.split(' ');need(len(tokens)>=3 and tokens[0]=='STBF1','record prefix');kind=tokens[1]
 if kind=='H':keys=['k','e','a','v','r','x','y','j','q','c'];words=0
 elif kind=='C':keys=['k','a','o','f','g','p','u','n','i','s','t','c'];words=0
 elif kind in('A','B'):keys=['k','c'];words=7 if kind=='A'else 6
 else:raise Invalid('record kind')
 need(len(tokens)==2+len(keys)+words,'exact record field count');result={}
 for token,key in zip(tokens[2:2+len(keys)],keys,strict=True):
  pair=token.split('=');need(len(pair)==2 and pair[0]==key,'field order/name');value=pair[1]
  if key=='c':n=number(value,32,8)
  elif kind=='H'and key in('a','v'):n=number(value,16,4)
  elif kind=='H'and key=='r':n=number(value,8,2)
  elif key in('k','e','g','u','s','t'):n=number(value,64)
  elif kind=='C'and key in('a','i'):n=number(value,1)
  elif key in('x','y','p'):n=number(value,8)
  else:n=number(value,32)
  result[key]=n
 result['words']=[number(v,32,8)for v in tokens[2+len(keys):]]
 return kind,result
def decode(payloads):
 need(len(payloads)==4,'exactly four records required');records={}
 for payload in payloads:
  kind,row=parse(payload);need(kind not in records,'duplicate record');records[kind]=row
 need(set(records)==set('HCAB'),'complete record kinds required')
 h,c,a,b=(records[k]for k in'HCAB');key=h['k'];crc=h['c']
 need(all(r['k']==key and r['c']==crc for r in records.values()),'mixed sample/CRC')
 attempted,valid,flags=h['a'],h['v'],h['r'];all_mask=8191
 need(attempted<=all_mask and valid&~attempted==0 and attempted&(attempted+1)==0,'attempted/valid mask')
 need(flags&~15==0 and bool(flags&1)==(attempted==all_mask) and bool(flags&2)==(valid==all_mask),'result flags')
 need(bool(flags&4)==(attempted!=all_mask),'pre-call budget stop flags')
 missing=attempted&~valid
 if missing:
  first=(missing&-missing).bit_length()-1;need(h['x']==first and h['y']in(1,2,3,4),'first read failure')
 else:need(h['x']==255 and h['y']==0,'unexpected read error')
 need(not(flags&8)or missing!=0,'epoch flag without failed read')
 need(h['y']!=2 or flags&8!=0,'missing epoch flag')
 need(h['e']>=key,'sample monotonic ordering')
 if not c['i']:need((c['s'],c['t'],h['j'],h['q'])==(0,0,0,0),'unbound identity values')
 else:need(c['s']!=0,'bound session must be nonzero')
 values=a['words']+b['words'];need(len(values)==13,'13 CSR words')
 for i,v in enumerate(values):need(bool(valid&(1<<i))or v==0,'invalid sample must be zero masked')
 data=struct.pack('<QQHHBBB',key,h['e'],attempted,valid,flags,h['x'],h['y'])
 data+=struct.pack('<BIIQBQIBQQII',c['a'],c['o'],c['f'],c['g'],c['p'],c['u'],c['n'],c['i'],c['s'],c['t'],h['j'],h['q'])
 data+=struct.pack('<13I',*values);need(zlib.crc32(data)==crc,'whole snapshot/context CRC')
 return dict(schema='stbf1-failure-snapshot-v1',sample_start_us=key,sample_end_us=h['e'],attempted_mask=attempted,valid_mask=valid,result_flags=flags,first_error_index=h['x'],first_error_code=h['y'],context=dict(active=bool(c['a']),ordinal=c['o'],frame=c['f'],generation=c['g'],phase=c['p'],progress_at_us=c['u'],stored_prefix=c['n'],identity_valid=bool(c['i']),session=c['s'],capture_us=c['t'],identity_frame=h['j'],identity_reference=h['q']),CSR_values={f'{0x700+i*4:03x}':v for i,v in enumerate(values)},crc32=f'{crc:08x}',atomic=False,best_effort_delivery=True,paced_reexport=False)
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('records',type=Path);a=p.parse_args()
 # CLI consumes four payload lines, deliberately not an unbounded serial log.
 print(json.dumps(decode(a.records.read_text().splitlines()),indent=2))
