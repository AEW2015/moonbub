"""Finite actual AR03 candidate/admission/commit and GF03 packet-credit flow.

Python reference work is measured on independent virtual servers; ESP service,
wire, true-FIFO endpoint and vblank costs are declared assumptions. Data packets
are paced individually with consumed credits; decoded AF03 publication is separate.
No calibrated ESP32/FPGA memory/scanline or native shared-CPU proof is implied.
"""
from collections import Counter, deque
from dataclasses import asdict, dataclass
import hashlib
import heapq
import math
from pathlib import Path
import sys
import time

import numpy as np

HERE = Path(__file__).resolve().parent
for folder in ('python-game-candidate-commit-study', 'python-game-local-refresh-study', 'python-game-unified-codec-study', 'python-game-unified-ui-study', 'python-game-feedback-study', 'python-codec-study'):
    sys.path.insert(0, str(HERE.parent/folder))
import candidate_codec as rc
import unified_codec as legacy
import framing as transport
import gateway
import corpus


@dataclass(frozen=True)
class Config:
    reference_policy: str = 'overlap'
    refresh_policy: str = 'local'
    admission_enabled: bool = True
    admission_age_ms: float = 200
    decode_allowance_ms: float = 30
    pacing_ms: float = 1.1
    aggregate_ms: float = 0
    packet_credit_timeout_ms: float = 30
    max_credit_queries: int = 3
    esp_cpu_fraction: float = .6
    esp_driver_us: float = 20
    control_cpu_ms: float = .05
    fifo_bytes: int = 8192
    fifo_drain_bytes_ms: float = 2000
    maximum_fifo_wait_ms: float = 2
    lose_first_packet_credit: bool = False
    lose_all_packet_credits: bool = False
    duplicate_packet_credit: bool = False
    drop_packet_frame: int = -1
    corrupt_packet_frame: int = -1
    corrupt_af_frame: int = -1
    misroute_frame: int = -1
    codec_mode: str = 'exact'
    exact_ui: bool = True
    ui_rectangles: tuple = ((22,54,160,24),(22,82,160,24),(168,360,320,24),(168,390,240,24))
    width: int = 720
    height: int = 480
    fps: float = 30
    frame_cap: int = 49152
    window: int = 3
    promotion_period: int = 16
    refresh_period: int = 0
    refresh_key_background_scale: int = 16
    drop_first_refresh_chunk: bool = False
    drop_first_refresh_ack: bool = False
    link_mbps: float = 8
    feedback_mbps: float = 8
    qspi_mbps: float = 160
    feedback_latency_ms: float = 10
    refresh_hz: float = 60
    preencode_age_ms: float = 100
    decode_age_ms: float = 150
    ack_timeout_ms: float = 250
    ingress_timeout_ms: float = 150
    drain_ms: float = 1000
    drop_first_key_chunk: bool = False
    drop_first_promotion_ack: bool = False
    conflict_first_promotion_feedback: bool = False
    corruption_ids: tuple = ()


def digest(a):
    return hashlib.sha256(a.tobytes()).hexdigest()


def banks(obj):
    return {str(slot): None if bank is None else dict(id=bank.frame_id, tag=bank.tag.hex(),
            logical_yuv8_bytes=sum(p.size for p in bank.planes),
            array_bytes=sum(p.nbytes for p in bank.planes)) for slot, bank in obj.banks.items()}


def validate_complete(complete,frame_cap=49152):
    meta=rc.identity(complete.data,epoch=complete.epoch,frame_cap=frame_cap)
    if (meta['epoch'],meta['frame_id'],meta['body_crc'])!=(complete.epoch,complete.frame,complete.frame_crc):
        raise ValueError('GF03 route is not bound to AR03 identity')
    return meta


