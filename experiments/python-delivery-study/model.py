"""Finite ownership/event model, not ESP32 execution, RTL or RF simulation."""
from __future__ import annotations
import collections
import dataclasses
import heapq
import math
import random


@dataclasses.dataclass
class Config:
    fps: float = 30
    link_mbps: float = 8
    qspi_mbps: float = 160
    encode_ms: float = 2
    decode_ms: float = 8
    refresh_hz: float = 60
    phase_ms: float = 0
    ready_jitter_ms: float = 0
    seed: int = 20261103
    compressed_slots: int = 2
    frame_cap: int = 49152
    framebuffers: int = 3
    max_age_before_send_ms: float = 100
    drain_ms: float = 2000
    steady_start_ms: float = 5000
    steady_end_ms: float = 55000
    link_stalls: tuple[tuple[float, float], ...] = ()
    loss_ids: tuple[int, ...] = ()


def wire_bytes(size):
    return size + math.ceil(size / 1024) * 68


def in_window(time, start, end):
    return start <= time < end - 1e-8


def percentile(values, fraction):
    return sorted(values)[math.ceil(fraction*len(values))-1] if values else None


def _validate(cfg, sizes, references):
    positive = (cfg.fps, cfg.link_mbps, cfg.qspi_mbps, cfg.refresh_hz)
    nonnegative = (cfg.encode_ms, cfg.decode_ms, cfg.phase_ms, cfg.ready_jitter_ms,
                   cfg.max_age_before_send_ms, cfg.drain_ms, cfg.steady_start_ms)
    if any(not math.isfinite(x) or x <= 0 for x in positive):
        raise ValueError('positive finite rates required')
    if any(not math.isfinite(x) or x < 0 for x in nonnegative):
        raise ValueError('nonnegative finite durations required')
    if not math.isfinite(cfg.steady_end_ms) or cfg.steady_end_ms <= cfg.steady_start_ms:
        raise ValueError('invalid predeclared steady window')
    if (type(cfg.compressed_slots) is not int or cfg.compressed_slots < 1 or
            type(cfg.frame_cap) is not int or cfg.frame_cap < 1 or
            type(cfg.framebuffers) is not int or cfg.framebuffers < 2):
        raise ValueError('invalid finite storage')
    if not sizes or any(type(x) is not int or x <= 0 for x in sizes):
        raise ValueError('nonempty positive integer sizes required')
    previous = -math.inf
    for start, end in cfg.link_stalls:
        if not math.isfinite(start) or not math.isfinite(end) or start < 0 or end <= start or start < previous:
            raise ValueError('stalls must be sorted nonoverlapping intervals')
        previous = end
    if any(type(i) is not int or not 0 <= i < len(sizes) for i in cfg.loss_ids):
        raise ValueError('invalid loss IDs')
    if references is not None and (len(references) != len(sizes) or any(
            ref is not None and (type(ref) is not int or not 0 <= ref < i)
            for i, ref in enumerate(references))):
        raise ValueError('invalid preceding reference IDs')


def link_finish(start, duration, stalls):
    """Deliver duration of link service while preserving every configured pause."""
    now, remaining = start, duration
    for low, high in stalls:
        if high <= now:
            continue
        if low > now:
            available = low-now
            if remaining <= available:
                return now+remaining
            remaining -= available
            now = low
        now = max(now, high)
    return now+remaining


