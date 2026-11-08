#include "Vv107_cdc_fabric.h"
#include "verilated.h"
#include <array>
#include <cstdint>
#include <deque>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
using Word=std::array<uint32_t,3>;
struct Entry{uint64_t cycle;Word data;};
struct Channel{std::deque<Entry> q;uint64_t accepted=0,delivered=0,max_owned=0,first_in=0,last_in=0,first_out=0,last_out=0,min_latency=UINT64_MAX,max_latency=0;};
static void check(bool ok,const std::string&s){if(!ok)throw std::runtime_error(s);}
static Word payload(unsigned i,uint64_t n){Word w={static_cast<uint32_t>(n),0x13579bdfU+i,0x2468aceU+i};
 if(i==0){w[1]&=4095;w[2]=0;}if(i==1)w[2]&=0x3fffffffU;if(i==2)w[2]&=0x7fffffU;if(i==3||i==4){w[1]=0;w[2]=0;}return w;}
int main(int argc,char**argv){try{
 check(argc==2,"usage trace.csv");Verilated::commandArgs(argc,argv);Vv107_cdc_fabric d;std::ofstream trace(argv[1]);check(trace.good(),"trace open");std::array<Channel,5> ch{};constexpr uint64_t N=10000;bool done=false;
 for(uint64_t cycle=0;cycle<50000;cycle++){
  const bool reset=cycle<12;d.reset_request=reset?15:0;std::array<Word,5> in{};for(unsigned i=0;i<5;i++)in[i]=payload(i,ch[i].accepted);
  d.command_valid=!reset&&ch[0].accepted<N;d.command_data=(uint64_t(in[0][1])<<32)|in[0][0];d.write_valid=!reset&&ch[1].accepted<N;d.ack_valid=!reset&&ch[2].accepted<N;
  for(unsigned k=0;k<3;k++){d.write_data[k]=in[1][k];d.ack_data[k]=in[2][k];}
  d.line_valid=!reset&&ch[3].accepted<N;d.line_data=in[3][0];d.pixel_valid=!reset&&ch[4].accepted<N;d.pixel_data=in[4][0];
  d.decoder_command_ready=1;d.memory_write_ready=1;d.decoder_ack_ready=1;d.memory_line_ready=1;d.display_pixel_ready=1;
  d.transport_clk=0;d.decoder_clk=0;d.memory_clk=0;d.display_clk=0;Verilated::time(2*cycle);d.eval();
  const std::array<bool,5> wr={bool(d.command_ready),bool(d.write_ready),bool(d.ack_ready),bool(d.line_ready),bool(d.pixel_ready)};
  const std::array<bool,5> rv={bool(d.decoder_command_valid),bool(d.memory_write_valid),bool(d.decoder_ack_valid),bool(d.memory_line_valid),bool(d.display_pixel_valid)};
  std::array<Word,5> out{};out[0]={uint32_t(d.decoder_command_data),uint32_t(d.decoder_command_data>>32),0};out[3]={d.memory_line_data,0,0};out[4]={d.display_pixel_data,0,0};for(unsigned k=0;k<3;k++){out[1][k]=d.memory_write_data[k];out[2][k]=d.decoder_ack_data[k];}
  for(unsigned i=0;i<5;i++){auto& c=ch[i];
   if(rv[i]){check(!c.q.empty()&&c.q.front().data==out[i],"rate payload/order");const uint64_t latency=cycle-c.q.front().cycle;c.q.pop_front();
    if(c.delivered==0)c.first_out=cycle;else check(cycle-c.last_out==2,"rate gap not2");c.last_out=cycle;c.delivered++;if(latency<c.min_latency)c.min_latency=latency;if(latency>c.max_latency)c.max_latency=latency;trace<<cycle<<",R,"<<i<<','<<out[i][0]<<','<<latency<<'\n';}
   if(!reset&&c.accepted<N&&wr[i]){c.q.push_back({cycle,in[i]});if(c.accepted==0)c.first_in=cycle;c.last_in=cycle;trace<<cycle<<",W,"<<i<<','<<c.accepted<<",0\n";c.accepted++;if(c.q.size()>c.max_owned)c.max_owned=c.q.size();check(c.q.size()<=9,"capacity exceeds8+1");}
  }
  d.transport_clk=1;d.decoder_clk=1;d.memory_clk=1;d.display_clk=1;Verilated::time(2*cycle+1);d.eval();done=true;for(const auto& c:ch)done=done&&c.delivered==N;if(done)break;
 }
 check(done,"rate watchdog");for(unsigned i=0;i<5;i++){const auto&c=ch[i];check(c.accepted==N&&c.q.empty()&&c.max_owned==9,"capacity/drain");std::cout<<"{\"channel\":"<<i<<",\"accepted\":"<<c.accepted<<",\"delivered\":"<<c.delivered<<",\"first_accepted_cycle\":"<<c.first_in<<",\"last_accepted_cycle\":"<<c.last_in<<",\"first_delivered_cycle\":"<<c.first_out<<",\"last_delivered_cycle\":"<<c.last_out<<",\"min_latency_clocks\":"<<c.min_latency<<",\"max_latency_clocks\":"<<c.max_latency<<",\"max_owned\":"<<c.max_owned<<",\"steady_delivery_words_per_clock\":0.5}\n";}
 d.final();trace.close();check(trace.good(),"trace close");std::cout<<"TEST_PASS_CDC_SYNC_RATE\n";return 0;
}catch(const std::exception&e){std::cerr<<"TEST_FAIL_CDC_SYNC_RATE "<<e.what()<<'\n';return 1;}}
