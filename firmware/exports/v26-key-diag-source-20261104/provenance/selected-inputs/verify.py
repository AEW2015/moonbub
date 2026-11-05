"""Read-only verification of final unflashed artifacts and historical snapshots."""
from pathlib import Path
import hashlib,json,sys
P=Path(__file__).resolve().parent;E=P/'evidence'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 f=E/'build-manifest.json';m=json.loads(f.read_text())
 if len(sys.argv)>1:assert sha(f)==sys.argv[1],'Manifest identity'
 snap=json.loads((P/m['prebuild']['snapshot']).read_text());assert sha(P/m['prebuild']['snapshot'])==m['prebuild']['sha256']
 for rel,h in snap['files'].items():assert sha(P/rel)==h,rel
 for rel,row in m['artifacts'].items():assert sha(P/rel)==row['sha256'] and(P/rel).stat().st_size==row['bytes'],rel
 history=[]
 for folder in sorted(E.glob('prebuild-*')):
  snapshot=json.loads((folder/'snapshot.json').read_text())
  for rel,h in snapshot['files'].items():assert sha(folder/'inputs'/rel)==h,(folder.name,rel)
  review=json.loads((folder/'source-stage-manifest.json').read_text())
  for rel,h in review['artifacts'].items():assert sha(folder/'review-evidence'/rel)==h,(folder.name,rel)
  history.append({'stage':folder.name,'inputs':len(snapshot['files']),'review_artifacts':len(review['artifacts'])})
 parent=json.loads((P/'parent-v25.json').read_text());base=Path(parent['origin'])
 assert sha(base/'evidence/manifest.json')==parent['manifest_sha256']
 for rel,h in parent['sources'].items():assert sha(base/rel)==h,rel
 for rel,row in parent['artifacts'].items():assert sha(base/rel)==row['sha256'],rel
 # The direct v25 guard also binds this descriptor. Verify its sealed v24
 # filesystem independently, rather than treating a copied descriptor as proof.
 p24=json.loads((base/'parent-v24.json').read_text());b24=Path(p24['origin'])
 assert sha(b24/'evidence/build-manifest.json')==p24['manifest_sha256']
 for rel,h in p24['source_files'].items():assert sha(b24/rel)==h,rel
 for rel,row in p24['artifacts'].items():assert sha(b24/rel)==row['sha256'],rel
 assert m['overall']=='INCOMPLETE' and m['installed'] is False and m['hardware_actions']=='NONE'
 assert m['checks']['target_check']==m['checks']['target_build']=='PASS'
 assert m['memory']['stack_watermark_unit_bytes']==1
 print(json.dumps({'status':'BINDINGS_PASS','manifest_sha256':sha(f),'prebuild_inputs':len(snap['files']),'artifacts':len(m['artifacts']),'historical_snapshots':history,'v25_sources':len(parent['sources']),'v25_artifacts':len(parent['artifacts']),'v24_sources':len(p24['source_files']),'v24_artifacts':len(p24['artifacts']),'overall':m['overall'],'physical_gates':'NOT_RUN','installed':False},indent=2))
if __name__=='__main__':main()