def simulate(frame_sizes, cfg=None, references=None):
    cfg = cfg or Config()
    sizes = list(frame_sizes)
    references = None if references is None else list(references)
    _validate(cfg, sizes, references)
    temporal = references is not None
    references = references if temporal else [None]*len(sizes)
    window_end = len(sizes)*1000/cfg.fps
    horizon = window_end + cfg.drain_ms
    events, serial = [], 0
    def event(at, kind, payload=None):
        nonlocal serial
        serial += 1
        priority = 1 if kind == 'vblank' else (2 if kind == 'capture' else 0)
        heapq.heappush(events, (at, priority, serial, kind, payload))
    rng = random.Random(cfg.seed)
    captures = [cfg.phase_ms+i*1000/cfg.fps for i in range(len(sizes))]
    for i, capture in enumerate(captures):
        event(capture, 'capture', i)
        event(capture+cfg.encode_ms+rng.uniform(0, cfg.ready_jitter_ms), 'ready', i)
    for i in range(math.floor(horizon*cfg.refresh_hz/1000)+1):
        event(i*1000/cfg.refresh_hz, 'vblank')
    slot_owner = [None]*cfg.compressed_slots
    slot_state = [None]*cfg.compressed_slots
    buffers = [{'owner': None, 'roles': set()} for _ in range(cfg.framebuffers)]
    buffers[0] = {'owner': -1, 'roles': {'front'}}
    front, pending, ref_buffer = 0, None, None
    waiting, network, qspi, decoder = None, None, None, None
    qspi_wait, decode_wait = collections.deque(), collections.deque()
    last_started, last_reference = -1, None
    now = 0.
    drops, decoded, presented, allocations = [], [], [], []
    max_slots = max_buffers = max_qspi_wait = max_decode_wait = max_host_wait = 0
    total_wire = 0
    capture_count = sent_count = 0

    def drop(frame, reason):
        drops.append({'id': frame, 'reason': reason, 'at_ms': now})

    def release_slot(slot):
        assert slot_owner[slot] is not None
        allocations.append({'at_ms': now, 'kind': 'slot_release', 'slot': slot, 'id': slot_owner[slot]})
        slot_owner[slot] = slot_state[slot] = None

    def pump():
        nonlocal waiting, network, qspi, decoder, last_started, total_wire, sent_count
        changed = True
        while changed:
            changed = False
            if decoder is None and decode_wait:
                slot = decode_wait[0]
                frame = slot_owner[slot]
                required = references[frame]
                if frame <= (last_reference if last_reference is not None else -1):
                    decode_wait.popleft(); drop(frame, 'stale_frame'); release_slot(slot); changed = True
                elif required is not None and required != last_reference:
                    decode_wait.popleft(); drop(frame, 'missing_reference'); release_slot(slot); changed = True
                else:
                    free = next((i for i, b in enumerate(buffers) if not b['roles']), None)
                    if free is not None:
                        decode_wait.popleft()
                        assert not buffers[free]['roles']
                        buffers[free] = {'owner': frame, 'roles': {'decoding'}}
                        if temporal and required is not None:
                            assert ref_buffer is not None and buffers[ref_buffer]['owner'] == required
                            buffers[ref_buffer]['roles'].add('read_pin')
                        decoder = (slot, free, ref_buffer if required is not None else None)
                        slot_state[slot] = 'decode'
                        event(now+cfg.decode_ms, 'decoded', decoder)
                        changed = True
            if qspi is None and qspi_wait:
                slot = qspi_wait.popleft()
                qspi = slot
                slot_state[slot] = 'qspi'
                event(now+sizes[slot_owner[slot]]*8/(cfg.qspi_mbps*1000), 'qspi_done', slot)
                changed = True
            if network is None and waiting is not None:
                frame = waiting
                if now-captures[frame] > cfg.max_age_before_send_ms:
                    waiting = None; drop(frame, 'stale_before_send'); changed = True
                else:
                    slot = next((i for i, owner in enumerate(slot_owner) if owner is None), None)
                    if slot is not None:
                        waiting = None
                        assert slot_owner[slot] is None
                        slot_owner[slot], slot_state[slot] = frame, 'network'
                        allocations.append({'at_ms': now, 'kind': 'slot_acquire', 'slot': slot, 'id': frame})
                        network, last_started = slot, frame
                        amount = wire_bytes(sizes[frame]); total_wire += amount; sent_count += 1
                        event(link_finish(now, amount*8/(cfg.link_mbps*1000), cfg.link_stalls), 'network_done', slot)
                        changed = True

    while events:
        at, _, _, kind, item = heapq.heappop(events)
        if at > horizon+1e-8:
            break
        assert at >= now-1e-8
        now = at
        if kind == 'capture':
            capture_count += 1
        elif kind == 'ready':
            frame = item
            if sizes[frame] > cfg.frame_cap:
                drop(frame, 'cap')
            elif frame <= last_started or (waiting is not None and frame <= waiting):
                drop(frame, 'stale_ready')
            else:
                if waiting is not None:
                    drop(waiting, 'host_latest_replaced')
                waiting = frame
                max_host_wait = max(max_host_wait, 1)
        elif kind == 'network_done':
            assert network == item and slot_state[item] == 'network'
            network = None
            if slot_owner[item] in cfg.loss_ids:
                drop(slot_owner[item], 'network_loss'); release_slot(item)
            else:
                slot_state[item] = 'qspi_wait'; qspi_wait.append(item)
        elif kind == 'qspi_done':
            assert qspi == item and slot_state[item] == 'qspi'
            qspi = None
            slot_state[item] = 'decode_wait'; decode_wait.append(item)
        elif kind == 'decoded':
            assert decoder == item
            slot, back, pin = item
            frame = slot_owner[slot]
            if pin is not None:
                buffers[pin]['roles'].remove('read_pin')
            buffers[back]['roles'].remove('decoding')
            if temporal:
                if ref_buffer is not None:
                    buffers[ref_buffer]['roles'].remove('reference')
                ref_buffer = back; buffers[back]['roles'].add('reference')
            if pending is not None:
                old = buffers[pending]['owner']
                buffers[pending]['roles'].remove('pending')
                drop(old, 'pending_superseded')
            pending = back; buffers[back]['roles'].add('pending')
            last_reference = frame
            decoded.append({'id': frame, 'at_ms': now, 'capture_ms': captures[frame]})
            release_slot(slot); decoder = None
        elif kind == 'vblank' and pending is not None:
            buffers[front]['roles'].remove('front')
            front = pending; pending = None
            buffers[front]['roles'].remove('pending'); buffers[front]['roles'].add('front')
            frame = buffers[front]['owner']
            presented.append({'id': frame, 'at_ms': now, 'capture_ms': captures[frame],
                              'age_ms': now-captures[frame]})
        pump()
        # Roles are the reuse contract, not arbitrary timestamp guesses.
        assert sum('front' in b['roles'] for b in buffers) == 1
        assert sum('decoding' in b['roles'] for b in buffers) <= 1
        assert sum('pending' in b['roles'] for b in buffers) <= 1
        assert len(set(x for x in slot_owner if x is not None)) == sum(x is not None for x in slot_owner)
        assert all(owner is not None or state is None for owner, state in zip(slot_owner, slot_state))
        max_slots = max(max_slots, sum(x is not None for x in slot_owner))
        max_buffers = max(max_buffers, sum(bool(b['roles']) for b in buffers))
        max_qspi_wait = max(max_qspi_wait, len(qspi_wait))
        max_decode_wait = max(max_decode_wait, len(decode_wait))

    strict = [r for r in presented if in_window(r['at_ms'], 0, window_end)]
    steady = [r for r in presented if in_window(r['at_ms'], cfg.steady_start_ms, cfg.steady_end_ms)]
    gaps = [b['at_ms']-a['at_ms'] for a, b in zip(steady, steady[1:])]
    steady_ids = [r['id'] for r in steady]
    assert len(set(r['id'] for r in presented)) == len(presented)
    assert [r['id'] for r in presented] == sorted(r['id'] for r in presented)
    presented_set = {r['id'] for r in presented}
    dropped_set = {r['id'] for r in drops}
    assert len(dropped_set) == len(drops)
    assert not presented_set.intersection(dropped_set)
    unresolved = sorted(set(range(len(sizes))) - presented_set - dropped_set)
    occupancy = {'compressed_slots': max_slots, 'framebuffers': max_buffers,
                 'qspi_wait': max_qspi_wait, 'decode_wait': max_decode_wait,
                 'host_waiting': max_host_wait}
    return {'config': dataclasses.asdict(cfg), 'input_frames': len(sizes), 'captured_by_horizon': capture_count,
            'transmitted': sent_count, 'wire_bytes': total_wire,
            'decoded': len(decoded), 'presented_strict': len(strict), 'presented_after_drain': len(presented),
            'capture_window_ms': [0, window_end], 'window_kind': '[start,end)',
            'steady_window_ms': [cfg.steady_start_ms, cfg.steady_end_ms],
            'steady_count': len(steady), 'steady_fps': len(steady)*1000/(cfg.steady_end_ms-cfg.steady_start_ms),
            'steady_age_ms': {'p50': percentile([r['age_ms'] for r in steady], .5),
                              'p95': percentile([r['age_ms'] for r in steady], .95),
                              'max': max((r['age_ms'] for r in steady), default=None)},
            'steady_gap_ms': {'p95': percentile(gaps, .95), 'max': max(gaps, default=None)},
            'steady_skipped_ids': sum(b-a-1 for a, b in zip(steady_ids, steady_ids[1:])),
            'drops_by_reason': dict(collections.Counter(r['reason'] for r in drops)),
            'peak_occupancy': occupancy, 'slots_at_end': slot_owner,
            'unresolved_ids_at_horizon': unresolved,
            'pending_host_at_end': waiting, 'buffers_at_end': [{'owner': b['owner'], 'roles': sorted(b['roles'])} for b in buffers],
            'presented': presented, 'decoded_events': decoded, 'drops': drops,
            'allocation_events': allocations,
            'scope': 'finite ownership/timing scenario; no data/RTL/physical memory/RF proof'}
