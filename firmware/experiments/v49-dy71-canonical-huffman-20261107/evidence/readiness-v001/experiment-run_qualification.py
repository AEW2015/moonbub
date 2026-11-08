from pathlib import Path
import os,subprocess,json,time,hashlib
root=Path(__file__).resolve().parent
source=Path('C:/moon/publish/firmware/experiments/v48-dy71-selftest-control-20261107')
env=dict(os.environ,PATH='C:/msys64/ucrt64/bin;'+os.environ['PATH'],TEMP='C:/moon/tmp',TMP='C:/moon/tmp')
steps=[]
def run(label,command,cwd=root):
 t=time.perf_counter()
 with(root/(label+'.log')).open('w')as out:r=subprocess.run(command,cwd=cwd,env=env,stdout=out,stderr=subprocess.STDOUT)
 steps.append({'label':label,'command':command,'cwd':str(cwd),'seconds':time.perf_counter()-t,'exit':r.returncode});(root/'execution.json').write_text(json.dumps(steps,indent=2)+'\n');print(label,r.returncode,flush=True)
 if r.returncode:print((root/(label+'.log')).read_text());raise SystemExit(r.returncode)
for variant in ('control','candidate'):
 out=root/variant
 for name in ('prepare12','corpus','rollback','huffman'):
  run(variant+'-'+name+'-compile',['C:/msys64/ucrt64/bin/g++.exe','-std=c++17','-Os','-Wall','-Wextra','-Werror','-fstack-usage','-I',str(out),str(root/'harness'/f'{name}.cpp'),'-o',str(out/(name+'.exe'))])
 run(variant+'-prepare12',[str(out/'prepare12.exe'),'150000','C:/moon/maintenance/v45-sequence/qualification'],source)
 run(variant+'-corpus',[str(out/'corpus.exe'),'C:/moon/maintenance/v44-localhost/native-corpus.tsv'])
 run(variant+'-rollback',[str(out/'rollback.exe'),str(source/'handheld/src/cu66/fixtures/prepare12')])
 run(variant+'-huffman',[str(out/'huffman.exe'),str(root/'cases.tsv')])
a=[line.split('\t')[:2]for line in(root/'control-huffman.log').read_text().splitlines()]
b=[line.split('\t')[:2]for line in(root/'candidate-huffman.log').read_text().splitlines()]
assert a==b,'Huffman semantic differential mismatch'
(root/'qualification.json').write_text(json.dumps({'status':'PASS','cases':len(a),'golden_corpus_frames':457,'golden_corpus_words':457*21120,'prepare_frames':12,'prepare_words':12*21120,'rollback':'PASS','differential':'identical outputs and error messages','hardware':'NOT_RUN','target':'NOT_BUILT'},indent=2)+'\n')
print('V49_HOST_QUALIFICATION_PASS')
