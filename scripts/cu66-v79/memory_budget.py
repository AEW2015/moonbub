#!/usr/bin/env python3
"""Read frozen evidence; model bounded tile dependencies, never predict decode FPS.

Python 3 stdlib only. No HDL, container, network, or earlier evidence is modified.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from collections import Counter, deque
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "fpga/experiments/cu66-v79/memory-study"
V78 = "fpga/experiments/cu66-v78/system/frames30-fixed30-tac2/results.json"
V76 = "fpga/experiments/cu66-v76/service/results.json"
LOOK = "fpga/experiments/cu66-v76/service/lookahead-results.json"
TRACE = "fpga/experiments/cu66-v76/service/trace.mem"
REFS = "fpga/experiments/cu66-v76/service/reference.mem"
META = "fpga/experiments/cu66-v76/service/trace.json"
INPUTS = [V78, V76, LOOK, TRACE, REFS, META,
          "fpga/experiments/cu66-v74/memory/cu74_tile_memory.sv",
          "fpga/experiments/cu66-v74/memory/cu74_word_bridge.sv",
          "fpga/experiments/cu66-v72/memory/cu72_sdram_controller.sv",
          "fpga/experiments/cu66-v78/system/tb_system.cpp",
          "fpga/experiments/cu66-v78/scanout/cu78_direct_scanout.sv",
          "scripts/cu66-v79/memory_budget.py"]
PANEL_PS = 541 * 834 * 34058
PANEL = PANEL_PS // 10000


def read_json(name):
    return json.loads((ROOT / name).read_text())


def sha(name):
    return hashlib.sha256((ROOT / name).read_bytes()).hexdigest()


def tile_addr(plane, index, bank):
    return (0x080000, 0x480000, 0x880000)[bank] + (0, 172800, 216000)[plane] + index * 32


def evidence():
    actual = read_json(V78)
    rows = []
    for f, t in zip(actual["frames"], actual["timings"]):
        # Every accepted P0 read misses in this campaign. P1 is HUD readback.
        assert f["p0_cache_hits"] == f["p1_cache_hits"] == 0
        assert f["p0_row_reads"] == f["p0_cache_misses"]
        assert f["actual_write_commands"] == 32400 + f["hud_write_requests"]
        assert f["actual_write_bus_beats"] == f["actual_write_commands"] * 8
        assert f["hud_read_requests"] == f["p1_cache_misses"] == 2640
        ref = f["p0_cache_misses"]
        display = f["actual_read_bursts"] - ref - f["p1_cache_misses"]
        assert display >= 0 and ref == (0 if f["key"] else 31224)
        rows.append(dict(fid=f["fid"], key=f["key"],
            canonical_write_bytes=518400, hud_write_bytes=42240,
            reference_read_bytes=ref * 16, hud_verify_read_bytes=42240,
            display_read_bytes_during_admission_to_ack=display * 16,
            total_wire_bytes=f["actual_write_bus_beats"] * 2 + f["actual_read_bursts"] * 16,
            raw_bus_floor_cycles=f["actual_write_bus_beats"] + f["actual_read_bursts"] * 8,
            validated_cycles=t["validated_decode_model_cycles"], ack_window_cycles=f["cycles"],
            p0_wait_cycles=f["p0_wait_cycles"], p0_service_cycles=f["p0_service_cycles"],
            p0_read_wait_cycles=f["p0_read_wait_cycles"],
            p0_read_service_cycles=f["p0_read_service_cycles"],
            ACT=f["ACT"], PRE=f["PRE"], REF=f["REF"]))
    return rows


def replay_measured():
    """Replay *measured* strip durations; no command-time fit is hidden here."""
    rows = []
    for file, label in [(V76, "baseline"), (LOOK, "measured_lookahead")]:
        for run in read_json(file)["runs"]:
            end = None
            misses = 0
            min_slack = None
            for strip in run["strips_detail"]:
                start = strip["release_cycle"] if end is None else max(end, strip["release_cycle"])
                end = start + strip["service_cycles"]
                assert start == strip["start_cycle"] and end == strip["end_cycle"]
                slack = strip["deadline_cycle"] - end
                min_slack = slack if min_slack is None else min(slack, min_slack)
                misses += slack < 0
            assert misses == run["deadline_misses"]
            rows.append(dict(source=label, route=run["route"], background=run["background"],
                             tac_ns=run["tac_ns"], issue_gap=run["issue_gap"],
                             deadline_misses=misses, minimum_slack_cycles=min_slack,
                             max_strip_service_cycles=run["max_service_cycles"],
                             busy_service_cycles=sum(s["service_cycles"] for s in run["strips_detail"]),
                             calibration="Exact replay of retained durations and timestamps only"))
    return rows


@dataclass
class Bus:
    """Source-parameter approximation of single-outstanding frozen controller.

    Accept-to-next-accept costs: read hit 15, write hit 13, ACT +4,
    conflicting-row PRE+ACT +8; all from the V72 state transitions.
    An extra bridge_gap is deliberately a sensitivity parameter.
    Refresh is approximated as 15 clocks at first eligible burst boundary,
    open rows close, next 750-clock interval starts at modeled REF command.
    This is not a cycle-accurate bridge/controller or data model.
    """
    gap: int = 3
    refresh_period: int = 750
    row_costs: bool = True
    time: int = 0

    def __post_init__(self):
        self.open = [None] * 4
        self.next_refresh = self.refresh_period if self.refresh_period else 10**30
        self.count = Counter()

    def issue(self, address, write=False):
        assert address % 8 == 0
        if self.time >= self.next_refresh:
            self.count["refresh"] += 1
            self.time += 15
            self.next_refresh = self.time - 10 + self.refresh_period
            self.open = [None] * 4
        bank, row = address >> 22, (address >> 9) & 8191
        assert 0 <= bank < 4
        extra = 0
        if self.row_costs and self.open[bank] != row:
            extra = 4 if self.open[bank] is None else 8
            self.count["ACT"] += 1
            self.count["PRE"] += self.open[bank] is not None
            self.open[bank] = row
        self.count["write" if write else "read"] += 1
        self.time += (13 if write else 15) + extra + self.gap
        return self.time


def load_work():
    refs = {int(line, 16) for line in (ROOT / REFS).read_text().splitlines()}
    assert len(refs) == 7806
    tiles = [(p, i, ((p << 17) | i) in refs)
             for p, count in enumerate((5400, 1350, 1350)) for i in range(count)]
    # V76's static SAFE map identifies dependencies, not actual decoder releases.
    strips = [[] for _ in range(90)]
    for line in (ROOT / TRACE).read_text().splitlines():
        word = int(line, 16)
        strips[word >> 24].append(word & 0xffffff)
    assert sum(map(len, strips)) == 35040
    return tiles, strips


def schedule(tiles, strips, *, window=1, compute=64, gap=3, policy="write_first",
             lcd=True, phase=0, row_costs=True, refresh=750):
    """Bounded DAG prototype; immutable reference front, disjoint candidate.

    All tile descriptors available at t=0 is optimistic. One in-order compute
    engine overlaps a single atomic BL8 bus. A slot remains owned until its
    output write drains. Window bounds in-flight descriptors AND full payloads.
    LCD gets at most four consecutive bursts while decode/HUD waits. Fixed
    one-strip-early releases and original deadlines never slide after a miss.
    """
    assert window >= 1 and compute >= 0 and gap >= 0
    bus = Bus(gap, refresh, row_costs)
    slots = {}
    admitted = retired = next_compute = 0
    cpu = None
    max_live = max_ready = lcd_streak = 0
    display_jobs = deque()
    display_cursor = 0
    display_done = 0
    misses = 0
    min_slack = None
    hud = 0
    max_pending_display = 0
    while retired < len(tiles) or hud < 5280:
        now = bus.time
        if cpu is not None and cpu[1] <= now:
            idx, _ = cpu
            assert slots[idx]["read"] == 4
            slots[idx]["computed"] = True
            cpu = None
        while admitted < len(tiles) and len(slots) < window:
            p, i, ref = tiles[admitted]
            slots[admitted] = dict(read=0 if ref else 4, write=0, computed=False)
            admitted += 1
        max_live = max(max_live, len(slots))
        assert len(slots) <= window
        if cpu is None and next_compute in slots and slots[next_compute]["read"] == 4:
            cpu = (next_compute, now + compute)
            next_compute += 1
            if compute == 0:
                slots[cpu[0]]["computed"] = True
                cpu = None
        max_ready = max(max_ready, sum(s["read"] == 4 for s in slots.values()))
        if lcd:
            # Repeat the entire native panel, including vertical blanking.
            while True:
                panel, strip = divmod(display_cursor, 90)
                base = phase + panel * PANEL_PS // 10000
                release = base + max(0, strip - 1) * 147403024 // 10000
                if release > now:
                    break
                deadline = base + (strip + 1) * 147403024 // 10000
                display_jobs.append([display_cursor, 0, deadline])
                display_cursor += 1
            max_pending_display = max(max_pending_display, len(display_jobs))
        reads = [k for k, s in slots.items() if s["read"] < 4]
        writes = [k for k, s in slots.items() if s["computed"] and s["write"] < 4]
        tile_idx = (writes or reads or [None])[0] if policy == "write_first" else (reads or writes or [None])[0]
        foreground = tile_idx is not None or retired == len(tiles)
        if display_jobs and (lcd_streak < 4 or not foreground):
            job = display_jobs[0]
            bus.issue(strips[job[0] % 90][job[1]])
            job[1] += 1
            lcd_streak += 1
            if job[1] == len(strips[job[0] % 90]):
                slack = job[2] - bus.time
                misses += slack < 0
                min_slack = slack if min_slack is None else min(slack, min_slack)
                display_done += 1
                display_jobs.popleft()
            continue
        if tile_idx is not None:
            state = slots[tile_idx]
            p, i, _ = tiles[tile_idx]
            writing = state["computed"] and state["write"] < 4
            # read_first cannot write an unread tile; write only after compute.
            if policy == "read_first" and tile_idx in reads:
                writing = False
            block = state["write" if writing else "read"]
            if writing:
                assert state["read"] == 4 and state["computed"]
            bus.issue(tile_addr(p, i, 1 if writing else 0) + block * 8, writing)
            state["write" if writing else "read"] += 1
            lcd_streak = 0
            if state["write"] == 4:
                del slots[tile_idx]
                retired += 1
            continue
        if retired == len(tiles):
            bus.issue(0x500000 + (hud % 2640) * 8, hud < 2640)
            hud += 1
            lcd_streak = 0
            continue
        assert cpu is not None, "scheduler deadlock"
        # If no memory request is eligible, skip to compute or next release.
        wake = cpu[1]
        if lcd:
            panel, strip = divmod(display_cursor, 90)
            wake = min(wake, phase + panel * PANEL_PS // 10000 + max(0, strip - 1) * 147403024 // 10000)
        assert wake > now
        bus.time = wake
    expected_reads = sum(t[2] for t in tiles) * 4 + 2640
    assert bus.count["write"] == len(tiles) * 4 + 2640
    # LCD may end mid-strip at decode completion; count physical requests, no tail drain.
    display_bursts = bus.count["read"] - expected_reads
    assert display_bursts >= 0 and next_compute == len(tiles)
    return dict(window=window, compute_cycles_per_tile=compute, bridge_gap_cycles=gap,
                policy=policy, lcd=lcd, phase_cycles=phase, row_costs=row_costs,
                refresh_period=refresh, model_completion_cycles=bus.time,
                model_completion_ms=bus.time / 100000, max_live_tiles=max_live,
                reference_payload_bound_bytes=window * 64,
                candidate_payload_bound_bytes=window * 64,
                descriptor_state_bound_bytes=window * 32,
                logical_tile_working_storage_bound_bytes=window * 160,
                physical_controller_outstanding_bound=1,
                max_reference_ready_tiles=max_ready, display_bursts=display_bursts,
                completed_display_strips=display_done, completed_strip_deadline_misses=misses,
                minimum_completed_strip_slack_cycles=min_slack,
                pending_display_strips_at_completion=len(display_jobs),
                maximum_pending_display_strips=max_pending_display,
                display_deadline_admission_screen_pass=max_pending_display <= 2 and misses == 0,
                reference_tile_count=sum(t[2] for t in tiles),
                counts=dict(bus.count), calibration="UNCALIBRATED_COUNTERFACTUAL_NOT_DECODE_LATENCY")


def checks(tiles, strips):
    tiny = tiles[:4]
    # Byte/command conservation, atomic bus costs, serial DAG and finite capacity.
    a = schedule(tiny, strips, window=1, compute=0, gap=0, lcd=False, row_costs=False, refresh=0)
    b = schedule(tiny, strips, window=4, compute=0, gap=0, lcd=False, row_costs=False, refresh=0)
    assert a["model_completion_cycles"] == b["model_completion_cycles"] == 16 * (15 + 13) + 2640 * (13 + 15)
    c = schedule(tiny, strips, window=1, compute=64, gap=0, lcd=False, row_costs=False, refresh=0)
    assert c["model_completion_cycles"] == a["model_completion_cycles"] + 4 * 64
    d = schedule(tiny, strips, window=4, compute=64, gap=0, lcd=False, row_costs=False, refresh=0)
    assert a["model_completion_cycles"] <= d["model_completion_cycles"] < c["model_completion_cycles"]
    e = schedule(tiny, strips, window=1, compute=0, gap=1, lcd=False, row_costs=False, refresh=0)
    assert e["model_completion_cycles"] - a["model_completion_cycles"] == 32 + 5280
    bus = Bus(gap=0, refresh_period=0)
    assert bus.issue(0x080000) == 19
    assert bus.issue(0x080008) == 34
    assert bus.issue(0x080200) == 57
    refresh_bus = Bus(gap=0, refresh_period=20)
    refresh_bus.issue(0x080000)
    refresh_bus.issue(0x080008)
    refresh_bus.issue(0x080010)
    assert refresh_bus.count["refresh"] == 1 and refresh_bus.count["ACT"] == 2
    # Negative control: malformed request cannot enter the atomic bus model.
    try:
        bus.issue(0x080001)
    except AssertionError:
        pass
    else:
        raise AssertionError("unaligned request accepted")
    return dict(status="PASS", groups=["frozen traffic conservation", "measured V76 fixed-deadline replay",
        "zero-compute outstanding cannot invent bandwidth", "serial compute cost exact",
        "bounded overlap sensitivity", "per-request gap sensitivity exact",
        "row-hit/conflict costs", "refresh closes open rows", "unaligned negative control",
        "all scenarios check read/compute/write ordering and finite payload ownership"])


def csv_text(rows):
    f = io.StringIO(newline="")
    writer = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return f.getvalue()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify retained artifacts without rewriting")
    args = parser.parse_args()
    actual = evidence()
    replay = replay_measured()
    tiles, strips = load_work()
    tests = checks(tiles, strips)
    scenarios = []
    for compute in (0, 64, 128):
        for window in (1, 2, 4, 8):
            for policy in ("write_first", "read_first"):
                scenarios.append(schedule(tiles, strips, window=window, compute=compute, policy=policy))
    for gap in (0, 1, 6, 10):
        scenarios.append(schedule(tiles, strips, window=4, compute=64, gap=gap))
    for phase in (PANEL // 2, PANEL - 1):
        scenarios.append(schedule(tiles, strips, window=4, compute=64, phase=phase))
    for rows, refresh in ((False, 0), (True, 0)):
        scenarios.append(schedule(tiles, strips, window=4, compute=64, row_costs=rows, refresh=refresh))
    # Implementable conservative prefetch need not speculate on live qmap:
    # fetch every tile, retiring unused hidden-tile payload on write completion.
    scenarios.append(schedule([(p, i, True) for p, i, _ in tiles], strips,
                              window=2, compute=64))
    delta = [r for r in actual if not r["key"]]
    # Floor counts exclude scanout, row costs, refresh, bridge and all codec/HUD CPU work.
    raw = (32400 + 2640 + 31224 + 2640) * 8
    controller = (32400 + 2640) * 13 + (31224 + 2640) * 15
    result = dict(schema="cu79-memory-feasibility-v1", status="PASS_ANALYSIS_ONLY_TARGET_OPEN",
        source_sha256={p: sha(p) for p in INPUTS}, actual_frame_traffic=actual,
        measured_service_replay=replay, counterfactuals=scenarios, tests=tests,
        floors=dict(delta_non_display_wire_bytes=raw * 2, delta_raw_bus_cycles=raw,
                    delta_controller_state_floor_cycles=controller,
                    all_tile_prefetch_extra_reference_bytes=294 * 64,
                    all_tile_prefetch_extra_read_commands=294 * 4,
                    all_tile_prefetch_controller_state_floor_cycles=controller + 294 * 4 * 15,
                    state_floor_scope="Single outstanding V72 accept-to-next-accept costs; no gaps, rows, refresh or display; not measured decode latency"),
        summary=dict(actual_validated_min_ms=min(r["validated_cycles"] for r in actual) / 100000,
                     actual_validated_max_ms=max(r["validated_cycles"] for r in actual) / 100000,
                     delta_display_window_bytes_min=min(r["display_read_bytes_during_admission_to_ack"] for r in delta),
                     delta_display_window_bytes_max=max(r["display_read_bytes_during_admission_to_ack"] for r in delta),
                     delta_p0_service_cycles_min=min(r["p0_service_cycles"] for r in delta),
                     delta_p0_service_cycles_max=max(r["p0_service_cycles"] for r in delta)),
        limitations=["No V78 command timestamps, codec tile-ready times or phase/lease trace calibrate the counterfactual scheduler.",
                     "V76 replay validates retained deadline accounting only; it does not calibrate altered arbitration or the V78 decoder.",
                     "All reference descriptors available at time zero is an optimistic relaxation; parsing, entropy dependencies, CPU service and packet transport are absent.",
                     "The LCD release/priority model uses the V76 synthetic strip trace, not exact V78 demand, cache residency or converter backpressure.",
                     "Controller state costs are source-derived approximations; gap, refresh phase and row locality are explicit sensitivities.",
                     "Wait/service and their read subsets are overlapping instrumentation; none is subtracted from wall latency.",
                     "No target FPS, physical timing/fit or strict validated latency follows from bus floors or model completion times."])
    artifacts = {"results.json": json.dumps(result, indent=2) + "\n",
                 "actual-frame-traffic.csv": csv_text(actual),
                 "counterfactuals.csv": csv_text([{k: v for k, v in r.items() if k != "counts"} for r in scenarios]),
                 "tests.json": json.dumps(tests, indent=2) + "\n"}
    if args.check:
        for name, content in artifacts.items():
            assert (OUT / name).read_text() == content, f"artifact mismatch: {name}; regenerate"
    else:
        OUT.mkdir(parents=True, exist_ok=True)
        for name, content in artifacts.items():
            (OUT / name).write_text(content)
    print(json.dumps(dict(status=result["status"], frames=len(actual), measured_replays=len(replay),
                          counterfactuals=len(scenarios), floors=result["floors"], summary=result["summary"], tests=tests["status"]), indent=2))


if __name__ == "__main__":
    main()
