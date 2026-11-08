#!/usr/bin/env python3
"""Execute current Python MSV1 packetizer over UDP and check trace negatives."""
import base64
import copy
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import socket
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'host'))
from moonshine.protocol import packets


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out=ROOT/'experiments/python-gamebub-v111/harness/trace-attempts'/stamp
    out.mkdir(parents=True)
    fixture=Path('/home/lori/gamebub-tools/esp-emu-study-0510/lcd-bypass/msv1-bridge-multi/src/0000.jpg')
    assert sha(fixture)=='8cc99ea7d50d1d20255e41ff7247b0770b3349e705c27152a41817418ce5c9de'
    source=ROOT/'host/moonshine/protocol.py'
    producer=dict(kind='python_msv1_packetizer',actual_source=str(source.relative_to(ROOT)),source_sha256=sha(source),
                  fixture_sha256=sha(fixture),invocation='moonshine.protocol.packets(jpeg, frame_id=0, capture_us=1000000)',
                  python=sys.version,sunshine_executed=False,native_encoder_executed=False)
    (out/'producer.json').write_text(json.dumps(producer,indent=2)+'\n')
    payloads=list(packets(fixture.read_bytes(),frame_id=0,capture_us=1000000))
    with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as s:
        s.bind(('127.0.0.1',0));port=s.getsockname()[1]
    trace_script=Path(__file__).with_name('trace.py')
    cmd=[sys.executable,str(trace_script),'capture','--out',str(out/'capture.json'),'--producer-manifest',str(out/'producer.json'),
         '--port',str(port),'--packets',str(len(payloads)),'--timeout','10']
    with (out/'capture.log').open('w') as log:
        p=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT)
        try:
            end=time.monotonic()+10
            while 'CAPTURE_READY' not in (out/'capture.log').read_text():
                assert p.poll() is None and time.monotonic()<end
                time.sleep(.02)
            with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as udp:
                for data in payloads:udp.sendto(data,('127.0.0.1',port))
            assert p.wait(timeout=15)==0
        finally:
            if p.poll() is None:p.kill();p.wait()
    spec=importlib.util.spec_from_file_location('v111_trace',trace_script)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    good=module.validate(out/'capture.json')
    assert good['datagrams']==26 and good['payload_bytes']==26159 and good['wire_bytes']==27199
    assert good['frames']==[dict(id=0,payload_bytes=26159,crc32='eceeb9c5',payload_sha256=sha(fixture))]
    original=json.loads((out/'capture.json').read_text())
    negative=[]
    for name in ('corrupt_payload_crc','missing_first_datagram','duplicate_first_datagram','nonmonotonic_clock','wrong_clock_domain'):
        altered=copy.deepcopy(original)
        if name=='corrupt_payload_crc':
            row=altered['datagrams'][-1];data=bytearray(base64.b64decode(row['base64']));data[-1]^=1
            row['base64']=base64.b64encode(data).decode();row['sha256']=hashlib.sha256(data).hexdigest()
        elif name=='missing_first_datagram':altered['datagrams'].pop(0)
        elif name=='duplicate_first_datagram':altered['datagrams'].insert(1,copy.deepcopy(altered['datagrams'][0]))
        elif name=='nonmonotonic_clock':altered['datagrams'][-1]['arrival_ns']=0
        else:altered['clock_domain']='FPGA_cycles'
        path=out/(name+'.json');path.write_text(json.dumps(altered,sort_keys=True)+'\n')
        try:module.validate(path)
        except AssertionError as error:negative.append(dict(name=name,status='EXPECTED_REJECTION',error=str(error),sha256=sha(path)))
        else:raise AssertionError('negative accepted: '+name)
    result=dict(schema='v111-python-packetizer-live-UDP-trace-probe-v1',status='PASS',actual_UDP_capture=True,
                producer=producer,capture_command=cmd,byte_trace=good,negative_controls=negative,
                source_sha256={str(p.relative_to(ROOT)):sha(p) for p in (source,trace_script,Path(__file__).resolve())},
                clock_domain='host_monotonic_ns',shared_simulation_time=False,sunshine_executed=False,
                target_timing_qualified=False,hardware_contact=False,
                artifact_sha256={p.name:sha(p) for p in out.iterdir() if p.is_file()})
    (out/'results.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    pointer=out.parents[1]/'trace-results.json'
    pointer.write_text(json.dumps(dict(status='PASS',selected_result=str((out/'results.json').relative_to(ROOT)),
                                    sha256=sha(out/'results.json'),actual_UDP_capture=True,sunshine_executed=False,
                                    target_timing_qualified=False),indent=2)+'\n')
    print('V111_TRACE_PROBE_PASS datagrams=26 payload=26159 wire=27199 negative_controls=5',out)


if __name__=='__main__':main()
