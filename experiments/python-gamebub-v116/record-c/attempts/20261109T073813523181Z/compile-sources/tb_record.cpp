#include "tb_control.cpp"
// Additional explicitly prepared controller contexts retain every old SVA and
// compare the frozen old fields directly. They do not claim reachability for
// phase4..7 or matching-error/no-prefetch/no-write-owner contexts.
struct RecordCoverage {
    uint64_t edges=0,range=0,good=0,bad=0,holds=0,priority=0;
    uint32_t record=0,position=0;unsigned bytes=0;
};
static void record_edge(Vscratch_probe&d,RecordCoverage&c,bool commit){
    d.clk=d.reference_clk=0;d.eval();
    need(!d.mismatch,"record fixture original whole raw/public oracle");
    need(OLD(pending_record)==c.record&&OLD(pending_bytes)==c.bytes&&OLD(pending_position)==c.position,"independent old record tuple before edge");
    if(commit){
        const unsigned bits=uint16_t(d.coef_value),block=d.coef_block,index=d.coef_index;
        c.record=NEW(raw_mode)||NEW(phase)==0?bits:((block&8191U)<<19)|(index<<13)|(bits&8191U);
        c.bytes=NEW(raw_mode)||NEW(phase)==0?2:4;
        c.position=NEW(raw_mode)?block*64+index:NEW(phase)==0?block:block*64+ranks[index];
        ++c.good;
    }else ++c.holds;
    d.clk=d.reference_clk=1;d.eval();
    need(!d.mismatch,"record fixture postedge whole old oracle");
    d.clk=d.reference_clk=0;d.eval();
    need(OLD(pending_record)==c.record&&OLD(pending_bytes)==c.bytes&&OLD(pending_position)==c.position,"independent frozen old record result");
    need(NEW(pending_record)==c.record&&NEW(pending_bytes)==c.bytes&&NEW(pending_position)==c.position,"independent selected record result");
    need(++c.edges<2000000,"record fixture finite clock watchdog");
}
static void record_context(Vscratch_probe&d,unsigned phase,bool raw,unsigned bits){
    // Complete dependent original controller poststate; neither logical pending
    // values nor physical bank/view/checker state are injected or reset.
    BOTH(state,1);BOTH(busy_owned,1);BOTH(phase,phase);BOTH(raw_mode,raw);BOTH(active_epoch,9);
    BOTH(blocks,8);BOTH(tile_overlap_mode,0);BOTH(prefetch_mode,0);BOTH(prefetch_offer,0);
    BOTH(overlap_mode,0);BOTH(write_slot_valid,0);BOTH(outstanding,0);
    BOTH(sealed,0);BOTH(done,0);BOTH(error,0);BOTH(previous_valid,0);BOTH(previous_position,0);
    BOTH(assembly_bytes,0);BOTH(assembler,0);BOTH(request_epoch,9);BOTH(transfer_address,32);BOTH(used_bytes,4096);
    for(unsigned n=0;n<4;++n){OLD(counts)[n]=NEW(counts)[n]=1000000;}
    unsigned index=raw?7:0;
    if(!raw&&(phase&3)!=0){const unsigned target=(phase&3)==1?1:(phase&3)==2?6:21;for(unsigned n=0;n<64;++n)if(ranks[n]==target)index=n;}
    const unsigned position=raw?64+index:phase==0?1:64+ranks[index];BOTH(written,position);
    d.reset=0;d.abort_valid=0;d.abort_epoch=9;d.begin_valid=0;d.coef_valid=1;
    d.coef_epoch=9;d.coef_band=phase&3;d.coef_block=1;d.coef_index=index;d.coef_value=bits;
    d.band_end_valid=d.seal_valid=d.mem_req_ready=d.mem_rsp_valid=d.mem_rsp_error=d.dense_ready=0;
    d.band_end_epoch=d.seal_epoch=9;d.band_end_band=phase&3;d.mem_rsp_epoch=9;
}
static RecordCoverage record_fixtures(){
    Vscratch_probe d;d.clk=d.reference_clk=0;d.pair_enable=1;d.reset=1;
    d.begin_valid=d.coef_valid=d.band_end_valid=d.seal_valid=d.abort_valid=d.mem_req_ready=d.mem_rsp_valid=d.mem_rsp_error=d.dense_ready=0;
    d.begin_blocks=1;d.begin_raw=d.begin_serial_clear=d.begin_overlap=d.begin_prefetch=d.begin_tile_overlap=0;
    d.begin_count1=d.begin_count2=d.begin_count3=d.begin_epoch=0;d.abort_epoch=0;
    d.coef_band=d.coef_block=d.coef_index=d.coef_value=d.coef_epoch=d.band_end_band=d.band_end_epoch=d.seal_epoch=d.mem_rsp_epoch=0;
    for(unsigned n=0;n<4;++n)d.mem_rsp_data[n]=0;
    RecordCoverage c;record_edge(d,c,false);d.reset=0;
    // Initialize all dependent cache/head position tuples with the inherited
    // complete coherent fixture helper; all its old assertions remain active.
    setup(d,1,0,0,0);
    for(unsigned raw=0;raw<2;++raw)for(unsigned phase=0;phase<8;++phase)
        for(unsigned bits=0;bits<65536;++bits){
            record_context(d,phase,raw!=0,bits);
            const int value=int16_t(bits);const bool good=value>=-2048&&value<=2048&&(raw||phase==0||value!=0);
            record_edge(d,c,good);++c.range;if(!good)++c.bad;
        }
    need(c.range==1048576&&c.good==65545&&c.bad==983031,"full16 coefficient domain/all8 phases/raw formats");
    // Every original outer branch, including matching response error that DOES
    // reach INGEST, and the same errors with actual owning prefetch/write slots.
    for(unsigned kind=0;kind<15;++kind){
        record_context(d,3,false,37);bool commit=true;
        switch(kind){
            case 1:d.reset=1;commit=false;break;
            case 2:d.abort_valid=1;commit=false;break;
            case 3:d.abort_valid=1;d.abort_epoch=10;break;
            case 4:d.coef_valid=0;commit=false;break;
            case 5:d.coef_value=2049;commit=false;break;
            case 6:d.mem_rsp_valid=1;commit=false;break;
            case 7:BOTH(outstanding,1);d.mem_rsp_valid=1;d.mem_rsp_epoch=10;commit=false;break;
            case 8:BOTH(outstanding,1);d.mem_rsp_valid=d.mem_rsp_error=1;break;
            case 9:BOTH(outstanding,1);BOTH(prefetch_offer,1);d.mem_rsp_valid=d.mem_rsp_error=1;commit=false;break;
            case 10:BOTH(outstanding,1);BOTH(overlap_mode,1);BOTH(write_slot_valid,1);d.mem_rsp_valid=d.mem_rsp_error=1;commit=false;break;
            case 11:BOTH(state,25);BOTH(outstanding,1);d.mem_rsp_valid=1;commit=false;break;
            case 12:d.band_end_valid=1;break; // coefficient wins over EOF
            case 13:d.band_end_valid=1;d.coef_valid=0;commit=false;break;
            case 14:d.reset=d.abort_valid=1;d.abort_epoch=10;commit=false;break;
            default:break;
        }
        record_edge(d,c,commit);++c.priority;
    }
    // Selected view is immutable while speculative garbage refreshes inactive
    // storage through held input, warm reset and accepted-input absence.
    record_context(d,0,true,0xffffU);record_edge(d,c,true);
    for(unsigned n=0;n<128;++n){
        record_context(d,n&7,(n&8)!=0,(n*977U)&65535U);d.coef_valid=0;
        d.reset=n%3==0;d.abort_valid=n%3==1;record_edge(d,c,false);
    }
    // Back-to-back replacement fixtures reuse one logical tuple and both banks;
    // successful zero and nonzero values cross all record formats.
    for(unsigned n=0;n<32;++n){record_context(d,n&7,(n&8)!=0,n&1?0:37);const bool good=(n&8)||((n&7)==0)||(n&1)==0;record_edge(d,c,good);}
    return c;
}
int main(int argc,char**argv){try{
    need(inherited_control_main(argc,argv)==0,"entire frozen B generic/corruption/physical-owner suite");
    const auto c=record_fixtures();
    std::cout<<"{\"type\":\"v116c_record_verdict\",\"status\":\"TEST_PASS\",\"seed\":"<<argv[1]<<",\"coefficient_domain_cases\":"<<c.range<<",\"invalid_coefficient_cases\":"<<c.bad<<",\"record_commits\":"<<c.good<<",\"record_hold_edges\":"<<c.holds<<",\"outer_priority_cases\":"<<c.priority<<",\"fixture_edges\":"<<c.edges<<",\"public_cycle_delta\":0,\"logical_pending_capacity\":1,\"physical_banks\":2,\"pair_skipped_edges\":0}\n";return 0;
}catch(const std::exception&e){std::cerr<<"V116C_RECORD_FAIL "<<e.what()<<'\n';return 1;}}
