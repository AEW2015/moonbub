#!/usr/bin/env python3
"""Independent scratch intent -> controller -> pins -> captured reply replay.

Keep the frozen video ownership oracle. Scratch uses the same PinOracle and
therefore the same command timing, open rows, actual DQ writes and read queue.
There is no alternate memory populated from logical scratch requests.
"""
import collections
import itertools
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'experiments/python-gamebub-v91l-shared-service'))
from memory_audit import Replay, need, numeric


def ordered_scratch(stream):
    priority = {'ownership': 0, 'mux_owner': 0, 'scratch_owner': 0,
                'wr_rsp_offer': 1, 'rd_rsp_offer': 1, 'ref_rsp_offer': 1,
                'scratch_rsp_offer': 1, 'kill': 2, 'scratch_kill': 2,
                'arbitrate': 3, 'mux_arbitrate': 3, 'scratch_arbitrate': 3,
                'reference_req': 4, 'ref_req': 5, 'ref_line_req': 6,
                'reference_line_req': 7, 'mux_req': 8, 'rd_req': 9,
                'rd_rsp': 10, 'mux_rsp': 11, 'ref_line_rsp': 12,
                'reference_line_rsp': 13, 'ref_rsp': 14, 'reference_rsp': 15,
                'scratch_live_req': 8, 'scratch_live_rsp': 8}
    for _, group in itertools.groupby((e for e in stream if 'time_ps' in e), key=lambda e: e['time_ps']):
        yield from sorted(group, key=lambda e: priority.get(e['type'], 9))


