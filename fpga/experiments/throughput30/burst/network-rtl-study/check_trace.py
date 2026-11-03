#!/usr/bin/env python3
"""Check external-drop accounting, presentation timing, and C-model pixel output."""
import argparse,hashlib,json,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[5]
COMPARE=ROOT/'fpga/experiments/throughput30/burst/compare-frame.py'

def rows(text,prefix):
 return [{k:int(v) for k,v in re.findall(r'(\w+)=(\d+)',line)} for line in text.splitlines() if line.startswith(prefix)]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in ('manifest','log','fixtures','dumps','cmodel','output'):p.add_argument('--'+name,type=Path,required=True)
 a=p.parse_args();m=json.loads(a.manifest.read_text());text=a.log.read_text()
 if 'TEST_PASS_NETWORK_QSPI_TRACE' not in text:raise ValueError('simulation PASS missing')
 presented=rows(text,'FRAME_RESULT ');dropped=rows(text,'FRAME_DROPPED ');totals=rows(text,'NETWORK_TRACE_RESULT ')
 if len(totals)!=1:raise ValueError('missing unique aggregate')
 totals=totals[0];trace={r['id']:r for r in m['complete']}
 ids=[r['id'] for r in presented];dropids=[r['id'] for r in dropped]
 if len(ids)!=len(set(ids)) or len(dropids)!=len(set(dropids)) or set(ids)&set(dropids):raise ValueError('duplicate or overlapping IDs')
 if set(ids)|set(dropids)!=set(trace):raise ValueError('trace ID accounting mismatch')
 if totals['presented']!=len(ids) or totals['external_queue_drops']!=len(dropids) or totals['trace_frames']!=len(trace):raise ValueError('aggregate mismatch')
 if ids!=sorted(ids):raise ValueError('presented IDs not ordered')
 if set(ids)&set(m['not_reassembled_ids']):raise ValueError('unreassembled frame presented')
 epoch=None;comparisons=[]
 for r in presented:
  tr=trace[r['id']];current_epoch=r['capture_cycle']-tr['capture_cycle']
  if epoch is None:epoch=current_epoch
  if current_epoch!=epoch or r['network_complete_cycle']!=epoch+tr['complete_cycle']:raise ValueError('network/capture timing mismatch')
  if not r['capture_cycle']<=r['network_complete_cycle']<=r['commit_cycle']<=r['present_cycle']:raise ValueError('nonmonotonic timing')
  if r['capture_to_present_cycles']!=r['present_cycle']-r['capture_cycle']:raise ValueError('bad age')
  if r['fixture']!=tr['fixture_index'] or r['writes']!=345600 or r['bursts']!=43200 or r['underruns']!=0:raise ValueError('presentation metadata mismatch')
  fixture=a.fixtures/f"{r['fixture']:04d}.jpg";dump=a.dumps/f"{r['id']:04d}-rgb565.txt"
  if sha(fixture)!=tr['jpeg_sha256']:raise ValueError('fixture hash mismatch')
  ppm=a.output.parent/f"{r['id']:04d}-cmodel.ppm"
  subprocess.run([str(a.cmodel),str(fixture),str(ppm)],check=True,capture_output=True)
  result=subprocess.run([sys.executable,str(COMPARE),str(ppm),str(dump),'--exact'],check=True,capture_output=True,text=True)
  metric=json.loads(result.stdout)
  if metric['exact_rgb565_pixels']!=345600:raise ValueError('related C model mismatch')
  comparisons.append({'id':r['id'],'pixels':metric['exact_rgb565_pixels'],'dump_sha256':sha(dump),'jpeg_sha256':sha(fixture)})
 if any(totals[k]!=0 for k in ('core_drops','core_overflows','underruns')):raise ValueError('core fault counters')
 result={'capture_count':m['captures'],'packet_reassembly_dropped_ids':m['not_reassembled_ids'],
         'rtl_queue_dropped_ids':dropids,'rtl_presented_ids':ids,'rtl_epoch':epoch,
         'max_capture_to_present_ms':max((r['capture_to_present_cycles'] for r in presented),default=0)/100000,
         'trace_sha256':m['trace_sha256'],'related_cmodel_exact_comparisons':comparisons,
         'limitations':'functional RTL/QSPI + synthetic network trace + hypothetical full-frame queue; no actual ESP32/Wi-Fi'}
 a.output.write_text(json.dumps(result,indent=2)+'\n')
 print(f"CHECK_PASS captured={m['captures']} incomplete={m['not_reassembled_ids']} queue_dropped={dropids} presented={ids} max_age_ms={result['max_capture_to_present_ms']:.5f}")
if __name__=='__main__':main()
