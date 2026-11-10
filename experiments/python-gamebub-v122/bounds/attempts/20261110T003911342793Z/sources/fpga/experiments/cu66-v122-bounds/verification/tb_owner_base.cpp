// The exact inherited oracle is retained as tb_admission.frozen.cpp. Its
// reversible adapter only translates hierarchy and binds new private poststate.
#define main admission_frozen_main
#include "tb_admission_legacy.cpp"
#undef main
#include "bounds_priming.hpp"

static uint64_t chunk_boundaries(unsigned seed) {
    Vadmission_probe d;
    auto &r=*d.rootp;
    uint64_t edges=0,cases=0,cancelled=0;
    std::mt19937 random(seed);
    d.clk=0;d.reset=1;d.start=0;d.abort_packet=0;d.cache_write=0;
    d.lookup_req=0;d.replay_req=0;d.in_valid=0;d.in_last=0;
    d.receipt_ready=0;d.packet_bytes=256;d.epoch=seed;
    auto tick=[&]() {
        d.clk=0;d.eval();require(!d.mismatch,"V116 all-public low-edge comparison");
        d.clk=1;d.eval();require(!d.mismatch,"V116 all-public high-edge comparison");
        d.clk=0;d.eval();require(!d.mismatch,"V116 all-public falling-edge comparison");
        require(++edges<2000000,"V116 finite boundary watchdog");
    };
    tick();d.reset=0;
    // Initialize every accessed backing byte via the original RX write port.
    // Prepared full32 consume fixtures never clock an out-of-range RAM request.
    QBOTH(state,1U);QBOTH(size_bytes,256U);QBOTH(received,0U);
    for(unsigned i=0;i<16;++i){d.in_valid=1;d.in_data=uint8_t(i*17U);tick();}
    d.in_valid=0;
    auto reset=[&](){d.reset=1;d.start=0;d.abort_packet=0;tick();d.reset=0;};
    auto begin=[&](unsigned plane,uint32_t blocks,bool ready=true) {
        reset();
        QBOTH(coord_valid,0U);QBOTH(state,18U);QBOTH(plane,plane);
        QBOTH(cursor,0U);QBOTH(residual_end,256U);QBOTH(size_bytes,256U);
        QBOTH(receipt_epoch,seed+uint32_t(cases));
        for(unsigned p=0;p<3;++p){QBOTH(plane_blocks[p],p==plane?blocks:uint32_t(random()));}
        QBOTH(count_cycles,UINT64_MAX-1U);QBOTH(count_stage_reads,UINT64_MAX);
        tick();
        require(d.debug_state==28U&&QNEW(selected_valid)&&!QNEW(selected_limit_valid),"capture on original PLANE_BEGIN only");
        require(QNEW(selected_plane)==plane&&QNEW(selected_blocks)==blocks&&QNEW(selected_owner)==d.receipt_epoch,"capture complete selected tuple");
        if(ready) {
            tick();
            require(d.debug_state==29U&&QNEW(selected_limit_valid),"prepare on later existing FETCH_REQ");
            require(QNEW(selected_limit)==uint32_t(46U+128U*blocks),"independent uint32 wrapped limit");
            require(d.count_cycles==0U&&d.count_stage_reads==0U,"uint64 counters retain wrap domain");
        }
    };
    const std::array<uint32_t,22> counts{{0U,1U,2U,1331U,1350U,5144U,5400U,0x01ffffffU,0x02000000U,0x02000001U,0x03ffffffU,0x04000000U,0x1fffffffU,0x20000000U,0x7fffffffU,0x80000000U,0xffffff00U,0xfffffffeU,0xffffffffU,65535U,65536U,0x01000000U}};
    const std::array<std::pair<uint32_t,uint32_t>,8> ends{{{0U,0U},{0U,4U},{8U,58U},{0xfffffff0U,0xffffffffU},{0xfffffffcU,0xffffffffU},{0xffffffffU,0xffffffffU},{0x80000000U,0xffffffffU},{0U,0xffffffffU}}};
    for(unsigned plane=0;plane<3;++plane)for(uint32_t blocks:counts) {
        const uint32_t limit=46U+128U*blocks;
        const std::array<uint32_t,16> words{{0U,1U,2U,45U,46U,47U,127U,128U,limit-1U,limit,limit+1U,blocks-1U,blocks,blocks+1U,0x80000000U,0xffffffffU}};
        for(unsigned state:{19U,20U,21U})for(uint32_t word:words)for(const auto &end:ends) {
            begin(plane,blocks);
            const uint32_t cursor=end.first,residual_end=end.second;
            QBOTH(state,state);QBOTH(word_value,word);QBOTH(cursor,cursor);QBOTH(residual_end,residual_end);
            // Consistent completed-word poststate; no backing read is clocked
            // for arbitrary full32 cursor values in this predicate fixture.
            QBOTH(word_index,3U);QBOTH(word_return,state);QBOTH(fetch_return,30U);
            QBOTH(word_cursor,uint32_t(cursor+3U));QBOTH(word_acc,word>>8U);QBOTH(byte_value,word&255U);
            if(state==19U||state==21U)prime_bounds(d,r);
            unsigned error=0,next=28U;
            if(state==19U) {
                if(word!=(blocks==0U?0U:1U)){error=12U;next=27U;}
                else if(word==0U)next=23U;
                else if(uint32_t(cursor+12U)>residual_end){error=13U;next=27U;}
            } else if(state==20U) {
                if(word!=blocks||word==0U){error=13U;next=27U;}
            } else if(word<46U||word>limit||uint64_t(cursor)+4ULL+uint64_t(word)>uint64_t(residual_end)) {
                error=13U;next=27U;
            }
            tick();
            require(d.error==error&&d.debug_state==next,"independent chunk error/state priority");
            require(QNEW(cursor)==uint32_t(cursor+4U)&&QOLD(cursor)==uint32_t(cursor+4U),"original uint32 cursor wrap");
            if(state==21U) {
                require(QNEW(chunk_length)==word,"length captured even on original rejection edge");
                if(!error)require(d.plane_offset[plane]==uint32_t(cursor+4U)&&d.plane_length[plane]==word,"original descriptor capture edge");
            }
            ++cases;
        }
    }
    // All planes, all four bytes, and each real preparation/fetch/wait/word
    // edge: every reset/start/abort priority combination, then a clean retry.
    for(unsigned plane=0;plane<3;++plane)for(unsigned phase=0;phase<14;++phase)for(unsigned flags=1;flags<8;++flags) {
        begin(plane,1U,false);
        if(phase==0){reset();QBOTH(state,18U);QBOTH(plane,plane);QBOTH(cursor,0U);QBOTH(residual_end,256U);QBOTH(plane_blocks[plane],1U);}
        else if(phase>=2) {
            const unsigned byte=(phase-2U)/3U,target=28U+(phase-2U)%3U;
            for(unsigned watchdog=0;watchdog<32;++watchdog) {
                if(QNEW(state)==target&&QNEW(word_index)==byte)break;
                tick();require(watchdog+1U<32U,"reach real byte preparation phase");
            }
        }
        d.reset=(flags&1U)!=0;d.start=(flags&2U)!=0;d.abort_packet=(flags&4U)!=0;
        tick();require(!QNEW(selected_valid)&&!QNEW(selected_limit_valid),"cancel invalidates entire preparation owner");
        require(d.debug_state==(flags==2U?31U:0U),"unchanged reset/start/abort priority");
        d.reset=0;d.start=0;d.abort_packet=0;
        begin(plane,1U);
        QBOTH(state,19U);QBOTH(word_value,1U);prime_bounds(d,r);tick();
        require(!d.error&&d.debug_state==28U,"clean retry after every cancellation phase");
        ++cancelled;
    }
    // Actual PLANE_NEXT must invalidate before the successor captures, including
    // the last plane. No malformed next descriptor is read speculatively.
    for(unsigned plane=0;plane<3;++plane) {
        begin(plane,0U);QBOTH(state,19U);QBOTH(word_value,0U);prime_bounds(d,r);tick();
        require(d.debug_state==23U,"empty plane number consume");tick();
        require(!QNEW(selected_valid)&&!QNEW(selected_limit_valid),"transition invalidates old plane tuple");
        require(d.debug_state==(plane==2U?24U:18U),"all plane transitions keep original cycle");
        if(plane<2U){tick();require(QNEW(selected_plane)==plane+1U&&QNEW(selected_valid),"capture successor after plane increment");tick();}
    }
    std::cout<<"{\"type\":\"v116_chunk_boundaries\",\"status\":\"TEST_PASS\",\"seed\":"<<seed
             <<",\"cases\":"<<cases<<",\"cancellation_cases\":"<<cancelled<<",\"clock_edges\":"<<edges<<"}\n";
    d.final();return edges;
}

