from pathlib import Path
import hashlib,json,subprocess,os,time,shutil
p=Path(__file__).resolve().parent;out=Path('C:/moon/dev/evidence/stb1-ce-final-cone-20261108-v001');sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
receipt=json.loads((p/'implementation-execution.json').read_text());assert receipt['returncode']==0 and receipt['completion_marker'] and receipt['inputs_unchanged'],'implementation must finish first'
assert not out.exists(),'root-approved unique output already exists'
probe=subprocess.run(['powershell','-NoProfile','-Command',"@(Get-CimInstance Win32_Process -Filter \"Name='vivado.exe'\" | Select-Object ProcessId,CommandLine) | ConvertTo-Json -Compress"],capture_output=True,text=True,check=True)
assert not probe.stdout.strip() or json.loads(probe.stdout)==[],'another Vivado still active'
script=p/'inspect-ce.tcl';dcp=p/'routed.dcp';assert sha(script)=='db9b19a368d00df18a409828ad7f2065bca6a4e0c2aa0af9ae05b9d5d4420aa1','reviewed script changed'
before={'script':str(script),'script_sha256':sha(script),'routed_DCP':str(dcp),'routed_DCP_sha256':sha(dcp),'out':str(out),'scope':'root approved read-only exact CE query after full implementation exit; no BIT/hardware'};(p/'final-cone-query-inputs.json').write_text(json.dumps(before,indent=2))
tmp=Path('C:/moon/tmp/stb1-ce-final-cone-v001');tmp.mkdir(exist_ok=False);env=dict(os.environ,TEMP=str(tmp),TMP=str(tmp));env.pop('NoDefaultCurrentDirectoryInExePath',None)
cmd=['C:/Xilinx/2025.2/Vivado/bin/vivado.bat','-mode','batch','-source',str(script),'-log',str(p/'final-cone-query-vivado.log'),'-journal',str(p/'final-cone-query-vivado.jou'),'-tclargs',str(out)]
start=time.monotonic()
with(p/'final-cone-query-console.log').open('x')as f:r=subprocess.run(cmd,cwd=p,env=env,stdout=f,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
text=(p/'final-cone-query-vivado.log').read_text(errors='replace');result={'command':cmd,'returncode':r.returncode,'seconds':time.monotonic()-start,'completion_marker':any(line.strip()=='READONLY_POSTROUTE_CE_CONE_COMPLETE'for line in text.splitlines()),'script_unchanged':sha(script)==before['script_sha256'],'routed_DCP_unchanged':sha(dcp)==before['routed_DCP_sha256'],'errors':[line for line in text.splitlines()if line.startswith('ERROR:')],'hardware':False,'BIT':False};(p/'final-cone-query-execution.json').write_text(json.dumps(result,indent=2))
if out.is_dir():
 for f in [p/'final-cone-query-inputs.json',p/'final-cone-query-execution.json',p/'final-cone-query-vivado.log',p/'final-cone-query-vivado.jou',p/'final-cone-query-console.log']:shutil.copy2(f,out/f.name)
print(json.dumps(result));assert r.returncode==0 and result['completion_marker'] and result['script_unchanged']and result['routed_DCP_unchanged']and not result['errors']
