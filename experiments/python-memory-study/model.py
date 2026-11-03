#!/usr/bin/env python3
"""Deterministic memory-service what-if model; no electrical/RTL timing proof."""
from __future__ import annotations

import argparse
import collections
import dataclasses
import hashlib
import heapq
import json
import math
from pathlib import Path

CLOCK = 100_000_000
FRAME_BYTES = 720 * 480 * 2
BURST_BYTES = 16


@dataclasses.dataclass
class Config:
    storage: str = "sdram"
    policy: str = "strict_display"
    fps: int = 30
    scan_hz: float = 60.0
    frames: int = 15
    frame_sizes: tuple[int, ...] = (26991,)
    reference: bool = False
    frame_cap: int = 262144
    compressed_slots: int = 2
    refresh_period: int = 780
    refresh_cycles: int = 12
    quantum_bursts: int = 8
    memory_clock: int = CLOCK
    sram_cycles_per_word: int = 3
    line_words: int = 480
    scan_lines: int = 720
    line_deadline_scale: float = 1.0
    drain_frames: int = 8


@dataclasses.dataclass
class Job:
    client: str
    frame: int
    bursts: int
    address: int
    write: bool
    deadline: int | None = None
    total: int = 0
    submitted: int = 0


class SlotPool:
    """Generation-tagged model: a slot is reusable only after accepted I/O drains."""
    def __init__(self, slots: int, cap: int):
        if slots < 1 or cap < 1:
            raise ValueError("nonpositive pool")
        self.cap = cap
        self.states = [dict(generation=0, owner=None, outstanding=0, valid=False, length=0)
                       for _ in range(slots)]

    def acquire(self, owner: int, length: int):
        if not 0 < length <= self.cap:
            raise ValueError("frame outside negotiated cap")
        for index, state in enumerate(self.states):
            if state["owner"] is None:
                state.update(generation=state["generation"] + 1, owner=owner,
                             outstanding=0, valid=False, length=length)
                return index, state["generation"]
        return None

    def check(self, token, offset: int, count: int):
        index, generation = token
        if not 0 <= index < len(self.states):
            raise ValueError("slot index")
        state = self.states[index]
        if state["generation"] != generation or state["owner"] is None:
            raise ValueError("stale ownership")
        if count <= 0 or offset < 0 or offset + count > state["length"]:
            raise ValueError("range outside slot")
        return state

    def issue(self, token, offset: int, count: int):
        self.check(token, offset, count)["outstanding"] += 1

    def drain(self, token):
        state = self.check(token, 0, 1)
        if not state["outstanding"]:
            raise ValueError("unexpected completion")
        state["outstanding"] -= 1

    def commit(self, token, integrity_ok: bool):
        state = self.check(token, 0, 1)
        if state["outstanding"] or not integrity_ok:
            raise ValueError("commit before drain or failed integrity")
        state["valid"] = True

    def release(self, token):
        state = self.check(token, 0, 1)
        if state["outstanding"]:
            raise ValueError("reuse before drain")
        state.update(owner=None, valid=False)


def allocation_report():
    return dict(sram_bytes=524288, rgb565_frame_bytes=FRAME_BYTES,
                proposed_split_bytes=sum(x * 1024 for x in (256, 32, 128, 64, 32)),
                proposed_assembly_bytes=131072, negotiated_cap_bytes=262144,
                assembly_supports_cap=False,
                two_224k_slots_plus_meta_reserve_bytes=2 * 224 * 1024 + 65536,
                two_256k_slots_remaining_metadata_bytes=0,
                yuv420_frame_bytes=518400, yuv420_remaining_bytes=5888)


def percentile(values, percent):
    if not values:
        return None
    values = sorted(values)
    return values[min(len(values) - 1, math.ceil(percent * len(values)) - 1)]


def within_window(cycle, end):
    """Half-open observation window: work at the exact endpoint is excluded."""
    return 0 <= cycle < end


