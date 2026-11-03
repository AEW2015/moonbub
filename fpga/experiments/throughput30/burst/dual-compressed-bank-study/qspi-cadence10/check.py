import json,pathlib,re,sys
s=pathlib.Path(sys.argv[1]).read_text();p=pathlib.Path(sys.argv[2]);
def rows(label):return [{k:int(v) for k,v in re.findall(r'(\w+)=(\d+)',line)} for line in s.splitlines() if line.startswith(label+' ')]
a=rows('ARRIVAL');d=rows('DROP_BUSY');ad=rows('ADMITTED');present=rows('PRESENT_PASS');scan=rows('SCAN_PASS')
ai=[x['id'] for x in a];di=[x['id'] for x in d];adi=[x['id'] for x in ad];pi=[x['id'] for x in present]
assert ai==list(range(10)) and len(adi)==len(set(adi)) and not set(adi)&set(di) and set(adi)|set(di)==set(ai)
assert pi==adi and [int(x.stem) for x in sorted(p.glob('*.txt'))]==sorted(adi)
epoch=a[0]['cycle'];assert all(x['cycle']==x['target']==epoch+x['id']*10000000//3 for x in a)
assert all(x['cycle']>=a[x['id']]['cycle'] for x in ad+d)
lat=[]
for x in present:
 id=x['id']; arrival=a[id]['cycle']; commit=next(y['cycle'] for y in ad if y['id']==id)
 assert x['cycle']>=commit>=arrival and x['writes']==345600 and x['bursts']==43200 and x['underruns']==0
 result=json.loads((p.parent/f'comparison{id:04}.json').read_text());assert result['pixels']==result['exact_rgb565_pixels']==345600
 lat.append((id,x['cycle']-arrival))
assert set(adi)<=set(x['id'] for x in scan) and all(x['pixels']==345600 for x in scan)
print('ACCOUNTING_PASS',f'admitted={adi}',f'dropped={di}',f'presented={pi}',f'arrival_to_present_cycles={lat}')
