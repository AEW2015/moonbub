"""Deterministic ideal link/queue model; no ESP32 execution or RF simulation."""
import math


def wire_bytes(size, payload=1024, application_header=40):
    """Hypothetical/MSV1-sized IPv4 UDP accounting; excludes Ethernet/Wi-Fi."""
    if size <= 0 or payload <= 0 or application_header < 0:
        raise ValueError('invalid packet bounds')
    return size + math.ceil(size / payload) * (application_header + 28)


def simulate(sizes, *, fps=30, link_mbps=8, qspi_mbps=160, decode_ms=8,
             refresh_hz=60, phase_ms=0, cap=49152, policy='latest', references=None):
    """Single nonpreemptive transmitter, one waiting slot or FIFO control.

    Only the latest-policy transmitter waiting queue is bounded. QSPI/decode
    stages have unbounded abstract queues, serialize within each stage, and
    overlap other stages; this is not receiver storage/backpressure proof.
    Capture times are scheduled inputs, not measured encode completion.

    references[i] is None for an independent frame or the exact prior frame
    index required for reconstruction. A transmitted frame with an unavailable
    reference still incurs network and QSPI costs, but is rejected before
    decoding. The one owned reconstructed reference advances after a successful
    decode, independently of presentation. Independent frames recover a chain.

    Each decoded frame first becomes eligible at its next vblank. If several
    share that vblank, only the newest decoded frame is presented. Presentation
    and strict-window counts include these winners, not superseded candidates.
    Strict window is [0, len(sizes)/fps), deliberately excluding phase offset.
    """
    if (not all(math.isfinite(x) for x in (fps, link_mbps, qspi_mbps, decode_ms, refresh_hz, phase_ms))
            or fps <= 0 or link_mbps <= 0 or qspi_mbps <= 0 or decode_ms < 0
            or refresh_hz <= 0 or cap <= 0 or phase_ms < 0 or policy not in ('latest', 'fifo')):
        raise ValueError('invalid model parameters')
    sizes = list(sizes)
    if any(type(n) is not int or n <= 0 for n in sizes):
        raise ValueError('invalid frame size')
    if references is None:
        references = [None]*len(sizes)
    else:
        references = list(references)
        if len(references) != len(sizes) or any(
                ref is not None and (type(ref) is not int or not 0 <= ref < i)
                for i,ref in enumerate(references)):
            raise ValueError('references must name a preceding frame or None')
    arrivals = [(phase_ms + i*1000/fps, i, n) for i, n in enumerate(sizes)]
    pending, records, drops, rejected = [], [], [], []
    cursor, now, qspi_free, decode_free = 0, 0., 0., 0.
    transmitted, last_reference = 0, None
    while cursor < len(arrivals) or pending:
        if not pending:
            now = max(now, arrivals[cursor][0])
        while cursor < len(arrivals) and arrivals[cursor][0] <= now + 1e-9:
            item = arrivals[cursor]
            cursor += 1
            if item[2] > cap:
                drops.append({'id': item[1], 'reason': 'cap'})
                continue
            if policy == 'latest' and pending:
                drops.extend({'id': old[1], 'reason': 'replaced'} for old in pending)
                pending.clear()
            pending.append(item)
        if not pending:
            continue
        capture, index, size = pending.pop(0)
        start = max(now, capture)
        end = start + wire_bytes(size)*8/(link_mbps*1000)
        qspi_end = max(end, qspi_free) + size*8/(qspi_mbps*1000)
        qspi_free = qspi_end
        transmitted += 1
        now = end
        # Commit checking occurs in receiver processing order, after previous
        # accepted decoding. Rejected entries cannot bypass queued prior work.
        receiver_ready = max(qspi_end, decode_free)
        required_reference = references[index]
        if required_reference is not None and required_reference != last_reference:
            rejected.append({'id': index, 'reason': 'missing_reference',
                             'required_reference': required_reference,
                             'last_valid_reference': last_reference,
                             'network_start_ms': start, 'qspi_end_ms': qspi_end,
                             'rejected_ms': receiver_ready})
            continue
        decoded = receiver_ready + decode_ms
        decode_free = decoded
        last_reference = index
        eligible = math.ceil((decoded-1e-10)*refresh_hz/1000)*1000/refresh_hz
        records.append({'id': index, 'capture_ms': capture, 'network_start_ms': start,
                        'qspi_end_ms': qspi_end, 'decoded_ms': decoded,
                        'eligible_vblank_ms': eligible,
                        'eligibility_age_ms': eligible-capture})
    winners = {}
    for row in records:
        winners[round(row['eligible_vblank_ms'], 8)] = row
    presented = sorted(winners.values(), key=lambda row: row['eligible_vblank_ms'])
    end_window = len(sizes)*1000/fps
    ages = sorted(row['eligibility_age_ms'] for row in presented)
    return {'input_count': len(sizes), 'transmitted': transmitted, 'decoded': len(records),
            'reference_rejected': len(rejected), 'rejected': rejected,
            'presented_eventual': len(presented),
            'presented_strict_window': sum(row['eligible_vblank_ms'] < end_window-1e-8 for row in presented),
            'window_end_ms': end_window, 'dropped': drops,
            'superseded_at_vblank': len(records)-len(presented),
            'max_age_ms': max(ages, default=None),
            'p95_age_ms': ages[math.ceil(.95*len(ages))-1] if ages else None,
            'records': records}
