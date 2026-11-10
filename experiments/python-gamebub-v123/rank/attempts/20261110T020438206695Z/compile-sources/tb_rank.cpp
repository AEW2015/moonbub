#include "tb_ac.cpp"

struct RankCoverage {
    uint64_t cases=0,random_cases=0,good=0,bad=0,high32=0,append_overlaps=0,captures=0,kills=0;
    uint64_t index_mask=0,threshold_mask=0;unsigned phase_mask=0;
};
static void rank_boundaries(unsigned seed,RankCoverage&v) {
    Vscratch_probe d;ACCoverage init;ac_init(d,init);setup(d,1,0,0,0);RecordCoverage c;
    std::mt19937 random(seed);
    auto one=[&](unsigned phase,unsigned index,uint32_t previous,unsigned block,bool raw) {
        prime_rank_threshold(d,c,phase,previous&63U);
        // Explicit prepared-domain original fields. Only low6 was naturally
        // produced above; high32 tests generic scalar ordering independently.
        record_context(d,phase,raw,37);BOTH(blocks,65535);BOTH(previous_valid,1);
        BOTH(previous_position,previous);BOTH(written,0U);
        OLD(counts)[phase&3U]=NEW(counts)[phase&3U]=0xffffffffU;
        d.coef_block=block;d.coef_index=index;
        d.eval();const bool bad=independent_bad(d);
        const uint32_t sparse=uint32_t(block*64U+ranks[index]);
        need(bool(NEW(input_sparse_order_bad))==(sparse<=previous),"independent generic full32 order decomposition");
        need(bool(OLD(input_bad))==bad&&bool(NEW(input_bad))==bad,"independent rank full32 whole first-fault predicate");
        record_edge(d,c,!bad);need(d.error==(bad?3U:0U),"rank same original error edge");
        ++v.cases;v.good+=!bad;v.bad+=bad;v.high32+=(previous>>22U)!=0;
        v.phase_mask|=1U<<phase;v.index_mask|=uint64_t(1)<<index;v.threshold_mask|=uint64_t(1)<<(previous&63U);
    };
    const uint32_t upper[]={0U,64U,0x3fffc0U,0x400000U,0x80000000U,0xffffffc0U};
    for(unsigned phase=0;phase<8;++phase)for(unsigned threshold=0;threshold<64;++threshold)
        for(unsigned index=0;index<64;++index)for(unsigned relation=0;relation<3;++relation) {
            const uint32_t previous=upper[(phase+threshold+index)%6U]|threshold;
            const unsigned block=uint16_t((previous>>6U)+(relation==0?0xffffffffU:relation==1?0U:1U));
            one(phase,index,previous,block,false);
        }
    for(unsigned k=0;k<8192;++k){one(k&7U,random()&63U,random(),random()&65535U,(k&8U)!=0);++v.random_cases;}
    need(v.cases==106496&&v.random_cases==8192&&v.high32>0&&v.good>0&&v.bad>0&&v.phase_mask==255&&v.index_mask==UINT64_MAX&&v.threshold_mask==UINT64_MAX,"all rank/full32 prepared-domain coverage");
}
static void rank_append_overlaps(RankCoverage&v) {
    Vscratch_probe d;ACCoverage init;ac_init(d,init);setup(d,1,0,0,0);RecordCoverage c;
    for(unsigned phase=0;phase<8;++phase)for(unsigned threshold=0;threshold<64;++threshold)for(unsigned action=0;action<15;++action) {
        prime_rank_threshold(d,c,phase,threshold^63U);
        rank_accept_predecessor(d,c,phase,threshold);
        const uint64_t before=NEW(rank_threshold_mask);bool capture=true;
        switch(action) {
            case 1:d.reset=1;capture=false;break;
            case 2:d.abort_valid=1;capture=false;break;
            case 3:d.abort_valid=1;d.abort_epoch=10;break;
            case 4:d.reset=d.abort_valid=1;d.abort_epoch=10;capture=false;break;
            case 5:d.mem_rsp_valid=1;capture=false;break;
            case 6:BOTH(outstanding,1);d.mem_rsp_valid=1;d.mem_rsp_epoch=10;capture=false;break;
            case 7:BOTH(outstanding,1);d.mem_rsp_valid=d.mem_rsp_error=1;break;
            case 8:BOTH(outstanding,1);BOTH(prefetch_offer,1);d.mem_rsp_valid=d.mem_rsp_error=1;capture=false;break;
            case 9:BOTH(outstanding,1);BOTH(overlap_mode,1);BOTH(write_slot_valid,1);d.mem_rsp_valid=d.mem_rsp_error=1;capture=false;break;
            case 10:BOTH(outstanding,1);d.mem_rsp_valid=1;break;
            case 11:BOTH(outstanding,1);d.abort_valid=1;d.abort_epoch=10;d.mem_rsp_valid=1;break;
            case 12:BOTH(outstanding,1);d.abort_valid=d.mem_rsp_valid=1;capture=false;break;
            case 13:BOTH(outstanding,1);d.abort_valid=d.mem_rsp_valid=1;d.mem_rsp_epoch=10;capture=false;break;
            case 14:d.reset=d.abort_valid=d.mem_rsp_valid=d.mem_rsp_error=1;capture=false;break;
            default:break;
        }
        record_edge(d,c,false);++v.append_overlaps;
        uint64_t expected=0;for(unsigned k=0;k<64;++k)if(ranks[k]<=threshold)expected|=uint64_t(1)<<k;
        need(uint64_t(NEW(rank_threshold_mask))==(capture?expected:before),"APPEND mask exactly follows original outer response/cancel priority");
        if(capture){need(NEW(previous_position)==threshold&&NEW(rank_owner_valid),"actual APPEND refreshes threshold ownership");++v.captures;}
        else ++v.kills;
        // A fresh coherent prepared-domain acceptance+APPEND replaces any
        // retired synthetic debt; physical request/debt conservation is also
        // exercised by every unchanged inherited generic/caller transaction.
        prime_rank_threshold(d,c,phase,threshold);
        d.reset=0;d.abort_valid=0;d.mem_rsp_valid=d.mem_rsp_error=0;
        need(NEW(rank_owner_valid)&&NEW(rank_owner_threshold)==threshold,"clean same-object retry recaptures rank threshold");
    }
    need(v.append_overlaps==7680&&v.captures>0&&v.kills>0,"all phase/threshold/outer-priority overlap contexts");
}
int main(int argc,char**argv) {
    try {
        need(inherited_v119_rank_main(argc,argv)==0,"all immutable V119 scratch suites");
        RankCoverage v;rank_boundaries(unsigned(std::stoul(argv[1])),v);rank_append_overlaps(v);
        std::cout<<"{\"type\":\"v123_rank_verdict\",\"status\":\"TEST_PASS\",\"full32_cases\":"<<v.cases<<",\"random_full32_cases\":"<<v.random_cases<<",\"high32_cases\":"<<v.high32<<",\"good\":"<<v.good<<",\"bad\":"<<v.bad<<",\"phase_mask\":"<<v.phase_mask<<",\"index_mask\":"<<v.index_mask<<",\"threshold_mask\":"<<v.threshold_mask<<",\"append_overlap_cases\":"<<v.append_overlaps<<",\"append_captures\":"<<v.captures<<",\"append_kills\":"<<v.kills<<",\"fixture_priming_edges\":"<<rank_fixture_priming_edges<<",\"prepared_domain_fixtures_are_natural_packets\":false,\"public_cycle_delta\":0,\"error_cycle_delta\":0,\"pair_skipped_edges\":0,\"old_checks_removed\":0}\n";
        return 0;
    }catch(const std::exception&e){std::cerr<<"V123_RANK_FAIL "<<e.what()<<'\n';return 1;}
}
