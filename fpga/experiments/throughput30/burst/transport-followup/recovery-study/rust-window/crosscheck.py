#!/usr/bin/env python3
"""Cross-check host-compiled Rust adapter against independent Python event model."""
import argparse,hashlib,json,struct,subprocess,sys,zlib
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
from study import fixture_data,simulate_link,window_presof_receiver,parse_packet
from moonshine.protocol import Reassembler, SOF

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--fixtures',type=Path,required=True)
 p.add_argument('--executable',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
 a=p.parse_args();jpeg=fixture_data(a.fixtures);rows=[]
 for rate in (8_000_000,10_000_000):
  for channel in ('none','iid','bursty'):
   events,net=simulate_link(jpeg,600,rate,73,channel,False,1200)
   if net['sender_replaced'] or net['sender_expired'] or any(e['at']-e['capture']>10_000_000 for e in events):
    raise SystemExit('corpus exceeds Rust adapter timing assumptions')
   result,outcomes,forwarded=window_presof_receiver(events,600,100)
   expected=[];probe=Reassembler()
   for packet,outcome in zip(forwarded,outcomes):
    if outcome=='abort':expected.append('A');probe.reset(False);continue
    h=parse_packet(packet)
    # The Rust sink must abort an incomplete FPGA transaction before a newer
    # SOF; the Python reference Reassembler overwrites it implicitly.
    if h.flags&SOF and probe.active is not None:
     expected.append('A');probe.reset(False)
    try:probe.accept(packet)
    except ValueError:pass
    if outcome=='error':continue # Rust rejects ingress or reference packet.
    crc=zlib.crc32(h.payload)&0xffffffff
    expected.append(f"P {h.frame_id} {h.offset} {len(h.payload)} {int(outcome=='done')} {crc:08x}")
   data=b''.join(struct.pack('!QH',e['at']//100,len(e['payload']))+e['payload'] for e in events if e['kind']=='data')
   run=subprocess.run([str(a.executable)],input=data,capture_output=True,check=True)
   actual=run.stdout.decode().splitlines();mismatch=sum(x!=y for x,y in zip(actual,expected))+abs(len(actual)-len(expected))
   row={'rate_bps':rate,'channel':channel,'seed':73,'input_datagrams':len(events),
        'expected_events':len(expected),'actual_events':len(actual),'mismatches':mismatch,
        'python_complete':result['complete'],'stdout_sha256':hashlib.sha256(run.stdout).hexdigest(),
        'rust_stderr':run.stderr.decode().strip()}
   rows.append(row);print(row,flush=True)
   if mismatch:raise SystemExit('Rust adapter differs from Python candidate: inspect before use')
 a.out.write_text(json.dumps({'scope':'actual unmodified Rust Receiver inside experimental Rust window vs Python event model; host only',
                              'jitter_us':1200,'frames_per_case':600,'results':rows},indent=2)+'\n')
if __name__=='__main__':main()
