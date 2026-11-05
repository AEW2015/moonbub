"""Fixed additional source IDs24..47; no frozen globals or policy changes."""
from pathlib import Path
START,STOP=24,48

def triplets(source_case,control_case,golden_case):
    if Path(source_case['media_file']).stem!=control_case['scene']or control_case['scene']!=golden_case['scene']:raise ValueError('same actual source cohort')
    result=[]
    for fid in range(START,STOP):
        values=source_case['frames'][fid],control_case['rows'][fid],golden_case['rows'][fid]
        if any(row['id']!=fid for row in values):raise ValueError('preserve original global source ID')
        if values[1]['selected_background']!=16:raise ValueError('frozen53 quantizer qualification')
        if values[1]['requested_key']!=(fid==START):raise ValueError('key24 then P25..47')
        if fid==START and values[1]['reference_id']!=4294967295:raise ValueError('fresh key24 has no previous reference')
        if fid>START and values[1]['reference_id']!=fid-1:raise ValueError('consecutive fixedzero HUD reference')
        result.append(values)
    return tuple(result)
