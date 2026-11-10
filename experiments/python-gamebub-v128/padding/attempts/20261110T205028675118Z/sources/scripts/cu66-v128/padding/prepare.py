#!/usr/bin/env python3
"""Prepare the owned V128 header-padding cache; default verifies read-only."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[3]
ORIGINAL = ROOT / 'fpga/experiments/cu66-v125-tile/cs88_admission_v91i2a.sv'
ORIGINAL_SHA = '2f65ff770775404071e383890c75549ccb08ec9998993c86f1662cfed65d71eb'
ALIAS = 'fpga/experiments/cu66-v91i2/cs88_admission_v91i2a.sv'
DEST = ROOT / 'fpga/experiments/cu66-v128-padding'
CACHE = '''    // V128_PADDING_CACHE_BEGIN: one unreset Boolean payload, owned only
    // after the current header's ordered116..127 byte-load edges. The final
    // byte is forwarded here while header[127] still has its old NBA value.
    logic prepared_header_padding_ok;
    always_ff @(posedge clk)if(state==HEADER_BYTE && header_index>=116 && header_index<=127)
        prepared_header_padding_ok<=header_index==116 ? byte_value==0 :
            prepared_header_padding_ok && byte_value==0;
    // V128_PADDING_CACHE_END
'''
OWNER = '''`ifndef SYNTHESIS
    // V128_PADDING_OWNER_BEGIN: verification-only freshness, not payload reset.
    logic padding_owner_valid=0;
    logic [31:0] padding_owner_epoch,padding_owner_size,padding_owner_next;
    logic padding_reference_ok;
    always_comb begin
        padding_reference_ok=1;
        for(integer padding_index=116;padding_index<128;padding_index=padding_index+1)
            if(header[padding_index]!=0)padding_reference_ok=0;
    end
    always_ff @(posedge clk)begin
        if(reset||start||abort_packet)padding_owner_valid<=0;
        else if(state==HEADER_BYTE && header_index>=116 && header_index<=127)begin
            if(header_index==116)begin
                padding_owner_valid<=1;
                padding_owner_epoch<=receipt_epoch;padding_owner_size<=size_bytes;
            end else begin
                assert(padding_owner_valid && padding_owner_epoch==receipt_epoch &&
                    padding_owner_size==size_bytes && padding_owner_next==header_index)
                    else $fatal(1,"V128 padding byte sequence lost its complete owner");
            end
            padding_owner_next<=header_index+32'd1;
        end else if(state==HEADER_CHECK)padding_owner_valid<=0;
    end
    always_ff @(posedge clk)if(!reset&&!start&&!abort_packet&&state==HEADER_CHECK)begin
        assert(padding_owner_valid && padding_owner_epoch==receipt_epoch &&
            padding_owner_size==size_bytes && padding_owner_next==128 && header_index==127)
            else $fatal(1,"V128 padding consume without full owned116..127 writer sequence");
        assert(prepared_header_padding_ok==padding_reference_ok)
            else $fatal(1,"V128 padding cache differs from current complete header");
    end
    // V128_PADDING_OWNER_END
`endif
'''
OLD_CONSUMER = '''                    logic padding_ok;
                    padding_ok=1;
                    for(integer k=116;k<128;k=k+1)if(header[k]!=0)padding_ok=0;
'''
NEW_CONSUMER = '''                    logic padding_ok;
                    padding_ok=prepared_header_padding_ok;
'''

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def pin(p):return {'path':str(Path(p).relative_to(ROOT)),'sha256':sha(p)}

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--apply',action='store_true');ap.add_argument('--root-grant');a=ap.parse_args()
    assert sha(ORIGINAL)==ORIGINAL_SHA
    before=ORIGINAL.read_text();text=before;edits=[]
    def replace(tag,old,new):
        nonlocal text
        assert text.count(old)==1,(tag,text.count(old));text=text.replace(old,new)
        edits.append({'tag':tag,'old':old,'new':new,'occurrences':1})
    anchor='    logic prepared_header_total_matches;\n'
    replace('unreset-owned-incremental-padding-payload',anchor,CACHE+OWNER+anchor)
    replace('consume-owned-current-header-padding',OLD_CONSUMER,NEW_CONSUMER)
    restored=text
    for e in reversed(edits):assert restored.count(e['new'])==1;restored=restored.replace(e['new'],e['old'])
    assert restored==before
    guards=re.findall(r'`ifndef SYNTHESIS\n.*?`endif',before,re.S)
    assert all(text.count(g)>=before.count(g) for g in guards)
    strip=lambda s:re.sub(r'`ifndef SYNTHESIS\n.*?`endif','',s,flags=re.S)
    assert len(re.findall(r'\balways_ff\b',strip(text)))==len(re.findall(r'\balways_ff\b',strip(before)))+1
    assert re.findall(r'\(\*.*?\*\)',before,re.S)==re.findall(r'\(\*.*?\*\)',text,re.S)
    tail_marker='// Isolated common-clock TDP scale storage; no reset/initialization promise.'
    assert before.split(tail_marker,1)[1]==text.split(tail_marker,1)[1]
    modules=re.findall(r'^\s*module\s+(\w+)',text,re.M);assert len(modules)==3
    target=DEST/ORIGINAL.name
    recipe={'schema':'v128-owned-header-padding-edit-recipe-v1','status':'SOURCE_PREPARED_NOT_RTL_QUALIFIED' if a.apply else 'READONLY_RECIPE_CHECK_NOT_APPLIED',
        'original':pin(ORIGINAL),'candidate':{'path':str(target.relative_to(ROOT)),'sha256':hashlib.sha256(text.encode()).hexdigest()},'alias':ALIAS,
        'preparer':pin(Path(__file__)),'edits':edits,'production_cache_fragment':CACHE,'additive_assertion_fragment':OWNER,
        'source_payload_bits_added':1,'source_payload_reset_added':False,'source_production_sequential_block_delta':1,
        'added_public_cycles':0,'added_synthesis_attributes':0,'old_guarded_blocks_retained':len(guards),
        'old_guarded_blocks_byte_exact':True,'reverse_reconstruction_exact':True,'original_RAM_module_tail_byte_exact':True,
        'cache_writer_indices':list(range(116,128)),'initialize_writer_index':116,'final_byte_forwarding':True,
        'existing_error_priority_unchanged':True,'old_padding_view_hold_outside_HEADER_CHECK':True,
        'qualification_scope':'Cache correctness requires actual complete owned116..127 writer sequence; no arbitrary missing-writer consume claim.'}
    if a.apply:
        assert a.root_grant=='ROOT_V128_PADDING_SOURCE'
        assert not DEST.exists(),'Refuse overwrite of candidate namespace'
        DEST.mkdir();target.write_text(text)
        (DEST/'edit-recipe.json').write_text(json.dumps(recipe,indent=2,sort_keys=True)+'\n')
        packaging={'schema':'v128-padding-lossless-admission-packaging-v1','production':str(target.relative_to(ROOT)),'production_sha256':sha(target),
            'fragments':[{'filename':target.name,'bytes':target.stat().st_size,'sha256':sha(target)}],
            'split_byte_offsets':[],'module_count':len(modules),'module_names':modules,'RAM_tail_unchanged':True}
        (DEST/'packaging.json').write_text(json.dumps(packaging,indent=2,sort_keys=True)+'\n')
        source_map={'schema':'v128-padding-component-source-map-v1','source_origins':{ALIAS:pin(target)},'changed_origin_count':1,
            'source_payload_bits_added':1,'public_cycle_delta':0,'edit_recipe':pin(DEST/'edit-recipe.json'),'packaging':pin(DEST/'packaging.json')}
        (DEST/'source-map.json').write_text(json.dumps(source_map,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'status':recipe['status'],'candidate':recipe['candidate'],'edits':len(edits),'retained_guards':len(guards),
                      'module_count':len(modules),'reverse_exact':True,'production_payload_bits_added':1,'public_cycle_delta':0},indent=2,sort_keys=True))
if __name__=='__main__':main()
