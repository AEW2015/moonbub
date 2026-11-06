#!/usr/bin/env python3
"""Reproduce the declared exact-part hardware flow; unavailable part is not synthesis."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'fpga/experiments/cu66-v75/build'
CONTAINER='gamebub-cu66-v69-vivado';VIVADO='/opt/Xilinx/2025.2/Vivado/bin/vivado'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 specfile=ROOT/'fpga/experiments/cu66-v75/system/sources.json';spec=json.loads(specfile.read_text());hardware=[p for p in spec['rtl_sources']if not p.endswith(('_sim.sv','_model.sv'))];assert len(hardware)==20
 pins={p:sha(ROOT/p)for p in hardware};headers=[ROOT/'fpga/experiments/cu66-v70/memory/cu70_memory_map.svh',ROOT/'fpga/experiments/cu66-v69/packet/cu66_profile.svh',ROOT/'fpga/experiments/cu66-v69/inverse/cu66_quant_rom.svh']
 def run(argv,name,timeout):
  with(OUT/name).open('w')as f:p=subprocess.run(argv,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,timeout=timeout)
  return p.returncode
 assert run(['docker','exec',CONTAINER,VIVADO,'-version'],'vivado-version.log',120)==0
 assert run(['docker','exec',CONTAINER,'sha256sum',VIVADO],'vivado-executable-sha256.log',30)==0
 argv=['docker','exec','-w',str(OUT),CONTAINER,VIVADO,'-mode','batch','-log','vivado-ooc.log','-journal','vivado-ooc.jou','-source','ooc_system.tcl']
 code=run(argv,'vivado-stdout.log',1800);text=(OUT/'vivado-stdout.log').read_text();unavailable=code==2 and 'UNAVAILABLE_EXACT_PART'in text
 assert unavailable,'Unexpected tool outcome; retain logs and inspect before a status claim'
 assert pins=={p:sha(ROOT/p)for p in hardware},'hardware sources changed'
 logs=[p for p in OUT.iterdir()if p.suffix in('.log','.jou')]
 d=dict(schema='cu75-exact-target-ooc-preflight-v1',status='UNAVAILABLE_EXACT_PART',reason='Declared exact part not installed; stopped before RTL synthesis/implementation',target_part='xc7a100tcsg324-1',container=CONTAINER,command=argv,exit_code=code,working_directory=str(OUT),top='cu75_system',parameters=dict(USE_STRIP=1,P0_CACHE_LINES=8),panel_clock_period_ns=34.058,tool=dict(executable=VIVADO,version=(OUT/'vivado-version.log').read_text(),executable_sha256=(OUT/'vivado-executable-sha256.log').read_text().split()[0]),source_spec=str(specfile.relative_to(ROOT)),source_spec_sha256=sha(specfile),hardware_sources=hardware,source_sha256=pins,include_header_sha256={str(p.relative_to(ROOT)):sha(p)for p in headers},script_sha256=sha(OUT/'ooc_system.tcl'),producer_script_sha256=sha(Path(__file__).resolve()),logs_sha256={p.name:sha(p)for p in logs},synthesis_started=False,implementation_started=False,scope='Exact-part availability check only; no target fit/route/Fmax/CDC or physical30fps/sub10ms result')
 (OUT/'status.json').write_text(json.dumps(d,indent=2)+'\n');print('V75_OOC_UNAVAILABLE_EXACT_PART sources=20 synthesis_started=false')
if __name__=='__main__':main()