def run(frames, manifest=None, config=None, *, clock_ns=time.perf_counter_ns):
    cfg = config or Config()
    rc = globals()["rc"]
    if (not frames or cfg.reference_policy != 'overlap' or cfg.refresh_policy!='local'
            or cfg.codec_mode not in ('gm','exact','prune4') or type(cfg.exact_ui) is not bool
            or type(cfg.ui_rectangles) is not tuple or len(cfg.ui_rectangles)>4
            or type(cfg.window) is not int or cfg.window not in (2, 3)
            or type(cfg.width) is not int or type(cfg.height) is not int
            or cfg.width < 2 or cfg.height < 2 or cfg.width % 2 or cfg.height % 2
            or not 128 <= cfg.frame_cap <= 49152
            or any(not math.isfinite(x) or x <= 0 for x in
                   (cfg.fps, cfg.link_mbps, cfg.feedback_mbps, cfg.qspi_mbps, cfg.refresh_hz,
                    cfg.ack_timeout_ms, cfg.ingress_timeout_ms))
            or any(not math.isfinite(x) or x < 0 for x in
                   (cfg.feedback_latency_ms, cfg.preencode_age_ms, cfg.decode_age_ms, cfg.drain_ms))
            or type(cfg.promotion_period) is not int or cfg.promotion_period < 0
            or type(cfg.refresh_period) is not int or cfg.refresh_period < 0
            or type(cfg.refresh_key_background_scale) is not int or cfg.refresh_key_background_scale not in (16,32)):
        raise ValueError('bounded joint AR03 execution configuration')
    for flag in (cfg.drop_first_key_chunk, cfg.drop_first_promotion_ack, cfg.conflict_first_promotion_feedback, cfg.drop_first_refresh_chunk, cfg.drop_first_refresh_ack):
        if type(flag) is not bool: raise ValueError('fault boolean')
    if any(type(i) is not int or not 0 <= i < len(frames) for i in cfg.corruption_ids):
        raise ValueError('fault capture ID')
    if (type(cfg.admission_enabled) is not bool or not 0<cfg.esp_cpu_fraction<=1
            or any(not math.isfinite(x) or x<=0 for x in (cfg.admission_age_ms,cfg.decode_allowance_ms,cfg.pacing_ms,cfg.packet_credit_timeout_ms,cfg.fifo_drain_bytes_ms))
            or any(not math.isfinite(x) or x<0 for x in (cfg.aggregate_ms,cfg.esp_driver_us,cfg.control_cpu_ms,cfg.maximum_fifo_wait_ms))
            or type(cfg.fifo_bytes) is not int or cfg.fifo_bytes<transport.PAYLOAD
            or type(cfg.max_credit_queries) is not int or not 0<=cfg.max_credit_queries<=3):raise ValueError('joint gateway configuration')
    if cfg.exact_ui:
        import ui_plugin
        patch_builder=ui_plugin.PatchSelector(rectangles=cfg.ui_rectangles)
    else: patch_builder=None
    enc = rc.Encoder(window=cfg.window,frame_cap=cfg.frame_cap,mode=cfg.codec_mode,patch_builder=patch_builder)
    rx = rc.Receiver(frame_cap=cfg.frame_cap)
    ingress = transport.Reassembler(slots=2, max_frame=cfg.frame_cap, timeout_ms=cfg.ingress_timeout_ms)
    capture_times = [i*1000/cfg.fps for i in range(len(frames))]
    end = len(frames)*1000/cfg.fps; horizon = end+cfg.drain_ms
    events = []; sequence = 0; now = 0.0
    def event(at, kind, value=None):
        nonlocal sequence
        sequence += 1
        heapq.heappush(events, (at, 1 if kind == 'vblank' else 0, sequence, kind, value))
    for i, at in enumerate(capture_times): event(at, 'capture', i)
    for i in range(math.floor(horizon*cfg.refresh_hz/1000)+1): event(i*1000/cfg.refresh_hz, 'vblank')
    for i in range(1, math.floor(horizon/25)+1): event(i*25, 'ingress_tick')

    slots = [None]*cfg.window; latest_raw = waiting = None
    resize_job = encode_job = packetize_job = network_job = feed_job = qspi_job = decode_job = feedback_job = parse_job = mutation_job = None
    q_packetize = deque(); q_wire = deque(); q_feed = deque(); q_qspi = deque(); q_decode = deque(); q_feedback = deque(); q_parse = deque()
    scaled = {}; rects = {}; rows = {}; work = []; feedback_rows = []; wire = []; publications = []
    outcomes = {}; drops = []; presented = []; commits = []; waits = []
    fb = [dict(id=None, roles={'front'}), dict(id=None, roles=set()), dict(id=None, roles=set())]
    front = 0; pending_display = None
    last_key = last_store = None
    dropped_key = lost_promotion_ack = conflicting_promotion = False
    dropped_refresh = lost_refresh_ack = False
    peak_sender = peak_pending = peak_ingress = peak_fb = peak_feedback = 0
    started_wall = time.perf_counter()

    def timed(stage, frame, function):
        started = clock_ns(); value = function(); duration = (clock_ns()-started)/1e6
        if not math.isfinite(duration) or duration < 0: raise ValueError('nonnegative measured host work')
        row = dict(stage=stage, id=frame, start_ms=now, done_ms=now+duration,
                   wall_ms=duration, service_ms=duration)
        work.append(row)
        return value, row

    gw=gateway.Engine(cfg,ingress,event,timed,feedback_rows)

    def encoder_semantics():
        return enc.banks.copy(), enc.pending.copy(), enc._generation, getattr(enc,"_geometry",None)

    def restore_encoder(state):
        enc.banks, enc.pending, enc._generation, geometry = state
        if hasattr(enc,"_geometry"):enc._geometry=geometry

    def receiver_semantics():
        return rx.banks.copy(), rx.last_frame_id, rx.active, set(rx._leases), getattr(rx,"_geometry",None)

    def restore_receiver(state):
        rx.banks, rx.last_frame_id, rx.active, rx._leases, geometry = state
        if hasattr(rx,"_geometry"):rx._geometry=geometry

    def drop(frame, reason):
        if frame not in outcomes:
            outcomes[frame] = 'dropped'; drops.append(dict(id=frame, at_ms=now, reason=reason))

    def physical_drained(frame):
        r = rows[frame]
        return (r['encode_done'] and not any(r.get(k) for k in
                ('packetize_owned', 'wire_owned', 'feed_owned', 'qspi_owned', 'decode_owned', 'feedback_owned'))
                and r.get('receiver_route',{}).get('frame_id',frame) not in ingress.pending and gw.frame_drained(frame))

    def release(frame, reason):
        r = rows[frame]
        assert physical_drained(frame)
        assert slots[r['slot']] == frame
        slots[r['slot']] = None; r['released_ms'] = now; r['release_reason'] = reason
        for key in ('packet', 'chunks', 'complete', 'task', 'expected'):
            r.pop(key, None)
        gw.forget(frame)
        scaled.pop(frame, None)

    def request_expiry(frame, reason):
        r = rows[frame]
        if r.get('released_ms') is None:
            r['expiry_requested'] = reason
            r['expiry_requested_ms'] = min(now, r.get('expiry_requested_ms', now))

    def queue_feedback(frame, data):
        r = rows[frame]
        if sum(p.get('feedback_owned', 0) for p in rows.values()) >= 4:
            feedback_rows.append(dict(kind='descriptor_drop', id=frame, at_ms=now)); return
        r['feedback_owned'] += 1
        q_feedback.append((frame, data))

    def nack_from_route(frame):
        r = rows[frame]
        if sum(p.get('feedback_owned', 0) for p in rows.values()) >= 4:
            feedback_rows.append(dict(kind='descriptor_drop', id=frame, at_ms=now)); return
        # Reject-only metadata comes from the received GF02 route, not decoded
        # source pixels or a sender correctness oracle. NACK publishes no bank.
        meta = dict(r['receiver_route'], destination_bank=rc.NO_BANK)
        data, row = timed('nack_build', frame, lambda: rc.feedback(meta, rc.NACK))
        r['feedback_owned'] += 1
        event(row['done_ms'], 'nack_ready', (frame, data))

    def pump():
        nonlocal latest_raw, waiting, resize_job, encode_job, packetize_job, network_job
        nonlocal feed_job, qspi_job, decode_job, feedback_job, parse_job, mutation_job
        nonlocal dropped_key, dropped_refresh, last_key, last_store
        changed = True
        while changed:
            changed = False
            if mutation_job is None and not (encode_job is not None and rows[encode_job].get('candidate_waiting')):
                for frame, r in rows.items():
                    if r.get('released_ms') is not None or not physical_drained(frame): continue
                    if r.get('expiry_requested'):
                        _, charge = timed('expire_apply', frame, lambda f=frame: enc.expire(f))
                        mutation_job = (frame, 'expire', r['expiry_requested'])
                        event(charge['done_ms'], 'mutation_done', mutation_job); changed = True; break
                    if r.get('ack_waiting') is not None:
                        packet = r['ack_waiting']
                        before = encoder_semantics()
                        def apply_ack():
                            try: return enc.ack(packet), None
                            except ValueError as error: return False, str(error)
                        (accepted, error), charge = timed('ack_apply', frame, apply_ack)
                        r['staged_ack_after'] = encoder_semantics()
                        restore_encoder(before)
                        r['ack_waiting'] = None
                        r['ack_apply_error'] = error
                        mutation_job = (frame, 'ack' if accepted else 'invalid_ack', 'decoded_ack')
                        event(charge['done_ms'], 'mutation_done', mutation_job); changed = True; break
            if resize_job is None and latest_raw is not None:
                frame = latest_raw; latest_raw = None
                (image, rect), charge = timed('resize', frame, lambda: corpus._letterbox(frames[frame], cfg.width, cfg.height))
                resize_job = (frame, image, rect)
                event(charge['done_ms'], 'resize_done', resize_job); changed = True
            if packetize_job is None and q_packetize:
                frame = q_packetize.popleft(); r = rows[frame]
                chunks, charge = timed('packetize', frame, lambda: transport.datagrams(r['packet'], 1, frame+1000 if cfg.misroute_frame==frame else frame, max_frame=cfg.frame_cap))
                r['chunks'] = chunks
                packetize_job = frame; event(charge['done_ms'], 'packetize_done', frame); changed = True
            while q_wire:
                fid=q_wire.popleft();gw.enqueue(fid,rows[fid]['chunks']);changed=True
            gw.pump(now)
            while gw.completions:
                fid,complete=gw.completions.pop(0);r=rows[fid]
                r['complete']=complete;r['receiver_route']=gw.frames[fid]['route'];r['wire_owned']=False;r['decode_owned']=True;q_decode.append(fid);changed=True
            while gw.rejections:
                fid,error,route=gw.rejections.pop(0);r=rows[fid]
                r['feed_errors'].append(error)
                if route is not None and not r.get('nack_queued'):
                    r['receiver_route']=route;r['nack_queued']=True;nack_from_route(fid)
                changed=True
            for fid,r in rows.items():
                if fid in gw.frames:
                    if gw.frames[fid]['route'] is not None:r['receiver_route']=gw.frames[fid]['route']
                    if gw.frames[fid]['consumed']==len(gw.frames[fid]['chunks']):r['wire_owned']=False
            if decode_job is None and q_decode:
                free = next((i for i, value in enumerate(fb) if not value['roles']), None)
                if free is not None:
                    frame = q_decode.popleft(); r = rows[frame]
                    if r.get('expiry_requested') or now-capture_times[frame] > cfg.decode_age_ms:
                        ingress.reject(r['complete']); r['decode_owned'] = False
                        drop(frame, 'deadline_before_decode'); nack_from_route(frame); changed = True
                    else:
                        fb[free] = dict(id=frame, roles={'decoding'})
                        r['decode_started_ms'] = now; r['read_pin_at_decode_start'] = r['complete'].frame in ingress.pending
                        before_banks = banks(rx)
                        def begin():
                            try:
                                validate_complete(r['complete'],cfg.frame_cap)
                                return rx.begin(r['complete'].data), None
                            except ValueError as error: return None, str(error)
                        (task, error), charge = timed('decode_begin', frame, begin)
                        r['task'] = task; r['decode_error'] = error; r['receiver_banks_before'] = before_banks
                        r['receiver_readers_during_begin'] = rx.readers
                        decode_job = (frame, free)
                        event(charge['done_ms'], 'decode_begin_done', decode_job); changed = True
            while q_feedback:
                frame,data=q_feedback.popleft();gw.reverse(data,'af',(frame,data),now,deliver=not rows[frame].get('lose_af_on_wire',False));changed=True
            if parse_job is None and q_parse:
                frame, data = q_parse.popleft()
                def parse():
                    try: return rc.parse_feedback(data), None
                    except ValueError as error: return None, str(error)
                (parsed, error), charge = timed('feedback_parse', frame, parse)
                parse_job = (frame, data, parsed, error)
                event(charge['done_ms'], 'feedback_parsed', parse_job); changed = True
            if encode_job is None and mutation_job is None and waiting is not None:
                frame = waiting
                if now-capture_times[frame] > cfg.preencode_age_ms:
                    waiting = None; scaled.pop(frame, None); drop(frame, 'stale_before_encode'); changed = True
                else:
                    refresh_due = cfg.refresh_period > 0 and last_key is not None and frame-last_key >= cfg.refresh_period
                    no_reference = not any(b is not None for b in enc.banks.values()) if cfg.refresh_policy=='local' else enc.banks[0] is None
                    key = no_reference or refresh_due
                    refresh_deferred = False
                    explicit_bank = None
                    if (cfg.refresh_policy=='local' and key and refresh_due
                            and not enc.can_prepare(True) and enc.banks[1] is not None
                            and enc.can_prepare()):
                        # Do not add bank0 readers while it drains/reserves a
                        # refresh writer. Confirmed bank1 remains independent.
                        key = False; refresh_deferred = True; explicit_bank = 1
                    refresh_key = key and last_key is not None
                    promotion_due = not key and not refresh_deferred and cfg.promotion_period > 0 and last_store is not None and frame-last_store >= cfg.promotion_period
                    promote = promotion_due
                    bank0_fallback = False
                    if cfg.reference_policy=='overlap' and promotion_due and not enc.can_prepare(False,True):
                        # Stop admitting new bank1 consumers while its old
                        # users drain or publication is uncertain. Bank0 work
                        # remains independent of the reserved bank1 writer.
                        promote = False; bank0_fallback = enc.banks[0] is not None
                        explicit_bank = 0 if bank0_fallback else 1
                    slot = next((i for i, value in enumerate(slots) if value is None), None)
                    if slot is not None and enc.can_prepare(key, promote):
                        waiting = None; slots[slot] = frame
                        # Map construction is explicitly paid as encoder work.
                        def make_map():
                            if cfg.width == 720:
                                return rc.gm.roi.declared_map(cfg.width,cfg.height,((16,48,192,80),(160,352,400,80)),8,
                                    cfg.refresh_key_background_scale if refresh_key else 16)
                            mw,mh=rc.gm.roi.geometry(cfg.width,cfg.height)
                            return np.full((mh,mw),cfg.refresh_key_background_scale if refresh_key else 16,np.uint8)
                        mapped, map_charge = timed('map', frame, make_map)
                        source_banks = banks(enc)
                        extra = {'reference_bank':explicit_bank} if explicit_bank is not None else {}
                        decision, charge = timed('candidate_build', frame, lambda: enc.build(scaled[frame],frame,scale_map=mapped,force_key=key,promote=promote,**extra))
                        # Serial map+encode work occupies the encoder server.
                        duration = map_charge['wall_ms']+charge['wall_ms']
                        charge['start_ms'] += map_charge['wall_ms']
                        charge['done_ms'] += map_charge['wall_ms']
                        r = dict(id=frame, slot=slot, key=decision.key, promoted=decision.promoted,
                                 refresh_key=refresh_key, refresh_due=refresh_due, refresh_deferred=refresh_deferred, background_scale=cfg.refresh_key_background_scale if refresh_key else 16,
                                 promotion_due=promotion_due, bank0_fallback=bank0_fallback,
                                 reference_bank=decision.reference_bank, reference_id=decision.reference_id,
                                 reference_tag=decision.reference_tag.hex(), destination_bank=decision.destination_bank,
                                 source_banks=source_banks, admitted=decision.accepted, info=rc.plain_info(decision),
                                 encode_started_ms=now, encode_done=False, encode_service_ms=duration,
                                 bytes=0 if decision.packet is None else len(decision.packet),
                                 packet=decision.packet, candidate=decision, committed=False, feed_errors=[], feedback_owned=0,
                                 packetize_owned=False, wire_owned=False, feed_owned=False,
                                 qspi_owned=False, decode_owned=False)
                        rows[frame] = r
                        # Candidate is private/uncommitted until build_done
                        # and causal transport admission. No expected oracle yet.
                        encode_job = frame; event(now+duration, 'encode_done', frame); changed = True

    while events:
        at, _, _, kind, value = heapq.heappop(events)
        if at > horizon+1e-8:break
        if waiting is not None and at > now:
            frame = waiting
            reason = ('encoder_busy' if encode_job is not None else 'mutation_busy' if mutation_job is not None else
                      'reference_drain' if enc.pending and cfg.promotion_period > 0 and last_store is not None and frame-last_store >= cfg.promotion_period else
                      'key_or_promotion_ack' if any(p['key'] or p['promoted'] for p in enc.pending.values()) else
                      'credit_limit' if len(enc.pending) >= cfg.window else 'other')
            if cfg.reference_policy=='overlap' and reason not in ('encoder_busy','mutation_busy'):
                key_due = enc.banks[0] is None or (cfg.refresh_period>0 and last_key is not None and frame-last_key>=cfg.refresh_period)
                reason = ('key_drain_or_ack' if key_due else
                          'credit_limit' if len(enc.pending)>=cfg.window else 'other')
            waits.append(dict(id=frame, reason=reason, start_ms=now, done_ms=at, duration_ms=at-now))
        now = at
        if kind == 'capture':
            if latest_raw is not None: drop(latest_raw, 'resize_latest_replaced')
            latest_raw = value
        elif kind == 'resize_done':
            assert resize_job is value; resize_job = None
            frame, image, rect = value
            if waiting is not None: drop(waiting, 'latest_replaced'); scaled.pop(waiting, None)
            waiting = frame; scaled[frame] = image; rects[frame] = rect
        elif kind in ('encode_done','candidate_admit'):
            assert encode_job==value;r=rows[value];c=r['candidate']
            if kind=='encode_done':r['build_done_ms']=now
            if mutation_job is not None:
                r['candidate_waiting']=True;r.setdefault('candidate_wait_since_ms',now);pump();continue
            r['candidate_waiting']=False;r['candidate_wait_ms']=now-r.get('candidate_wait_since_ms',now);encode_job=None
            n=math.ceil(r['bytes']/transport.PAYLOAD) if c.accepted else 0
            # Only current body size, measured age and declared service/backlog
            # allowances enter admission. No receiver queues/pixels/future data.
            wire_bytes=r['bytes']+n*(transport.HEADER.size+gateway.TOKEN.size+28)
            wire_ms=(gw.queued_bytes()+wire_bytes)*8/(cfg.link_mbps*1000)
            if gw.wire_busy:wire_ms+=max(0,gw.wire[-1]['done_ms']-now)
            cost=gw.cost
            esp_ms=sum(sum(gateway.frozen.packet_service_us(transport.HEADER.size+min(transport.PAYLOAD,r['bytes']-i*transport.PAYLOAD),i,cost)[k]
                           for k in ('cpu_us','poll_us','dma_blocking_us'))/1000 for i in range(n))
            credit_ms=math.ceil(n/6)*cfg.feedback_latency_ms
            estimate=now-capture_times[value]+max(wire_ms,max(0,n-1)*cfg.pacing_ms)+esp_ms+credit_ms+cfg.aggregate_ms+cfg.decode_allowance_ms
            r['admission_estimate_age_ms']=estimate
            reason='cap_rejected' if not c.accepted else 'admission_rejected' if cfg.admission_enabled and estimate>cfg.admission_age_ms else None
            if reason is None:
                def commit():
                    try:return enc.commit(c),None
                    except ValueError as e:return None,str(e)
                (decision,error),charge=timed('candidate_commit',value,commit)
                if error is not None:
                    r['commit_error']=error;reason='stale_candidate'
                else:
                    r['admitted']=True;r['committed']=True;r['info']=decision.info
                    r['expected']=enc.expected_hash(value);r['expected_base']=enc.expected_base_hash(value)
                    r['packet_sha256']=hashlib.sha256(decision.packet).hexdigest();r['route_crc']=enc.pending[value]['body_crc']
                    r['candidate']=None;r['commit_done_ms']=charge['done_ms'];r['commit_service_ms']=charge['wall_ms'];r['encode_service_ms']+=charge['wall_ms']
                    encode_job=value;event(charge['done_ms'],'candidate_commit_done',value)
            if reason is not None:
                r['admitted']=False;r['rejection_reason']=reason
                _,charge=timed('candidate_discard',value,lambda:enc.discard(c))
                r['candidate']=None;r['discard_service_ms']=charge['wall_ms'];r['encode_service_ms']+=charge['wall_ms'];encode_job=value;event(charge['done_ms'],'candidate_discard_done',value)
            c=None
        elif kind == 'candidate_discard_done':
            assert encode_job==value;encode_job=None;r=rows[value];r['encode_done']=True;r['encode_done_ms']=now
            drop(value,r['rejection_reason']);release(value,r['rejection_reason'])
        elif kind == 'candidate_commit_done':
            assert encode_job==value;encode_job=None;r=rows[value];r['encode_done']=True;r['encode_done_ms']=now
            if now-capture_times[value]>cfg.decode_age_ms:
                drop(value,'deadline_after_commit');request_expiry(value,'deadline_after_commit')
            else:r['packetize_owned']=True;q_packetize.append(value)
        elif kind == 'packetize_done':
            assert packetize_job == value; packetize_job = None; r = rows[value]
            r['packetize_owned'] = False; r['wire_owned'] = True; q_wire.append(value)
            r['send_started_ms']=now;event(now+cfg.ack_timeout_ms,'ack_timeout',value)
        elif kind.startswith('gw_'):
            response=gw.step(kind,value,now)
            if response is not None:
                if response[0]=='af':q_parse.append(response[1])
                else:
                    assert response[0]=='af_lost';rows[response[1][0]]['feedback_owned']-=1
        elif kind == 'decode_begin_done':
            assert decode_job is value
            frame, free = value; r = rows[frame]
            if r['task'] is None:
                ingress.reject(r['complete']); r['decode_owned'] = False; fb[free]['roles'].clear()
                decode_job = None; drop(frame, 'decode_rejected'); nack_from_route(frame)
            elif r.get('expiry_requested') or now-capture_times[frame] > cfg.decode_age_ms:
                _, charge = timed('decode_abort', frame, lambda: rx.abort(r['task']))
                event(charge['done_ms'], 'decode_abort_done', value)
            else:
                before = receiver_semantics()
                output, charge = timed('decode_complete', frame, lambda: rx.complete(r['task']))
                r['staged_receiver_after'] = receiver_semantics()
                restore_receiver(before)
                r['output'] = output; event(charge['done_ms'], 'decode_complete_done', value)
        elif kind == 'decode_abort_done':
            assert decode_job is value; decode_job = None
            frame,free=value; r=rows[frame]
            ingress.reject(r['complete']); r['decode_owned']=False
            r['abort_done_ms']=now; r['read_pin_release_ms']=now
            r.pop('task',None); fb[free]['roles'].clear()
            drop(frame,'deadline_after_decode_work'); nack_from_route(frame)
        elif kind == 'decode_complete_done':
            assert decode_job is value
            frame, free = value; r = rows[frame]
            if r.get('expiry_requested') or now-capture_times[frame] > cfg.decode_age_ms:
                # Completion work was paid, but its future reference is not
                # published when a deadline/expiry intervenes during that work.
                r.pop('output'); r.pop('staged_receiver_after')
                _,charge=timed('decode_abort',frame,lambda:rx.abort(r['task']))
                event(charge['done_ms'],'decode_abort_done',value)
                pump()
                continue
            decode_job = None
            restore_receiver(r.pop('staged_receiver_after'))
            rgb, info, ack = r.pop('output'); r.pop('task', None)
            assert digest(rgb) == r['expected']
            assert info['base_rgb_sha256'] == r['expected_base']
            assert ingress.pending[frame].get('complete') is r['complete']
            ingress.commit(r['complete']); r['decode_owned'] = False
            r['decode_done_ms'] = now; r['read_pin_release_ms'] = now
            r['receiver_banks_after'] = banks(rx)
            publications.append(dict(id=frame, at_ms=now, key=r['key'], promoted=r['promoted'], banks=banks(rx)))
            mse = corpus.metrics(scaled[frame], rgb, rects[frame])['active']['mse']
            mse565 = corpus.metrics(corpus.expand565(corpus.rgb565(scaled[frame])),
                                    corpus.expand565(corpus.rgb565(rgb)),rects[frame])['active']['mse']
            original_words=corpus.rgb565(scaled[frame]);display_words=corpus.rgb565(rgb)
            selected_exact_pixels=0;selected_mismatches=0
            for patch in info['patches']:
                x,y,w,h=patch['rect'];selected_exact_pixels+=w*h
                selected_mismatches+=int(np.count_nonzero(original_words[y:y+h,x:x+w]!=display_words[y:y+h,x:x+w]))
            assert selected_mismatches==0
            commits.append(dict(id=frame, at_ms=now, rgb_sha256=digest(rgb), active_rgb888_mse=mse,
                                active_rgb565_mse=mse565,
                                base_rgb_sha256=info['base_rgb_sha256'],selected_exact_pixels=selected_exact_pixels,
                                selected_ui_mismatches=selected_mismatches,
                                reference_bank=r['reference_bank'], reference_id=r['reference_id'], info=info))
            if now-capture_times[frame] > cfg.decode_age_ms or r.get('expiry_requested'):
                fb[free]['roles'].clear(); drop(frame, 'deadline_at_decode_completion')
            else:
                if pending_display is not None:
                    old = fb[pending_display]['id']; drop(old, 'superseded_before_vblank'); fb[pending_display]['roles'].clear()
                fb[free]['roles'] = {'pending'}; pending_display = free
            if cfg.drop_first_refresh_ack and r['refresh_key'] and not lost_refresh_ack:
                lost_refresh_ack = True; r['fault_refresh_ack_lost'] = True
                r['lose_af_on_wire']=True;queue_feedback(frame,ack)
                feedback_rows.append(dict(kind='lost_refresh', id=frame, at_ms=now, bytes=len(ack)))
            elif cfg.drop_first_promotion_ack and r['promoted'] and not lost_promotion_ack:
                lost_promotion_ack = True; r['fault_promotion_ack_lost'] = True
                r['lose_af_on_wire']=True;queue_feedback(frame,ack)
                feedback_rows.append(dict(kind='lost', id=frame, at_ms=now, bytes=len(ack)))
            else:
                queue_feedback(frame, ack)
                if cfg.conflict_first_promotion_feedback and r['promoted'] and not conflicting_promotion:
                    conflicting_promotion = True
                    if sum(p.get('feedback_owned',0) for p in rows.values()) < 4:
                        nack, charge = timed('conflict_nack_build',frame,lambda: rc.feedback(rc.identity(r['packet']),rc.NACK))
                        r['feedback_owned'] += 1; event(charge['done_ms'], 'nack_ready', (frame,nack))
        elif kind == 'nack_ready':
            frame, data = value; q_feedback.append((frame,data))
        elif kind == 'feedback_wire_done':
            assert feedback_job is value; feedback_job = None
            event(now+cfg.feedback_latency_ms, 'feedback_arrived', value)
        elif kind == 'feedback_arrived':
            q_parse.append(value)
        elif kind == 'feedback_parsed':
            assert parse_job is value; parse_job = None
            frame, data, parsed, error = value; r = rows[frame]; r['feedback_owned'] -= 1
            valid = (error is None and parsed['epoch'] == 1 and parsed['frame_id'] == frame
                     and parsed['body_crc'] == r['route_crc'])
            accepted = False
            if valid and r.get('released_ms') is None and not r.get('expiry_requested'):
                # Full AF03 publication fields are checked again by Encoder.ack
                # only after every physical owner drains, before any bank use.
                if parsed['status'] == rc.NACK: request_expiry(frame, 'receiver_nack')
                else: r['ack_waiting'] = data
                accepted = True
            feedback_rows.append(dict(kind='parsed', id=frame, at_ms=now, accepted=accepted,
                                      status=None if parsed is None else parsed['status'], sender_banks=banks(enc)))
        elif kind == 'ack_timeout':
            r = rows[value]
            if r.get('released_ms') is None: request_expiry(value, 'ack_timeout')
        elif kind == 'mutation_done':
            assert mutation_job is value; mutation_job = None
            frame, action, reason = value; r = rows[frame]
            if action == 'ack':
                if r.get('expiry_requested'):
                    r.pop('staged_ack_after')
                    feedback_rows.append(dict(kind='ack_discarded_after_expiry',id=frame,at_ms=now,sender_banks=banks(enc)))
                    # Pending state is still reserved; the next pump pays
                    # expiry and releases only after all physical owners drain.
                    if encode_job is not None and rows[encode_job].get('candidate_waiting'):event(now,'candidate_admit',encode_job)
                    pump()
                    continue
                restore_encoder(r.pop('staged_ack_after'))
                if r['key']: last_key = last_store = frame
                elif r['promoted']: last_store = frame
                feedback_rows.append(dict(kind='ack_applied', id=frame, at_ms=now, sender_banks=banks(enc)))
            elif action == 'expire':
                drop(frame, reason)
                feedback_rows.append(dict(kind='expired',id=frame,at_ms=now,sender_banks=banks(enc)))
            else:
                r.pop('staged_ack_after',None)
                feedback_rows.append(dict(kind='invalid_ack',id=frame,at_ms=now,sender_banks=banks(enc)))
            if action != 'invalid_ack': release(frame, reason)
            if encode_job is not None and rows[encode_job].get('candidate_waiting'):event(now,'candidate_admit',encode_job)
        elif kind == 'ingress_tick':
            for frame in ingress.expire(now):
                if frame in rows and rows[frame].get('released_ms') is None:
                    rows[frame]['partial_ingress_expired_ms']=now
                    if rows[frame].get('receiver_route') is not None:nack_from_route(frame)
        elif kind == 'vblank':
            if pending_display is not None:
                fb[front]['roles'].discard('front'); front = pending_display; pending_display = None
                frame = fb[front]['id']; fb[front]['roles'] = {'front'}
                if frame not in outcomes:
                    outcomes[frame] = 'presented'; presented.append(dict(id=frame,at_ms=now,age_ms=now-capture_times[frame]))
        else: raise AssertionError(kind)
        pump()
        peak_sender=max(peak_sender,sum(x is not None for x in slots)); peak_pending=max(peak_pending,len(enc.pending))
        peak_ingress=max(peak_ingress,len(ingress.pending)); peak_fb=max(peak_fb,sum(bool(b['roles']) for b in fb))
        peak_feedback=max(peak_feedback,sum(r.get('feedback_owned',0) for r in rows.values()))
        assert peak_sender<=cfg.window and peak_pending<=cfg.window and peak_ingress<=2 and peak_fb<=3 and peak_feedback<=4
        assert all(sum(b is not None for b in obj.banks.values())<=2 for obj in (enc,rx))
    unresolved = sorted(set(range(len(frames)))-set(outcomes))
    steady=(500,end-500) if end>1000 else None
    rate=None if steady is None else sum(steady[0]<=p['at_ms']<steady[1] for p in presented)*1000/(steady[1]-steady[0])
    private={'packet','chunks','complete','task','expected','expected_base','ack_waiting','output','staged_ack_after','staged_receiver_after','candidate'}
    public=[{k:v for k,v in r.items() if k not in private} for r in rows.values()]
    return dict(config=asdict(cfg),capture_count=len(frames),capture_window_ms=[0,end],
                steady_window_ms=steady,diagnostic_ids_per_second=rate,
                presented_strict=sum(p['at_ms']<end for p in presented),presented_eventual=len(presented),
                presented=presented,drops=drops,drops_by_reason=dict(Counter(d['reason'] for d in drops)),
                prepared=len(rows),packets=public,commits=commits,work=work,wire=wire,feedback=feedback_rows,
                publications=publications,admission_wait_ms={s:sum(w['duration_ms'] for w in waits if w['reason']==s) for s in set(w['reason'] for w in waits)},
                unresolved_ids=unresolved,unresolved_candidate=enc.active_candidate is not None,unresolved_candidate_readers=enc.readers,
                gateway=dict(peak_mailbox=gw.peak_mailbox,peak_tokens=gw.peak_tokens,peak_control=gw.peak_control,peak_fifo=gw.peak_fifo,
                    outstanding_tokens=sum(t is not None for t in gw.tokens),control_outstanding=gw.control is not None,
                    queued_frames=len(gw.pending),counters=dict(gw.counter),wire=gw.wire,credits=gw.credit_rows),unresolved_sender_slots=slots,unresolved_encoder_pending=sorted(enc.pending),
                unresolved_ingress=sorted(ingress.pending),unresolved_receiver_readers=rx.readers,
                unresolved_decode=rx.active is not None,peak_sender=peak_sender,peak_pending=peak_pending,
                peak_ingress=peak_ingress,peak_framebuffers=peak_fb,peak_feedback=peak_feedback,
                sender_banks_final=banks(enc),receiver_banks_final=banks(rx),
                sender_peak_reference_array_bytes=enc.peak_retained_array_bytes,
                receiver_peak_reference_array_bytes=rx.peak_retained_array_bytes,
                forward_ipv4_udp_bytes=sum(w['bytes'] for w in gw.wire),
                reverse_ipv4_udp_bytes=sum(w['bytes'] for w in feedback_rows if w['kind']=='wire'),
                python_wall_seconds=time.perf_counter()-started_wall,
                scope='ActualAR03build/admit/commit/discard,GF03wrappedpacketcredits,realreassemblyanddecodedAF03publication;measuredPythonwork+assumedESP/wire/FIFO/vblank;noFPGAline/nativeCPU/hardwareproof')
