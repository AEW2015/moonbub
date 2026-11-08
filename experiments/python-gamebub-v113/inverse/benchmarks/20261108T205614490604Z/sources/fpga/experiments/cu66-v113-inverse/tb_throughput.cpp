#include "Vcu66_inverse_stream_v91j.h"
#include "verilated.h"
#include <array>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
static void need(bool b,const std::string&s){if(!b)throw std::runtime_error(s);}
static std::vector<uint8_t> unhex(const std::string&s){std::vector<uint8_t> v;for(size_t n=0;n<s.size();n+=2)v.push_back(uint8_t(std::stoul(s.substr(n,2),nullptr,16)));return v;}
static int i32(const std::vector<uint8_t>&v,unsigned n){uint32_t a=0;for(unsigned i=0;i<4;++i)a|=uint32_t(v[n*4+i])<<(8*i);return int32_t(a);}
int main(int argc,char**argv){try{need(argc==2,"goldens argument");std::ifstream f(argv[1]);std::string line;unsigned tests=0;
 while(std::getline(f,line)){std::istringstream row(line);std::string name,c,dq,r;unsigned error,p,q;row>>name>>error>>p>>q>>c>>dq>>r;if(name!="p0_q0_zero"&&name!="p0_q0_ac_pos_limit")continue;auto coef=unhex(c),res=unhex(r);
 for(unsigned profile=0;profile<2;++profile){Vcu66_inverse_stream_v91j d;d.clk=0;d.reset=1;d.start=d.cancel=d.input_done=d.in_valid=0;d.fault_ack_i=0;d.in_epoch=77;d.in_child_epoch=88;d.in_plane=p;d.in_qscale=q;d.in_block=d.in_tile=d.in_qcell=d.in_index=d.in_value=d.in_metadata_bad=d.in_domain_bad=0;d.out_ready=1;uint64_t cycle=0,first=0,last=0,accepted=0,outputs=0,first_out=0,last_out=0,overlap=0,installs=0,outstalls=0,min_gap=99999,max_gap=0,prev_accept=0;
 auto tick=[&](){d.clk=0;d.out_ready=profile==0||(cycle%257)<83;d.eval();bool take=d.in_valid&&d.in_ready;if(take){if(!accepted)first=cycle;else{min_gap=std::min(min_gap,cycle-prev_accept);max_gap=std::max(max_gap,cycle-prev_accept);}prev_accept=cycle;last=cycle;++accepted;}if(d.in_valid&&!d.in_ready)++installs;if(d.out_valid&&!d.out_ready)++outstalls;if(d.out_valid&&d.math_state!=0)++overlap;if(d.out_valid&&d.out_ready){need(d.out_token==outputs/64+1&&d.out_index==outputs%64,"throughput residual order");need(int32_t(d.out_value<<8)>>8==i32(res,d.out_index),"throughput residual golden");if(!outputs)first_out=cycle;last_out=cycle;++outputs;}d.clk=1;d.eval();++cycle;need(cycle<100000,"throughput watchdog");need(!d.error,"throughput error");return take;};
 tick();d.reset=0;d.start=1;tick();d.start=0;uint64_t begin=cycle;
 for(unsigned tile=0;tile<16;++tile){for(unsigned ix=0;ix<64;++ix){d.in_valid=1;d.in_index=ix;d.in_value=uint16_t(coef[ix*2])|(uint16_t(coef[ix*2+1])<<8);while(!tick()){} }}
 d.in_valid=0;d.input_done=1;while(!d.done)tick();need(outputs==1024&&accepted==1024,"throughput totals");std::cout<<"{\"type\":\"throughput\",\"case\":\""<<name<<"\",\"profile\":"<<profile<<",\"tiles\":16,\"total_cycles\":"<<cycle-begin<<",\"coefficient_span_cycles\":"<<last-first+1<<",\"first_output_offset\":"<<first_out-begin<<",\"last_output_offset\":"<<last_out-begin<<",\"min_accept_gap\":"<<min_gap<<",\"max_accept_gap\":"<<max_gap<<",\"input_stalls\":"<<installs<<",\"output_stalls\":"<<outstalls<<",\"math_and_offer_cycles\":"<<overlap<<"}\n";++tests;}}
 need(tests==4,"throughput cases");std::cout<<"{\"status\":\"TEST_PASS\",\"throughput_cases\":"<<tests<<"}\n";return 0;}catch(const std::exception&e){std::cerr<<"TEST_FAIL "<<e.what()<<'\n';return 1;}}
