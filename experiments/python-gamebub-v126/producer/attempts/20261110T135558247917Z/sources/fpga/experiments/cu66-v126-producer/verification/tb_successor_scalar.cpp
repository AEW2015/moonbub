#include "Vproducer_scalar_probe.h"
#include "verilated.h"
#include <array>
#include <cstdint>
#include <iostream>
#include <random>
#include <stdexcept>
#include <string>

static void need(bool ok,const char*why){if(!ok)throw std::runtime_error(why);}
static unsigned oracle(unsigned p,unsigned t){t&=8191U;return (p?t:((t/90U)/2U)*45U+(t%90U)/2U)&2047U;}
int main(int argc,char**argv){try{
    need(argc==2,"scalar seed required");const unsigned seed=unsigned(std::stoul(argv[1]));std::mt19937 rng(seed);
    Vproducer_scalar_probe d;uint64_t edges=0,cases=0,holds=0,wrap13=0,plus2wrap=0,plane3=0,trunc11=0,cancels=0,spec_changes=0;
    d.clk=0;d.reset=1;d.abort_packet=d.accepted_start=0;d.operation=6;
    d.fixture_plane=d.fixture_tile=d.fixture_cell=d.fixture_frame=d.fixture_child=0;
    auto tick=[&](unsigned op){d.operation=op;d.clk=0;d.eval();d.clk=1;d.eval();d.clk=0;d.eval();need(++edges<4000000ULL,"scalar finite watchdog");};
    tick(6);d.reset=0;
    auto load=[&](unsigned p,unsigned t,uint32_t frame,uint32_t child){d.fixture_plane=p;d.fixture_tile=t;d.fixture_cell=oracle(p,t);d.fixture_frame=frame;d.fixture_child=child;tick(0);};
    auto seed_key=[&](unsigned p,unsigned t,uint32_t frame,uint32_t child){
        // Bootstrap only old geometry; both new payload stages use real source
        // task/ROM writers. This is an extracted prepared domain, not a packet.
        load(p,(t-1U)&8191U,frame,child);tick(1);
        load(p,t,frame,child);tick(2);
        need(d.addr_valid&&d.cell_valid&&d.addr_tile==t&&d.cell_tile==t&&d.addr_plane==p&&d.cell_plane==p&&d.addr_frame==frame&&d.cell_frame==frame&&d.cell_child==child,"full scalar geometry/frame/child keys from actual writers");
        need(d.out_address==((t+1U)&8191U)&&d.cell_address==d.out_address&&d.out_successor_cell==oracle(p,(t+1U)&8191U),"independent wrapped address before exact table lookup");
    };
    auto test=[&](unsigned p,unsigned t,uint32_t frame,uint32_t child){
        seed_key(p,t,frame,child);const unsigned cell=d.out_successor_cell,address=d.out_address;
        for(unsigned h=0;h<3;++h){d.fixture_plane=rng()%4;d.fixture_tile=rng()&8191U;d.fixture_frame=rng();d.fixture_child=rng();tick(6);
            need(d.out_address==address&&d.out_successor_cell==cell&&d.addr_valid&&d.cell_valid&&d.cell_frame==frame&&d.cell_child==child,"changed fixture inputs cannot alter held owned stages");++holds;}
        tick(3);need(d.out_tile==((t+1U)&8191U)&&d.out_current_cell==oracle(p,d.out_tile)&&d.out_address==((t+2U)&8191U)&&d.addr_valid&&!d.cell_valid,"first advance copies ROM result and prepares oldt+2");
        tick(2);tick(3);need(d.out_tile==((t+2U)&8191U)&&d.out_current_cell==oracle(p,d.out_tile)&&d.out_address==((t+3U)&8191U),"consecutive skip geometry remains exact through thirteen-bit wrap");
        const unsigned held_t=d.out_tile;tick(4);const unsigned next=p==2U?p:(p+1U)&3U;
        need(d.out_plane==next&&d.out_tile==held_t&&d.out_current_cell==oracle(next,held_t)&&!d.addr_valid&&!d.cell_valid,"NEXT_PLANE exact current-cell intermediate and plane3 wrap");
        tick(5);need(d.out_tile==0&&d.out_current_cell==0&&d.out_address==1&&d.addr_valid&&!d.cell_valid,"nonempty plane clear establishes successor1");
        wrap13+=t==8191U;plus2wrap+=t>=8190U;plane3+=p==3U;trunc11+=p==0U&&((t/90U)/2U)*45U+(t%90U)/2U>2047U;++cases;
    };
    for(unsigned p=0;p<4;++p)for(unsigned t=0;t<8192;++t)test(p,t,seed+t,p*0x40000000U+t);
    for(unsigned i=0;i<65536;++i)test(rng()%4,rng()&8191U,rng(),rng());
    const std::array<unsigned,8> tiles{{0,1,89,90,127,128,8190,8191}};
    const std::array<unsigned,5> phases{{1,2,3,4,5}};
    std::array<uint64_t,8> cancel_counts{};
    for(unsigned p=0;p<4;++p)for(unsigned t:tiles)for(unsigned op:phases)for(unsigned flags=1;flags<8;++flags){
        seed_key(p,t,seed,0x80000000U|seed);
        if(op==2U){
            // Change address with a real writer, keeping old ROM payload, so
            // canceled MAP_REQ really has an opportunity to change its bits.
            tick(1);load(p,(t+1U)&8191U,seed,0x80000000U|seed);
        }
        const unsigned before_addr=d.out_address,before_cell=d.out_successor_cell,before_p=d.out_plane;
        d.reset=flags&1U;d.abort_packet=bool(flags&2U);d.accepted_start=bool(flags&4U);tick(op);
        need(!d.addr_valid&&!d.cell_valid&&d.out_tile==0&&d.out_current_cell==0,"logical cancellation wins before any geometry consume");
        need(d.out_address==before_addr&&d.out_successor_cell==(op==2U?oracle(before_p,before_addr):before_cell),"unreset phase-local ROM sampling has correct cancellation semantics");
        spec_changes+=op==2U&&d.out_successor_cell!=before_cell;
        d.reset=d.abort_packet=d.accepted_start=0;seed_key(p,t,seed,0x80000000U|seed);++cancels;++cancel_counts[flags];
    }
    need(cases==98304&&cancels==1120&&holds==294912&&edges==1190177,"exact scalar/domain/cancellation clocks");
    need(wrap13>0&&plus2wrap>0&&plane3>0&&trunc11>0&&spec_changes>0,"full13 and full11 wrap plus changed canceled-ROM payload observed");
    for(unsigned f=1;f<8;++f)need(cancel_counts[f]==160U,"every cancellation overlap spans all scalar planes/boundaries/phases");
    std::cout<<"{\"type\":\"v126_successor_scalar_verdict\",\"status\":\"TEST_PASS\",\"seed\":"<<seed<<",\"exhaustive_full13_cases\":32768,\"random_cases\":65536,\"cases\":"<<cases<<",\"clock_edges\":"<<edges<<",\"hold_edges\":"<<holds<<",\"cancel_cases\":"<<cancels<<",\"successor13_wrap_cases\":"<<wrap13<<",\"plus2_wrap_cases\":"<<plus2wrap<<",\"plane3_cases\":"<<plane3<<",\"y_cell11_truncation_cases\":"<<trunc11<<",\"canceled_rom_value_changes\":"<<spec_changes<<",\"new_payload_or_owner_forces\":0,\"prepared_scalar_domain_is_natural_packets\":false}\n";d.final();return 0;
}catch(const std::exception&e){std::cerr<<"V126_SCALAR_FAIL "<<e.what()<<'\n';return 1;}}
