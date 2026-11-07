#!/usr/bin/env python3
"""Exact, checked derivations; original scalar implementation stays frozen."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]; AREA=Path(__file__).resolve().parent
records=[]
def load(name):return (ROOT/name).read_text()
def rep(s,a,b,n=1):
 assert s.count(a)==n,(a,s.count(a),n)
 return s.replace(a,b)
def save(name,src,s):
 (AREA/name).parent.mkdir(parents=True,exist_ok=True)
 (AREA/name).write_text(s)
 records.append(dict(source=src,source_sha256=hashlib.sha256((ROOT/src).read_bytes()).hexdigest(),derived=name,derived_sha256=hashlib.sha256(s.encode()).hexdigest()))
extra='''    output logic [63:0] count_direct_consumes,count_canonical_consumed,
    output logic direct_consume,
    output logic [18:0] direct_addr,
    output logic [31:0] direct_epoch,
    output logic [7:0] direct_data,
'''
ports='''    input logic probe_hit,
    input logic [7:0] probe_data,
    output logic probe_valid,
    output logic [18:0] probe_addr,
    output logic [31:0] probe_epoch,
'''+extra
src='fpga/experiments/cu66-v91k-cache/canonical_rgb565_cached.sv';s=load(src)
s=rep(s,'    output logic mem_req_valid,',ports+'    output logic mem_req_valid,')
s=rep(s,'    logic running;','    logic running;\n    logic fill_write;\n    logic [7:0] fill_data;')
s=rep(s,'    assign mem_req_valid=running&&(state==FILL_REQ||state==LUMA_REQ)&&!pending&&!kill;', '''    // Probe eligibility is independent of the hit-gated external request.
    assign probe_valid=running&&(state==FILL_REQ||state==LUMA_REQ)&&!pending&&!kill&&!start;
    assign probe_addr=mem_req_addr;
    assign probe_epoch=epoch;
    assign direct_consume=probe_valid&&probe_hit;
    assign direct_addr=probe_addr;
    assign direct_epoch=epoch;
    assign direct_data=probe_data;
    assign mem_req_valid=probe_valid&&!probe_hit;
    assign fill_write=(pending&&mem_rsp_valid&&mem_rsp_epoch==epoch&&running&&
        state==FILL_WAIT&&!mem_rsp_error&&!kill)||(direct_consume&&state==FILL_REQ);
    assign fill_data=direct_consume?probe_data:mem_rsp_data;''')
s=rep(s,'        if(pending&&mem_rsp_valid&&mem_rsp_epoch==epoch&&running&&\n                state==FILL_WAIT&&!mem_rsp_error&&!kill)begin','        if(fill_write)begin')
# Only the unchanged byte-enable RAM write block uses the common source mux.
first=s.index('        if(fill_write)begin');last=s.index('    always_comb begin',first)
s=s[:first]+s[first:last].replace('<=mem_rsp_data;','<=fill_data;')+s[last:]
s=rep(s,'                count_row_fills<=0;count_cache_hits<=0;','                count_row_fills<=0;count_cache_hits<=0;\n                count_direct_consumes<=0;count_canonical_consumed<=0;',2)
s=rep(s,'                    if(mem_rsp_epoch==epoch)count_responses<=count_responses+1;','''                    if(mem_rsp_epoch==epoch)count_responses<=count_responses+1;
                    if(mem_rsp_epoch==epoch&&!mem_rsp_error&&(state==FILL_WAIT||state==LUMA_WAIT))
                        count_canonical_consumed<=count_canonical_consumed+1;''')
fill=s[s.index('                        if(fill_column==359)begin'):s.index('                    end else if(state==LUMA_WAIT)')]
s=rep(s,'                if(mem_req_valid&&mem_req_ready)begin','''                if(direct_consume)begin
                    count_direct_consumes<=count_direct_consumes+1;
                    count_canonical_consumed<=count_canonical_consumed+1;
                    if(state==FILL_REQ)begin
'''+fill+'''                    end else begin luma<=probe_data;state<=LOOKUP_REQ;end
                end
                if(mem_req_valid&&mem_req_ready)begin''')
s=rep(s,'count_reads==518400&&count_row_fills==240','count_canonical_consumed==518400&&count_reads==count_responses&&count_reads+count_direct_consumes==count_canonical_consumed&&count_row_fills==240')
s=rep(s,'        if(mem_req_valid)assert(','''        if(direct_consume)assert(!pending&&!mem_req_valid&&probe_valid&&probe_addr<518400&&(state==FILL_REQ||state==LUMA_REQ))else $fatal(1,"direct consume ownership");
        if(mem_req_valid)assert(''')
save('canonical_rgb565_cached.sv',src,s)
src='fpga/experiments/cu66-v91k-lines/canonical_line_reader.sv';s=load(src)
s=rep(s,'    input logic byte_req_valid,','''    input logic probe_valid,
    input logic [18:0] probe_addr,
    input logic [31:0] probe_epoch,
    output logic probe_hit,
    output logic [7:0] probe_data,
    input logic byte_req_valid,''')
s=rep(s,'    logic request_hit;','''    logic request_hit;
    logic [1:0] probe_plane;
    assign probe_plane=probe_addr<345600?2'd0:probe_addr<432000?2'd1:2'd2;
    // A read-only view of the existing three 16B plane slots: zero new payload.
    assign probe_hit=probe_valid&&active&&state==IDLE&&!pending&&!byte_pending&&!byte_rsp_valid&&
        !reset&&!cancel&&!start&&!finish&&error==0&&probe_epoch==epoch&&probe_addr<518400&&
        line_valid[probe_plane]&&line_address[probe_plane]=={probe_addr[18:4],4'b0};
    assign probe_data=probe_hit?line_data[probe_plane][8*probe_addr[3:0]+:8]:8'd0;''')
save('canonical_line_reader.sv',src,s)
src='fpga/experiments/cu66-v91k-lines/canonical_rgb565_lines.sv';s=load(src)
s=rep(s,'    output logic byte_rsp_error\n', '    output logic byte_rsp_error,\n'+extra.rstrip(',\n')+'\n')
s=rep(s,'    logic core_ready,','''    logic probe_valid,probe_hit;
    logic [18:0] probe_addr;
    logic [31:0] probe_epoch;
    logic [7:0] probe_data;
    logic core_ready,''')
s=rep(s,'    canonical_rgb565_cached core (','''    canonical_rgb565_cached core (
        .probe_valid(probe_valid),.probe_addr(probe_addr),.probe_epoch(probe_epoch),.probe_hit(probe_hit),.probe_data(probe_data),
        .count_direct_consumes(count_direct_consumes),.count_canonical_consumed(count_canonical_consumed),
        .direct_consume(direct_consume),.direct_addr(direct_addr),.direct_epoch(direct_epoch),.direct_data(direct_data),''')
s=rep(s,'    canonical_line_reader reader (','''    canonical_line_reader reader (
        .probe_valid(probe_valid),.probe_addr(probe_addr),.probe_epoch(probe_epoch),.probe_hit(probe_hit),.probe_data(probe_data),''')
save('canonical_rgb565_lines.sv',src,s)
src='fpga/experiments/cu66-v91l-converter/canonical_rgb565_tiled.sv';s=load(src)
s=rep(s,'    output logic byte_rsp_error\n', '    output logic byte_rsp_error,\n'+extra.rstrip(',\n')+'\n')
connections='''  .count_direct_consumes(count_direct_consumes),.count_canonical_consumed(count_canonical_consumed),
  .direct_consume(direct_consume),.direct_addr(direct_addr),.direct_epoch(direct_epoch),.direct_data(direct_data),
'''
s=rep(s,' canonical_rgb565_lines converter(',' canonical_rgb565_lines converter(\n'+connections)
save('canonical_rgb565_tiled.sv',src,s)
src='fpga/experiments/cu66-v91l-converter/canonical_rgb565_timed.sv';s=load(src)
s=rep(s,' output logic [15:0] peek_data,',extra+' output logic [15:0] peek_data,')
burst=rep(s,' canonical_rgb565_tiled #(.RETAIN_ROWS(RETAIN_ROWS)) joined(',' canonical_rgb565_tiled #(.RETAIN_ROWS(RETAIN_ROWS)) joined(\n'+connections)
save('burst/canonical_rgb565_timed.sv',src,burst)
scalar=rep(s,' wire read_clk;', ''' assign count_direct_consumes=0;
 assign count_canonical_consumed=count_responses;
 assign direct_consume=0;assign direct_addr=0;assign direct_epoch=0;assign direct_data=0;
 wire read_clk;''')
save('scalar/canonical_rgb565_timed.sv',src,scalar)
(AREA/'derivations.json').write_text(json.dumps(dict(schema='cu66-v91l-burst-derivations-v1',sources=records,payload_bytes_added=0,counters='reads/responses remain external byte leases/returns; consumed counts successful external returns plus direct hits'),indent=2)+'\n')
