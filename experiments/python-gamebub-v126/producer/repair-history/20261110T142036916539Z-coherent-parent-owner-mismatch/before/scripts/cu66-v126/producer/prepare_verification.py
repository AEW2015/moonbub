#!/usr/bin/env python3
"""Prepare source-bound geometry fixtures and lossless producer adapters only."""
import hashlib
import json
import re
from pathlib import Path

R=Path(__file__).resolve().parents[3]
S=R/'fpga/experiments/cu66-v126-producer'
V=S/'verification'
OLD=R/'fpga/experiments/cu66-v124-owner'


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')


def main():
    V.mkdir(parents=True,exist_ok=True);adapters=[];unchanged=[]
    def derive(original,target,edits):
        text=original.read_text()
        for e in edits:
            assert text.count(e['before'])==1,e['before'];text=text.replace(e['before'],e['after'],1)
        target.write_text(text)
        adapters.append(dict(original=str(original.relative_to(R)),original_sha256=sha(original),candidate=str(target.relative_to(R)),candidate_sha256=sha(target),edits=edits))
    for kind,original in [('original',OLD/'cs88_coefficients_v91k.sv'),('candidate',S/'cs88_coefficients_v91k.sv')]:
        derive(original,V/('ready_'+kind+'.sv'),[dict(before='module cs88_coefficients_v91k #',after='module ready_'+kind+' #')])
    for name in ['tb_ready.cpp','tb_controller.cpp']:
        original=OLD/'verification'/name;target=V/name;target.write_bytes(original.read_bytes())
        unchanged.append(dict(original=str(original.relative_to(R)),candidate=str(target.relative_to(R)),sha256=sha(target)))
    derive(OLD/'verification/ready_probe.sv',V/'ready_probe.sv',[
        dict(before='output logic probe_scale_equal);',after='output logic probe_scale_equal,output logic probe_refill_overlap);'),
        dict(before='\nendmodule',after='\nassign probe_refill_overlap=(old_dut.REFILL_OVERLAP!=0);\nendmodule')])
    derive(OLD/'verification/tb_owner.cpp',V/'tb_owner.cpp',[
        dict(before='#define BOTH(n,v) do{OLD(n)=(v);NEW(n)=(v);}while(0)',after='#define BOTH(n,v) do{OLD(n)=(v);NEW(n)=(v);}while(0)\n#include "successor_monitor.hpp"'),
        dict(before='static void tick_owner(Vready_probe&d){d.clk=0;equal(d);d.clk=1;equal(d);d.clk=0;equal(d);}',after='static void tick_owner(Vready_probe&d){d.clk=0;equal(d);const auto staged=successor_before(d,true);d.clk=1;equal(d);successor_after(d,staged,true);d.clk=0;equal(d);}')])
    derive(OLD/'verification/tb_owner_lanes.cpp',V/'tb_owner_lanes.cpp',[
        dict(before='int main(int argc,char**argv)',after='int inherited_lanes_main(int argc,char**argv)')])
    derive(OLD/'verification/caller_pair.hpp',V/'caller_pair.hpp',[
        dict(before='#include <stdexcept>',after='#include <stdexcept>\n#include "successor_monitor.hpp"'),
        dict(before='''    void eval() {
        Vready_probe::eval();''',after='''    void eval() {
        const bool rising=clk&&!monitor_clock_;
        SuccessorBefore staged{};
        if(rising)staged=successor_before(*this,false);
        Vready_probe::eval();'''),
        dict(before='''            throw std::runtime_error("V124 actual controller whole public/private/raw-scale pair mismatch");
    }
};''',after='''            throw std::runtime_error("V124 actual controller whole public/private/raw-scale pair mismatch");
        if(rising)successor_after(*this,staged,false);
        monitor_clock_=clk;
    }
private:
    bool monitor_clock_=false;
};''')])
    source=S/'cs88_coefficients_v91k.sv';text=source.read_text()
    quant=re.search(r'    function automatic logic \[10:0\] quant_cell\(.*?    endfunction',text,re.S).group()
    tiles=re.search(r'    function automatic logic \[12:0\] tiles\(.*?    endfunction',text,re.S).group()
    start=text.index('    logic [12:0] prepared_successor_tile;');end=text.index('`endif',start)+len('`endif')
    registers=text[start:end]
    address_task=re.search(r'    task automatic prepare_successor_address\(.*?    endtask',text,re.S).group()
    rom="    always_ff @(posedge clk)if(state==MAP_REQ)\n        prepared_successor_cell<=quant_cell(plane,prepared_successor_tile);"
    assert text.count(rom)==1
    capture='''                            cell_owner_valid<=1;cell_owner_frame<=frame_epoch;
                            cell_owner_child_epoch<=current_child_epoch;
                            cell_owner_plane<=plane;cell_owner_tile<=tile_cursor;
                            cell_owner_address<=prepared_successor_tile;'''
    advance="prepare_successor_address(tile_cursor+13'd1,tile_cursor+13'd2);"
    initial="prepare_successor_address(13'd0,13'd1);"
    next_cell="producer_cell_cache<=quant_cell(plane+2'd1,tile_cursor);"
    assert text.count(capture)==text.count(initial)==text.count(next_cell)==1 and text.count(advance)==2
    wrapper='''module producer_scalar_probe (
    input logic clk,reset,abort_packet,accepted_start,
    input logic [2:0] operation,
    input logic [1:0] fixture_plane,input logic [12:0] fixture_tile,
    input logic [10:0] fixture_cell,
    input logic [31:0] fixture_frame,fixture_child,
    output logic [1:0] out_plane,addr_plane,cell_plane,
    output logic [12:0] out_tile,out_address,addr_tile,cell_tile,cell_address,
    output logic [10:0] out_current_cell,out_successor_cell,
    output logic addr_valid,cell_valid,
    output logic [31:0] out_frame,out_child,addr_frame,cell_frame,cell_child
);
    localparam logic [7:0] MAP_REQ=9;
    wire [7:0] state=operation==2?MAP_REQ:8'd0;
    logic [1:0] plane;
    logic [12:0] tile_cursor;
    logic [10:0] producer_cell_cache;
    logic [31:0] frame_epoch,current_child_epoch;
'''
    tail='''
    // Fixture loads apply only old geometry. They are not controller chronology.
    // Data/task fragments above are exact production; range eligibility and
    // physical lookup ownership are checked by the whole-producer pair.
    always_ff @(posedge clk)begin
        if(reset||abort_packet)begin
            plane<=0;tile_cursor<=0;producer_cell_cache<=0;
            frame_epoch<=0;current_child_epoch<=0;
            address_owner_valid<=0;cell_owner_valid<=0;
        end else if(accepted_start)begin
            plane<=0;tile_cursor<=0;producer_cell_cache<=0;frame_epoch<=fixture_frame;
            address_owner_valid<=0;cell_owner_valid<=0;
        end else case(operation)
            0:begin
                plane<=fixture_plane;tile_cursor<=fixture_tile;producer_cell_cache<=fixture_cell;
                frame_epoch<=fixture_frame;current_child_epoch<=fixture_child;
            end
            1:begin ADVANCE_CALL end
            2:begin
CELL_CAPTURE
            end
            3:begin
                ADVANCE_CALL
                tile_cursor<=tile_cursor+1;producer_cell_cache<=prepared_successor_cell;
            end
            4:begin
                address_owner_valid<=0;cell_owner_valid<=0;
                if(plane!=2)begin plane<=plane+1;NEXT_CELL end
            end
            5:begin INITIAL_CALL tile_cursor<=0;producer_cell_cache<=0;end
            default:begin end
        endcase
    end
    assign out_plane=plane;assign out_tile=tile_cursor;
    assign out_current_cell=producer_cell_cache;
    assign out_address=prepared_successor_tile;assign out_successor_cell=prepared_successor_cell;
    assign addr_valid=address_owner_valid;assign cell_valid=cell_owner_valid;
    assign addr_frame=address_owner_frame;assign addr_plane=address_owner_plane;assign addr_tile=address_owner_tile;
    assign cell_frame=cell_owner_frame;assign cell_child=cell_owner_child_epoch;assign cell_plane=cell_owner_plane;
    assign cell_tile=cell_owner_tile;assign cell_address=cell_owner_address;
    assign out_frame=frame_epoch;assign out_child=current_child_epoch;
endmodule
'''.replace('ADVANCE_CALL',advance).replace('INITIAL_CALL',initial).replace('NEXT_CELL',next_cell).replace('CELL_CAPTURE',capture)
    fragments=[registers,tiles,quant,address_task,rom]
    (V/'producer_scalar_probe.sv').write_text(wrapper+'\n'.join(fragments)+tail)
    extraction=dict(source=str(source.relative_to(R)),source_sha256=sha(source),target=str((V/'producer_scalar_probe.sv').relative_to(R)),target_sha256=sha(V/'producer_scalar_probe.sv'),wrapper=wrapper,fragments=fragments,tail=tail,call_fragments=[advance,initial,next_cell,capture],scope='Exact production functions/register/task/ROM fragments and old geometry writes. Scalar wrapper stages arbitrary full13 keys by old-field fixture loading; it is not original controller eligibility/state/debt behavior. Full request range, firstfault and response owner checks belong to actual producer/caller pairs.')
    # Every old C++ need/require body remains as an immutable semantic check.
    import collections
    checks=lambda t:collections.Counter(re.findall(r'(?:need|require_owner)\(.*?\);',t,re.S))
    for e in adapters:
        if e['original'].endswith(('.cpp','.hpp')):assert not checks((R/e['original']).read_text())-checks((R/e['candidate']).read_text())
    authored=['successor_monitor.hpp','successor_priming.hpp','tb_successor.cpp','tb_successor_scalar.cpp']
    new_inputs=[dict(path=str((V/name).relative_to(R)),sha256=sha(V/name)) for name in authored if (V/name).exists()]
    save(S/'verification-recipe.json',dict(schema='v126-producer-verification-derivation-v1',adapters=adapters,unchanged=unchanged,scalar_extraction=extraction,new_verification_inputs=new_inputs,old_require_checks_removed=0,new_payload_or_owner_forces=0,prepared_priming_is_natural_traffic=False))
    print('V126_PRODUCER_VERIFICATION_PREPARED',len(adapters),len(unchanged))


if __name__=='__main__':main()
