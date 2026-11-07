#!/usr/bin/env python3
"""Measure real PC JPEG/framing work, and recount frozen custom-wire framing.

Native gateway/RTL service, Wi-Fi, capture, source cadence and device timing are
outside these wall-clock measurements. Opaque custom packets require an explicit
research sink and do not install a decoder or satisfy its reference contract.
"""
from collections import Counter
from dataclasses import replace
import datetime
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import signal
import statistics
import struct
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'experiments/python-gamebub-v97/host'
sys.path.insert(0, str(ROOT / 'host'))
from PIL import Image, ImageDraw
from moonshine import protocol as legacy
from moonshine import protocol97 as compact
from moonshine.transport97_sender import Sender, LatestPrepared


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stats(values):
    ordered = sorted(values)
    return dict(min=min(ordered), median=statistics.median(ordered),
                p95=ordered[min(len(ordered)-1, int(len(ordered)*0.95))], max=max(ordered))


def source_image(kind, index):
    if kind == 'noise':
        return Image.frombytes('RGB', (720,480), random.Random(97000+index).randbytes(720*480*3))
    image = Image.new('RGB', (720,480), (16,24,32))
    draw = ImageDraw.Draw(image)
    if kind == 'ui':
        for n in range(16):
            draw.rectangle((16+n*40,40,40+n*40,430), fill=((n*31+index*13)%256, (n*17)%256, (n*9)%256))
        draw.rectangle((420,10,710,70), fill='black')
        draw.text((435,25),'GAME BUB V97  720x480  FRAME '+str(index), fill='white')
    else:
        for y in range(0,480,16):
            for x in range(0,720,16):
                draw.rectangle((x,y,x+15,y+15), fill=('white' if ((x//16+y//16+index)%2) else 'black'))
        draw.rectangle(((index*37)%640,150,(index*37)%640+70,250), fill=(255,64,8))
    return image


def main():
    out = AREA / 'attempts' / (datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'-'+uuid.uuid4().hex[:8])
    out.mkdir(parents=True)
    v92_pointer = ROOT / 'experiments/python-gamebub-v92/wire/results.json'
    v92 = json.loads(v92_pointer.read_text())
    baseline = ROOT / v92['selected_report']
    archive = baseline.parent / 'packets.bin.gz'
    sources = [Path(__file__).resolve(), ROOT/'host/moonshine/protocol.py', ROOT/'host/moonshine/protocol97.py',
               ROOT/'host/moonshine/transport97_sender.py', ROOT/'host/moonshine/encoding.py', v92_pointer, baseline, archive]
    pins = {str(path.relative_to(ROOT)): sha(path) for path in sources}
    report = dict(schema='cu66-v97-host-preparation-v1', status='FAIL', source_sha256=pins,
                  python=sys.version, pillow=Image.__version__, hardware_30fps_proven=False,
                  actual_esp32_execution=False, setup_exchange_bytes=80,
                  jpeg_rows=[], opaque_rows=[], checks=[])
    for path in sources:
        if path.suffix != '.gz':
            target = out/'sources'/path.relative_to(ROOT)
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(path.read_bytes())
    old = signal.getsignal(signal.SIGALRM)
    def expired(signum, frame):
        raise TimeoutError('host experiment watchdog')
    signal.signal(signal.SIGALRM,expired)
    signal.alarm(300)
    started = time.monotonic()
    try:
        def paired(session, config=compact.SinkConfig()):
            sender = Sender(session, config)
            receiver = compact.Receiver(config, session.core_generation)
            sender.acknowledge(receiver.setup(sender.setup_request()))
            return sender, receiver
        def reject(name, call):
            try:call()
            except (ValueError, struct.error):report['checks'].append(dict(name=name, rejected=True))
            else:raise AssertionError(('unexpected acceptance',name))
        unpaired = Sender(compact.Session(9701))
        reject('host_preparation_before_setup_ack', lambda:unpaired.prepare(source_image('ui',0),0,0))
        session = compact.Session(9701)
        sender, receiver = paired(session)
        latest = LatestPrepared()
        first = None
        for index in range(12):
            kind = ('ui','motion','noise')[index%3]
            image = source_image(kind,index)
            frame = sender.prepare(image,index,1000000+index*33333,quality=65)
            frame_path = out/f'jpeg-{index:02}.jpg'
            frame_path.write_bytes(frame.payload)
            reconstructed = bytearray()
            for packet in frame.datagrams:
                chunk = receiver.accept(packet)
                reconstructed.extend(chunk.payload)
            assert bytes(reconstructed) == frame.payload and chunk.crc_complete
            control = tuple(legacy.packets(frame.payload,index,frame.capture_us))
            oracle = legacy.Reassembler()
            result = None
            for packet in control: result=oracle.accept(packet)
            assert result[1] == frame.payload
            latest.offer(frame)
            report['jpeg_rows'].append(dict(index=index,kind=kind,payload_bytes=len(frame.payload),
                payload_sha256=frame.payload_sha256,datagrams=len(frame.datagrams),
                compact_application_bytes=frame.application_bytes, compact_ipv4_udp_bytes=frame.ipv4_udp_bytes,
                legacy_datagrams=len(control), legacy_application_bytes=sum(map(len,control)),
                legacy_ipv4_udp_bytes=sum(map(len,control))+28*len(control),timings_ns=frame.timings_ns))
            if first is None:first=frame
        assert latest.replaced == 11 and latest.take().frame_id == 11 and latest.take() is None
        reject('latest_rejects_stale_frame',lambda:latest.offer(first))
        reject('latest_requires_clear_for_epoch_change',lambda:latest.offer(replace(first,epoch=9999,frame_id=12)))
        latest.clear();latest.offer(replace(first,epoch=9999,frame_id=12));assert latest.take().epoch==9999
        reject('negative_frame_identity',lambda:sender.prepare_bytes(first.payload,-1,0))
        reject('invalid_capture_timestamp',lambda:sender.prepare_bytes(first.payload,12,1<<64))
        reject('opaque_bytes_not_valid_jpeg',lambda:sender.prepare_bytes(b'CS92'+b'x'*100,12,0))
        reject('complete_application_budget_enforced',lambda:sender.prepare_bytes(first.payload,12,0,max_application_bytes=1))
        reject('unsupported_profile_default',lambda:Sender(compact.Session(3,profile=int.from_bytes(b'CS92','big'),frame_cap=49152,sink_caps=compact.CAP_OPAQUE)))
        profile = int.from_bytes(b'CS92','big')
        config = compact.SinkConfig(opaque_profile=profile)
        host, sink = paired(compact.Session(9702,profile=profile,frame_cap=49152,sink_caps=compact.CAP_OPAQUE),config)
        totals=Counter();last_cohort=None;fid=0
        with gzip.open(archive,'rb') as stream:
            while True:
                head=stream.read(8)
                if not head:break
                assert len(head)==8
                ml,pl=struct.unpack('<II',head);assert ml<=32768 and 132<=pl<=49152
                meta=json.loads(stream.read(ml));payload=stream.read(pl)
                assert len(payload)==pl and hashlib.sha256(payload).hexdigest()==meta['packet_sha256']
                if meta['policy'] != 'context_byte_min':continue
                if meta['cohort']!=last_cohort:
                    last_cohort=meta['cohort'];fid=0
                    host,sink=paired(compact.Session(9800+last_cohort,profile=profile,frame_cap=49152,sink_caps=compact.CAP_OPAQUE),config)
                compact_frame=host.prepare_bytes(payload,fid,fid*33333)
                actual=b''.join(sink.accept(p).payload for p in compact_frame.datagrams)
                assert actual==payload
                control=tuple(legacy.packets(payload,fid,fid*33333))
                row=dict(cohort=meta['cohort'],source_fid=meta['fid'],payload_bytes=pl,datagrams=len(compact_frame.datagrams),
                         compact_application_bytes=compact_frame.application_bytes,compact_ipv4_udp_bytes=compact_frame.ipv4_udp_bytes,
                         legacy_datagrams=len(control),legacy_application_bytes=sum(map(len,control)),
                         legacy_ipv4_udp_bytes=sum(map(len,control))+28*len(control),timings_ns=compact_frame.timings_ns)
                report['opaque_rows'].append(row)
                totals.update({k:v for k,v in row.items() if k.endswith('_bytes') or k.endswith('datagrams')})
                fid+=1
        assert len(report['opaque_rows'])==457
        report.update(status='PASS_PC_PREPARE_AND_FRAMING', synthetic_jpeg_frames=12, opaque_frames=457,
                      host_checks=len(report['checks']), latest_queue_replacements=11,
                      synthetic_jpeg_prepare_ns=stats([r['timings_ns']['complete_host_prepare'] for r in report['jpeg_rows']]),
                      opaque_crc_packetize_ns=stats([r['timings_ns']['crc_packetize'] for r in report['opaque_rows']]),
                      opaque_totals=dict(totals),
                      scope='PC JPEG encode+validation+CRC+packetization on twelve synthetic frames and framing-only transport over457frozenCS92payloads through explicitly configured opaque Python sink. No live Sunshine capture/encoder, deployed firmware, ESP32 timing, WiFi service, DMA execution, decoder/publication or fixed source-cadence proof.')
        assert pins=={name:sha(ROOT/name) for name in pins},'inputs changed during run'
    except BaseException as error:
        report['failure']=repr(error);raise
    finally:
        signal.alarm(0);signal.signal(signal.SIGALRM,old)
        report['wall_seconds']=time.monotonic()-started
        report['artifacts_sha256']={str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file() and p.name!='results.json'}
        (out/'results.json').write_text(json.dumps(report,indent=2)+'\n')
        if report['status'].startswith('PASS'):(AREA/'results.json').write_text(json.dumps(dict(report,selected_report=str((out/'results.json').relative_to(ROOT))),indent=2)+'\n')
    print(report['status'],'JPEG',report.get('synthetic_jpeg_frames'),'opaque',report.get('opaque_frames'))


if __name__=='__main__':
    main()
