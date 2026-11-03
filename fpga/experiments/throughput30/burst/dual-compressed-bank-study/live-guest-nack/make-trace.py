import hashlib,struct,sys
from pathlib import Path
root=next(p for p in Path(__file__).resolve().parents if (p/'host/moonshine/protocol.py').is_file());sys.path.insert(0,str(root/'host'))
from moonshine.protocol import packets
fixture=Path(sys.argv[1]);output=Path(sys.argv[2]);old=Path(sys.argv[3]).read_bytes()
expected=['8cc99ea7d50d1d20255e41ff7247b0770b3349e705c27152a41817418ce5c9de','c7db8fa330fca9bf715ad2e915dd84051b43de0e70009a8b93f181046a805fb0','a76055f8d43e1b0affe2810697f0f2f795302751ab2e592c43eb83cd19cfa13e','f3037dd5c0f873dab3584d8517322f19ce1ae74f18ba9fb36f766696d50c0b47']
blob=b''
for i in range(4):
 data=(fixture/f'{i:04}.jpg').read_bytes();assert hashlib.sha256(data).hexdigest()==expected[i]
 for p in packets(data,i,(i*10_000_000//3)//100):blob+=struct.pack('>H',len(p))+p
assert blob.startswith(old) and hashlib.sha256(old).hexdigest()=='bef1ac9f645d0378849d4e3b0d6b4d7c935e309338a41c6a067891596405d372'
with output.open('xb') as f:f.write(blob)
print('TRACE_SHA256',hashlib.sha256(blob).hexdigest())
