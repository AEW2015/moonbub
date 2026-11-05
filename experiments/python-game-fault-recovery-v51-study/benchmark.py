"""Actual receiver fault/retry/key recovery on six deterministic delivery traces."""
from pathlib import Path
import hashlib,json,struct,sys,zlib
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'python-game-stream-rx-v48-study'));import receiver as stream
h=stream.h;SOURCE=HERE.parent/'python-game-binary-qual-v40-study'
SCENARIOS=('drop7','corrupt7','badtag7','duplicate6','reorder8','retry7')
def digest(b):return hashlib.sha256(b).hexdigest()
def snapshot(rx):
 return dict(rid=rx.rid,last=rx.last,reference_tag=None if rx.ref is None else h.m.C.reference_tag(rx.ref).hex(),hud_sha256=None if rx.hud is None else[digest(p['words'].astype('<u2').tobytes()) for p in rx.hud])
def mutate(packet,kind):
 if kind=='corrupt':
  pos=len(packet)//2;return packet[:pos]+bytes([packet[pos]^1])+packet[pos+1:]
 if kind=='badtag':
  fields=list(stream.envelope.HEADER.unpack_from(packet));fields[10]=bytes([fields[10][0]^1])+fields[10][1:];body=stream.envelope.HEADER.pack(*fields)+packet[stream.envelope.HEADER.size:-4];return body+struct.pack('<I',zlib.crc32(body))
 return packet

def actions(name):
 out=[]
 if name=='reorder8':return[(i,'good') for i in range(7)]+[(8,'good'),(7,'good'),(8,'good')]+[(i,'good') for i in range(9,33)]
 for i in range(33):
  if i==7 and name in('drop7','corrupt7','badtag7'):kind={'drop7':'drop','corrupt7':'corrupt','badtag7':'badtag'}[name]
  else:kind='good'
  if i==7 and name=='retry7':out.append((7,'corrupt'))
  out.append((i,kind))
  if i==6 and name=='duplicate6':out.append((6,'good'))
 return out

def pins():
 source=h.load(SOURCE/'results.json');paths={ROOT/p for p in source['source_pins_sha256']};paths|={SOURCE/'results.json',HERE/'benchmark.py',HERE.parent/'python-game-stream-rx-v48-study/receiver.py',HERE.parent/'python-game-stream-rx-v48-study/envelope.py',HERE.parent/'python-game-stream-rx-v48-study/helpers.py',HERE.parent/'python-game-stream-rx-v48-study/results.json',HERE.parent/'python-game-block-rx-v44-study/decoder.py',HERE.parent/'python-game-symmetric-inverse-v45-study/model.py'};return{p.relative_to(ROOT).as_posix():h.sha(p) for p in sorted(paths)}
def main():
 before=pins();data=h.load(SOURCE/'results.json');cases=[]
 for case in data['cases']:
  for scenario in SCENARIOS:
   rx=stream.Receiver();expected_last=-1;expected_rid=h.m.NO_REF;rows=[]
   for order,(fid,kind) in enumerate(actions(scenario)):
    source=case['rows'][fid];packet=h.raw(source['packet'],SOURCE);wire=mutate(packet,kind);pre=snapshot(rx);valid=kind not in('drop','corrupt','badtag');expected=valid and fid>expected_last and(source['key'] or source['reference_id']==expected_rid);error=None;accepted=False
    if kind!='drop':
     try:out,patches,meta,_=rx.receive(wire);accepted=True
     except ValueError as exc:error=str(exc)
    assert accepted==expected,(scenario,fid,kind,error)
    post=snapshot(rx)
    if accepted:
     expected_last=expected_rid=fid;assert post['reference_tag']==source['normalized_tag'];display=h.f.f.n.overlay(h.m.C.corpus.rgb565(h.m.ft.planes_to_rgb(out)),tuple(p['words'] for p in patches));assert h.f.f.n.digest(display)==source['display_sha256']
    else:assert post==pre,('failed receive changed state',scenario,fid,kind)
    rows.append(dict(order=order,source_id=fid,kind=kind,source_packet=source['packet'],delivered_sha256=None if kind=='drop' else digest(wire),receiver_called=kind!='drop',accepted=accepted,expected_accepted=expected,error=error,before=pre,after=post,key=source['key']))
   assert rx.last==32
   summary=dict(actions=len(rows),receiver_calls=sum(r['receiver_called'] for r in rows),accepted=sum(r['accepted'] for r in rows),rejected=sum(r['receiver_called'] and not r['accepted'] for r in rows),dropped=sum(not r['receiver_called'] for r in rows),final_frame=rx.last,all_rejected_state_unchanged=True,independent_key24_accepted=any(r['source_id']==24 and r['accepted'] for r in rows))
   cases.append(dict(scene=case['scene'],scenario=scenario,rows=rows,summary=summary));assert pins()==before;(HERE/'results.json').write_text(json.dumps(dict(schema='gamebub-fault-recovery-v51',source_sha256=before,cases=cases,complete=False),indent=2)+'\n');print(json.dumps(dict(scene=case['scene'],scenario=scenario,**summary)),flush=True)
 summary={k:sum(c['summary'][k] for c in cases) for k in('actions','receiver_calls','accepted','rejected','dropped')};summary['cases']=len(cases)
 (HERE/'results.json').write_text(json.dumps(dict(schema='gamebub-fault-recovery-v51',source_sha256=before,cases=cases,complete=True,summary=summary,scope=['Actualstream48receivecalls,nohardware/transport/sockets;storedsourcepacketsusedwithoutnewencoding.','Sixdeterministicfaulttracesper4sourcecohorts;33sourceIDs/cohortreusedacrosscases.','Drop/corruption/badtagforcesPdependencyrejectionuntilindependentperiodickey24;duplicates/reorder/retryexerciseatomicstate.','Displaymodeledonlybypublishedreference/outputhash;noFPGAfence,UART/USB,ESP32orpanelrecoveryproven.','Noelapsedrecovery/FPSclaim;actualinputcadencesdifferandnetworkkeyrequestsnotimplemented.']),indent=2)+'\n');print(json.dumps(summary),flush=True)
if __name__=='__main__':main()
