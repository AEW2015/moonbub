"""Independent full-array direct receiver on retained fault/retry delivery traces."""
from pathlib import Path
import hashlib,importlib.util,json,struct,sys,zlib
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent;SOURCE=HERE.parent/'python-game-binary-qual-v40-study'
def mod(n,p):
 s=importlib.util.spec_from_file_location(n,p);v=importlib.util.module_from_spec(s);sys.modules[n]=v;s.loader.exec_module(v);return v
h=mod('fault51_verify_direct43_helpers',HERE.parent/'python-game-direct-rx-v43-study/helpers.py');before=sys.modules.get('helpers')
try:sys.modules['helpers']=h;old=mod('fault51_verify_direct43',HERE.parent/'python-game-direct-rx-v43-study/receiver.py')
finally:
 if before is None:sys.modules.pop('helpers',None)
 else:sys.modules['helpers']=before

def digest(b):return hashlib.sha256(b).hexdigest()
def snapshot(rx):return dict(rid=rx.rid,last=rx.last,reference_tag=None if rx.ref is None else h.m.C.reference_tag(rx.ref).hex(),hud_sha256=None if rx.hud is None else[digest(p['words'].astype('<u2').tobytes()) for p in rx.hud])
def delivery(name):
 a=[(i,'good') for i in range(33)]
 if name in('drop7','corrupt7','badtag7'):a[7]=(7,{'drop7':'drop','corrupt7':'corrupt','badtag7':'badtag'}[name])
 elif name=='duplicate6':a.insert(7,(6,'good'))
 elif name=='reorder8':a.insert(7,(8,'good'))
 elif name=='retry7':a.insert(7,(7,'corrupt'))
 else:raise ValueError('unknown retained fault plan')
 return a

def main():
 d=h.load(HERE/'results.json');source=h.load(SOURCE/'results.json');assert d['complete'];assert len(d['cases'])==24;totals=dict(actions=0,receiver_calls=0,accepted=0,rejected=0,dropped=0,cases=24)
 for p,v in d['source_sha256'].items():assert h.sha(ROOT/p)==v,p
 names=('drop7','corrupt7','badtag7','duplicate6','reorder8','retry7')
 for ix,c in enumerate(d['cases']):
  src=source['cases'][ix//6];name=names[ix%6];assert c['scene']==src['scene'] and c['scenario']==name;plan=delivery(name);assert len(plan)==len(c['rows']);rx=old.Receiver();counts=dict(actions=len(plan),receiver_calls=0,accepted=0,rejected=0,dropped=0)
  for i,((fid,kind),r) in enumerate(zip(plan,c['rows'],strict=True)):
   assert(r['order'],r['source_id'],r['kind'])==(i,fid,kind);f=src['rows'][fid];assert r['source_packet']==f['packet'];packet=h.raw(f['packet'],SOURCE)
   if kind=='corrupt':
    at=len(packet)//2;wire=packet[:at]+bytes([packet[at]^1])+packet[at+1:]
   elif kind=='badtag':
    fields=list(old.HEADER.unpack_from(packet));fields[10]=bytes([fields[10][0]^1])+fields[10][1:];body=old.HEADER.pack(*fields)+packet[old.HEADER.size:-4];wire=body+struct.pack('<I',zlib.crc32(body))
   else:wire=packet
   pre=snapshot(rx);assert pre==r['before'];expected=(kind=='good' and fid>rx.last and(f['key'] or f['reference_id']==rx.rid));accepted=False;error=None
   if kind!='drop':
    counts['receiver_calls']+=1;assert r['delivered_sha256']==digest(wire)
    try:out,patches,meta,_=rx.receive(wire);accepted=True
    except ValueError as exc:error=str(exc)
   else:counts['dropped']+=1;assert r['delivered_sha256'] is None
   post=snapshot(rx);assert post==r['after'];assert accepted==expected==r['accepted']==r['expected_accepted']
   if accepted:
    assert post['reference_tag']==f['normalized_tag'];display=h.f.f.n.overlay(h.m.C.corpus.rgb565(h.m.ft.planes_to_rgb(out)),tuple(p['words'] for p in patches));assert h.f.f.n.digest(display)==f['display_sha256'];counts['accepted']+=1
   elif kind!='drop':assert error and r['error'] and post==pre;counts['rejected']+=1
   else:assert post==pre
  for k,v in counts.items():assert c['summary'][k]==v;totals[k]+=v
  assert rx.last==c['summary']['final_frame']==32 and c['summary']['independent_key24_accepted'] and c['summary']['all_rejected_state_unchanged']
 assert d['summary']==totals;print(json.dumps(dict(**totals,independent_direct43_replay=True,all_rejected_states_unchanged=True,all_valid_outputs_match_stored_source=True,all24_cases_recovered=True,encoding_called=False,transport_or_physical_display_recovery_proven=False)))
if __name__=='__main__':main()
