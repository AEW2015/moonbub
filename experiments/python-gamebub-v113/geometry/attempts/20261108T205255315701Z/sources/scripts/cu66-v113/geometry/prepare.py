from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[3]; S=R/'fpga/experiments/cu66-v113-geometry';V=S/'verification';V.mkdir(parents=True,exist_ok=True)
P=R/'fpga/experiments/cu66-v110-count-domain/br88_context.sv'; original=P.read_text(); s=original;edits=[]
def edit(a,b):
 global s
 assert s.count(a)==1,(a[:100],s.count(a));s=s.replace(a,b,1);edits.append(dict(before=a,after=b))
fields='''    // Private two-stage preparation; no public handshake or latency changes.
    logic [21:0] geometry_byte0,geometry_byte1,geometry_byte2,geometry_byte3;
    logic geometry_bytes_valid,geometry_valid;
    logic [7:0] geometry_byte_band,geometry_band;
    logic [31:0] geometry_byte_position,geometry_position;
    logic [15:0] geometry_byte_emitted,geometry_emitted;
    logic [21:0] prepared_geometry;
'''
edit('    logic [31:0] start_limit;','    logic [31:0] start_limit;\n'+fields)
func='''    function automatic logic [21:0] prepared_position_geometry(
        input logic [1:0] b,input logic [21:0] w0,w1,w2,w3);
        logic [7:0] total,corrected;
        logic [15:0] q0,q1,q2,q3,quotient;
        begin
            total=remainder_sum4({2'd0,w0[5:0]},{2'd0,w1[5:0]},{2'd0,w2[5:0]},{2'd0,w3[5:0]});
            corrected=correction_index(b,total);
            q0=quotient_sum5(w0[21:6],w1[21:6],w2[21:6],w3[21:6],16'd0);
            q1=quotient_sum5(w0[21:6],w1[21:6],w2[21:6],w3[21:6],16'd1);
            q2=quotient_sum5(w0[21:6],w1[21:6],w2[21:6],w3[21:6],16'd2);
            q3=quotient_sum5(w0[21:6],w1[21:6],w2[21:6],w3[21:6],16'd3);
            case(corrected[7:6])
                0:quotient=q0;
                1:quotient=q1;
                2:quotient=q2;
                3:quotient=q3;
            endcase
            return {quotient,corrected[5:0]};
        end
    endfunction
'''
stage='''    // At E request acceptance registers PREFIX in Rice. PREFIX at E+1 and
    // SUFFIX at E+2 precede its response consumption at E+3, even k==0.
    // Stage one is ready at E; stage two is ready at E+1. Request stalls
    // repeat coherent preparation. Reset/start/abort revoke both valid bits.
    always_ff @(posedge clk) begin
        if (reset || abort_context || start) begin
            geometry_bytes_valid<=0;geometry_valid<=0;
        end else begin
            if (state==REQ_LEVEL || state==REQ_DC) begin
                geometry_byte0<=byte_qr(context_band[1:0],0,position[7:0]);
                geometry_byte1<=byte_qr(context_band[1:0],1,position[15:8]);
                geometry_byte2<=byte_qr(context_band[1:0],2,position[23:16]);
                geometry_byte3<=byte_qr(context_band[1:0],3,position[31:24]);
                geometry_byte_band<=context_band;geometry_byte_position<=position;
                geometry_byte_emitted<=emitted[15:0];geometry_bytes_valid<=1;
                geometry_valid<=0;
            end
            if ((state==WAIT_LEVEL || state==WAIT_DC) && geometry_bytes_valid) begin
                case(geometry_byte_band)
                    1,2,3:prepared_geometry<=prepared_position_geometry(geometry_byte_band[1:0],geometry_byte0,geometry_byte1,geometry_byte2,geometry_byte3);
                    default:prepared_geometry<={geometry_byte_emitted,6'd0};
                endcase
                geometry_band<=geometry_byte_band;geometry_position<=geometry_byte_position;
                geometry_emitted<=geometry_byte_emitted;geometry_valid<=1;
            end
            if (state!=REQ_LEVEL && state!=REQ_DC && state!=WAIT_LEVEL && state!=WAIT_DC) begin
                geometry_bytes_valid<=0;geometry_valid<=0;
            end
        end
    end
'''
edit('    always_comb begin\n        case (band)',func+stage+'    always_comb begin\n        case (band)')
edit("                    out_block<=16'(sparse_block); out_index<=sparse_index;",'                    {out_block,out_index}<=prepared_geometry;')
# Original scalar / modulo oracle is independent of byte ROM and reduction.
assertions='''    function automatic logic [21:0] original_scalar_geometry(input logic [7:0] b,input logic [31:0] n,input logic [15:0] e);
        case(b)
            1:return {16'(n/32'd5),ZIGZAG[6'(32'd1+n%32'd5)]};
            2:return {16'(n/32'd15),ZIGZAG[6'(32'd6+n%32'd15)]};
            3:return {16'(n/32'd43),ZIGZAG[6'(32'd21+n%32'd43)]};
            default:return {e,6'd0};
        endcase
    endfunction
    always_ff @(posedge clk) if (!reset && !abort_context && !start &&
        parser_valid && parser_ready && parser_error==0 && (state==WAIT_DC || state==WAIT_LEVEL)) begin
        assert(geometry_valid) else $fatal(1,"geometry unavailable on actual Rice response");
        assert(geometry_band==context_band && geometry_position==position && geometry_emitted==emitted[15:0])
            else $fatal(1,"geometry key mismatch");
        assert({sparse_block,sparse_index}==original_scalar_geometry(context_band,position,emitted[15:0]))
            else $fatal(1,"original byte geometry differs from scalar");
        assert(prepared_geometry==original_scalar_geometry(context_band,position,emitted[15:0]))
            else $fatal(1,"prepared geometry differs from original scalar");
    end
'''
edit('`ifndef SYNTHESIS\n    always_ff', '`ifndef SYNTHESIS\n'+assertions+'    always_ff')
(S/'br88_context.sv').write_text(s)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
(S/'edit-recipe.json').write_text(json.dumps(dict(schema='v113-private-geometry-v1',original=str(P.relative_to(R)),candidate=str((S/'br88_context.sv').relative_to(R)),original_sha256=sha(P),candidate_sha256=sha(S/'br88_context.sv'),edits=edits,added_public_cycles=0,all_original_assertions_retained=True,PREVALIDATED_EVENT_COUNT_scope_unchanged=True),indent=2)+'\n')
# Full actual context bodies; adapters only rename and expose existing combinational geometry.
adapters=[]
for name,p in [('original',P),('candidate',S/'br88_context.sv')]:
 t=p.read_text();changes=[['module br88_context','module context_'+name],['\n);',',\n    output logic [15:0] verify_sparse_block,\n    output logic [5:0] verify_sparse_index\n);'],['\nendmodule','\n    assign verify_sparse_block=sparse_block;assign verify_sparse_index=sparse_index;\nendmodule']]
 for a,b in changes:assert t.count(a)==1;t=t.replace(a,b,1)
 q=V/('context_'+name+'.sv');q.write_text(t);adapters.append(dict(source=str(p.relative_to(R)),source_sha256=sha(p),path=str(q.relative_to(R)),sha256=sha(q),edits=changes))
