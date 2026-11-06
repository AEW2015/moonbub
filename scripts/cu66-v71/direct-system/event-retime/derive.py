"""Event-only reversible retime patch; owner/HUD producer logic unchanged."""
from pathlib import Path
import hashlib,json
r=Path(__file__).resolve().parents[4];p=r/'fpga/experiments/cu66-v71/direct-system/board-math-v001/cu71_receiver_direct_math.sv';d=r/'fpga/experiments/cu66-v71/direct-system/event-retime-v001';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(p)=='7991bfc59ddf2942080185196b103e9af0b72b94857460f5570b92d035bd71d3'
s=p.read_text();olddecl='    logic [255:0] events[0:7];';newdecl=olddecl+'''
    // Physical payload writes lag the logical event edge; diagnostic bypass
    // preserves the original immediate ring contents. Payload needs no reset.
    logic [255:0] event_record_pending;
    logic [2:0] event_write_index;
    logic event_pending_valid;
    logic [7:0] event_slot_valid;'''
a=s.index('    always_ff @(posedge clk)begin\n        if(rst)begin\n            event_sequence<=0;');b=s.index('    always_comb begin\n        diag_data=0;',a);old=s[a:b]
record="{8'd0,last_address,stage,event_code,fatal_code,8'd0,\n                event_fid,event_generation[63:32],event_generation[31:0],clock_count[63:32],clock_count[31:0],event_sequence}"
assert record in old
new='''    always_ff @(posedge clk)begin
        // No event-derived CE or bulk reset on the computed 256-bit record.
        event_record_pending<='''+record+''';
        event_write_index<=event_sequence[2:0];
        if(rst)begin
            event_sequence<=0;event_overwrites<=0;
            event_pending_valid<=0;event_slot_valid<=0;
        end else begin
            // Procedural-if X semantics match the original event predicate.
            event_pending_valid<=0;
            if(event_code!=0)begin
                event_pending_valid<=1;
                event_slot_valid[event_sequence[2:0]]<=1;
                event_sequence<=event_sequence+1;
                if(event_sequence>=8)event_overwrites<=event_overwrites+1;
            end
            if(event_pending_valid)events[event_write_index]<=event_record_pending;
        end
    end
'''
oldread="                    diag_data=events[diag_address[7:5]][int'(diag_address[4:2])*32+:32];"
newread='''                    begin
                        if(event_pending_valid&&diag_address[7:5]==event_write_index)
                            diag_data=event_record_pending[int'(diag_address[4:2])*32+:32];
                        else if(event_slot_valid[diag_address[7:5]])
                            diag_data=events[diag_address[7:5]][int'(diag_address[4:2])*32+:32];
                    end'''
swaps=[('module cu71_receiver_direct_math #(','module cu71_receiver_eventpipe #('),(olddecl,newdecl),(old,new),(oldread,newread)]
t=s
for x,y in swaps:assert t.count(x)==1;t=t.replace(x,y)
back=t
for x,y in reversed(swaps):assert back.count(y)==1;back=back.replace(y,x)
assert back==s
out=d/'cu71_receiver_eventpipe.sv';assert not out.exists();out.write_text(t,newline='\n')
(d/'patch.json').write_text(json.dumps(dict(parent=str(p.relative_to(r)).replace('\\','/'),parent_sha256=sha(p),source_sha256=sha(out),reversal_exact=True,swaps=swaps,scope='Eventdeclarations/storage/ringreadonly; producer,logicalcounteredge,allowner/HUD/firstfaultlogicunchanged'),indent=2)+'\n')
# Extract exact storage/read fragments into independent 4-state A/B models.
ports='''(input logic clk,rst,input logic[7:0]event_code,stage,fatal_code,
 input logic[23:0]last_address,input logic[31:0]event_fid,input logic[63:0]event_generation,clock_count,
 input logic[9:0]diag_address,output logic[31:0]diag_data,event_sequence,event_overwrites);
'''
for name,decl,block,read in [('event_old',olddecl,old,oldread),('event_new',newdecl,new,newread)]:
 text='module '+name+ports+decl+'\n'+block+'''always_comb begin
 diag_data=0;
 if(diag_address==10'h058)diag_data=event_sequence;
 else if(diag_address==10'h05c)diag_data=event_overwrites;
 else if(diag_address>=10'h100&&diag_address<10'h200&&diag_address[1:0]==0)
'''+read+'\nend\nendmodule\n'
 (d/(name+'.sv')).write_text(text,newline='\n')
print('DERIVED_EVENT_RETIME',sha(out))