int inherited_admission_main(int argc,char **argv) {
    try {
        require(argc==3,"usage: Vadmission_probe vectors.txt seed");
        chunk_boundaries(unsigned(std::stoul(argv[2])));
        return admission_frozen_main(argc,argv);
    } catch(const std::exception &e) {
        std::cerr<<"V116_ADMISSION_TEST_FAIL "<<e.what()<<'\n';return 1;
    }
}

int inherited_owner_main(int argc,char**argv){try{
 require(inherited_admission_main(argc,argv)==0,"inherited complete admission suite");Vadmission_probe d;auto&r=*d.rootp;d.clk=0;d.reset=1;d.start=d.abort_packet=d.cache_write=d.lookup_req=d.replay_req=d.in_valid=d.in_last=d.receipt_ready=0;d.packet_bytes=256;d.epoch=119;
 auto tick=[&](){d.clk=0;d.eval();require(!d.mismatch,"all admission fields low");d.clk=1;d.eval();require(!d.mismatch,"all admission fields high");d.clk=0;d.eval();require(!d.mismatch,"all admission fields falling");};
 tick();d.reset=0;uint64_t cases=0;
 const std::array<uint32_t,15> lengths{{0U,1U,2U,975U,976U,977U,65535U,0x7fffffffU,0x80000000U,0xffffff7fU,0xffffff80U,0xffffff81U,0xfffffffeU,0xffffffffU,128U}};
 for(uint32_t length:lengths)for(unsigned which=0;which<2;++which)for(unsigned trailing=0;trailing<2;++trailing){
  const uint32_t end=uint32_t(128U+length);const std::array<uint32_t,9> cursors{{0U,127U,128U,end-1U,end,end+1U,0x7fffffffU,0x80000000U,0xffffffffU}};
  for(uint32_t cursor:cursors){d.reset=1;tick();d.reset=0;
   QBOTH(coord_valid,0U);QBOTH(state,which?12U:8U);QBOTH(mode_bytes,length);QBOTH(q_start,end);QBOTH(mode_cursor,cursor);QBOTH(bits_left,0U);QBOTH(bit_cache,trailing?1U:0U);QBOTH(key_frame,0U);QBOTH(size_bytes,256U);QBOTH(snapshot_valid,0U);
   d.eval();require(!d.mismatch,"coherent mode bound preparation");tick();
   const bool reject=which?(cursor!=end||trailing):(cursor>=end);
   require(d.error==(reject?8U:0U),"independent full32 mode bound first reason");++cases;
  }
 }
 std::cout<<"{\"type\":\"v119_mode_bound\",\"status\":\"TEST_PASS\",\"cases\":"<<cases<<",\"original_oracle_checks_removed\":0}\n";return 0;
 }catch(const std::exception&e){std::cerr<<"V119_MODE_BOUND_FAIL "<<e.what()<<'\n';return 1;}}
