#!/usr/bin/env python3
"""Additional coefficient parity and complete iterator-drain qualification."""
from pathlib import Path
import importlib.util
import json
import sys
import numpy as np
import model as m

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('unified27_control_verify',HERE/'verify.py')
v=importlib.util.module_from_spec(spec);sys.modules[spec.name]=v;spec.loader.exec_module(v)


def main():
    data=v.b.load(HERE/'results.json');prior=v.b.load(v.b.OLD/'full_results.json')
    trace_frames=streams=blocks=0
    for case in data['cases']:
        oldcase=next(c for c in prior['cases'] if c['scene']==case['scene'])
        for row,oldrow in zip(case['rows'],oldcase['rows']):
            packet=v.raw(row['base_packet']);meta=m.parse(packet)
            if case['policy']=='frozen_trace':
                oldmeta=m.old.parse(v.raw(oldrow['base_packet'],v.b.OLD))
                for name in ('vectors','scale_map'):np.testing.assert_array_equal(meta[name],oldmeta[name])
                for a,b in zip(meta['coefficients'],oldmeta['coefficients']):np.testing.assert_array_equal(a,b)
                trace_frames+=1
            fields=m.HEADER.unpack_from(packet);pos=m.HEADER.size+fields[-5]+fields[-4]
            for plane,(size,coefficients) in enumerate(zip(fields[-3:],meta['coefficients'])):
                payload=packet[pos:pos+size];pos+=size
                if payload[0]!=3:continue
                width=720 if plane==0 else 360
                iterator=m.ec.iter_block_major(payload[1:],len(coefficients),(width+7)//8)
                for expected in coefficients:
                    assert np.array_equal(next(iterator),expected);blocks+=1
                # Resume after the final yield so trailing/padding validation
                # executes; zip alone can stop before this completion barrier.
                try:next(iterator)
                except StopIteration:pass
                else:raise AssertionError('unexpected extra coefficient block')
                streams+=1
    assert trace_frames==96
    print(json.dumps(dict(frozen_trace_frames=trace_frames,all_coefficients_vectors_maps_exact=True,
                          fully_drained_EC26_streams=streams,coefficient_blocks=blocks,
                          iterator_completion_before_publication_required=True)))


if __name__=='__main__':main()
