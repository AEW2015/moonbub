#include "tb_slot.cpp"
// Additive current/foreign abort tests over all real descriptor preparation
// stages. No state or epoch backdoor injection, assumptions or checker masking.
int main(int argc,char**argv){try{
    need(inherited_slot_main(argc,argv)==0,"complete immutable inherited scratch proof");
    const unsigned seed=unsigned(std::stoul(argv[1]));
    std::ofstream trace(std::string(argv[2])+"-abort.jsonl");need(bool(trace),"abort trace open");
    unsigned prepare_cases=0,foreign_cases=0,current_cases=0,error_cases=0;
    for(unsigned phase=0;phase<3;++phase)for(unsigned raw=0;raw<2;++raw)
        for(unsigned action=0;action<5;++action)for(unsigned response=0;response<3;++response){
            ProbeBench b(seed+prepare_cases,trace);b.d.adapter_enabled=false;
            b.d.begin_blocks=1;b.d.begin_raw=raw;b.d.begin_epoch=17;
            b.d.begin_count1=b.d.begin_count2=b.d.begin_count3=0;
            b.d.begin_overlap=b.d.begin_prefetch=1;b.d.begin_tile_overlap=!raw;
            b.d.begin_valid=1;b.d.candidate_only_edge();b.d.begin_valid=0;
            for(unsigned j=0;j<phase;++j)b.d.candidate_only_edge();
            need(b.d.verify_preparing&&b.d.active_epoch==17,"real preparation owner setup");
            // Initial active epoch zero and foreign future epoch are both
            // mismatched; current epoch must cancel on this very edge.
            b.d.abort_valid=action<3;b.d.abort_epoch=action==0?0:action==1?18:17;
            b.d.reset=action>=3;
            if(action==4){b.d.abort_valid=1;b.d.abort_epoch=18;}
            b.d.mem_rsp_valid=response!=0;b.d.mem_rsp_epoch=123;b.d.mem_rsp_error=response==2;
            b.d.clk=0;b.d.eval();
            const bool expected=b.d.reset||(b.d.abort_valid&&b.d.abort_epoch==17);
            need(bool(b.d.verify_prepare_cancel)==expected,"independent generic selected-owner abort predicate");
            if(action<2){need(!expected,"foreign abort accidentally matches");++foreign_cases;}
            else{need(expected,"current/reset abort failed");++current_cases;}
            b.d.candidate_only_edge();b.d.mem_rsp_valid=b.d.mem_rsp_error=0;
            b.d.abort_valid=b.d.reset=0;b.d.clk=0;b.d.eval();
            if(expected)need(!b.d.busy&&b.d.begin_ready&&!b.d.debug_outstanding,"preparation kill lost immediate retirement");
            else if(response){need(b.d.error==6&&!b.d.busy,"foreign abort masked unsolicited response failure");++error_cases;}
            ++prepare_cases;
        }
    unsigned pending_cases=0;
    for(unsigned read=0;read<2;++read)for(unsigned tile=0;tile<2;++tile){
        ProbeBench b(seed+1000+pending_cases,trace);auto p=packet(3,false,seed+pending_cases);
        b.ingest(p,6U|(tile<<3));
        for(unsigned n=0;!(b.pending&&b.owner_write==!bool(read));++n){need(n<20000,"physical abort lease setup watchdog");b.tick();}
        b.hold_ack=true;b.d.abort_valid=1;b.d.abort_epoch=b.epoch^0x80000000U;
        b.tick();need(b.pending&&!b.d.verify_prepare_cancel,"foreign abort retired physical owner");
        b.d.abort_epoch=b.epoch;b.tick();b.d.abort_epoch=b.epoch+1;
        for(unsigned n=0;n<8;++n){b.tick();need(b.pending&&b.d.debug_state==25&&!b.d.verify_prepare_cancel&&!b.d.dense_valid,"foreign abort released drain debt");}
        b.d.abort_valid=0;b.abort_and_drain(false);need(!b.pending&&!b.d.busy,"current owner ACK drain failed");++pending_cases;
    }
    need(pending_cases==4,"physical write/read foreign/current/drain coverage");
    need(prepare_cases==90&&foreign_cases==36&&current_cases==54&&error_cases==24,"all preparation/cancel/failure branches covered");
    std::cout<<"{\"type\":\"v116b_generic_abort_verdict\",\"status\":\"TEST_PASS\",\"seed\":"<<seed<<",\"prepared_abort_cases\":"<<prepare_cases<<",\"foreign_abort_cases\":"<<foreign_cases<<",\"current_or_reset_cases\":"<<current_cases<<",\"unsolicited_response_error_cases\":"<<error_cases<<",\"physical_pending_abort_cases\":"<<pending_cases<<",\"public_cycle_delta\":0,\"pair_skipped_edges\":0,\"old_assertions_removed\":0}\n";
    return 0;
}catch(const std::exception&e){std::cerr<<"V116B_CONTROL_FAIL "<<e.what()<<'\n';return 1;}}
