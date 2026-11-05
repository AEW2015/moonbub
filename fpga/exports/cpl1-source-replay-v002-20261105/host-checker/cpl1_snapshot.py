"""Offline decoder for v32's cached CPL1 pages. Never opens a device/socket.

The input log's origin is not attested by this parser. A match establishes only
that the supplied cached values agree with the named fixed fixture contract.
"""
import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import sys

MARKER = "USB_TRACE cpl1 "
ANSI = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
PAGE = re.compile(r"USB_TRACE cpl1 v=1 page=([0-9]+) cookie=([0-9a-f]{8}) gen=([0-9]+) off=([0-9a-f]{3}) words=([0-9a-f]{8}(?:,[0-9a-f]{8}){3})")
STATE = re.compile(r"USB_TRACE cpl1 v=1 result=([A-Za-z]+)(?: pages=10)?")
EXPECTED_FIELDS = frozenset("owner epoch frame generation rom_bytes canonical_bytes hud_words pad_write_beats_launched transpose_words base_tag_numeric hud_tag_numeric result_stage result_code result_checked result_seen lcd_underruns bridge_lost_writes canvas_crc32_hex completed_canvas_words coordinate_errors".split())

@dataclass(frozen=True)
class Snapshot:
    words: tuple[int, ...]

    def validate(self):
        w = self.words
        if len(w) != 40 or any(type(x) is not int or not 0 <= x <= 0xffffffff for x in w):
            raise ValueError("expected40 numeric u32 words")
        if w[0] == 0 or not 0 < w[1] < 0xffffffff or w[2] != 0x10000:
            raise ValueError("invalid cookie/generation/schema")
        if w[3] & 8:
            raise ValueError("configuration quarantined")
        if w[3] & ~0x1fff or w[3] & 0x1800 or w[25] & ~0x7f or w[25] & 3 != 3:
            raise ValueError("state/platform reserved, exhaustion or unlocked flags")
        if w[24] & ~0x3ff0f or w[35] & ~31 or w[35] & 16 or w[38] or w[39]:
            raise ValueError("result/canvas reserved or exhausted fields")
        if w[35] & 1 and (w[32] == 0 or w[34] != 345600 or w[35] & 0x1c or w[36]):
            raise ValueError("inconsistent completed canvas")
        return self

    def fields(self):
        self.validate()
        w = self.words
        number = lambda start, count: sum(w[start+i] << (32*i) for i in range(count))
        return dict(cookie=w[0], snapshot_generation=w[1], schema=w[2], state_flags=w[3],
                    core_cycle=number(4, 2), owner=number(6, 2), epoch=w[8], frame=w[9], generation=w[10],
                    rom_bytes=w[11], canonical_bytes=w[12], hud_words=w[13], pad_write_beats_launched=w[14],
                    transpose_words=w[15], base_tag_numeric=f"{number(16,4):032x}", hud_tag_numeric=f"{number(20,4):032x}",
                    result_stage=w[24]&15, result_code=(w[24]>>8)&255,
                    result_checked=bool(w[24]&(1<<16)), result_seen=bool(w[24]&(1<<17)),
                    platform_flags=w[25], lcd_underruns=w[26], native_frame_boundaries=w[27],
                    bootstrap_releases=w[28], consumer_writer_releases=w[29], bridge_lost_writes=w[30],
                    ignored_core_writes=w[31], canvas_sequence=w[32], canvas_crc32_hex=f"{w[33]:08x}",
                    completed_canvas_words=w[34], canvas_flags=w[35], coordinate_errors=w[36], current_canvas_words=w[37])

def parse(text):
    """Return independently keyed page groups and state messages; no latest guess."""
    groups, states = {}, []
    for line_no, original in enumerate(text.splitlines(), 1):
        line = ANSI.sub("", original)
        if MARKER not in line:
            continue
        line = line[line.index(MARKER):].strip()
        if len(line.encode("ascii", errors="strict")) > 192:
            raise ValueError(f"oversized CPL1 payload at line{line_no}")
        m = PAGE.fullmatch(line)
        if not m:
            state = STATE.fullmatch(line)
            if not state:
                raise ValueError(f"unrecognized/truncated CPL1 record at line{line_no}")
            states.append(dict(line=line_no, result=state[1]))
            continue
        page, cookie, gen, off = int(m[1]), int(m[2],16), int(m[3]), int(m[4],16)
        if not 0 <= page < 10 or off != 0x500+16*page or cookie == 0 or not 0 < gen < 0xffffffff:
            raise ValueError(f"invalid page envelope at line{line_no}")
        group = groups.setdefault((cookie,gen), {})
        if page in group:
            raise ValueError(f"duplicate CPL1 page{page} for cookie{cookie:08x}/gen{gen}")
        group[page] = tuple(int(x,16) for x in m[5].split(","))
    return groups, states

