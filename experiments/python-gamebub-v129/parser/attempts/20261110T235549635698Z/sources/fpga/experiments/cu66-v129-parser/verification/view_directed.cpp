// Additive real-interface tests. The historical body and paired oracle stay intact.
static unsigned view_directed(unsigned seed) {
    Sim sim(seed);
    unsigned checks=0;
    auto view=[&](unsigned value,bool zero) {
        require(sim.d.out_value==value,"V116 exact outside-valid value");
        require(bool(sim.d.probe_output_zero)==zero,"V116 zero-view classification");
        if(!zero)require(sim.d.probe_payload==value,"V116 owned payload selection");
        ++checks;
    };
    auto wait_state=[&](unsigned state) {
        for(unsigned n=0;n<100 && sim.d.probe_state!=state;++n)sim.step();
        require(sim.d.probe_state==state,"V116 directed state watchdog");
    };
    auto prime=[&](bool word16,bool serial) {
        sim.start(2,word16,serial);sim.request(1,24);
        sim.word(0xc0000000U,2,true);sim.response(0,1,2);
        view(1,false);
        for(unsigned n=0;n<4;++n){sim.step();view(1,false);}
    };
    for(bool serial:{false,true})for(bool word16:{false,true}) {
        // Ordinary nonzero then zero, without a start between requests. New
        // requests and consumed responses retain the previous successful data.
        sim.start(4,word16,serial);sim.word(0xe0000000U,4,true);
        sim.request(1,24);sim.response(0,1,2);view(1,false);
        sim.request(1,24);view(1,false);
        sim.response(0,0,4);view(0,false);
        // Error after a successful nonzero must hide retained private payload.
        prime(word16,serial);sim.request(0,24);sim.response(2,0,2);view(0,true);
        require(sim.d.probe_payload==1,"V116 truncation changed private payload");
        sim.request(0,24);sim.response(2,0,2);view(0,true);
        // BAD_PARAM and malformed padded input each retain hidden old payload.
        prime(word16,serial);sim.request(20,24);sim.response(1,0,2);view(0,true);
        require(sim.d.probe_payload==1,"V116 bad parameter changed payload");
        prime(word16,serial);sim.start(3,word16,serial);view(0,true);
        sim.request(1,24);sim.word(0x80000001U,3,true);sim.response(3,0,0);view(0,true);
        require(sim.d.probe_payload==1,"V116 bad word changed payload");
        // Prefix and suffix truncation, zero-length input, successful zero and
        // escape zero all distinguish a logical clear from a successful zero.
        sim.start(7,word16,serial);sim.request(0,24);sim.word(0,7,true);sim.response(2,0,7);view(0,true);
        sim.start(3,word16,serial);sim.request(4,24);sim.word(0x80000000U,3,true);sim.response(2,0,1);view(0,true);
        sim.start(0,word16,serial);sim.request(0,24);sim.response(2,0,0);view(0,true);
        sim.start(1,word16,serial);sim.request(0,0);sim.word(0x80000000U,1,true);sim.response(0,0,1);view(0,false);
        sim.start(15,word16,serial);sim.request(19,0);sim.word(0,15,true);sim.response(0,0,15);view(0,false);
        // Real protocol cancellation in every state, including held RESPONSE.
        // A new owner's first request never exposes the prior owner's payload.
        for(unsigned state=0;state<4;++state)for(unsigned guards=1;guards<4;++guards)
            for(bool ready:{false,true}) {
                prime(word16,serial);sim.start(2,word16,serial);
                if(state!=0)sim.request(1,24);
                if(state>=2)sim.word(0xc0000000U,2,true);
                wait_state(state);
                if(state==3){sim.step();view(1,false);}
                const unsigned payload=sim.d.probe_payload;
                sim.d.reset=(guards&1)!=0;sim.d.stream_start=(guards&2)!=0;
                sim.d.stream_bits=1;sim.d.in_valid=1;sim.d.in_bits=1;
                sim.d.in_data=0x80000000U;sim.d.in_last=1;
                sim.d.req_valid=1;sim.d.req_k=31;sim.d.req_escape=31;
                sim.d.out_ready=ready;sim.d.eval();
                require(!sim.d.req_ready&&!sim.d.in_ready,"V116 cancellation public input masks");
                sim.step();view(0,true);
                require(sim.d.probe_payload==payload,"V116 cancellation rewrote payload");
                require(!sim.d.out_valid&&sim.d.probe_state==0,"V116 cancellation priority");
                sim.d.reset=0;sim.d.stream_start=0;sim.d.in_valid=0;
                sim.d.req_valid=0;sim.d.out_ready=0;
                if(guards&1){sim.step();view(0,true);}
                sim.start(1,word16,serial);sim.request(0,24);view(0,true);
                sim.word(0x80000000U,1,true);sim.response(0,0,1);view(0,false);
            }
    }
    return checks;
}
