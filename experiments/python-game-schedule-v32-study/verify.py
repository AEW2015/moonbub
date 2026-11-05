from pathlib import Path
import hashlib,json
import benchmark as b
import model
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]

def validate_cohorts(schedule_cases, controller_cases):
    """Require exact cohort, ordered-frame, and packet-descriptor lineage."""
    if not isinstance(schedule_cases, list) or not isinstance(controller_cases, list):
        raise ValueError('campaign cases must be lists')
    source = {}
    for case in controller_cases:
        key = (case.get('scene'), case.get('policy'))
        if key in source:
            raise ValueError('duplicate controller cohort')
        source[key] = case
    if len(source) != 6:
        raise ValueError('controller campaign must contain exactly six cohorts')
    keys = [(case.get('scene'), case.get('policy')) for case in schedule_cases]
    if len(keys) != 6 or len(set(keys)) != 6 or set(keys) != set(source):
        raise ValueError('schedule must cover the exact six scene/policy cohorts')
    for case in schedule_cases:
        key = (case['scene'], case['policy'])
        rows, source_rows = case.get('rows'), source[key].get('rows')
        if (not isinstance(rows, list) or not isinstance(source_rows, list)
                or len(rows) != 48 or len(source_rows) != 48
                or [row.get('id') for row in rows] != list(range(48))
                or [row.get('id') for row in source_rows] != list(range(48))):
            raise ValueError(f'{key}: rows must be ordered IDs 0..47')
        if set(case.get('summary', {})) != {'1', '2', '3'}:
            raise ValueError(f'{key}: summary must cover exactly one, two, and three banks')
        for row, source_row in zip(rows, source_rows):
            if row.get('base_packet') != source_row.get('base_packet'):
                raise ValueError(f'{key}/{row.get("id")}: packet descriptor lineage mismatch')
            if [point.get('banks') for point in row.get('points', [])] != [1, 2, 3]:
                raise ValueError(f'{key}/{row.get("id")}: schedule points must be ordered banks 1..3')
    return source


def validate_controls(controls, vector_groups):
    """Require the complete four-frame measured one-bank control set."""
    expected = [(group.get('scene'), group.get('frame_id'))
                for group in vector_groups if 'scene' in group]
    actual = [(control.get('scene'), control.get('frame_id'))
              for control in controls]
    if (len(expected) != 4 or len(set(expected)) != 4
            or len(actual) != 4 or len(set(actual)) != 4
            or set(actual) != set(expected)):
        raise ValueError('controls must cover the exact four v31 scene/frame groups')
    for control in controls:
        if [point.get('banks') for point in control.get('points', [])] != [1, 2, 3]:
            raise ValueError('each v31 control must include bank counts 1, 2, and 3')
    return True


def main():
    data=json.loads((HERE/'results.json').read_text())
    for p,h in data['source_sha256'].items():assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h,p
    assert data['new_RTL_implemented'] is False and data['physical_30fps_proven'] is False
    old=HERE.parent/'rtl-game-inverse-v31-study';vectors=json.loads((old/'vectors.json').read_text());rtl=json.loads((old/'results/results.json').read_text())
    validate_controls(data.get('controls'),vectors.get('groups'))
    d=vectors['files']['kind'];packed=(old/d['path']).read_bytes();assert hashlib.sha256(packed).hexdigest()==d['stored_sha256']
    raw=b.zlib.decompress(packed);assert hashlib.sha256(raw).hexdigest()==d['raw_sha256'];allk=[int(x,16) for x in raw.split()]
    for c in data['controls']:
        group=next(g for g in vectors['groups'] if (g.get('scene'),g.get('frame_id'))==(c['scene'],c['frame_id']))
        kinds=allk[group['start_block']:group['start_block']+8100]
        measured=next(r for case in rtl['simulations'] if case['bypass']==1 and case['stalls']==0 for r in case['frames'] if (r['scene'],r['frame_id'])==(c['scene'],c['frame_id']))
        assert c['old_RTL_cycles']==measured['service_cycles']
        for p in c['points']:
            result=model.schedule(kinds,p['banks']);assert model.validate(result)
            assert {k:v for k,v in result.items() if k!='rows'}==p
        assert c['points'][0]['done_cycles']==c['old_RTL_cycles']
    campaign=HERE.parent/'python-game-controller-v32-study'
    controller_data=json.loads((campaign/'results.json').read_text())
    controller_cases=validate_cohorts(data['cases'],controller_data['cases'])
    frames=blocks=0
    folder=campaign
    for case in data['cases']:
        rows=case['rows']
        for row in rows:
            packet,_=b.read(row['base_packet'],folder);meta=b.codec.parse(packet);kinds=[]
            for c in meta['coefficients']:
                for block in c:
                    nonzero=int(b.np.count_nonzero(block));kinds.append(0 if not nonzero else 1 if nonzero==1 and block[0,0]!=0 else 2)
            assert len(kinds)==8100
            assert dict(zero=kinds.count(0),dc=kinds.count(1),general=kinds.count(2))==row['kinds']
            for point in row['points']:
                result=model.schedule(kinds,point['banks']);assert model.validate(result)
                assert result['done_cycles']==point['cycles'] and result['payload_storage_bits']==point['payload_storage_bits']
            frames+=1;blocks+=len(kinds)
        for banks in (1,2,3):
            r=case['summary'][str(banks)];points=[row['points'][banks-1] for row in case['rows']]
            assert r['mean_projection_ms_at_unclosed_100MHz']==sum(p['cycles'] for p in points)/48/100000
            assert r['worst_projection_ms_at_unclosed_100MHz']==max(p['cycles'] for p in points)/100000
            assert r['payload_storage_bits']==banks*model.PAYLOAD_BITS_PER_BANK
    assert frames==288 and blocks==288*8100
    print(json.dumps(dict(frames=frames,source_blocks=blocks,modeled_schedules=frames*3,one_bank_control_frames=4,new_RTL_implemented=False,physical_30fps_proven=False)))

if __name__=='__main__':main()
