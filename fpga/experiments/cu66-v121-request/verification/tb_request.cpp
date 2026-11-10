#include "tb_refill_legacy.cpp"

int main(int argc, char **argv) {
    try {
        need(argc==2,"usage: Vrequest_probe seed");
        need(inherited_main(argc,argv)==0,"inherited queue regression failed");
        Bench b(unsigned(std::stoul(argv[1])));
        unsigned legal_boundary_cases=0, stalled_boundary_cases=0, random_cases=0;
        uint64_t complete_bytes=0, simultaneous=0;
        for(uint32_t at:{0U,1U,0xffffU,0x10000U,0x7fffffffU,0x80000000U,0xffff0000U,0xfffffffeU,0xffffffffU}) {
            for(uint32_t n:{0U,1U,2U,3U,17U}) {
                if(uint64_t(at)+n>0x100000000ULL)continue;
                b.begin(n,at,0x80000000U+legal_boundary_cases);
                b.finish();
                need(b.d.req_addr==uint32_t(at+n),"unqualified full32 final address mismatch");
                complete_bytes+=n;++legal_boundary_cases;
            }
        }
        // Large lengths exercise unsigned eligibility without iterating 2^32
        // bytes. A blocked offer is observed and then revoked, never accepted
        // outside the inherited no-overflow caller contract.
        for(uint32_t at:{0U,0x7fffffffU,0x80000000U,0xfffffffeU,0xffffffffU}) {
            for(uint32_t n:{0U,1U,0x7fffffffU,0x80000000U,0xffffffffU}) {
                b.begin(n,at,0xffffffffU-stalled_boundary_cases);
                b.read_ready=false;b.child_ready=false;
                for(unsigned k=0;k<13;++k) {
                    b.tick();
                    need(bool(b.d.req_valid)==(n!=0),"unsigned full32 initial eligibility changed");
                    need(b.d.req_addr==at&&!b.d.count_requests,"stalled full32 cursor changed");
                }
                b.cancel_now();need(b.d.req_addr==0,"cancel did not clear unqualified cursor");
                ++stalled_boundary_cases;
            }
        }
        for(unsigned k=0;k<2048;++k) {
            uint32_t at=b.rng(),n=b.random(97),tag=b.rng();
            if(uint64_t(at)+n>0x100000000ULL)at-=n;
            b.begin(n,at,tag);b.finish();
            complete_bytes+=n;simultaneous+=b.simultaneous;++random_cases;
        }
        // Accepted physical read responses are still presented on the revoke
        // edge. Neither queue may turn revocation into a memory cancellation.
        uint64_t revoke_before=b.physical_responses_on_revoke;
        for(unsigned mode=0;mode<4;++mode) {
            b.begin(9,0x80000031U+mode,0xfffffffcU+mode);b.tick();
            need(b.d.pending&&b.flight.has_value(),"physical revoke setup absent");
            if(mode==0)b.d.cancel=1;
            if(mode==1)b.d.reset=1;
            if(mode==2)b.d.clear_stats=1;
            if(mode==3){b.d.start=1;b.d.start_offset=0xffffffffU;b.d.start_length=1;b.d.start_epoch=23;}
            b.tick();b.d.cancel=b.d.reset=b.d.clear_stats=b.d.start=0;
            need(!b.flight,"physical response debt did not drain on revoke edge");
            b.cancel_now();
        }
        need(b.physical_responses_on_revoke-revoke_before==4,"accepted responses suppressed by revoke");
        need(simultaneous>0,"random suite missed simultaneous push/pop");
        std::cout<<"{\"type\":\"v121_request_verdict\",\"status\":\"TEST_PASS\",\"legal_boundary_cases\":"<<legal_boundary_cases
                 <<",\"stalled_full32_cases\":"<<stalled_boundary_cases<<",\"random_cases\":"<<random_cases
                 <<",\"completed_bytes\":"<<complete_bytes<<",\"simultaneous_push_pop\":"<<simultaneous
                 <<",\"physical_responses_on_revoke\":"<<(b.physical_responses_on_revoke-revoke_before)
                 <<",\"cycles\":"<<b.cycles<<",\"old_require_checks_removed\":0,\"added_public_cycles\":0}\n";
        return 0;
    } catch(const std::exception &e) {std::cerr<<"V121_REQUEST_TEST_FAIL "<<e.what()<<'\n';return 1;}
}
