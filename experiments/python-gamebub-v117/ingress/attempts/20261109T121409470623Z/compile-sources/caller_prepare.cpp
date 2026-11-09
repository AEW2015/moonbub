static unsigned caller_prepare_cancels(Sim& sim,const Case& sparse,const Case& raw){
    unsigned checks=0;
    for(const Case* packet:{&sparse,&raw})for(unsigned phase=0;phase<3;++phase)
        for(unsigned action=0;action<3;++action){
            sim.overlap=sim.prefetch=sim.tile_overlap=true;sim.slow=true;
            sim.start(*packet,false);size_t at=0;
            for(unsigned n=0;sim.d.dbg_scratch_state!=30;++n){
                require(n<200000,"V116B real caller prepare setup watchdog");
                sim.d.in_valid=at<packet->packet.size();
                if(sim.d.in_valid){sim.d.in_data=packet->packet[at];sim.d.in_last=at+1==packet->packet.size();}
                if(sim.step().input)++at;
            }
            sim.d.in_valid=0;
            for(unsigned j=0;j<phase;++j)sim.step();
            require(sim.d.dbg_scratch_state==(phase==2?31:30)&&!sim.pending.valid&&!sim.d.out_valid,"V116B real preparation owner/debt");
            if(action==0){sim.d.abort_packet=1;sim.step();sim.d.abort_packet=0;}
            else if(action==1){sim.d.reset=1;sim.step();sim.d.reset=0;}
            else{sim.start(*packet,false);sim.d.abort_packet=1;sim.step();sim.d.abort_packet=0;}
            sim.d.in_valid=0;sim.d.out_ready=1;
            for(unsigned j=0;j<10;++j){sim.step();require(!sim.pending.valid&&!sim.d.out_valid&&!sim.d.mem_req_valid,"V116B stale owner after prepare cancellation");}
            require(!sim.d.busy&&!sim.d.draining,"V116B prepare cancellation did not quiesce");
            sim.run(*packet,false,true);++checks;
        }
    require(checks==18,"V116B caller complete preparation cancel coverage");return checks;
}
