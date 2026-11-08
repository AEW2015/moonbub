#!/usr/bin/env python3
import hashlib,json,importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];BASE=ROOT/'fpga/experiments/cu66-v109-fetch/br88_packet_ingress_sync_v91h.sv';ORIGINAL=ROOT/'fpga/experiments/cu66-v108-capacity/br88_packet_ingress_sync_v91h.sv';OUT=ROOT/'fpga/experiments/cu66-v109-request';V=OUT/'verification'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 assert sha(BASE)=='4d6a16d0b89aa067fe3e7acc01351ea0bacac694cc63fb681a1471ee4683d044';text=BASE.read_text();edits=[]
 def edit(a,b):
  nonlocal text
  assert text.count(a)==1,a;text=text.replace(a,b,1);edits.append(dict(before=a,after=b,expected_occurrences=1))
 edit('    logic [31:0] expected_fetch_addr;', '''    logic [31:0] expected_fetch_addr;
    // Request payload is owned only in FETCH_REQ; no reset or kill enable.
    logic [31:0] prepared_request_addr, next_request_addr;
    logic prepared_request_in_bounds;
    logic [5:0] next_request_index;
    always_comb begin
        next_request_index=fetch_index+6'd1;
        next_request_addr=fetch_base+32'(next_request_index);
        if(fetch_kind==F_HEADER && next_request_index>=42)
            next_request_addr=size_bytes-4+32'(next_request_index)-42;
        if(fetch_kind==F_DESCRIPTOR && next_request_index==6)
            next_request_addr=fetch_base+lengths[band]-1;
    end''')
 edit('            fetch_base<=base; fetch_return<=continuation; buffer_bytes<=0; state<=FETCH_REQ;', '''            fetch_base<=base; fetch_return<=continuation; buffer_bytes<=0; state<=FETCH_REQ;
            // Initial index is zero for every fetch kind: the first address is base.
            prepared_request_addr<=base;
            prepared_request_in_bounds<=base<size_bytes && base<32'(MAX_PACKET_BYTES);''')
 edit('        stage_read_req=state==FETCH_REQ && !cancelled && fetch_address<size_bytes &&\n            fetch_address<32\'(MAX_PACKET_BYTES) && !(context_active && (ctx_error!=0 || ctx_done));', '''        stage_read_req=state==FETCH_REQ && !cancelled && prepared_request_in_bounds &&
            !(context_active && (ctx_error!=0 || ctx_done));''')
 edit("ram_data<=memory[AW'(fetch_address)]; ram_addr<=fetch_address; ram_epoch<=context_epoch;", "ram_data<=memory[AW'(prepared_request_addr)]; ram_addr<=prepared_request_addr; ram_epoch<=context_epoch;")
 edit('    always_ff @(posedge clk) begin\n        if(reset || abort_packet) begin', '''    always_ff @(posedge clk) begin
        // Speculative private preparation is independent of cancellation. On a
        // successful nonfinal WAIT this becomes the next request's payload. A
        // final response, failure or cancellation leaves it unowned; begin_fetch
        // always replaces it before a new sequence can enter FETCH_REQ.
        if(state==FETCH_WAIT) begin
            prepared_request_addr<=next_request_addr;
            prepared_request_in_bounds<=next_request_addr<size_bytes && next_request_addr<32'(MAX_PACKET_BYTES);
        end
        if(reset || abort_packet) begin''')
 edit("else if(fetch_address>=size_bytes || fetch_address>=32'(MAX_PACKET_BYTES)) fail_packet(4);",'else if(!prepared_request_in_bounds) fail_packet(4);')
 edit('        assert(!stage_read_req || (!stage_write && fetch_address<size_bytes && fetch_address<32\'(MAX_PACKET_BYTES)))', '''        if(state==FETCH_REQ)begin
            assert(prepared_request_addr==fetch_address)else $fatal(1,"prepared request address owner mismatch");
            assert(prepared_request_in_bounds==(fetch_address<size_bytes && fetch_address<32'(MAX_PACKET_BYTES)))
                else $fatal(1,"prepared request bounds owner mismatch");
        end
        assert(!stage_read_req || (!stage_write && fetch_address<size_bytes && fetch_address<32'(MAX_PACKET_BYTES)))''')
 p=OUT/BASE.name;p.write_text(text);rebuilt=BASE.read_text()
 for e in edits:rebuilt=rebuilt.replace(e['before'],e['after'],1)
 assert rebuilt==text
 for e in reversed(edits):assert rebuilt.count(e['after'])==1;rebuilt=rebuilt.replace(e['after'],e['before'],1)
 assert rebuilt==BASE.read_text()
 (OUT/'edit-recipe.json').write_text(json.dumps(dict(schema='v109-request-existing-prepare-edges-v1',status='PREPARED_NOT_RTL_QUALIFIED',public_added_cycles=0,production={BASE.name:dict(original=str(BASE.relative_to(ROOT)),original_sha256=sha(BASE),candidate_sha256=sha(p),edits=edits)},qualification_baseline=dict(path=str(ORIGINAL.relative_to(ROOT)),sha256=sha(ORIGINAL))),indent=2,sort_keys=True)+'\n')
 adapters=[]
 for variant,source in [('original',ORIGINAL),('candidate',p)]:
  a='module br88_packet_ingress_sync_v91h ';b='module ingress_'+variant+' ';t=source.read_text();assert t.count(a)==1;q=V/('ingress_'+variant+'.sv');q.write_text(t.replace(a,b,1));adapters.append(dict(source=str(source.relative_to(ROOT)),path=str(q.relative_to(ROOT)),source_sha256=sha(source),sha256=sha(q),renames=[[a,b]]))
 for n in ('ingress_capture_probe.sv','tb_capture.cpp'):(V/n).write_bytes((BASE.parent/'verification'/n).read_bytes())
 fixture=BASE.parent/'verification/tb_fetch.cpp';t=fixture.read_text();before='BOTH(ram_valid,0U);d.eval();uint32_t address=c.base+c.index;';after='BOTH(ram_valid,0U);uint32_t address=c.base+c.index;';assert t.count(before)==1;t=t.replace(before,after,1);before2='address=c.base+c.length-1;need(d.stage_read_addr==address';after2='''address=c.base+c.length-1;
   // Explicit prepared prior-request formula; never derive this from ram_addr.
   NEW(prepared_request_addr)=address;
   NEW(prepared_request_in_bounds)=address<c.size&&address<49152U;
   d.eval();need(d.stage_read_addr==address''';assert t.count(before2)==1;t=t.replace(before2,after2,1);(V/'tb_fetch.cpp').write_text(t)
 (V/'adapters.json').write_text(json.dumps(dict(schema='v109-request-complete-body-adapters-v1',adapters=adapters,all_public_ports_compared=True,inherited_frozen_fixture_files={n:sha(BASE.parent/'verification'/n) for n in ('ingress_capture_probe.sv','tb_capture.cpp')},fixture_source=str(fixture.relative_to(ROOT)),fixture_source_sha256=sha(fixture),fixture_edits=[[before,after],[before2,after2]],fixture_sha256=sha(V/'tb_fetch.cpp')),indent=2,sort_keys=True)+'\n')
 print('REQUEST_PREPARED',sha(p))
if __name__=='__main__':main()