# Reuse entire existing checker/wrapper; generic original changes to current Count body.
for name in ['context_probe.sv','inherited_context.cpp','tb_count_domain.cpp']:
 q=V/name;q.write_bytes((R/'fpga/experiments/cu66-v110-count-domain/verification'/name).read_bytes())
# Geometry stage standalone probe: exact functions, fields, and production stage block.
start=s.index('    // Exact full32-bit');end=s.index('    always_comb begin\n        case (band)')
functions=s[start:end].replace(stage,'')
probe='''module geometry_stage_probe (
 input logic clk,reset,start,abort_context,
 input logic [3:0] state,input logic [7:0] context_band,
 input logic [31:0] position,emitted,
 output logic geometry_valid,geometry_bytes_valid,
 output logic [21:0] prepared_geometry,
 output logic [7:0] geometry_band,
 output logic [31:0] geometry_position,
 output logic [15:0] geometry_emitted);
 localparam logic [3:0] REQ_DC=1,WAIT_DC=2,REQ_LEVEL=5,WAIT_LEVEL=6;
'''+s[s.index('    localparam logic [5:0] ZIGZAG'):s.index('    logic [3:0] state;')]+fields.replace('    logic geometry_bytes_valid,geometry_valid;\n','').replace('    logic [7:0] geometry_byte_band,geometry_band;','    logic [7:0] geometry_byte_band;').replace('    logic [31:0] geometry_byte_position,geometry_position;','    logic [31:0] geometry_byte_position;').replace('    logic [15:0] geometry_byte_emitted,geometry_emitted;','    logic [15:0] geometry_byte_emitted;').replace('    logic [21:0] prepared_geometry;\n','')+functions+stage+'endmodule\n'
(V/'geometry_stage_probe.sv').write_text(probe)
(V/'adapters.json').write_text(json.dumps(dict(adapters=adapters,geometry_stage=dict(exact_production_fields=True,exact_production_stage=True,exact_production_functions=True)),indent=2)+'\n')

exec((Path(__file__).parent/'extra.py').read_text())
