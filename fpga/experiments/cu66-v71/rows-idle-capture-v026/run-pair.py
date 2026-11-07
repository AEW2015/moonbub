from pathlib import Path
import hashlib,json,os,subprocess,time
p=Path(__file__).resolve().parent;e=p/'pair01';e.mkdir();rows=[];env=dict(os.environ,PATH='C:/msys64/ucrt64/bin;'+os.environ['PATH'])
sources=[p/n for n in ['cu71_tile_rows_reference.sv','cu71_tile_rows.sv','tb_rows_pair.sv']]
(e/'source-freeze.json').write_text(json.dumps({f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in sources},indent=2))
for banks in [1,2]:
 label='banks'+str(banks)
 commands=[('compile',['C:/msys64/ucrt64/bin/iverilog.exe','-g2012','-s','tb_rows_pair','-Ptb_rows_pair.BANKS='+str(banks),'-o',str(e/(label+'.vvp'))]+[str(f) for f in sources]),('run',['C:/msys64/ucrt64/bin/vvp.exe',str(e/(label+'.vvp'))])]
 for phase,cmd in commands:
  start=time.monotonic();q=subprocess.run(cmd,env=env,capture_output=True,text=True,timeout=300);(e/(label+'-'+phase+'.log')).write_text(q.stdout+q.stderr);rows.append(dict(banks=banks,phase=phase,cmd=cmd,returncode=q.returncode,seconds=time.monotonic()-start));(e/'execution.json').write_text(json.dumps(rows,indent=2));print(label,phase,q.returncode,flush=True)
  if q.returncode:print(q.stdout+q.stderr);raise SystemExit(1)
 assert 'ROW_IDLE_CAPTURE_PAIR_PASS'in(e/(label+'-run.log')).read_text()
(e/'result.json').write_text(json.dumps(dict(status='PASS_OBSERVED_OLD_NEW_ROWS_AND_AUTHORITATIVE_PAYLOAD',scope='RTL paired simulation; two full key/non-key frames per bank configuration, qualified bytes/control/counters/abort/reset/invalid cases; no formal/whole-codec/timing/hardware claim',source_freeze_sha256=hashlib.sha256((e/'source-freeze.json').read_bytes()).hexdigest()),indent=2)+'\n')
