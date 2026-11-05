#!/usr/bin/env python3
"""Logical traffic accounting, not a simulated/physical throughput result."""
import hashlib
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[2]
AREA=ROOT/'fpga/experiments/cu66-v70/system'
def main():
 result_path=AREA/'full-direct/results.json';result=json.loads(result_path.read_text())
 lcd=ROOT/'fpga/experiments/cu66-v70/display/cu70_lcd_lines.sv';source=lcd.read_text()
 h=int(re.search(r'H_TOTAL\s*=\s*(\d+)',source)[1]);v=int(re.search(r'V_TOTAL\s*=\s*(\d+)',source)[1])
 refresh=1e12/(2*result['clocks']['pixel_half_period_ps']*h*v)
 frame={'canonical_write':518400,'visible_P_reference_read':(8100-294)*64,
  'HUD_processor_write':42240,'HUD_processor_readback':42240,
  'painter_YUV_read':518400,'painter_HUD_read':42240,'portrait_RGB_write':768000}
 current_game=sum(frame.values())*30;current_scan=768000*refresh
 proposed_game=sum(frame[k]for k in ('canonical_write','visible_P_reference_read','HUD_processor_write','HUD_processor_readback'))*30
 proposed_scan=(518400+42240)*refresh
 raw=2*1e12/result['clocks']['memory_period_ps']
 d={'status':'ACCOUNTING_ONLY_NOT_IMPLEMENTED_PROPOSAL','source_sha256':{
  str(lcd.relative_to(ROOT)):hashlib.sha256(lcd.read_bytes()).hexdigest(),
  str(result_path.relative_to(ROOT)):hashlib.sha256(result_path.read_bytes()).hexdigest(),
  str(Path(__file__).relative_to(ROOT)):hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},
  'coded_game_fps':30,'modeled_native_panel_refresh_hz':refresh,
  'current_per_P_frame_useful_bytes':frame,'current_bytes_per_second':current_game+current_scan,
  'current_fraction_of_raw_x16_bus':(current_game+current_scan)/raw,
  'proposed_direct_YUV_scanout_bytes_per_second':proposed_game+proposed_scan,
  'proposed_fraction_of_raw_x16_bus':(proposed_game+proposed_scan)/raw,
  'proposal':'transposed canonical YUV references with canonical-order hash before storage; bounded line caches and exact DSP color/HUD output at scanout, avoiding full RGB framebuffer conversion/copy',
  'assumptions':['fullusefulplane/HUDreadonceperpanelrefresh','onchipgeneratedblackborders','onefullcandidatewrite+onevisiblezero-motionreference readpergameframe','currentprocessorHUDwrite+readbackkept','pixel/memoryclocksdeclaredmodelonly'],
  'not_included':['BL8overfetch/packing','command/row/turnaroundoverhead','refresh','cachemisses/redundantfetches','compressedstaging/ingress','softwareCPUtime','control/diagnostictraffic'],
  'not_proven':['proposalRTLexists','sustainedbandwidth','FPGAfit/clock','30fps']}
 (AREA/'logical-traffic.json').write_text(json.dumps(d,indent=2)+'\n')
 print(f'ACCOUNTING current={d["current_bytes_per_second"]/1e6:.3f}MB/s proposed={d["proposed_direct_YUV_scanout_bytes_per_second"]/1e6:.3f}MB/s raw_payload_fraction={d["current_fraction_of_raw_x16_bus"]:.3f}/{d["proposed_fraction_of_raw_x16_bus"]:.3f} NOT_A_PERFORMANCE_PROOF')
if __name__=='__main__':main()
