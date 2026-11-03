#!/usr/bin/env python3
"""Compare matched actual-codec cohorts with independently checked metrics."""
import hashlib
import json
from pathlib import Path

from validation import summarize_presentation

HERE = Path(__file__).resolve().parent


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def signature(manifest):
    return (manifest['source_sha256'], tuple(manifest['selected_pts']), tuple(manifest['frame_sha256']))


def main():
    stop_path = HERE/'results.json'
    anchor_path = HERE.parent/'python-anchor-study/results.json'
    stop, anchor = json.loads(stop_path.read_text()), json.loads(anchor_path.read_text())
    stop_names = {signature(m): n for n, m in stop['manifests'].items()}
    pairs = []
    for scene in anchor['scenes']:
        name = stop_names[signature(scene['manifest'])]
        for a in scene['cases']:
            if a['label'] == 'faults':
                continue  # Fault feedback differs: anchor NACKs, stop-and-wait waits for timeout.
            adaptive = a['label'].startswith('adaptive')
            candidates = [s for s in stop['scenarios'] if s['scene'] == name
                          and s['config']['feedback_ms'] == a['config']['feedback_ms']
                          and s['case'] != 'fault_campaign'
                          and bool(s['config']['cap_backoff_scales']) == adaptive]
            if len(candidates) != 1:
                raise AssertionError('ambiguous comparator')
            s = candidates[0]
            for key in ('fps','quant_scale','encode_ms','decode_ms','link_mbps','qspi_mbps','refresh_hz','frame_cap','ack_timeout_ms'):
                if s['config'][key] != a['config'][key]:
                    raise AssertionError('different assumed service configuration')
            n = len(scene['manifest']['frame_sha256'])
            end = n*1000/a['config']['fps']
            captures = [{'id':i,'capture_ms':i*1000/a['config']['fps']} for i in range(n)]
            rows = {}
            for label, result, presentations in (('stopwait',s,s['presentations']),('anchor',a,a['presented'])):
                metrics = summarize_presentation(captures,presentations,end,(500,end-500))
                expected = result['presented_strict']
                if metrics['presented_count'] != expected or metrics['steady_fps'] != result['steady_fps']:
                    raise AssertionError('independent metric check failed')
                rows[label] = metrics
            pairs.append({'scene':name,'feedback_ms':a['config']['feedback_ms'],'adaptive':adaptive,
                          'source_sha256':scene['manifest']['source_sha256'],
                          'frame_sha256':scene['manifest']['frame_sha256'],
                          'stopwait':{**rows['stopwait'],'eventual':s['presented_after_drain'],
                                      'wire_bytes_including_drain':s['wire_bytes'],
                                      'presented_psnr_db':s['pooled_presented_active_psnr_db'],
                                      'scale_histogram':s['presented_scale_histogram']},
                          'anchor':{**rows['anchor'],'eventual':a['presented_eventual'],
                                    'wire_bytes_including_drain':a['transmitted_wire_bytes'],
                                    'presented_psnr_db':a['active_psnr_db_presented_ids'],
                                    'peak_packet_bytes':a['peak_retained_packet_bytes']},
                          'quality_scope':'Different reference policy, reconstructed pixels and possibly presented subsets; not matched perceptual quality'})
    result = {'evidence':'Matched input cohorts and service assumptions; actual codecs with virtual stage times, not hardware',
              'source_sha256':{str(p):digest(p) for p in (HERE/'compare_models.py',HERE/'validation.py')},
              'input_sha256':{str(stop_path):digest(stop_path),str(anchor_path):digest(anchor_path)},
              'pairs':pairs}
    (HERE/'comparison.json').write_text(json.dumps(result,indent=2)+'\n')
    print('verified',len(pairs),'matched comparisons')
    for pair in pairs:
        if pair['feedback_ms'] == 20 or pair['adaptive']:
            print(pair['scene'],pair['feedback_ms'],'adaptive',pair['adaptive'],
                  pair['stopwait']['steady_fps'],pair['anchor']['steady_fps'],
                  pair['stopwait']['eventual'],pair['anchor']['eventual'])


if __name__=='__main__':
    main()
