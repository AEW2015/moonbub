#include "Vscalar_probe.h"
#include "verilated.h"
#include <array>
#include <cstdint>
#include <iostream>
#include <random>
#include <set>
#include <stdexcept>
#include <string>

static void need(bool ok,const char*why){if(!ok)throw std::runtime_error(why);}
static bool hidden(unsigned p,uint32_t t){
    if(p)return t>=1046&&t<=1064;
    constexpr std::array<std::array<uint32_t,2>,9> ranges{{{{633,651}},{{723,741}},{{993,1011}},{{1083,1101}},{{4071,4110}},{{4161,4200}},{{4251,4290}},{{4431,4460}},{{4521,4550}}}};
    for(const auto&x:ranges)if(t>=x[0]&&t<=x[1])return true;
    return false;
}
int main(int argc,char**argv){try{
    need(argc==2,"usage scalar_probe seed");const unsigned seed=unsigned(std::stoul(argv[1]));
    Vscalar_probe d;std::mt19937 rng(seed);uint64_t cases=0,edges=0,holds=0,cancels=0,high=0,plane3=0,wraps=0;
    uint64_t hidden_true=0,terminal_true=0,group_true=0;std::array<uint64_t,8> kill_counts{};
    d.clk=0;d.reset=1;d.start=d.abort_packet=d.capture=d.group_capture=d.group_begin=0;
    d.key_terminal_capture=d.plane_clear_capture=0;
    d.plane=0;d.tile=d.group_end=d.receipt_epoch=0;
    auto tick=[&](){d.clk=0;d.eval();d.clk=1;d.eval();d.clk=0;d.eval();need(++edges<12000000,"finite scalar watchdog");};
    tick();d.reset=0;
    auto test=[&](unsigned p,uint32_t t,uint32_t g){
        const uint32_t epoch=seed+uint32_t(cases);const bool h=hidden(p,t),term=t==(p?1350U:5400U),gt=t==g;
        d.plane=p;d.tile=t;d.group_end=g;d.receipt_epoch=epoch;d.capture=d.group_capture=1;tick();d.capture=0;
        need(bool(d.out_hidden)==h&&bool(d.out_terminal)==term&&bool(d.out_group)==gt,"independent full32 captured scalar equations");
        need(d.tile_valid&&d.group_valid&&d.tile_epoch==epoch&&d.group_epoch==epoch&&d.tile_key==t&&d.group_key==t&&d.group_end_key==g&&d.tile_plane==p&&d.group_plane==p,"complete scalar capture ownership");
        for(unsigned hold=0;hold<2;++hold){d.plane=rng()%4;d.tile=rng();d.group_end=rng();d.receipt_epoch=rng();tick();
            need(bool(d.out_hidden)==h&&bool(d.out_terminal)==term&&bool(d.out_group)==gt&&d.tile_epoch==epoch&&d.group_epoch==epoch&&d.tile_key==t&&d.group_end_key==g,"changed unowned inputs cannot alter held scalar/key");++holds;}
        d.group_begin=1;tick();d.group_begin=0;need(d.tile_valid&&!d.group_valid&&bool(d.out_group)==gt,"group begin invalidates ownership without min-cone payload capture");
        // Every overlap cancels an attempted group capture, then a real capture retries.
        for(unsigned flags=1;flags<8;++flags){
            d.reset=bool(flags&1);d.start=bool(flags&2);d.abort_packet=bool(flags&4);d.capture=d.group_capture=1;
            tick();need(!d.tile_valid&&!d.group_valid&&bool(d.out_hidden)==h&&bool(d.out_terminal)==term&&bool(d.out_group)==gt,"cancel outranks attempted capture and leaves payload unreset");
            d.reset=d.start=d.abort_packet=0;d.plane=p;d.tile=t;d.group_end=g;d.receipt_epoch=epoch;tick();
            need(d.tile_valid&&d.group_valid&&bool(d.out_hidden)==h&&bool(d.out_terminal)==term&&bool(d.out_group)==gt,"clean full-key recapture after cancellation");
            d.capture=0;++cancels;++kill_counts[flags];
        }
        // A tile-only writer invalidates group ownership and does not write its payload.
        d.capture=1;d.group_capture=0;tick();d.capture=0;
        need(d.tile_valid&&!d.group_valid&&bool(d.out_group)==gt,"tile-only writer leaves group payload and revokes its ownership");
        high+=t>8191U||g>8191U;plane3+=p==3U;wraps+=uint32_t(t+16U)<t;
        hidden_true+=h;terminal_true+=term;group_true+=gt;++cases;
    };
    std::set<uint32_t> values;for(uint32_t t=0;t<8192;++t)values.insert(t);
    for(unsigned bit=13;bit<32;++bit){const uint32_t one=uint32_t(1U)<<bit;for(uint32_t v:{one-1U,one,one+1U,one+633U,one+1350U,one+5400U})values.insert(v);}
    for(uint32_t v:{0xfffffff0U,0xfffffff1U,0xfffffffeU,0xffffffffU})values.insert(v);
    for(unsigned p=0;p<4;++p)for(uint32_t t:values){const uint32_t limit=p?1350U:5400U;
        const std::array<uint32_t,7> ends{{t,uint32_t(t-1U),uint32_t(t+1U),uint32_t(t+16U),limit,0U,0xffffffffU}};
        for(uint32_t g:ends)test(p,t,g);
    }
    const uint64_t boundary=cases;
    for(unsigned i=0;i<65536;++i){const unsigned p=rng()%4;const uint32_t t=rng();test(p,t,(i%3)?rng():t);}
    uint64_t terminal_transitions=0;
    for(unsigned mode=0;mode<2;++mode)for(unsigned p=0;p<4;++p){
        d.plane=p;d.tile=p?1350U:5400U;d.group_end=d.tile;d.receipt_epoch=seed;
        d.capture=d.group_capture=1;tick();need(d.out_terminal&&d.out_group,"prime terminal scalar before extracted successor call");
        d.key_terminal_capture=mode==0;d.plane_clear_capture=mode==1;tick();
        if(mode==1&&p==2U)need(d.out_terminal&&d.out_group&&d.group_valid&&d.tile_key==1350U&&d.tile_plane==2U,"last-plane group transition retains original no-write behavior");
        else {const unsigned next=mode==0&&p==2U?p:(p+1U)&3U;
            need(!d.out_hidden&&!d.out_terminal&&d.out_group&&!d.group_valid&&d.tile_key==0U&&d.tile_plane==next,"literal terminal successor preserves all4 planes and two-bit wrap");}
        d.capture=d.key_terminal_capture=d.plane_clear_capture=0;++terminal_transitions;
    }
    need(cases==boundary+65536&&high>0&&plane3>0&&wraps>0&&hidden_true>0&&terminal_true>0&&group_true>0,"all scalar fullwidth truth domains reached");
    for(unsigned f=1;f<8;++f)need(kill_counts[f]==cases,"every scalar key has all cancel overlaps");
    std::cout<<"{\"type\":\"v125_tile_scalar_verdict\",\"status\":\"TEST_PASS\",\"seed\":"<<seed
      <<",\"boundary_cases\":"<<boundary<<",\"random_full32_cases\":65536,\"cases\":"<<cases<<",\"clock_edges\":"<<edges
      <<",\"hold_edges\":"<<holds<<",\"cancel_cases\":"<<cancels<<",\"highbit_cases\":"<<high<<",\"plane3_cases\":"<<plane3
      <<",\"uint32_plus16_wrap_cases\":"<<wraps<<",\"hidden_true\":"<<hidden_true<<",\"terminal_true\":"<<terminal_true<<",\"group_true\":"<<group_true
      <<",\"terminal_transition_cases\":"<<terminal_transitions
      <<",\"new_predicate_or_owner_forces\":0,\"extracted_domain_is_natural_packets\":false}\n";d.final();return 0;
}catch(const std::exception&e){std::cerr<<"V125_SCALAR_FAIL "<<e.what()<<'\n';return 1;}}
