#include "tb_successor_scalar.cpp"

int main(int argc,char**argv){try{
    need(inherited_successor_scalar_main(argc,argv)==0,"all V126 source-bound full13 successor scalar checks retained");
    const unsigned seed=unsigned(std::stoul(argv[1]));std::mt19937 rng(seed);
    Vproducer_scalar_probe d;d.clk=0;d.reset=1;d.abort_packet=d.accepted_start=0;d.operation=6;
    d.fixture_plane=d.fixture_tile=d.fixture_cell=d.fixture_frame=d.fixture_child=0;
    uint64_t cases=0,edges=0,true_cases=0,false_cases=0,scalar_only=0,bank_only=0;
    unsigned mode_mask=0,emit_mask=0,patterns=0;
    auto check=[&](uint32_t epoch,unsigned block,uint32_t scalar_epoch,unsigned scalar_block,
                   uint32_t e0,uint32_t e1,unsigned b0,unsigned b1,unsigned mode,unsigned emit,unsigned pattern){
        d.owner_expected_epoch=epoch;d.expected_block=block;
        d.raw_scalar_epoch=scalar_epoch;d.raw_scalar_block=scalar_block;
        d.bank_epoch0=e0;d.bank_epoch1=e1;d.bank_block0=b0;d.bank_block1=b1;
        d.raw_mode=mode&1U;d.tile_overlap_mode=(mode>>1U)&1U;d.dbg_emit_bank=emit;
        const bool scalar=(scalar_epoch==epoch&&scalar_block==block);
        const bool lane0=e0==epoch&&b0==block,lane1=e1==epoch&&b1==block;
        const uint32_t chosen_epoch=mode==2U?(emit?e1:e0):scalar_epoch;
        const unsigned chosen_block=mode==2U?(emit?b1:b0):scalar_block;
        const bool selected=chosen_epoch==epoch&&chosen_block==block;
        auto compare=[&](){
            need(bool(d.scalar_owner_match)==scalar,"independent uint32/uint16 scalar lane oracle");
            need(d.tile_owner_match==unsigned(lane0|(lane1<<1U)),"independent both-bank full-width oracle");
            need(bool(d.child_owner_match)==selected&&bool(d.original_owner_match)==selected,"original selected fields vs new three lanes exact identity");
        };
        d.clk=0;d.eval();compare();d.clk=1;d.eval();compare();d.clk=0;d.eval();compare();
        ++edges;++cases;true_cases+=selected;false_cases+=!selected;
        scalar_only+=scalar&&!lane0&&!lane1;bank_only+=!scalar&&(lane0||lane1);
        mode_mask|=1U<<mode;emit_mask|=1U<<emit;patterns|=1U<<(pattern&15U);
    };
    const std::array<uint32_t,8> epochs{{0U,1U,65535U,65536U,0x7fffffffU,0x80000000U,0xfffffffeU,0xffffffffU}};
    const std::array<unsigned,6> blocks{{0U,1U,32767U,32768U,65534U,65535U}};
    for(uint32_t epoch:epochs)for(unsigned block:blocks)for(unsigned pattern=0;pattern<64;++pattern)
      for(unsigned mode=0;mode<4;++mode)for(unsigned emit=0;emit<2;++emit){
        check(epoch,block,epoch^((pattern&1U)?0U:0x80000000U),block^((pattern&2U)?0U:0x8000U),
              epoch^((pattern&4U)?0U:0x80000000U),epoch^((pattern&16U)?0U:0x80000000U),
              block^((pattern&8U)?0U:0x8000U),block^((pattern&32U)?0U:0x8000U),mode,emit,pattern);
    }
    need(cases==24576U,"exact full-width boundary owner scalar matrix");
    for(unsigned k=0;k<65536U;++k){
        const uint32_t epoch=rng();const unsigned block=rng()&65535U,pattern=k&63U;
        check(epoch,block,(pattern&1U)?epoch:rng(),(pattern&2U)?block:rng()&65535U,
              (pattern&4U)?epoch:rng(),(pattern&16U)?epoch:rng(),
              (pattern&8U)?block:rng()&65535U,(pattern&32U)?block:rng()&65535U,k&3U,(k>>2U)&1U,pattern);
    }
    need(cases==90112U&&edges==90112U&&true_cases&&false_cases&&scalar_only&&bank_only&&mode_mask==15U&&emit_mask==3U&&patterns==65535U,"exact scalar owner campaign and branch coverage");
    std::cout<<"{\"type\":\"v127_owner_factor_scalar_verdict\",\"status\":\"TEST_PASS\",\"seed\":"<<seed<<",\"boundary_cases\":24576,\"random_cases\":65536,\"cases\":"<<cases<<",\"clock_edges\":"<<edges<<",\"eval_checks\":"<<cases*3U<<",\"mode_mask\":"<<mode_mask<<",\"emit_mask\":"<<emit_mask<<",\"true_cases\":"<<true_cases<<",\"false_cases\":"<<false_cases<<",\"scalar_only_match_cases\":"<<scalar_only<<",\"bank_only_match_cases\":"<<bank_only<<",\"new_predicate_forces\":0,\"extracted_scalar_domain_is_natural_packets\":false}\n";
    d.final();return 0;
}catch(const std::exception&e){std::cerr<<"V127_OWNER_SCALAR_FAIL "<<e.what()<<'\n';return 1;}}
