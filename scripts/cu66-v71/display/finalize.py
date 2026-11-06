"""Summarize source-bound display simulation gates without hardware promotion."""
from pathlib import Path
import argparse,hashlib,json
r=Path(__file__).resolve().parents[3];d=r/'fpga/experiments/cu66-v71/display'
a=argparse.ArgumentParser();a.add_argument('--output',required=True);args=a.parse_args()
o=(r/args.output).resolve();o.mkdir(parents=True,exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
selected=['prefetch-metrics02','memory-lookahead-fast01','memory-lookahead-slow01','memory-full-raster-fast01','memory-full-raster-slow01']
artifacts=[];checks=[]
for name in selected:
 e=d/'evidence'/name;result=json.loads((e/'result.json').read_text())
 if name=='prefetch-metrics02':assert result['status']=='PASS_ASYNCHRONOUS_BL8_SCANOUT_COMPONENT'
 else:
  assert result['status']=='PASS_SELECTED_LINE_INTEGRATION' and result['normal_load_underrun_gate']
  for n in ['cu71_scanout_prefetch.sv','cu71_lcd_lines.sv']:
   assert sha(d/n)==result['sources'][n],('Selected source changed',n,name)
  for n in ['cu71_memory_system.sv','cu71_word_bridge.sv','cu71_tile_memory.sv','moonshine_sdram_burst.sv']:
   assert sha(r/'fpga/experiments/cu66-v71/memory'/n)==result['sources'][n],('Memory source changed',n,name)
  if 'full-raster' in name:assert result['complete_rasters']==1 and result['last_line']==799
 for n in ['result.json','execution.json']:
  f=e/n;artifacts.append(dict(path=str(f.relative_to(r)).replace('\\','/'),role='simulation_evidence',sha256=sha(f)))
 checks.append(dict(id=name,status='PASS',scope=result.get('limits',result.get('scope','Component simulation only'))))
for name in ['cu71_scanout.sv','cu71_scanout_prefetch.sv','cu71_lcd_lines.sv','tb_scanout.cpp','tb_scanout_prefetch_metrics.cpp','tb_scanout_memory.sv','provenance.json','README.md']:
 f=d/name;artifacts.append(dict(path=str(f.relative_to(r)).replace('\\','/'),role='source_or_document',sha256=sha(f)))
checks.extend([dict(id='physical',status='NOT_RUN'),dict(id='routed_timing_and_fit',status='NOT_RUN'),dict(id='CU66_decode_to_display_system',status='NOT_RUN'),dict(id='30_unique_presentations_per_second',status='NOT_PROVEN')])
(o/'manifest.json').write_text(json.dumps(dict(overall='PASS_SCOPED_SIMULATION_ONLY_NOT_HARDWARE_READY',artifacts=artifacts,checks=checks,
 limits='Full-raster fixture memory is testbench initialized; actual reads/controller/refresh and concurrent background writes are exercised. No network/decoder/physical proof. Failed original cadence and accounting attempts preserved.'),indent=2)+'\n')
print('CU71_DISPLAY_SCOPED_MANIFEST_COMPLETE',o)
