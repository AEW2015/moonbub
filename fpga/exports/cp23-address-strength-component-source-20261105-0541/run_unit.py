import pathlib,os,subprocess,hashlib,json,time,sys,shutil
P=pathlib.Path(__file__).resolve().parent
E=P/'evidence'/sys.argv[1];E.mkdir(parents=True,exist_ok=False)
files=['tb_gather_unit.sv','parents/ar03_yuv_line_gather.sv','parents/ar03_rgb565_kernel.sv','native_base.cpp','selected-samples.bin','fixture-column.hex',*[str(f.relative_to(P)) for f in (P/'oracle-native').rglob('*') if f.is_file()]]
manifest={}
for f in files:
 q=E/'inputs'/f;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes((P/f).read_bytes());manifest[f]=hashlib.sha256(q.read_bytes()).hexdigest()
(E/'manifest.json').write_text(json.dumps(manifest,indent=2))
(E/'fixture-column.hex').write_bytes((P/'fixture-column.hex').read_bytes())
env=dict(os.environ)
def tool(name):
 value=os.environ.get(name.upper().replace('+','P')) or shutil.which(name) or shutil.which(name+'.exe')
 fallback=pathlib.Path('C:/msys64/ucrt64/bin')/(name+'.exe')
 if not value and fallback.exists():value=str(fallback)
 if not value:raise SystemExit('Missing '+name+' on PATH')
 env['PATH']=str(pathlib.Path(value).resolve().parent)+os.pathsep+env.get('PATH','')
 return value
def run(n,cmd):
 with (E/(n+'.log')).open('w') as log:r=subprocess.run(cmd,cwd=E,env=env,stdout=log,stderr=subprocess.STDOUT)
 print(n,r.returncode,flush=True)
 if r.returncode:raise SystemExit(r.returncode)
run('native-compile',[tool('g++'),'-std=c++20','-O2',str(E/'inputs/native_base.cpp'),'-o',str(E/'native.exe')])
run('native',[str(E/'native.exe'),str(E/'inputs/selected-samples.bin')])
(E/'native-reset-samples.bin').write_bytes(bytes(v^255 for v in (E/'inputs/selected-samples.bin').read_bytes()))
(E/'native-first.hex').write_bytes((E/'native-base-rgb.hex').read_bytes())
run('native-reset',[str(E/'native.exe'),str(E/'native-reset-samples.bin')])
(E/'native-reset-rgb.hex').write_bytes((E/'native-base-rgb.hex').read_bytes())
(E/'native-base-rgb.hex').write_bytes((E/'native-first.hex').read_bytes())
run('compile',[tool('iverilog'),'-g2012','-Wall','-s','tb','-o',str(E/'unit.vvp'),*[str(E/'inputs'/f)for f in files[:3]]])
run('simulation',[tool('vvp'),'-i',str(E/'unit.vvp')])
assert 'GATHER_BRAM_NATIVE_UNIT_PASS' in (E/'simulation.log').read_text()

