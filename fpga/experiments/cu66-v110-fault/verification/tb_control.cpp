#include <verilated.h>
#include "Vcontrol_probe.h"
#include <array>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>

static bool hidden(unsigned p,unsigned t){
    if(p!=0)return t/45==23 && t%45>=11 && t%45<30;
    const unsigned x=t%90,y=t/90;
    return (x>=3&&x<22&&((y>=7&&y<9)||(y>=11&&y<13))) ||
           (x>=21&&x<61&&y>=45&&y<48) || (x>=21&&x<51&&y>=49&&y<51);
}
static unsigned cell(unsigned p,unsigned t){return p==0?(t/90/2)*45+(t%90)/2:t;}
struct Driver {
    Vcontrol_probe d;
    std::ofstream trace;
    uint64_t clocks=0,checks=0,outputs=0,advances=0,holds=0,digest=1469598103934665603ULL;
    uint32_t rng=104401,frame_epoch=17,fid=100;
    std::array<unsigned,3> blocks{};
    bool predicted=false,pending=false;
    unsigned delay=0;
    uint32_t ref_epoch=0,ref_fid=0,ref_tile=0,ref_plane=0;
    uint64_t ref_generation=0;
    unsigned old_p=99,old_t=99999,old_s=99;
    explicit Driver(const char*path):trace(path){if(!trace)throw std::runtime_error("trace open");
        d.clk=0;
        d.reset=0;
        d.start=0;
        d.cancel=0;
        d.admitted_ready=0;
        d.key_frame=0;
        d.input_done=0;
        d.epoch=0;
        d.frame_fid=0;
        d.accepted_ref_valid=0;
        d.accepted_ref_fid=0;
        d.accepted_ref_generation=0;
        d.lookup_ready=0;
        d.lookup_rsp=0;
        d.lookup_mode=0;
        d.lookup_scale=0;
        d.in_valid=0;
        d.in_epoch=0;
        d.in_child_epoch=0;
        d.in_token=0;
        d.in_plane=0;
        d.in_qscale=0;
        d.in_block=0;
        d.in_tile=0;
        d.in_qcell=0;
        d.in_index=0;
        d.in_value=0;
        d.out_ready=0;
        d.ref_req_ready=0;
        d.ref_rsp_valid=0;
        d.ref_rsp_epoch=0;
        d.ref_rsp_fid=0;
        d.ref_rsp_generation=0;
        d.ref_rsp_plane=0;
        d.ref_rsp_tile=0;
        for(unsigned n=0;n<16;++n)d.ref_rsp_pixels[n]=0;
        d.ref_rsp_error=0;
        d.accepted_ref_valid=1;d.accepted_ref_fid=42;d.accepted_ref_generation=77;
        for(unsigned n=0;n<16;++n)d.ref_rsp_pixels[n]=0x80808080U;
    }
    uint32_t random(){rng^=rng<<13;rng^=rng>>17;rng^=rng<<5;return rng;}
    void require(bool ok,const std::string&why){if(!ok)throw std::runtime_error(why+" clock="+std::to_string(clocks)+" state="+std::to_string(d.state)+" plane="+std::to_string(d.verify_plane)+" tile="+std::to_string(d.verify_tile));}
    void check(){
        d.verify_abort_packet=d.cancel&&((clocks&1U)!=0);
        d.eval();++checks;
        require(!d.mismatch,"public output or verification-coordinate mismatch");
        if(clocks){
            const unsigned p=d.verify_plane,t=d.verify_tile;
            require(p<=2 && t<(p==0?5400U:1350U),"coordinate range");
            require(d.lookup_cell==cell(p,t) && d.verify_cell==cell(p,t),"independent cell oracle");
            require(d.verify_y_column==(p==0?t%90:0),"column oracle");
            require(d.verify_y_odd_row==(p==0?(t/90)&1:0),"row parity oracle");
        }
        digest^=uint64_t(d.state)|(uint64_t(d.verify_plane)<<4)|(uint64_t(d.verify_tile)<<6)|(uint64_t(d.verify_cell)<<19)|(uint64_t(d.out_valid)<<30)|(uint64_t(d.out_value)<<31)|(uint64_t(d.error)<<39);
        digest*=1099511628211ULL;
    }
    void tick(){
        d.clk=0;check();
        const unsigned p=d.verify_plane,t=d.verify_tile,s=d.state;
        const bool take_output=d.out_valid&&d.out_ready;
        const bool output_last=take_output&&d.out_index==63;
        if(take_output){
            unsigned expected=128;
            if(d.out_mode==2)expected=unsigned(128+int((d.out_tile+d.out_index)%17)-8);
            require(d.out_value==expected,"independent canonical pixel oracle");++outputs;
        }
        const bool got_ref=d.ref_req_valid&&d.ref_req_ready;
        const bool rsp=d.ref_rsp_valid&&d.ref_rsp_ready;
        const bool residual=d.in_valid&&d.in_ready&&d.verify_fill_index==63;
        const bool killed=d.reset||d.cancel||d.start;
        const uint32_t save_epoch=d.ref_req_epoch,save_fid=d.ref_req_fid,save_tile=d.ref_req_tile,save_plane=d.ref_req_plane;
        const uint64_t save_gen=d.ref_req_generation;
        d.clk=1;check();++clocks;
        if(killed)blocks.fill(0);else if(residual&&d.error==0)++blocks[p];
        if(rsp)pending=false;
        if(got_ref){require(!pending,"external reference overwrite");pending=true;delay=3;ref_epoch=save_epoch;ref_fid=save_fid;ref_generation=save_gen;ref_tile=save_tile;ref_plane=save_plane;}
        const bool advance=d.verify_plane!=p||d.verify_tile!=t;
        if(advance)++advances;else++holds;
        if(advance||d.state!=s||killed||clocks<20||(clocks%997)==0){
            trace<<"{\"clock\":"<<clocks<<",\"plane\":"<<unsigned(d.verify_plane)<<",\"tile\":"<<d.verify_tile
              <<",\"cell\":"<<d.verify_cell<<",\"lookup\":"<<d.lookup_cell<<",\"column\":"<<unsigned(d.verify_y_column)
              <<",\"odd\":"<<unsigned(d.verify_y_odd_row)<<",\"state\":"<<unsigned(d.state)
              <<",\"reset\":"<<unsigned(d.reset)<<",\"cancel\":"<<unsigned(d.cancel)<<",\"start\":"<<unsigned(d.start)
              <<",\"advance\":"<<advance<<",\"out_last\":"<<output_last<<"}\n";
        }
        d.clk=0;check();
        require(clocks<10000000,"finite total clock watchdog");
    }
    void base(bool stall=true){
        d.reset=0;d.cancel=0;d.start=0;d.epoch=frame_epoch;d.frame_fid=fid;d.key_frame=!predicted;
        d.admitted_ready=!stall||(random()%5)!=0;d.input_done=1;
        d.lookup_ready=!stall||(random()%5)!=0;d.lookup_rsp=d.state==3&&(!stall||(random()%5)!=0);
        d.lookup_mode=hidden(d.verify_plane,d.verify_tile)?1:predicted&&d.verify_tile%3==0?0:2;d.lookup_scale=1;
        d.in_valid=d.state==4&&(!stall||(random()%5)!=0);d.out_ready=!stall||(random()%5)!=0;
        d.in_epoch=frame_epoch;d.in_child_epoch=9;d.in_token=uint32_t(d.verify_plane)*10000+d.verify_tile+1;
        d.in_plane=d.verify_plane;d.in_tile=d.verify_tile;d.in_qcell=cell(d.verify_plane,d.verify_tile);
        d.in_qscale=1;d.in_index=d.verify_fill_index;d.in_block=blocks[d.verify_plane];
        d.in_value=uint32_t(int((d.verify_tile+d.verify_fill_index)%17)-8)&0xffffff;
        d.ref_req_ready=!pending&&(!stall||(random()%5)!=0);
        if(pending&&delay)--delay;
        d.ref_rsp_valid=pending&&delay==0;
        d.ref_rsp_epoch=ref_epoch;d.ref_rsp_fid=ref_fid;d.ref_rsp_generation=ref_generation;
        d.ref_rsp_plane=ref_plane;d.ref_rsp_tile=ref_tile;d.ref_rsp_error=0;
    }
    void reset(){base(false);d.reset=1;tick();base(false);d.reset=1;tick();base(false);}
    void begin(bool pred){predicted=pred;++frame_epoch;++fid;base(false);d.start=1;tick();base(false);}
    void drain(){for(unsigned n=0;n<12;++n){base(false);d.admitted_ready=0;d.lookup_ready=0;d.lookup_rsp=0;d.in_valid=0;tick();}require(!d.ref_pending,"old physical reference did not drain");}
    void frame(bool pred){
        reset();begin(pred);const auto before=outputs;
        const auto start_clock=clocks;unsigned wait_done_holds=0;
        while(!d.done){
            base(true);
            if(d.state==10&&wait_done_holds<7){d.input_done=0;++wait_done_holds;}
            tick();require(d.error==0,"valid full-frame rejection");
            require(clocks-start_clock<2000000,"frame clock watchdog");
        }
        require(outputs-before==518400,"whole frame pixel count");
        require(d.count_outputs==518400,"RTL whole frame pixel count");
        require(d.verify_plane==2&&d.verify_tile==0&&d.verify_cell==0,"WAIT_DONE final wrap");
    }
    void directed(unsigned target,unsigned command){
        reset();begin(true);
        if(target==0){base(false);d.cancel=1;tick();}
        const auto start_clock=clocks;
        while(d.state!=target){base(false);tick();require(d.error==0,"directed setup error");require(clocks-start_clock<5000,"directed setup watchdog");}
        base(false);d.reset=command==0||command==3;d.cancel=command==1||command==4;d.start=command>=2;
        ++frame_epoch;++fid;d.epoch=frame_epoch;d.frame_fid=fid;
        const bool old_ref=d.ref_pending;tick();
        require(d.verify_plane==0&&d.verify_tile==0&&d.lookup_cell==0,"kill/start coordinate initialization");
        require(!old_ref||d.ref_pending,"kill discarded old physical owner");
        drain();
    }
    void bad_cell(){reset();begin(false);while(d.state!=4){base(false);tick();}
        base(false);d.in_valid=1;d.in_qcell^=1;tick();require(d.error==4,"bad qcell accepted");
        base(false);d.cancel=1;tick();drain();
    }
};
int main(int argc,char**argv){try{
    Verilated::commandArgs(argc,argv);if(argc!=2)throw std::runtime_error("trace required");
    Driver x(argv[1]);x.frame(false);x.frame(true);
    for(unsigned state=0;state<10;++state)for(unsigned command=0;command<5;++command)x.directed(state,command);
    x.bad_cell();x.trace.close();x.d.final();
    std::cout<<"{\"status\":\"TEST_PASS\",\"full_frames\":2,\"directed_checks\":51,\"clock_edges\":"<<x.clocks
      <<",\"half_cycle_public_comparisons\":"<<x.checks<<",\"output_bytes\":"<<x.outputs<<",\"coordinate_advances\":"<<x.advances
      <<",\"coordinate_holds\":"<<x.holds<<",\"all_clock_digest\":\""<<std::hex<<x.digest<<"\"}\n";
    return 0;
}catch(const std::exception&e){std::cerr<<"TEST_FAIL: "<<e.what()<<"\n";return 1;}}
