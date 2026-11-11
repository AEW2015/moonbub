#include "Vheader_index_pair.h"
#include "verilated.h"
#include <cstdint>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

static void check(bool b, const std::string& m) { if (!b) throw std::runtime_error(m); }
static void put(std::vector<uint8_t>& p, unsigned at, uint32_t v) { for (unsigned i=0;i<4;++i) p.at(at+i)=uint8_t(v>>(8*i)); }
static void crc(std::vector<uint8_t>& p) { uint32_t c=~uint32_t(0);for(size_t i=0;i+4<p.size();++i){c^=p[i];for(unsigned j=0;j<8;++j)c=(c>>1)^((c&1)?0xedb88320U:0U);}put(p,unsigned(p.size()-4),~c); }
static std::vector<uint8_t> packet(bool raw) {
    unsigned n=raw?174:71;std::vector<uint8_t> p(n,0);p[0]='B';p[1]='R';p[2]='8';p[3]='8';p[4]=1;p[5]=raw;put(p,6,1);p[10]=1;
    if(raw)put(p,14,128);else{put(p,14,7);for(unsigned i=1;i<4;++i)put(p,14+4*i,6);p[43]=255;put(p,44,1);p[48]=0x80;}crc(p);return p;
}
struct Sim {
    Vheader_index_pair d;uint64_t cycles=0, evals=0;unsigned stalls=0,gaps=0,errors=0,aborts=0,passed=0,purposes=0;
    void eval(){d.eval();++evals;check(d.pair_equal,"pair mismatch cycle "+std::to_string(cycles));}
    void edge(){d.clk=0;eval();d.clk=1;eval();++cycles;d.clk=0;eval();}
    void reset(){d.reset=1;edge();d.reset=0;}
    void start(const std::vector<uint8_t>& p){d.in_valid=0;d.in_last=0;d.packet_bytes=p.size();d.blocks=1;d.epoch=9+passed;d.start=1;edge();d.start=0;}
    void send(const std::vector<uint8_t>& p,int wrong_last=-1,bool jitter=false){
        for(size_t i=0;i<p.size();++i){
            if(jitter && i%5==0){d.in_valid=0;for(unsigned g=0;g<3;++g){edge();++gaps;}}
            d.in_valid=1;d.in_data=p[i];d.in_last=(wrong_last==-2?false:(wrong_last>=0?int(i)==wrong_last:i+1==p.size()));
            d.clk=0;eval();check(d.in_ready,"input not ready at byte "+std::to_string(i));edge();
            if(wrong_last>=0 && int(i)==wrong_last)break;
        }d.in_valid=0;d.in_last=0;
    }
    void ready_pattern(unsigned n){d.out_ready=(n%13>=7);d.meta_ready=(n%17>=11);d.band_end_ready=(n%19>=13);}
    void finish(bool jitter){
        for(unsigned n=0;n<100000 && !d.done && !d.error;++n){if(jitter)ready_pattern(n);d.clk=0;eval();if(d.stage_read_req)purposes|=1U<<d.stage_purpose;if((d.out_valid&&!d.out_ready)||(d.meta_valid&&!d.meta_ready)||(d.band_end_valid&&!d.band_end_ready))++stalls;edge();}
        check(d.done && !d.error,"valid packet did not finish");++passed;d.out_ready=1;d.meta_ready=1;d.band_end_ready=1;edge();
    }
    void expect_error(){for(unsigned n=0;n<10&&!d.error;++n)edge();check(d.error==2,"expected malformed in_last error 2");++errors;}
    void cancel(){d.in_valid=0;d.abort_packet=1;edge();d.abort_packet=0;++aborts;}
    template<class Pred> void until(Pred pred,const char* label){for(unsigned n=0;n<100000;++n){d.clk=0;eval();if(pred())return;edge();}throw std::runtime_error(std::string("timeout ")+label);}
};
int main(int argc,char**argv){Verilated::commandArgs(argc,argv);try{
    Sim s;s.d.meta_ready=1;s.d.out_ready=1;s.d.band_end_ready=1;s.reset();auto raw=packet(true), coded=packet(false);
    for(int i: {0,1,12,41,69}){s.start(coded);s.send(coded,i,true);s.expect_error();s.start(raw);s.send(raw,-1,true);s.finish(true);}
    s.start(coded);s.send(coded,-2,true);s.expect_error();s.start(coded);s.send(coded,-1,true);s.finish(true);
    // Kill in RECEIVE after valid gaps and input bytes, then recover.
    s.start(raw);for(unsigned i=0;i<17;++i){s.d.in_valid=1;s.d.in_data=raw[i];s.d.in_last=0;s.edge();}s.cancel();s.start(coded);s.send(coded,-1,true);s.finish(true);
    // Kill while a header fetch is in flight.
    s.start(raw);s.send(raw,-1,true);s.until([&](){return s.d.stage_pending || s.d.stage_read_req;},"fetch pending");s.cancel();s.start(raw);s.send(raw,-1,true);s.finish(true);
    // Hold metadata and coefficient outputs before cancellation, then recover.
    s.d.meta_ready=0;s.start(coded);s.send(coded,-1,true);s.until([&](){return s.d.meta_valid;},"metadata");for(unsigned i=0;i<16;++i){check(s.d.meta_valid,"metadata dropped while held");s.edge();}s.cancel();s.d.meta_ready=1;s.start(coded);s.send(coded,-1,true);s.finish(true);
    s.d.out_ready=0;s.start(raw);s.send(raw,-1,true);s.until([&](){return s.d.out_valid;},"output");for(unsigned i=0;i<16;++i){check(s.d.out_valid,"output dropped while held");s.edge();}s.cancel();s.d.out_ready=1;s.start(raw);s.send(raw,-1,true);s.finish(true);
    check((s.purposes&15)==15,"missing fetch purpose");check(s.stalls>100 && s.gaps>100,"insufficient stall/gap coverage");
    std::cout<<"{\"status\":\"TEST_PASS\",\"cycles\":"<<s.cycles<<",\"evaluations\":"<<s.evals<<",\"input_gap_cycles\":"<<s.gaps<<",\"output_stall_cycles\":"<<s.stalls<<",\"malformed_cases\":"<<s.errors<<",\"abort_cases\":"<<s.aborts<<",\"recovered_packets\":"<<s.passed<<",\"fetch_purpose_mask\":"<<s.purposes<<"}"<<std::endl;return 0;
}catch(const std::exception&e){std::cerr<<"TEST_FAIL "<<e.what()<<std::endl;return 1;}}
