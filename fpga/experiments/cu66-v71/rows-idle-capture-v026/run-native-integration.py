"""Re-run actual decoder/raster with the new selected row source; scalar CSR platform."""
from pathlib import Path
import argparse,hashlib,json,os,re,shutil,subprocess,time
a=argparse.ArgumentParser();a.add_argument('--corner',choices=['fast','slow'],required=True);v=a.parse_args();p=Path(__file__).resolve().parent;root=Path('C:/mb70');parent=root/'fpga/experiments/cu66-v71/result-admission-system-v023'/('integration-'+v.corner+'01');out=p/('integration-'+v.corner+'01');out.mkdir();b=root/'dy71-v026-20261107-v001';sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
assert json.loads((p/'proof02/result.json').read_text())['source_sha256']['cu71_tile_rows.sv']==sha(p/'cu71_tile_rows.sv')
shutil.copytree(parent/'inputs',out/'inputs')
row='fpga/experiments/cu66-v71/rows-idle-capture-v026/cu71_tile_rows.sv';d=out/'inputs'/row;d.parent.mkdir(parents=True);shutil.copyfile(b/'inputs'/row,d);assert sha(d)==sha(p/'cu71_tile_rows.sv')
for name in ['driver.cpp','observer.sv','harness.rs','hud.dll','sdk-core.exe']:shutil.copyfile(parent/name,out/name)
oldlin=parent.as_posix().replace('C:/','/mnt/c/');newlin=out.as_posix().replace('C:/','/mnt/c/');(out/'driver.cpp').write_text((out/'driver.cpp').read_text().replace(oldlin,newlin))
cmd=[x.replace(oldlin,newlin)for x in json.loads((parent/'execution.json').read_text())[0]['command']];oldrow='fpga/experiments/cu66-v71/rows/cu71_tile_rows.sv';assert cmd[-1].count(oldrow)==1;cmd[-1]=cmd[-1].replace(oldrow,row);cmd[-1]=re.sub(r'-j [12](?= |$)','-j 1',cmd[-1]);rows=[]
def run(label,cmd):
 start=time.monotonic()
 with(out/(label+'.log')).open('x')as f:q=subprocess.run(cmd,cwd=out,env=dict(os.environ,PATH='C:/msys64/ucrt64/bin;'+os.environ['PATH']),stdout=f,stderr=subprocess.STDOUT)
 rows.append(dict(label=label,cmd=cmd,returncode=q.returncode,seconds=time.monotonic()-start));(out/'execution.json').write_text(json.dumps(rows,indent=2)+'\n');print(v.corner,label,q.returncode,flush=True);assert q.returncode==0,label
run('verilated-build',cmd)
files=[f for f in(out/'inputs').rglob('*')if f.is_file()]+[out/n for n in ['driver.cpp','observer.sv','harness.rs','hud.dll','sdk-core.exe']]
(out/'source-binding.json').write_text(json.dumps(dict(system_core='cu71_system_final_v023',row_source=row,row_sha256=sha(d),compile_command=cmd,files_sha256={str(f):sha(f)for f in files},scope='New selected row source in actual decoder/native raster. Existing scalar ABI1 CSR simulation platform; new bulk/ABI2/physical pin path is separately verified.'),indent=2)+'\n')
run('native-integration',[str(out/'sdk-core.exe'),newlin+'/build/Vdy71_platform_sim',str(out/'rtl-stderr.log'),'8'])
(out/'compare-executed.py').write_text((parent/'compare-executed.py').read_text().replace(parent.as_posix(),out.as_posix()))
run('native-raster-comparison',['python',str(out/'compare-executed.py')]);assert json.loads((out/'comparison.json').read_text())['status']=='PASS_EXACT_NATIVE_RASTER'
print('V026_NEW_ROWS_'+v.corner.upper()+'_NATIVE_RASTER_PASS_NO_HARDWARE',flush=True)
