"""Preserve every original SHA fixture, add independent hashlib boundaries/randoms."""
from pathlib import Path
import hashlib,json,random,zlib
r=Path(__file__).resolve().parents[3];old=r/'fpga/experiments/cu66-v69/hash';out=r/'fpga/experiments/cu66-v71/hash';(out/'fixtures').mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rows=[];pins={str(old/'fixtures.tsv'):sha(old/'fixtures.tsv'),str(old/'fixture-evidence.json'):sha(old/'fixture-evidence.json')}
for line in(old/'fixtures.tsv').read_text().splitlines():
    name,path,size,digest=line.split('\t');source=old/path;raw=zlib.decompress(source.read_bytes());assert len(raw)==int(size)and hashlib.sha256(raw).hexdigest()==digest
    target=out/path;target.write_bytes(source.read_bytes());rows.append(line);pins[str(source)]=sha(source)
rng=random.Random(710070)
lengths=list(range(131))+[255,256,257,447,448,449,511,512,513,1023,1024,1025,4095,4096,4097]
lengths+=[rng.randrange(65537)for _ in range(64)]
new=[]
for index,n in enumerate(lengths):
    raw=rng.randbytes(n);packed=zlib.compress(raw,9);digest=hashlib.sha256(raw).hexdigest();path='fixtures/'+hashlib.sha256(packed).hexdigest()+'.zlib';(out/path).write_bytes(packed)
    line=f'sha71_hashlib_{index}_{n}\t{path}\t{n}\t{digest}';rows.append(line);new.append(dict(name=line.split('\t')[0],length=n,sha256=digest))
(out/'fixtures.tsv').write_text('\n'.join(rows)+'\n',newline='\n')
(out/'fixtures.json').write_text(json.dumps(dict(original_cases=98,new_cases=len(new),total_cases=len(rows),seed=710070,source_sha256=pins,new_hashlib_cases=new,fixture_sha256=sha(out/'fixtures.tsv'),assets={name:sha(out/name)for name in sorted({line.split('\t')[1]for line in rows})},scope='Original98NIST/padding/random/canonical fixtures fully rechecked against hashlib, plus deterministic independent random bytes/boundaries. No new capture or hardware.'),indent=2)+'\n')
print('SHA71_FIXTURES',len(rows),'original',98,'new',len(new))