def select(groups, key=None):
    if key is None:
        if len(groups) != 1:
            raise ValueError("require exactly one snapshot, or explicit cookie AND generation")
        key = next(iter(groups))
    if key not in groups:
        raise ValueError("requested cookie/generation absent")
    group = groups[key]
    if set(group) != set(range(10)):
        raise ValueError(f"missing snapshot pages: {sorted(set(range(10))-set(group))}")
    s = Snapshot(tuple(word for page in range(10) for word in group[page])).validate()
    if (s.words[0],s.words[1]) != key:
        raise ValueError("embedded cookie/generation does not match page envelope")
    return s

def fixture_checks(snapshot, expectation):
    """Exact fixed fixture checks; raw actual CRC/tags are never replaced."""
    f = snapshot.fields()
    if expectation.get("schema") != "CPL1-fixed-frame0-expectation-v1":
        raise ValueError("unsupported expectation schema")
    if set(expectation.get("exact_fields", {})) != EXPECTED_FIELDS:
        raise ValueError("incomplete or unknown expectation fields")
    checks = {k: dict(actual=f[k], expected=v, matches=f[k] == v)
              for k,v in expectation["exact_fields"].items()}
    for name, matches in {
        "completed_state": snapshot.words[3] & 0x7a7 == 0x7a7 and snapshot.words[3] & 0x58 == 0,
        "canvas_present": f["canvas_sequence"] > 0,
        "digest_valid_without_gap": snapshot.words[35] & 1 == 1 and snapshot.words[35] & 0x1c == 0,
        "bootstrap_once": f["bootstrap_releases"] == 1,
        "consumer_writer_release_once": f["consumer_writer_releases"] == 1,
    }.items():
        checks[name] = dict(matches=matches)
    return dict(matches=all(c["matches"] for c in checks.values()), checks=checks,
                limits="Supplied retained values only. Pad launches are not chip ACKs; repeating canvases are not unique FPS; no bank-free/ownership ACK inferred.")

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--log", type=Path, required=True)
    ap.add_argument("--cookie", type=lambda s:int(s,0))
    ap.add_argument("--generation", type=lambda s:int(s,0))
    ap.add_argument("--expectation", type=Path)
    ap.add_argument("--require-fixture", action="store_true")
    ap.add_argument("--output", type=Path)
    a = ap.parse_args()
    if (a.cookie is None) != (a.generation is None): ap.error("cookie and generation are paired")
    if a.require_fixture and a.expectation is None: ap.error("require-fixture needs expectation")
    raw = a.log.read_bytes()
    groups, states = parse(raw.decode("utf-8-sig",errors="strict"))
    key = None if a.cookie is None else (a.cookie,a.generation)
    s = select(groups,key)
    result = dict(status="VALID_SUPPLIED_CACHED_SNAPSHOT", log_sha256=hashlib.sha256(raw).hexdigest(),
                  origin="Not attested; parser performs no hardware or network I/O", fields=s.fields(),
                  raw_words=[f"{x:08x}" for x in s.words], observed_state_messages=states,
                  other_snapshot_groups=len(groups)-1)
    if a.expectation:
        expected_raw=a.expectation.read_bytes()
        result["expectation_sha256"]=hashlib.sha256(expected_raw).hexdigest()
        result["fixture"]=fixture_checks(s,json.loads(expected_raw))
    encoded=json.dumps(result,indent=2)+"\n"
    if a.output:
        with a.output.open("x",encoding="utf-8") as f:f.write(encoded)
    else:print(encoded,end="")
    return 2 if a.require_fixture and not result["fixture"]["matches"] else 0

if __name__ == "__main__":
    try:sys.exit(main())
    except (ValueError,KeyError,OSError) as e:
        print(f"CPL1_REJECT: {e}",file=sys.stderr);sys.exit(2)
