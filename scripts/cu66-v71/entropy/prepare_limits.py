"""Register per-band event limits before parameter/event range comparisons."""
from pathlib import Path
import hashlib,json
r=Path(__file__).resolve().parents[3];p=r/'fpga/experiments/cu66-v71/entropy';parent=p/'cu71_ab38_decoder_arithpipe_v2.sv';out=p/'cu71_ab38_decoder_arithpipe_v3.sv';sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
s=parent.read_text().replace('module cu71_ab38_decoder_arithpipe_v2 #(', 'module cu71_ab38_decoder_arithpipe_v3 #(')
s=s.replace('    logic [31:0] event_counts [0:2];', '''    logic [31:0] event_counts [0:2];
    // HEADER_CHECK establishes these private bounds before PARAM_CHECK.
    // Full17-bit block count times6-bit width fits23bits; no reset required.
    logic [22:0] event_limits [0:2];''')
anchor='                        for(i=0;i<4;i=i+1)lengths[i]<=h32(14+4*i);';assert s.count(anchor)==1
s=s.replace(anchor,'''                        event_limits[0]<=23'(23'(nblocks)*23'd5);
                        event_limits[1]<=23'(23'(nblocks)*23'd15);
                        event_limits[2]<=23'(23'(nblocks)*23'd43);
'''+anchor)
old="event_counts[stream-1]>{15'd0,nblocks}*{26'd0,band_width(stream-1)}";assert s.count(old)==1
s=s.replace(old,"event_counts[stream-1]>{9'd0,event_limits[2'(stream-2'd1)]}")
old="$signed({15'd0,nblocks}*{26'd0,band_width(band)})";assert s.count(old)==2
s=s.replace(old,"$signed({9'd0,event_limits[band]})")
out.write_text(s,newline='\n');m=json.loads((p/'arith-v2-derivation.json').read_text())
(p/'arith-v3-derivation.json').write_text(json.dumps({'parent':parent.relative_to(r).as_posix(),'parent_sha256':sha(parent),'candidate':out.relative_to(r).as_posix(),'candidate_sha256':sha(out),'new_states':m['new_states'],'scope':'Registeredexacteventlimits5*N/15*N/43*Naftervalidheader, beforeallparameter/eventrangechecks; removesstreamselect->multiply->compare. Noadditionalstates/latencyorclockchanges.','hardware':False},indent=2)+'\n');print('PREPARED_REGISTERED_EVENT_LIMITS',sha(out))
