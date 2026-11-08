from pathlib import Path
import os,subprocess,json,hashlib,random
p=Path(__file__).resolve().parents[1];out=p/'evidence/pins08';out.mkdir(exist_ok=True)
env=dict(os.environ,PATH=str(Path('C:/msys64/ucrt64/bin'))+';'+os.environ['PATH'],TEMP=str(Path('C:/moon/tmp')),TMP=str(Path('C:/moon/tmp')))
sources=[p/'reference'/n for n in ['cu71_balanced_identity_v019.sv','cu71_packet_staging_safe.sv','cu71_packet_arbiter_cut_v001.sv','moonshine_qspi_endpoint.sv','dy71_hud_bulk_v025.sv','cu71_bus_cdc_bulk_v025.sv']]+[p/'rtl/cu71_staging_burst_v1.sv',p/'rtl/dy71_local_control_staging_burst_v1.sv',p/'tests/tb_staging_burst_pins_v1.sv']
(out/'source-freeze.json').write_text(json.dumps({str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in sources},indent=2));rows=[]
env.pop('NoDefaultCurrentDirectoryInExePath',None)
rng=random.Random(20261108)
cases=[(0.0,31.25,5.0,0),(2.3,125.0,50.0,0),(1.1,62.5,17.0,0),(0.7,31.25,5.0,1)]+[(round(rng.uniform(0,9),3),rng.choice([31.25,62.5,125.0]),5.0,0)for _ in range(4)]
cases=[tuple(c)+(1031,)for c in cases]+[(2.781,31.25,5.0,0,49152)]
for i,(phase,half,core,overflow,payload_bytes) in enumerate(cases):
 binary=out/f'case{i}.vvp';cmd=['C:/msys64/ucrt64/bin/iverilog.exe','-g2012','-I'+(p/'reference').as_posix(),'-y','C:/Xilinx/2025.2/Vivado/data/verilog/src/unisims','-s','tb_staging_burst_pins_v1','-s','glbl',f'-Ptb_staging_burst_pins_v1.PHASE={phase}',f'-Ptb_staging_burst_pins_v1.HALF={half}',f'-Ptb_staging_burst_pins_v1.COREHALF={core}',f'-Ptb_staging_burst_pins_v1.OVERFLOW={overflow}',f'-Ptb_staging_burst_pins_v1.PAYLOAD_BYTES={payload_bytes}','-o',binary.as_posix()]+[f.as_posix()for f in sources]+['C:/Xilinx/2025.2/Vivado/data/verilog/src/glbl.v']
 for label,argv in [('compile',cmd),('run',['C:/msys64/ucrt64/bin/vvp.exe',binary.as_posix()])]:
  r=subprocess.run(argv,env=env,capture_output=True,text=True,timeout=300);(out/f'case{i}-{label}.log').write_text(r.stdout+r.stderr);rows.append({'case':i,'phase':phase,'half':half,'corehalf':core,'overflow':overflow,'payload_bytes':payload_bytes,'label':label,'argv':argv,'returncode':r.returncode});(out/'execution.json').write_text(json.dumps(rows,indent=2));print(i,label,r.returncode,flush=True)
  if r.returncode: print(r.stdout+r.stderr);raise SystemExit(1)
 assert 'STAGING_BURST_PINS_PASS' in (out/f'case{i}-run.log').read_text()
(out/'result.json').write_text(json.dumps({'status':'PASS_PINLEVEL_ENDPOINT_CDC_NATIVE_STAGING','cases':len(cases),'scope':'actual selected endpoint/CDC/staging+prototype control/FIFO; synthetic idle owner; no whole decoder/SDRAM/timing/hardware qualification'},indent=2))