class ScratchReplay(Replay):
    def __init__(self, require_written_reads=False):
        super().__init__(require_written_reads)
        self.scratch = None
        self.scratch_completed = []
        self.scratch_counts = collections.Counter()
        self.scratch_pin_writes = self.scratch_pin_reads = self.scratch_captures = 0
        self.live_scratch = None
        self.live_counts = collections.Counter()
        self.line_epochs = {}
        self.outer_owner = 0
        self.outer_decision = None
        self.last_scratch = True
        self.outer_grants = collections.Counter()

    def feed(self, e):
        k = e['type']
        t = e.get('time_ps', self.time)
        need(t >= self.time, 'scratch receipts reverse time')
        if k.startswith('scratch_'):
            self.scratch_counts[k] += 1
            self.time = t
            self.scratch_event(e)
            return
        if k == 'ctrl_req' and e['owner'] == 3:
            a = self.scratch
            need(a is not None and a['valid'] and not a['killed'] and a['offered'] is None,
                 'scratch command lacks live valid logical owner')
            need(self.active is None, 'scratch command overlaps accepted video transaction')
            need(self.outer_owner == 2, 'scratch command outside physical arbiter grant')
            index = len(a['commands'])
            need(index < (8 if a['write'] else 1), 'scratch command credit overflow')
            base = 0xc00000 + (a['address'] >> 1)
            need(e['address'] == base + (index if a['write'] else 0) and e['write'] == a['write'],
                 'scratch physical command address/op differs')
            expected = (numeric(a['data']) >> (16 * index)) & 65535 if a['write'] else 0
            need(e['data'] == expected, 'scratch controller write word differs')
            a['commands'].append(dict(e, seen=False, pin_time=None))
            self.time = t
            return
        if k == 'pin' and e['command'] in (4, 5) and e['bank'] == 3:
            a = self.scratch
            need(a is not None and self.active is None, 'scratch pin command lacks exclusive logical owner')
            command = next((c for c in a['commands'] if not c['seen']), None)
            need(command is not None, 'scratch pin command lacks accepted controller request')
            row = self.pin.open_rows.get(3)
            need(row is not None, 'scratch pin column into closed row')
            address = (3 << 22) | (row << 9) | e['address']
            need(address == command['address'] and (e['command'] == 4) == bool(command['write']),
                 'scratch pin address/op differs from controller request')
            need(t > command['time_ps'], 'scratch pin command precedes controller acceptance')
            if e['command'] == 4:
                need(e['dq'] == command['data'], 'scratch pin DQ differs from accepted write')
                self.written.add(address)
                self.scratch_pin_writes += 1
            else:
                if self.require_written_reads:
                    need(all(address+i in self.written for i in range(8)),
                         'native scratch read includes words never physically written')
                self.scratch_pin_reads += 1
            command['seen'] = True
            command['pin_time'] = t
            self.pin.command(e)
            self.time = t
            return
        if k == 'controller_read' and e['owner'] == 3:
            a = self.scratch
            need(a is not None and not a['write'] and self.active is None,
                 'scratch capture routed to wrong logical owner')
            need(len(a['words']) < 8, 'scratch extra BL8 captured word')
            self.pin.controller_read(e)
            a['words'].append(e['data'])
            self.scratch_captures += 1
            self.time = t
            return
        if k in ('wr_req', 'rd_req'):
            need(self.outer_owner == 1 and self.scratch is None, 'video request outside physical arbiter grant')
        # The old video checker continues to see global ACT/PRE/REF/raw read
        # events. Its actual physical memory also contains the scratch writes.
        super().feed(e)

    def scratch_event(self, e):
        k, t = e['type'], e['time_ps']
        if k == 'scratch_arbitrate':
            need(self.outer_owner == 0 and self.active is None and self.scratch is None,
                 'physical arbiter selects over owned transaction')
            need(bool(e['last_scratch']) == self.last_scratch, 'physical arbiter fairness history differs')
            video, scratch = bool(e['video_offer']), bool(e['scratch_offer'])
            self.outer_decision = (1 if video and (not scratch or self.last_scratch) else 2) if video or scratch else None
        elif k == 'scratch_owner':
            need(e['old_owner'] == self.outer_owner and e['owner'] != self.outer_owner,
                 'physical arbiter owner history differs')
            owner = e['owner']
            need(owner in (0, 1, 2), 'invalid physical arbiter owner')
            if owner:
                need(self.outer_owner == 0 and owner == self.outer_decision,
                     'physical arbiter round-robin grant differs')
                self.last_scratch = owner == 2
                self.outer_grants[owner] += 1
                self.outer_decision = None
            else:
                need(self.active is None and self.scratch is None and self.owner == 0,
                     'physical arbiter releases before logical owner drain')
                need(not self.pin.reads and not self.pin.controller_reads, 'physical arbiter releases before read drain')
            self.outer_owner = owner
        elif k == 'scratch_live_req':
            need(self.live_scratch is None, 'native scratch request overwrites accepted owner')
            self.live_scratch = dict(e, request_seen=False, response_seen=False)
            self.live_counts['requests'] += 1
        elif k == 'scratch_live_rsp':
            a, live = self.scratch, self.live_scratch
            need(a is not None and live is not None and live['request_seen'] and not live['response_seen'],
                 'native scratch reply lacks matching physical request')
            need(all(e[key] == live[key] == a[key] for key in ('epoch', 'write', 'address')),
                 'native scratch reply identity differs')
            need(e['id'] == live['id'] == a['native_id'] and e['index'] == live['index'],
                 'native scratch reply source/index differs')
            need(e['error'] == 0 and a['offered'] is not None and not a['offered']['error'],
                 'native scratch reply not backed by successful physical offer')
            need(bytes.fromhex(e['data']) == numeric(a['offered']['data']).to_bytes(16, 'little'),
                 'native scratch reply bytes differ from physical capture')
            live['response_seen'] = True
            self.live_counts['responses'] += 1
        elif k == 'scratch_req':
            need(self.scratch is None and self.active is None, 'scratch logical request overlaps owner')
            need(self.outer_owner == 2, 'scratch request outside physical arbiter grant')
            address = e['address']
            valid = e['epoch'] != 0 and 0 <= address <= 262128 and address % 16 == 0
            self.scratch = dict(e, valid=valid, killed=False, commands=[], words=[], offered=None,
                                idle_count=0, last_idle=None, saw_busy=False)
            if self.require_written_reads:
                live = self.live_scratch
                need(live is not None and not live['request_seen'], 'physical scratch request lacks native handshake')
                need(all(live[key] == e[key] for key in ('epoch', 'write', 'address')) and
                     bytes.fromhex(live['data']) == numeric(e['data']).to_bytes(16, 'little'),
                     'native scratch request bytes/identity differ')
                live['request_seen'] = True
                self.scratch['native_id'] = live['id']
                if not e['write']:
                    need(self.line_epochs.get(address) == e['epoch'],
                         'native scratch read precedes matching-epoch full physical write ACK')
        elif k == 'scratch_kill':
            need(e.get('reset') or e.get('cancel'), 'scratch kill without reset/cancel')
            if self.scratch is not None and self.scratch['offered'] is None:
                self.scratch['killed'] = True
        elif k == 'scratch_fence':
            a = self.scratch
            if a is not None:
                if e['state'] == 2:
                    a['saw_busy'] = True
                if e['state'] in (3, 5):
                    if not a['write']:
                        need(len(a['words']) == 8 and e['beats'] == 8,
                             'scratch read drain before all eight captures')
                    if a['last_idle'] is not None:
                        need(t-a['last_idle'] == 10000, 'scratch idle drain samples not consecutive')
                    a['last_idle'] = t
                    a['idle_count'] = a['idle_count']+1 if e['controller_idle'] else 0
        elif k in ('scratch_rsp_offer', 'scratch_rsp'):
            a = self.scratch
            need(a is not None, 'scratch response lacks accepted owner')
            need(e['epoch'] == a['epoch'], 'scratch response epoch differs')
            offered = {key: e[key] for key in ('epoch', 'error', 'data')}
            if k.endswith('_offer'):
                need(a['offered'] is None, 'duplicate scratch response offer')
                need(e['error'] == int(not a['valid'] or a['killed']), 'scratch error disagrees with cancellation/rejection')
                need(all(c['seen'] for c in a['commands']), 'scratch response before commands reach pins')
                if not e['error']:
                    need(len(a['commands']) == (8 if a['write'] else 1), 'scratch success lacks full physical service')
                if a['commands']:
                    need(a['idle_count'] == 2 and a['last_idle'] is not None and t >= a['last_idle']+10000,
                         'scratch response before two idle drain samples')
                    if a['write']:
                        need(a['saw_busy'], 'scratch write response missed busy fence')
                        need(t-a['commands'][-1]['pin_time'] >= 41000, 'scratch response before write recovery')
                    else:
                        need(len(a['words']) == 8 and t-a['commands'][0]['pin_time'] >= 131000,
                             'scratch response before full BL8 recovery')
                value = 0 if a['write'] or e['error'] else sum(v << (16*i) for i, v in enumerate(a['words']))
                need(numeric(e['data']) == value, 'scratch held reply differs from physical captured words')
                a['offered'] = offered
            else:
                need(a['offered'] == offered, 'scratch held reply mutated before ACK')
                need(not self.pin.reads and not self.pin.controller_reads, 'scratch ACK before unbackpressured read drain')
                self.scratch_completed.append(dict(write=a['write'], address=a['address'], epoch=a['epoch'],
                    native_id=a.get('native_id'), error=e['error'], commands=len(a['commands']),
                    request_time_ps=a['time_ps'], ack_time_ps=t))
                if self.require_written_reads:
                    need(self.live_scratch is not None and self.live_scratch['response_seen'],
                         'physical scratch ACK missing native observer')
                    self.live_scratch = None
                if a['write'] and not e['error']:
                    self.line_epochs[a['address']] = a['epoch']
                self.scratch = None

    def finish(self):
        need(self.scratch is None and self.live_scratch is None, 'terminal scratch owner remains')
        need(self.outer_owner == 0, 'terminal physical arbiter grant remains')
        result = super().finish()
        def aggregate(key):
            grouped = {}
            for a in self.scratch_completed:
                group = str(a[key])
                stats = grouped.setdefault(group, dict(requests=0, responses=0, write_requests=0, read_requests=0,
                commands=0, max_address=0, first_request_ps=a['request_time_ps'], last_ack_ps=0,
                min_request_ack_ps=None, max_request_ack_ps=0, successful=0, errors=0))
                stats['requests'] += 1
                stats['responses'] += 1
                stats['write_requests' if a['write'] else 'read_requests'] += 1
                stats['commands'] += a['commands']
                stats['max_address'] = max(stats['max_address'], a['address'])
                stats['last_ack_ps'] = max(stats['last_ack_ps'], a['ack_time_ps'])
                latency = a['ack_time_ps']-a['request_time_ps']
                stats['min_request_ack_ps'] = latency if stats['min_request_ack_ps'] is None else min(stats['min_request_ack_ps'], latency)
                stats['max_request_ack_ps'] = max(stats['max_request_ack_ps'], latency)
                stats['successful' if not a['error'] else 'errors'] += 1
            return grouped
        result.update(scratch_transactions=len(self.scratch_completed),
                      scratch_writes=sum(bool(a['write']) for a in self.scratch_completed),
                      scratch_reads=sum(not a['write'] for a in self.scratch_completed),
                      scratch_pin_write_words=self.scratch_pin_writes,
                      scratch_pin_BL8_reads=self.scratch_pin_reads,
                      scratch_captured_words=self.scratch_captures,
                      physical_arbiter_grants=dict(self.outer_grants), native_scratch_observers=dict(self.live_counts),
                      scratch_by_child_epoch=aggregate('epoch'), scratch_by_native_id=aggregate('native_id'),
                      video_write_words=result['physical_write_words']-self.scratch_pin_writes,
                      video_captured_words=result['physical_captured_words']-self.scratch_captures)
        return result
