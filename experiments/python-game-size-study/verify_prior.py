#!/usr/bin/env python3
"""Regenerate the72 frozen GM01 packets and compare216 exact plane lengths."""
import hashlib
import json
from pathlib import Path
import sys
import preflight as s
import numpy as np

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'python-codec-study'))
import corpus


def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    prior_path=HERE.parent/'python-game-codec-study/results.json'
    prior=json.loads(prior_path.read_text());packets=planes=0
    paths=[HERE/'verify_prior.py',HERE/'preflight.py',Path(s.gc.__file__),Path(s.gc.roi.__file__),
           Path(s.gc.ft.__file__),Path(s.gc.mt.__file__),Path(s.gc.token_coeff.__file__),Path(s.cc.__file__),
           Path(s.gc.word_coeff.__file__),Path(corpus.__file__)]
    hashes={str(p):digest(p) for p in paths}
    for scene in prior['scenes']:
        frames,manifest=corpus.load_video(scene['manifest']['source'],max_frames=12,start_seconds=4)
        assert manifest['frame_sha256']==scene['manifest']['frame_sha256']
        for profile in ('uniform16','roi8bg16','roi8bg32'):
            enc=s.gc.Encoder();h,w=frames[0].shape[:2];mw,mh=s.gc.roi.geometry(w,h)
            scale_map=np.full((mh,mw),16,np.uint8) if profile=='uniform16' else s.gc.roi.declared_map(w,h,((16,48,192,80),(160,352,400,80)),8,16 if profile=='roi8bg16' else 32)
            for i,rgb in enumerate(frames):
                packet=enc.prepare(rgb,i,scale_map=scale_map,force_key=i==6,mode='zero')
                expected=next(r for r in scene['records'] if r['profile']==profile and r['id']==i)
                assert hashlib.sha256(packet).hexdigest()==expected['packet_sha256'],'priorpacket changed'
                parsed=s.gc.parse(packet,1);lengths=s.gc.HEADER.unpack_from(packet)[13:]
                for plane,(c,n) in enumerate(zip(parsed['coefficients'],lengths)):
                    pw=w if plane==0 else w//2
                    assert s.coefficient_size(c,(pw+7)//8)==n;planes+=1
                enc.ack(i,epoch=1);packets+=1
    assert hashes=={str(p):digest(p) for p in paths},'sourcechanged'
    result={'source_sha256':hashes,'prior_result_sha256':digest(prior_path),'regenerated_packet_sha_matches':packets,
            'exact_plane_length_checks':planes,'scope':'Actualre-encodingandCP02decodingtoverifylengthsagainstfrozenpacketSHA;notanotherFPSbenchmark'}
    (HERE/'prior-check.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='source_sha256'},indent=2))


if __name__=='__main__':main()