def simulate(cfg: Config):
    if cfg.storage not in ("bram", "sdram", "sram"):
        raise ValueError("storage")
    if cfg.policy not in ("strict_display", "deadline_rr"):
        raise ValueError("policy")
    if cfg.fps <= 0 or cfg.scan_hz <= 0 or cfg.frames < 1 or cfg.quantum_bursts < 1:
        raise ValueError("nonpositive rate/count")
    if (cfg.memory_clock <= 0 or cfg.line_words <= 0 or cfg.scan_lines <= 0 or
            cfg.sram_cycles_per_word < 0 or cfg.frame_cap <= 0 or cfg.drain_frames < 0 or
            cfg.line_deadline_scale <= 0):
        raise ValueError("invalid geometry, clock, capacity, service or deadline")
    if not cfg.frame_sizes or any(type(size) is not int or size <= 0 for size in cfg.frame_sizes):
        raise ValueError("frame sizes must be positive integers")
    if cfg.refresh_period <= cfg.refresh_cycles or cfg.refresh_cycles < 0:
        raise ValueError("refresh parameters")
    cap = min(cfg.frame_cap, 49152) if cfg.storage == "bram" else cfg.frame_cap
    pool = SlotPool(cfg.compressed_slots, cap)
    window = round(cfg.frames * cfg.memory_clock / cfg.fps)
    end = window + round(cfg.drain_frames * cfg.memory_clock / cfg.fps)
    line_period = cfg.memory_clock / (cfg.scan_hz * cfg.scan_lines)
    events, serial = [], 0
    def event(at, kind, data):
        nonlocal serial
        serial += 1
        heapq.heappush(events, (at, serial, kind, data))
    for frame in range(cfg.frames):
        event(round(frame * cfg.memory_clock / cfg.fps), "capture", frame)
    # Scanout continues during drain: ending workload must not create free bandwidth.
    for line in range(math.ceil(end / line_period)):
        event(round(line * line_period), "line", line)
    queues = {name: collections.deque() for name in
              ("display", "pixels", "reference", "compressed_write", "compressed_read")}
    names = list(queues)
    rr = 0
    now, next_refresh = 0, cfg.refresh_period
    active_rows = [None] * 4
    accepted = completed = cap_drops = busy_drops = 0
    deadline_misses = lines_complete = strict_lines = strict_misses = 0
    max_line_latency, worst_frame_age = 0, 0
    tokens, pending, frame_finish, presented = {}, {}, {}, {}
    service = collections.Counter()
    requests = collections.Counter()
    rowhits = rowmisses = refreshes = refresh_busy = 0
    high_water = collections.Counter()
    max_compressed_bytes = 0
    active_bytes = {}
    sram_free = 0

    def submit(client, frame, byte_count, address, write, deadline=None, at=None):
        at = now if at is None else at
        job = Job(client, frame, (byte_count + 15) // 16, address, write,
                  deadline, submitted=at)
        event(at, "job", job)

    def start_decode(frame):
        # Optimistic: decoder computation is zero, memory writes/reference reads remain.
        pending[frame] = 1 + int(cfg.reference)
        submit("pixels", frame, FRAME_BYTES, 0x100000, True)
        if cfg.reference:
            submit("reference", frame, FRAME_BYTES, 0x200000, False)

    def complete(job):
        nonlocal completed, deadline_misses, lines_complete, strict_lines, strict_misses
        nonlocal max_line_latency, worst_frame_age
        if job.client == "display":
            lines_complete += 1
            latency = now - job.submitted
            max_line_latency = max(max_line_latency, latency)
            deadline_misses += now > job.deadline
            if job.deadline <= window:
                strict_lines += 1
                strict_misses += now > job.deadline
        elif job.client == "compressed_write":
            pool.drain(tokens[job.frame])
            pool.commit(tokens[job.frame], True)
            pool.issue(tokens[job.frame], 0, active_bytes[job.frame])
            submit("compressed_read", job.frame, active_bytes[job.frame],
                   0xC0000 + tokens[job.frame][0] * 0x100000, False)
        elif job.client == "compressed_read":
            pool.drain(tokens[job.frame])
            pool.release(tokens.pop(job.frame))
            active_bytes.pop(job.frame)
            start_decode(job.frame)
        elif job.client in ("pixels", "reference"):
            pending[job.frame] -= 1
            if not pending[job.frame]:
                completed += 1
                frame_finish[job.frame] = now
                # Display publication is only a hypothetical next-vblank timestamp.
                scan_period = cfg.memory_clock / cfg.scan_hz
                presented[job.frame] = math.ceil(now / scan_period) * scan_period
                capture = round(job.frame * cfg.memory_clock / cfg.fps)
                worst_frame_age = max(worst_frame_age, now - capture)

    while now < end:
        while events and events[0][0] <= now:
            at, _, kind, data = heapq.heappop(events)
            if kind == "capture":
                size = cfg.frame_sizes[data % len(cfg.frame_sizes)]
                if size <= 0 or size > cap:
                    cap_drops += 1
                    continue
                token = pool.acquire(data, size)
                if token is None:
                    busy_drops += 1
                    continue
                accepted += 1
                tokens[data] = token
                active_bytes[data] = size
                max_compressed_bytes = max(max_compressed_bytes, sum(active_bytes.values()))
                # Ingress is ideal ready-at-capture. No network, QSPI or decoder compute.
                if cfg.storage == "sdram":
                    pool.issue(token, 0, size)
                    submit("compressed_write", data, size,
                           0xC0000 + token[0] * 0x100000, True)
                else:
                    # BRAM is idealized zero latency. SRAM shares one independent port;
                    # write+read at configurable cycles/word, not datasheet qualification.
                    cycles = 0 if cfg.storage == "bram" else (
                        2 * math.ceil(size / 2) * cfg.sram_cycles_per_word)
                    sram_free = max(now, sram_free) + cycles
                    pool.issue(token, 0, size)
                    event(sram_free, "external_ready", data)
            elif kind == "external_ready":
                pool.drain(tokens[data])
                pool.commit(tokens[data], True)
                pool.release(tokens.pop(data))
                active_bytes.pop(data)
                start_decode(data)
            elif kind == "line":
                line = data % cfg.scan_lines
                submit("display", data, cfg.line_words * 2, line * cfg.line_words * 2,
                       False, round(at + line_period * cfg.line_deadline_scale), at=at)
            elif kind == "job":
                queues[data.client].append(data)
                high_water[data.client] = max(high_water[data.client], len(queues[data.client]))

        if now >= next_refresh:
            # Accumulate refresh debt; never make missed refreshes vanish.
            now += cfg.refresh_cycles
            refresh_busy += cfg.refresh_cycles
            refreshes += 1
            next_refresh += cfg.refresh_period
            active_rows = [None] * 4
            continue

        display = queues["display"]
        urgent = bool(display and display[0].deadline - now <=
                      display[0].bursts * 23 + cfg.quantum_bursts * 23 + cfg.refresh_cycles)
        if display and (cfg.policy == "strict_display" or urgent):
            selected = "display"
        else:
            selected = None
            for delta in range(len(names)):
                index = (rr + delta) % len(names)
                if queues[names[index]]:
                    selected = names[index]
                    rr = (index + 1) % len(names)
                    break
        if selected is None:
            if not events:
                break
            now = min(events[0][0], next_refresh, end)
            continue
        job = queues[selected][0]
        # A scheduling grant is bounded to N serialized BL8 requests. They cannot be
        # interrupted by a line release. Refresh is checked between grants.
        for _ in range(min(cfg.quantum_bursts, job.bursts)):
            word = job.address // 2
            bank, row = (word >> 22) & 3, (word >> 9) & 8191
            hit = active_rows[bank] == row
            cycles = (13 if job.write else 15) + (0 if hit else 8)
            active_rows[bank] = row
            rowhits += hit
            rowmisses += not hit
            now += cycles
            service[job.client] += cycles
            requests[job.client] += 1
            job.address += BURST_BYTES
            job.bursts -= 1
            job.total += BURST_BYTES
        if not job.bursts:
            queues[selected].popleft()
            complete(job)

    frame_ages = [(finish - round(frame * cfg.memory_clock / cfg.fps)) * 1000 /
                  cfg.memory_clock for frame, finish in frame_finish.items()]
    pending_line_misses = sum(job.deadline <= min(window, now)
                              for job in queues["display"])
    strict_misses += pending_line_misses
    return dict(config=dataclasses.asdict(cfg), scope="synthetic_memory_service_only",
                admitted=accepted, cap_drops=cap_drops, busy_drops=busy_drops,
                captured=cfg.frames,
                reconstructed_by_window=sum(within_window(t, window) for t in frame_finish.values()),
                hypothetical_vblank_eligible_by_window=sum(within_window(t, window) for t in presented.values()),
                reconstructed_after_drain=completed, pending_at_drain=accepted-completed,
                strict_window_ms=window*1000/cfg.memory_clock,
                window_kind="[0,N/fps)",
                drain_end_ms=now*1000/cfg.memory_clock,
                line_deadline_misses_by_window=strict_misses,
                line_deadline_misses_during_run=deadline_misses,
                lines_completed_by_deadline_window=strict_lines,
                lines_completed_total=lines_complete,
                max_line_completion_cycles=max_line_latency,
                line_period_cycles=line_period,
                frame_memory_age_ms=dict(p50=percentile(frame_ages,.5), p95=percentile(frame_ages,.95),
                                         maximum=max(frame_ages) if frame_ages else None),
                service_cycles=dict(service), queue_high_water_jobs=dict(high_water),
                request_counts=dict(requests),
                padded_payload_bytes={name: count * BURST_BYTES for name,count in requests.items()},
                controller_busy_fraction=(sum(service.values())+refresh_busy)/now,
                max_occupied_compressed_bytes=max_compressed_bytes,
                row_hit_requests=rowhits, row_miss_requests=rowmisses,
                refresh_commands=refreshes, refresh_busy_cycles=refresh_busy,
                queued_jobs_at_end={name:len(q) for name,q in queues.items()})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frame-sizes", type=Path,
                        help="JSON list of positive encoded sizes, or {'frame_sizes':[...]} ")
    parser.add_argument("--frames", type=int, default=15)
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("results.json"))
    args = parser.parse_args()
    sizes = (26991,)
    if args.frame_sizes:
        content = json.loads(args.frame_sizes.read_text())
        sizes = tuple(content["frame_sizes"] if isinstance(content,dict) else content)
        if not sizes or any(type(x) is not int or x <= 0 for x in sizes):
            raise ValueError("sizes must be positive integers")
    scenarios = []
    for fps in (30,60):
        for hz in (60.0,65.076):
            for reference in (False,True):
                for storage in ("bram","sdram","sram"):
                    cfg = Config(storage=storage, fps=fps, scan_hz=hz, reference=reference,
                                 frames=args.frames, frame_sizes=sizes)
                    scenarios.append(simulate(cfg))
    # Fairness alternative and high-cap tail under explicit serialized SRAM timings.
    for policy in ("strict_display","deadline_rr"):
        scenarios.append(simulate(Config(storage="sdram", policy=policy, fps=60,
                                         reference=True, frames=args.frames, frame_sizes=sizes)))
    for storage in ("bram","sdram","sram"):
        scenarios.append(simulate(Config(storage=storage, frames=args.frames,
                                         frame_sizes=(26991,49152,262144))))
    sources = {name: hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
               for name in ("model.py","test_model.py")}
    input_hash = hashlib.sha256(args.frame_sizes.read_bytes()).hexdigest() if args.frame_sizes else None
    result = dict(version=1, source_sha256=sources, frame_sizes_input_sha256=input_hash,
                  allocation=allocation_report(), scenarios=scenarios)
    args.output.write_text(json.dumps(result, indent=2)+"\n")
    print(f"Wrote {len(scenarios)} scenarios to {args.output}")
    for row in scenarios:
        c=row["config"]
        print(c["storage"], c["fps"], c["scan_hz"], "ref="+str(c["reference"]),
              c["policy"], "admitted="+str(row["admitted"]),
              "complete="+str(row["reconstructed_after_drain"]),
              "strict_eligible="+str(row["hypothetical_vblank_eligible_by_window"]),
              "line_misses="+str(row["line_deadline_misses_during_run"]),
              "max_age_ms="+str(row["frame_memory_age_ms"]["maximum"]))


if __name__ == "__main__":
    main()
