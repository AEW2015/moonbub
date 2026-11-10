#include "tb_match.cpp"

static void full32_bounds(unsigned seed) {
    Vadmission_probe d;auto&r=*d.rootp;std::mt19937 random(seed);
    uint64_t cases=0,cancels=0,high32=0,wrap=0,edges=0;
    d.clk=0;d.reset=1;d.start=d.abort_packet=d.in_valid=d.in_last=d.cache_write=d.lookup_req=d.replay_req=d.receipt_ready=0;
    d.packet_bytes=256;d.epoch=seed;
    auto tick=[&]() {
        d.clk=0;d.eval();require(!d.mismatch,"bounds oracle all-public preedge");
        d.clk=1;d.eval();require(!d.mismatch,"bounds oracle all-public high edge");
        d.clk=0;d.eval();require(!d.mismatch,"bounds oracle all-public falling edge");
        require(++edges<1000000ULL,"bounds independent finite watchdog");
    };
    tick();d.reset=0;
    auto context=[&](unsigned state,uint32_t cursor,uint32_t word,uint32_t end,uint32_t blocks,unsigned plane) {
        d.reset=1;tick();d.reset=0;
        QBOTH(state,state);QBOTH(coord_valid,0U);QBOTH(plane,plane);
        QBOTH(cursor,cursor);QBOTH(word_value,word);QBOTH(residual_end,end);
        QBOTH(size_bytes,256U);QBOTH(receipt_epoch,seed+uint32_t(cases));
        QBOTH(plane_blocks[plane],blocks);
        QBOTH(selected_valid,1U);QBOTH(selected_limit_valid,1U);
        QBOTH(selected_plane,plane);QBOTH(selected_owner,d.receipt_epoch);
        QBOTH(selected_blocks,blocks);QBOTH(selected_zero,blocks==0U);
        QBOTH(selected_limit,uint32_t(46U+128U*blocks));
    };
    // Independent random full32 domain with deliberate full64 overflow aliases,
    // exact boundaries, wrapped uint32 +12, and overlapping first faults.
    for(unsigned i=0;i<16384U;++i) {
        const unsigned state=i&1U?19U:21U,plane=i%3U;
        const uint32_t cursor=i%5U?random():0xffffffffU;
        const uint32_t blocks=i%7U?random():1U;
        const uint32_t limit=46U+128U*blocks;
        uint32_t word=random();if(i%4U==0U)word=i%8U?46U:limit;
        if(state==19U&&i%3U)word=blocks?1U:0U;
        uint32_t end=random();
        if(i%3U==0U)end=uint32_t(uint64_t(cursor)+4ULL+word);
        if(i%11U==0U)end=uint32_t(cursor+12U);
        context(state,cursor,word,end,blocks,plane);prime_bounds(d,r);
        const uint64_t sum=uint64_t(cursor)+4ULL+uint64_t(word);
        const bool invalid=word<46U||word>limit||sum>uint64_t(end);
        unsigned error=0,next=28U;
        if(state==19U) {
            if(word!=(blocks==0U?0U:1U)){error=12U;next=27U;}
            else if(word==0U)next=23U;
            else if(uint32_t(cursor+12U)>end){error=13U;next=27U;}
        }else if(invalid){error=13U;next=27U;}
        tick();require(d.error==error&&d.debug_state==next,"independent randomized first-fault/state oracle");
        require(QNEW(cursor)==uint32_t(cursor+4U),"full32 cursor consume wraps");
        high32+=sum>0xffffffffULL;wrap+=uint32_t(cursor+12U)<cursor;++cases;
    }
    // Every new pipeline edge, both continuations, all priority combinations.
    for(unsigned state:{19U,21U})for(unsigned phase=0;phase<4U;++phase)for(unsigned flags=1;flags<8U;++flags) {
        context(state,8U,state==19U?1U:46U,256U,1U,phase%3U);
        require(!prime_bounds(d,r,int(phase),flags),"cancellation exercised actual preparation edge");
        require(!QNEW(bounds_owner_valid),"canceled bounds ownership cannot authorize consume");
        context(state,8U,state==19U?1U:46U,256U,1U,phase%3U);
        prime_bounds(d,r);tick();require(!d.error&&d.debug_state==28U,"clean retry recaptures complete bounds");++cancels;
    }
    require(cases==16384U&&cancels==56U&&high32>0&&wrap>0,"full32/full64/cancellation coverage");
    std::cout<<"{\"type\":\"v122_bounds_verdict\",\"status\":\"TEST_PASS\",\"random_full32_cases\":"<<cases<<",\"cancellation_cases\":"<<cancels<<",\"full64_high32_cases\":"<<high32<<",\"uint32_wrap_cases\":"<<wrap<<",\"fixture_priming_edges\":"<<bounds_priming_edges<<",\"oracle_edges\":"<<edges<<",\"added_natural_public_cycles\":0,\"prepared_domain_fixtures_are_natural_packets\":false,\"old_require_checks_removed\":0}\n";
    d.final();
}

int main(int argc,char**argv) {
    try {
        require(inherited_match_main(argc,argv)==0,"all original V120 header/owner/packet/port oracles retained");
        full32_bounds(unsigned(std::stoul(argv[2])));return 0;
    }catch(const std::exception&e){std::cerr<<"V122_BOUNDS_FAIL "<<e.what()<<'\n';return 1;}
}
