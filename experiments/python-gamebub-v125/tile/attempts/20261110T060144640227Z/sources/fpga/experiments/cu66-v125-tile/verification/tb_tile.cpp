#include "tb_bounds.cpp"

struct TileCase {
    unsigned state,p;uint32_t tile,end;unsigned tag=0,bits=1,mixed=0,bit=0,second=1,first=0,visible=16,ones=5;
};
static void prepared_tile_campaign(unsigned seed){
    Vadmission_probe d;auto&r=*d.rootp;uint64_t edges=0,contexts=0,canceled=0,first=0,malformed=0,speculative=0;
    const uint64_t primer_start=tile_priming_edges;
    d.clk=0;d.reset=1;d.start=d.abort_packet=d.in_valid=d.in_last=d.cache_write=d.lookup_req=d.replay_req=d.receipt_ready=0;
    d.packet_bytes=256;d.epoch=seed;
    auto tick=[&](){
        d.clk=0;d.eval();require(!d.mismatch,"tile campaign all-public preedge");
        const auto before=tile_before(d,false);
        d.clk=1;d.eval();require(!d.mismatch,"tile campaign all-public high edge");tile_after(d,before,false);
        d.clk=0;d.eval();require(!d.mismatch,"tile campaign all-public falling edge");
        require(++edges<100000,"tile campaign finite watchdog");
    };
    tick();d.reset=0;
    auto setup=[&](const TileCase&c){
        d.reset=1;tick();d.reset=0;
        const unsigned column=c.p?0U:c.tile%90U,odd=c.p?0U:(c.tile/90U)%2U;
        const unsigned base=c.p?0U:(c.tile/180U)*45U,cell=c.p?c.tile:base+column/2U;
        QBOTH(coord_valid,1U);QBOTH(coord_y_column,column);QBOTH(coord_y_odd,odd);QBOTH(coord_pair_base,base);QBOTH(coord_cell,cell);
        QBOTH(plane,c.p);QBOTH(tile,c.tile);QBOTH(group_end,c.end);QBOTH(receipt_epoch,seed+uint32_t(contexts));
        QBOTH(state,0U);QBOTH(group_tag,c.tag);QBOTH(bits_left,c.bits);QBOTH(bit_cache,c.bit?128U:0U);
        QBOTH(mixed_bit,c.mixed);QBOTH(tag_second,c.second);QBOTH(first_tag_bit,c.first);QBOTH(group_visible,c.visible);QBOTH(mixed_ones,c.ones);
        QBOTH(mode_cursor,128U);QBOTH(mode_bytes,64U);QBOTH(q_start,192U);QBOTH(size_bytes,256U);
        prime_tile_key(d,r);QBOTH(state,c.state);++contexts;
    };
    const std::vector<TileCase> scenarios{
        {6,0,632,648},{6,0,633,649},{6,0,5400,5400},{6,1,1350,1350},{6,2,1350,1350},
        {10,0,632,634,0},{10,0,632,634,1},{10,0,633,635,2},{10,0,652,654,2},{10,0,20,19,0},
        {10,0,650,650,2,1,0,0,1,0,16,0},{10,0,650,650,2,1,0,0,1,0,16,16},{10,0,650,650,2,1,0,0,1,0,16,5},
        {8,0,10,26,0,1,0,0,1,0},{8,0,10,26,0,1,0,1,1,0},{8,0,10,26,0,1,0,0,1,1},
        {8,0,10,26,0,1,0,1,1,1},{8,0,633,649,0,1,0,1,1,1,0},
        {8,0,651,653,2,1,1,0},{8,0,651,653,2,1,1,1},
        {11,0,5400,5400},{11,1,1350,1350},{11,2,1350,1350},{11,0,5399,5399},
        {0,0,10,26},{26,0,10,26},{27,0,10,26}
    };
    for(const auto&c:scenarios){
        setup(c);const bool terminal=c.tile==(c.p?1350U:5400U);
        unsigned expected_state=c.state,expected_error=0;uint32_t expected_tile=c.tile;unsigned expected_plane=c.p;
        if(c.state==6U){if(terminal){expected_tile=0;if(c.p==2U)expected_state=12U;else expected_plane=c.p+1U;}else expected_tile=c.tile+1U;}
        else if(c.state==10U){
            if(c.tile==c.end){if(c.tag==2U&&(c.ones==0U||c.ones==c.visible)){expected_error=8;expected_state=27;}else expected_state=11;}
            else if(tile_hidden_oracle(c.p,c.tile)||c.tag==0U||c.tag==1U)expected_tile=c.tile+1U;
            else expected_state=8;
        }else if(c.state==8U){
            if(c.mixed){expected_tile=c.tile+1U;expected_state=10;}
            else {const unsigned tag=(c.first<<1U)|c.bit;
                if(c.visible==0U){if(tag!=3U){expected_error=8;expected_state=27;}else {expected_tile=c.end;expected_state=11;}}
                else if(tag==3U){expected_error=8;expected_state=27;}else expected_state=10;
            }
        }else if(c.state==11U){if(terminal){if(c.p==2U)expected_state=12;else{expected_tile=0;expected_plane=c.p+1U;expected_state=7;}}else expected_state=7;}
        tick();require(d.debug_state==expected_state&&d.error==expected_error&&QNEW(tile)==expected_tile&&QNEW(plane)==expected_plane,"independent original branch/equality/error priority");
        malformed+=expected_error!=0;
        // First real consume after the writer, before any forced context changes.
        if(expected_state==6U||expected_state==10U||expected_state==11U){tick();++first;}
    }
    // GROUP_BEGIN must not compare the old end or capture through its min cone.
    for(unsigned trial=0;trial<4;++trial){
        const unsigned p=trial<3U?trial:0U;const uint32_t count=p?1350U:5400U;
        const uint32_t tile=trial<3U?count-1U:count,expected_end=trial<3U?count:16U;
        TileCase c{11,p,tile,tile};setup(c);
        tick();require(d.debug_state==7U,"real GROUP_NEXT predecessor");
        const bool old_group=QNEW(prepared_group_terminal);tick();
        require(d.debug_state==8U&&QNEW(group_end)==expected_end&&!QNEW(group_pred_owner_valid)&&bool(QNEW(prepared_group_terminal))==old_group,"new registered end invalidates owner and holds old payload");
        QBOTH(bits_left,1U);QBOTH(mixed_bit,0U);QBOTH(tag_second,1U);QBOTH(first_tag_bit,0U);QBOTH(bit_cache,0U);
        tick();require(d.debug_state==10U&&QNEW(group_pred_owner_valid)&&QNEW(group_pred_owner_end)==expected_end&&!QNEW(prepared_group_terminal),"tag commit captures current registered end instead of previous group end");
        tick();++first;
    }
    // Every original writer/first-consume fixture sees every cancel overlap.
    for(const auto&c:scenarios)for(unsigned flags=1;flags<8;++flags){
        setup(c);d.reset=flags&1U;d.start=bool(flags&2U);d.abort_packet=bool(flags&4U);tick();
        require(d.debug_state==(flags==2U?31U:0U)&&!QNEW(tile_pred_owner_valid)&&!QNEW(group_pred_owner_valid),"all cancellation precedence at writer/consume");
        d.reset=d.start=d.abort_packet=0;++canceled;
        setup(c);tick();
    }
    // An original speculative mixed mode write must survive the later error8.
    for(unsigned bit=0;bit<2;++bit){
        TileCase c{8,0,651,652,2,1,1,bit,1,0,16,bit?15U:0U};setup(c);
        QOLD(mode_store__DOT__words)[651]=3;QNEW(mode_store__DOT__words)[651]=3;
        tick();require(d.debug_state==10U&&QOLD(mode_store__DOT__words)[651]==(bit?2U:0U)&&QNEW(mode_store__DOT__words)[651]==(bit?2U:0U),"speculative mode write remains on original mixed edge");
        tick();require(d.debug_state==27U&&d.error==8U,"later mixed cardinality fault retains priority");
        require(QNEW(mode_store__DOT__words)[651]==(bit?2U:0U),"later rejection never rolls back original speculative write");++speculative;
    }
    require(canceled==scenarios.size()*7U&&first>0&&malformed>0&&speculative==2,"all prepared transition/firstfault domains");
    std::cout<<"{\"type\":\"v125_tile_campaign\",\"status\":\"TEST_PASS\",\"contexts\":"<<contexts<<",\"semantic_clock_edges\":"<<edges<<",\"primer_clock_edges\":"<<tile_priming_edges-primer_start<<",\"total_clock_edges\":"<<edges+tile_priming_edges-primer_start<<",\"cancel_cases\":"<<canceled<<",\"first_followup_consumes\":"<<first<<",\"malformed_contexts\":"<<malformed<<",\"speculative_mode_checks\":"<<speculative<<",\"prepared_domain_fixtures_are_natural_packets\":false}\n";
    d.final();
}
static void emit_counts(const std::array<uint64_t,9>&a){std::cout<<'[';for(unsigned i=0;i<a.size();++i){if(i)std::cout<<',';std::cout<<a[i];}std::cout<<']';}
int main(int argc,char**argv){try{
    require(inherited_bounds_main(argc,argv)==0,"complete retained V122 admission/header/bounds/original oracles");
    prepared_tile_campaign(unsigned(std::stoul(argv[2])));
    for(unsigned i=0;i<tile_writer_names.size();++i)require(tile_monitor.natural_writers[i]+tile_monitor.prepared_writers[i]>0,"every actual predecessor writer observed");
    for(unsigned i=0;i<7;++i)require(tile_monitor.first_consumes[i]>0,"every consumed predicate-writer first-consume observed");
    require(tile_monitor.overwritten_before_consume[7]>0,"plane-clear snapshot is shadowed by real group tag commit before consume");
    for(unsigned flags=1;flags<8;++flags)require(tile_monitor.cancels[flags]>0,"all cancellation overlaps observed");
    for(unsigned state=0;state<33;++state)for(unsigned flags=1;flags<8;++flags)require(tile_monitor.cancel_state_counts[state][flags]>0,"all original states retain every cancellation overlap");
    std::cout<<"{\"type\":\"v125_tile_verdict\",\"status\":\"TEST_PASS\",\"seed\":"<<argv[2]<<",\"natural_writers\":";emit_counts(tile_monitor.natural_writers);
    std::cout<<",\"prepared_writers\":";emit_counts(tile_monitor.prepared_writers);std::cout<<",\"first_consume_counts\":";emit_counts(tile_monitor.first_consumes);
    std::cout<<",\"overwritten_before_consume\":";emit_counts(tile_monitor.overwritten_before_consume);
    std::cout<<",\"cancel_state_counts\":[";for(unsigned s=0;s<33;++s){if(s)std::cout<<',';std::cout<<'[';for(unsigned f=0;f<8;++f){if(f)std::cout<<',';std::cout<<tile_monitor.cancel_state_counts[s][f];}std::cout<<']';}std::cout<<']';
    std::cout<<",\"cancel_counts\":[";for(unsigned i=0;i<8;++i){if(i)std::cout<<',';std::cout<<tile_monitor.cancels[i];}
    std::cout<<"],\"monitored_clock_edges\":"<<tile_monitor.edges<<",\"natural_clock_edges\":"<<tile_monitor.natural_edges<<",\"prepared_monitored_clock_edges\":"<<tile_monitor.prepared_edges<<",\"hold_edges\":"<<tile_monitor.holds<<",\"consume_edges\":"<<tile_monitor.consume_edges<<",\"natural_start_edges\":"<<tile_monitor.natural_starts<<",\"total_primer_clock_edges\":"<<tile_priming_edges<<",\"new_predicate_or_owner_forces\":0,\"old_require_checks_removed\":0,\"added_natural_public_cycles\":0,\"prepared_domain_fixtures_are_natural_packets\":false}\n";return 0;
}catch(const std::exception&e){std::cerr<<"V125_TILE_FAIL "<<e.what()<<'\n';return 1;}}
