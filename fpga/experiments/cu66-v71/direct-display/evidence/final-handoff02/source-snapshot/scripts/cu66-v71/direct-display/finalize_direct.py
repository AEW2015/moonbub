"""Publish source-bound direct-display component handoff without promoting hardware."""
from pathlib import Path
import argparse,hashlib,json,re,shutil
r=Path(__file__).resolve().parents[3];d=r/'fpga/experiments/cu66-v71/direct-display';a=argparse.ArgumentParser();a.add_argument('--output',required=True);args=a.parse_args();o=(r/args.output).resolve();o.mkdir(parents=True,exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
proofs=['pixel-pipe02','cache-pixel01','cache-dma01','direct-owner05','direct-owner-pipe02','direct-pin-fast03','direct-pin-slow01','direct-pipe-pin-fast01','direct-pipe-pin-slow01','direct-burst-contention-fast01','direct-burst-banktradeoff-fast01','direct-ooc01','direct-pipe-ooc01']
results={};artifacts={}
for name in proofs:
 p=d/'evidence'/name;result=json.loads((p/'result.json').read_text());assert result['status'].startswith('PASS'),(name,result['status']);results[name]=result['status']
 for f in p.iterdir():
  if f.is_file()and f.suffix in ['.json','.log','.rpt','.tcl','.sh','.dcp']:artifacts[str(f.relative_to(r)).replace('\\','/')]=sha(f)
 for source,h in result.get('sources',{}).items():
  basename=Path(source).name
  if basename.startswith('cu71_')and(d/basename).exists():assert sha(d/basename)==h,(name,basename)
rtl=[d/n for n in ['cu71_direct_scanout.sv','cu71_direct_scanout_pipe.sv','cu71_cache_dma.sv','cu71_direct_cache.sv','cu71_yuv_pixel_pipe.sv','cu71_lcd_lines_direct.sv']]
contracts=[d/'frozen-port-contract-v001.json',d/'frozen-port-contract-pipe-v002.json'];sources={str(p.relative_to(r)).replace('\\','/'):sha(p)for p in rtl+contracts+[d/'README.md',Path(__file__)]}
for p in rtl+contracts+[d/'README.md',Path(__file__)]:
 f=o/'source-snapshot'/p.relative_to(r);f.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,f)
timing=(d/'evidence/direct-pipe-ooc01/synthesized-timing.rpt').read_text();intra=timing.split('| Intra Clock Table')[1].split('| Inter Clock Table')[0];mem=re.search(r'^mem_clk\s+(-?\d+\.\d+)',intra,re.M);pixel=re.search(r'^pixel_clk\s+(-?\d+\.\d+)',intra,re.M);assert mem and float(mem[1])>0 and pixel and float(pixel[1])>0
manifest=dict(status='PASS_ISOLATED_DIRECT_DISPLAY_COMPONENT_GATES_NOT_BOARD_RELEASE',sources=sources,evidence_status=results,evidence_artifacts=artifacts,selected_candidate_module='cu71_direct_scanout_pipe',counts=json.loads((d/'evidence/direct-pipe-ooc01/primitive-counts.json').read_text()),synthesis_intra_setup_slack_ns={'mem_clk':float(mem[1]),'pixel_clk':float(pixel[1])},overall_timing_pass=False,hardware_programmed=False,hardware_playback=False,thirty_fps_qualified=False,remaining=['Full decoder/root owner COMMIT and lease integration','Concurrent read-modify-write/copy/decode cadence','Explicit direct-profile CSR/firmware/network contract','Routed CDC/bundled payload constraints and complete board timing','32-bit internal cookie exhaustion: separate64bit successor or qualified coordinated reset before long-duration release'])
(o/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');shutil.copyfile(Path(__file__),o/'executed-finalizer.py');print(manifest['status'],o)
