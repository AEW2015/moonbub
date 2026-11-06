#!/usr/bin/env python3
"""Independent serialized-tile checks against frozen canonical plane SHA256s."""
import hashlib
import json
from pathlib import Path
from data import iter_frames

ROOT = Path(__file__).resolve().parent

def main():
    previous = None
    cohort = None
    count = keys = copy_total = equal_delta = key_zero = 0
    cohorts = [0]*4
    for frame in iter_frames():
        if cohort != frame["cohort"]:
            cohort = frame["cohort"]
            previous = None
        tiles = frame["tiles"]
        assert len(tiles) == 8100 and all(len(tile) == 64 for tile in tiles)
        exact = bytes(int(previous is not None and tile == previous[i]) for i,tile in enumerate(tiles))
        assert frame["same_mask"] == exact
        expected = bytes(int(not frame["key"] and not h and z) for h,z in zip(frame["hidden_mask"], frame["zero_coeff_mask"]))
        assert frame["copy_ref_mask"] == expected
        assert all(not c or e for c,e in zip(expected,exact))
        assert sum(frame["hidden_mask"]) == 294
        assert all(tile == bytes([128])*64 for tile,h in zip(tiles,frame["hidden_mask"]) if h)
        canonical=hashlib.sha256()
        for plane,w,h in zip(frame["planes"],(720,360,360),(480,240,240)):
            assert len(plane) == w*h//64
            raster=bytearray(w*h)
            bw=w//8
            for i,tile in enumerate(plane):
                base=(i//bw)*8*w + (i%bw)*8
                for y in range(8):
                    raster[base+y*w:base+y*w+8]=tile[y*8:y*8+8]
            canonical.update(raster)
        assert canonical.hexdigest() == frame["canonical_sha256"]
        previous=tiles
        count+=1; keys+=frame["key"]; cohorts[cohort]+=1
        copy_total+=sum(expected)
        if not frame["key"]:
            equal_delta+=sum(e and not h for e,h in zip(exact,frame["hidden_mask"]))
        else:
            key_zero+=sum(z and not h for z,h in zip(frame["zero_coeff_mask"],frame["hidden_mask"]))
    assert (count,keys,cohorts)==(457,20,[119,119,119,100])
    report={"pass":True,"frames":count,"keys":keys,"deltas":count-keys,"cohort_counts":cohorts,"safe_copy_visible_delta":copy_total,"exact_equal_visible_delta":equal_delta,"nonzero_equal_visible_delta":equal_delta-copy_total,"zero_coeff_visible_key_full_write":key_zero,"checks":["gzip and raw SHA256 and exact record coverage","every exported decoded byte reassembled into original flat canonical SHA256","every exact equality mask bit recomputed from actual prior tiles","every COPY classification recomputed from delta/visible/zero","every safe COPY byte-equal","every hidden tile CONST128"]}
    (ROOT/"verification.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report))

if __name__ == "__main__": main()
