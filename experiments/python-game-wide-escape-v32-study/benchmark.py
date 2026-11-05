from pathlib import Path
import hashlib,json,time,zlib,sys
import numpy as np
import model as m
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];OLD=HERE.parent/'python-game-wide-motion-v32-study'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def raw(desc,folder=OLD):
 packed=(folder/desc['path']).read_bytes();assert hashlib.sha256(packed).hexdigest()==desc['stored_sha256'];data=zlib.decompress(packed);assert len(data)==desc['raw_bytes'] and hashlib.sha256(data).hexdigest()==desc['raw_sha256'];return data

def blob(data):
 packed=zlib.compress(data,9);p='objects/'+hashlib.sha256(packed).hexdigest()+'.zlib';(HERE/'objects').mkdir(exist_ok=True);(HERE/p).write_bytes(packed)
 return dict(path=p,raw_bytes=len(data),raw_sha256=hashlib.sha256(data).hexdigest(),stored_sha256=hashlib.sha256(packed).hexdigest())
def main():
 old=json.loads((OLD/'results.json').read_text());paths={ROOT/p for p in old['source_sha256']};paths.add(OLD/'results.json');cases=[]
 for case in old['cases']:
  rows=[]
  for row in case['rows']:
   d=row['wide']['vectors'];paths.add(OLD/d['path']);v=np.frombuffer(raw(d),np.int8).reshape(15,23,2)
   packet,work=m.pack(v,return_work=True);start=time.perf_counter_ns();out=m.unpack(packet);decode_ms=(time.perf_counter_ns()-start)/1e6;np.testing.assert_array_equal(v,out)
   charged=0 if row['key'] else len(packet);raw_mv=row['wide']['raw_motion_budget_bytes'];oldbudget=row['wide']['hypothetical_complete_budget_bytes'];budget=oldbudget-raw_mv+charged
   rows.append(dict(id=row['id'],key=row['key'],vectors=d,packet=blob(packet),work=work,decode_ms=decode_ms,motion_charged_bytes=charged,raw_motion_budget_bytes=raw_mv,raw_complete_budget_bytes=oldbudget,escape_hypothetical_complete_budget_bytes=budget,baseline_actual_complete_budget_bytes=row['baseline']['actual_complete_budget_bytes'],residual_bytes=row['wide']['residual_bytes'],qmap_bytes=row['qmap_bytes'],hud_bytes=row['hud_bytes'],wide_hybrid=row['wide']['hybrid'],wide_hybrid_sha256=row['wide']['hybrid_sha256'],wide_prediction_sse=row['wide']['prediction_sse'],wide_original_work_ms=row['wide']['total_with_incumbent_work_ms'],new_total_source_work_ms=row['wide']['total_with_incumbent_work_ms']+work['pack_ms'],valid_GM27_frame=False))
  summary=dict(frames=len(rows),baseline_actual_complete_budget_bytes=sum(x['baseline_actual_complete_budget_bytes'] for x in rows),raw_complete_budget_bytes=sum(x['raw_complete_budget_bytes'] for x in rows),escape_hypothetical_complete_budget_bytes=sum(x['escape_hypothetical_complete_budget_bytes'] for x in rows),raw_motion_bytes=sum(x['raw_motion_budget_bytes'] for x in rows),escape_motion_bytes=sum(x['motion_charged_bytes'] for x in rows),escape_count=sum(x['work']['escape_count'] for x in rows),pack_ms_per_source=sum(x['work']['pack_ms'] for x in rows)/len(rows),decode_ms_per_source=sum(x['decode_ms'] for x in rows)/len(rows),total_source_work_ms=sum(x['new_total_source_work_ms'] for x in rows)/len(rows))
  cases.append(dict(scene=case['scene'],rows=rows,summary=summary));print(json.dumps(dict(scene=case['scene'],summary=summary)),flush=True)
 paths|={Path(v.__file__).resolve() for v in list(sys.modules.values()) if getattr(v,'__file__',None) and Path(v.__file__).resolve().is_relative_to(ROOT)}
 paths|={HERE/n for n in ['model.py','benchmark.py','test_model.py','verify.py']}
 result=dict(schema='gamebub-wide-escape-v32',source_sha256={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(paths)},cases=cases,scope=['Actual WV32 motion components with CRC and bounded independent decode; no wide GM27 frame/profile/receiver implemented.','Same retained noncausal v30 strict accepted references and all wide source reconstructions as original wide-motion experiment.','Prospective body budget replaces only raw MV charge:80Bframe+qmap+actualWV32+actualresidual+currentHU25+60Bbinding. Keys still charge zero MV.','Encoder times add actual WV32 construction including frozen narrow all-mode search to original paid baseline+wide work. Parser time separately reported. No hardware30fps proof or HEVCAV1 superiority claim.'])
 (HERE/'results.json').write_text(json.dumps(result,separators=(',',':'))+'\n')
if __name__=='__main__':main()
