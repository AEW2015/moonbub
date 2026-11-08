#include "Vv107_cdc_fabric.h"
#include "verilated.h"
#include <array>
#include <cstdint>
#include <deque>
#include <fstream>
#include <iostream>
#include <random>
#include <stdexcept>
#include <string>
using Word=std::array<uint32_t,3>;
struct Channel {Channel(int s,int d,int w):src(s),dst(d),width(w){} int src,dst,width; bool pending=false; Word data{}; std::deque<Word> q; uint64_t sent=0,received=0,dropped=0,full=0,held=0;};
static void require(bool ok,const std::string& message){if(!ok)throw std::runtime_error(message);}
int main(int argc,char** argv){
 try {
    require(argc==3,"usage: Vv107_cdc_fabric seed trace");
    const uint32_t seed=static_cast<uint32_t>(std::stoul(argv[1]));std::mt19937 rng(seed);
    Verilated::commandArgs(argc,argv);Vv107_cdc_fabric d;std::ofstream trace(argv[2]);require(trace.good(),"trace open");
    std::array<Channel,5> c={{{0,1,44},{1,2,94},{2,1,87},{3,2,24},{2,3,16}}};
    const std::array<int,4> half={3,5,7,11};std::array<bool,4> clocks{};uint64_t edges=0;unsigned epoch=0;bool prior_reset=false;
    auto emit=[&](uint64_t t,char op,int ch,const Word& w){trace<<t<<','<<op<<','<<ch<<','<<epoch<<','<<w[0]<<','<<w[1]<<','<<w[2]<<'\n';};
    auto set_inputs=[&](){d.command_valid=c[0].pending;d.command_data=(uint64_t(c[0].data[1])<<32)|c[0].data[0];d.write_valid=c[1].pending;d.ack_valid=c[2].pending;
      for(int k=0;k<3;k++){d.write_data[k]=c[1].data[k];d.ack_data[k]=c[2].data[k];}
      d.line_valid=c[3].pending;d.line_data=c[3].data[0];d.pixel_valid=c[4].pending;d.pixel_data=c[4].data[0];};
    for(uint64_t t=0;t<120000;t++){
        Verilated::time(t);
        unsigned req=t<71?15: t>=20000&&t<20033?1:t>=40000&&t<40013?2:t>=60000&&t<60017?4:t>=80000&&t<80019?8:t>=100000&&t<100027?15:0;
        if(req&&!prior_reset){epoch++;for(auto& ch:c){ch.dropped+=ch.q.size();ch.q.clear();ch.pending=false;}emit(t,'E',-1,{});}
        prior_reset=req!=0;d.reset_request=req;
        for(auto& ch:c)if(!ch.pending&&req==0&&t<110000&&(rng()%100)<82){
            ch.pending=true;ch.data={static_cast<uint32_t>(rng()),static_cast<uint32_t>(rng()),static_cast<uint32_t>(rng())};
            if(ch.width<32){ch.data[0]&=(uint32_t(1)<<ch.width)-1;ch.data[1]=0;ch.data[2]=0;}
            else if(ch.width<64){ch.data[1]&=(uint32_t(1)<<(ch.width-32))-1;ch.data[2]=0;}
            else ch.data[2]&=(uint32_t(1)<<(ch.width-64))-1;
        }
        set_inputs();
        // Long deterministic stalls force full queues; random stalls overlap.
        const bool ready=t%3000>=440;
        d.decoder_command_ready=ready&&(rng()%4!=0);d.memory_write_ready=ready&&(rng()%3!=0);d.decoder_ack_ready=ready&&(rng()%3!=0);d.memory_line_ready=ready&&(rng()%4!=0);d.display_pixel_ready=ready&&(rng()%3!=0);
        d.eval();
        const std::array<bool,5> wr={bool(d.command_ready),bool(d.write_ready),bool(d.ack_ready),bool(d.line_ready),bool(d.pixel_ready)};
        const std::array<bool,5> rv={bool(d.decoder_command_valid),bool(d.memory_write_valid),bool(d.decoder_ack_valid),bool(d.memory_line_valid),bool(d.display_pixel_valid)};
        const std::array<bool,5> rr={bool(d.decoder_command_ready),bool(d.memory_write_ready),bool(d.decoder_ack_ready),bool(d.memory_line_ready),bool(d.display_pixel_ready)};
        std::array<Word,5> out{};out[0]={uint32_t(d.decoder_command_data),uint32_t(d.decoder_command_data>>32),0};out[3]={d.memory_line_data,0,0};out[4]={d.display_pixel_data,0,0};
        for(int k=0;k<3;k++){out[1][k]=d.memory_write_data[k];out[2][k]=d.decoder_ack_data[k];}
        std::array<bool,4> rise{};
        for(int i=0;i<4;i++){
            const bool stopped=(i==2&&((t>=30000&&t<30500)||(t>=59990&&t<60150)))||(i==1&&t>=50000&&t<50500)||(i==0&&t>=70000&&t<70500)||(i==3&&t>=90000&&t<90500);
            // Delayed first clocks exercise release while the peer is absent.
            if(t>=uint64_t(i*37)&&!stopped&&t%half[i]==0){rise[i]=!clocks[i];clocks[i]=!clocks[i];edges+=rise[i];}
        }
        for(int i=0;i<5;i++){
            auto& ch=c[i];
            if(rise[ch.dst]&&rv[i]&&rr[i]){require(req==0,"transfer during global reset");require(!ch.q.empty(),"phantom/old-epoch response ch="+std::to_string(i)+" t="+std::to_string(t));require(ch.q.front()==out[i],"payload/order ch="+std::to_string(i)+" t="+std::to_string(t));ch.q.pop_front();ch.received++;emit(t,'R',i,out[i]);}
            if(rise[ch.dst]&&rv[i]&&!rr[i])ch.held++;
            if(rise[ch.src]&&ch.pending&&!wr[i]&&req==0)ch.full++;
            if(rise[ch.src]&&ch.pending&&wr[i]){require(req==0,"write during reset");ch.q.push_back(ch.data);ch.sent++;emit(t,'W',i,ch.data);ch.pending=false;}
        }
        d.transport_clk=clocks[0];d.decoder_clk=clocks[1];d.memory_clk=clocks[2];d.display_clk=clocks[3];d.eval();
        if(req)require(d.local_reset==15,"coordinated async assertion");
        require(!Verilated::gotFinish(),"unexpected finish");
    }
    for(int i=0;i<5;i++){const auto& ch=c[i];require(ch.q.empty(),"drain failed");require(ch.sent==ch.received+ch.dropped,"accounting");require(ch.received>500&&ch.dropped>0&&ch.full>100&&ch.held>100,"coverage ch="+std::to_string(i));
      std::cout<<"{\"channel\":"<<i<<",\"accepted\":"<<ch.sent<<",\"delivered\":"<<ch.received<<",\"reset_discarded\":"<<ch.dropped<<",\"backpressure_edges\":"<<ch.full<<",\"held_output_edges\":"<<ch.held<<"}\n";}
    trace.close();require(trace.good(),"trace close");d.final();std::cout<<"TEST_PASS_CDC seed="<<seed<<" edges="<<edges<<" reset_epochs="<<epoch<<" ticks=120000\n";return 0;
 } catch(const std::exception& e){std::cerr<<"TEST_FAIL_CDC "<<e.what()<<'\n';return 1;}
}
