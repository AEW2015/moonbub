"""Decode USB_C38 Base64+CRC records, preserving all raw fields and flags."""
import base64
import json
import struct
import zlib

LAYOUT = struct.Struct('<BBHIQQQIIIIIHBBQHQQQ')
NAMES = ('version type index epoch sequence time_us received_us incoming_id incoming_offset '
         'active_id expected_offset queued flags kind phase phase_since_us detail lock_us qspi_us consumer_us').split()
KINDS = ['Enqueue','Dequeue','Phase','QueueOverflow','Failure','Recycle','Complete','Transfer']
PHASES = ['Idle','Packet','Begin','Admission','Flush','Lock','Access','Qspi','Commit','ErrorAbort','Log','Feedback','Yield','Recycle','BufferDrop','Maintenance']

def decode(line):
    token = line.split('USB_C38 ',1)[1].strip()
    raw = base64.b64decode(token,validate=True)
    if len(raw)!=94 or zlib.crc32(raw[:-4])!=struct.unpack('<I',raw[-4:])[0]:
        raise ValueError('Length/CRC mismatch')
    r=dict(zip(NAMES,LAYOUT.unpack(raw[:-4])))
    if r['version']!=1 or r['type'] not in (0,1) or r['flags']&~0x1ff:
        raise ValueError('Unsupported version/type/flags')
    if r['type']==0 and (r['kind']>=len(KINDS) or r['phase']>=len(PHASES)):
        raise ValueError('Unknown event mapping')
    if r['type']==1 and (r['kind']!=255 or r['phase']!=255):
        raise ValueError('Invalid failure mapping')
    r['kind_name']=KINDS[r['kind']] if r['type']==0 else 'FailureIdentity'
    r['phase_name']=PHASES[r['phase']] if r['type']==0 else None
    for bit,name in enumerate(['incoming_frame_valid','incoming_offset_valid','active_frame_valid',
            'active_offset_valid','queue_valid','phase_valid','duration_clipped','tail_ambiguous','consumer_valid']):
        r[name]=bool(r['flags']&(1<<bit))
    return r

if __name__=='__main__':
    import argparse
    from pathlib import Path
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('raw',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    if a.output.exists():p.error('Output already exists')
    rows=[];errors=[]
    for i,line in enumerate(a.raw.read_text(errors='replace').splitlines()):
        if 'USB_C38 ' in line:
            try:rows.append(decode(line))
            except (ValueError,IndexError) as e:errors.append(dict(line=i+1,error=str(e)))
    seen=set();duplicates=[]
    for r in rows:
        key=(r['epoch'],r['type'],r['index'])
        if key in seen:duplicates.append(key)
        seen.add(key)
    a.output.write_text(json.dumps(dict(records=rows,decode_errors=errors,duplicate_indices=duplicates,
        limits='Compare index coverage with frozen summary counts; no claim that absent records were never received.'),indent=2)+'\n')
    if errors or duplicates:raise SystemExit(1)
