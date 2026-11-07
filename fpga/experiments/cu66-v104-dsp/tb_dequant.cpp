#include <verilated.h>
#include "Vdequant_probe.h"
#include "oracle_quant.hpp"
#include <array>
#include <cstdint>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>

using Tile=std::array<int32_t,64>;
struct Inputs { bool rst=false,abort=false,valid=false,ready=false,chroma=false; unsigned scale=0; uint32_t id=0; Tile tile{}; };
struct Oracle {
    unsigned state=0,group=0,scale=0; bool chroma=false,error=false; uint32_t id=0; Tile coeff{},out{};
    static bool bad(const Inputs&i) { if(i.scale==3)return true;for(auto c:i.tile)if(c< -2048||c>2048)return true;return false; }
    void step(const Inputs&i) {
        if(i.rst||i.abort) {state=0;group=0;scale=0;chroma=false;error=false;id=0;coeff.fill(0);out.fill(0);return;}
        if(state==0&&i.valid) {
            coeff=i.tile;chroma=i.chroma;scale=i.scale;id=i.id;error=bad(i);group=0;
            bool zero=true;for(auto c:coeff)zero&=c==0;
            if(error||zero){out.fill(0);state=2;}else state=1;
        } else if(state==1) {
            for(unsigned j=0;j<8;++j){unsigned n=group*8+j;unsigned b=chroma?QC[n]:QY[n];unsigned q=scale==0?(b+1)/2:scale==1?b:b*2;if(q>255)q=255;out[n]=coeff[n]*int32_t(q);}
            if(group==7)state=2;else ++group;
        } else if(state==2&&i.ready)state=0;
    }
    bool in_ready(const Inputs&i)const{return state==0&&!i.rst&&!i.abort;}
    bool out_valid(const Inputs&i)const{return state==2&&!i.rst&&!i.abort;}
};
static uint32_t random32(uint32_t&s){s^=s<<13;s^=s>>17;s^=s<<5;return s;}
template<size_t N> static std::string hex_words(const VlWide<N>&w){std::ostringstream o;o<<std::hex<<std::setfill('0');for(size_t n=N;n>0;--n)o<<std::setw(8)<<w[n-1];return o.str();}
template<size_t N>static int32_t packed20(const VlWide<N>&w,unsigned n){unsigned bit=n*20,word=bit/32,shift=bit%32;uint64_t v=w[word];if(word+1<N)v|=uint64_t(w[word+1])<<32;uint32_t b=uint32_t(v>>shift)&0xfffff;return (b&0x80000)?int32_t(b)-1048576:int32_t(b);}
struct Bench {
    Vdequant_probe d; Oracle m; std::ofstream trace; uint32_t rng; uint64_t edges=0,samples=0,accepts=0,held=0,resets=0,aborts=0,comparisons=0; unsigned directed=0;
    explicit Bench(uint32_t seed,const std::string&path):trace(path),rng(seed){if(!trace)throw std::runtime_error("trace open");}
    Inputs noise(){Inputs i;i.valid=(random32(rng)&3)==0;i.ready=(random32(rng)&1)!=0;i.chroma=(random32(rng)&1)!=0;i.scale=random32(rng)&3;i.id=random32(rng);for(auto&v:i.tile)v=int16_t(random32(rng));return i;}
    void drive(const Inputs&i){d.rst=i.rst;d.abort_i=i.abort;d.in_valid=i.valid;d.out_ready=i.ready;d.in_chroma=i.chroma;d.in_scale_code=i.scale;d.in_id=i.id;for(unsigned n=0;n<32;++n)d.in_coefficients[n]=0;for(unsigned n=0;n<64;++n)d.in_coefficients[n/2]|=uint32_t(uint16_t(i.tile[n]))<<((n%2)*16);}
    void check(const Inputs&i){
        if(d.original_in_ready!=d.candidate_in_ready||d.original_out_valid!=d.candidate_out_valid||d.original_out_id!=d.candidate_out_id||d.original_out_error!=d.candidate_out_error)throw std::runtime_error("public metadata mismatch edge "+std::to_string(edges));
        if(d.original_in_ready!=m.in_ready(i)||d.original_out_valid!=m.out_valid(i)||d.original_out_id!=m.id||d.original_out_error!=m.error)throw std::runtime_error("oracle metadata mismatch edge "+std::to_string(edges));
        for(unsigned n=0;n<64;++n){int32_t a=packed20(d.original_out_dequantized,n),b=packed20(d.candidate_out_dequantized,n);if(a!=b||a!=m.out[n])throw std::runtime_error("partial packed output mismatch edge "+std::to_string(edges)+" lane "+std::to_string(n));++comparisons;}
        ++samples;
    }
    void step(Inputs i,const char*tag){
        drive(i);d.clk=0;d.eval();if(edges)check(i);
        if(m.in_ready(i)&&i.valid)++accepts;
        if(m.out_valid(i)&&!i.ready)++held;
        if(i.rst)++resets;
        if(i.abort)++aborts;
        m.step(i);d.clk=1;d.eval();++edges;check(i);d.clk=0;d.eval();check(i);
        trace<<"{\"edge\":"<<edges<<",\"tag\":\""<<tag<<"\",\"rst\":"<<int(i.rst)<<",\"abort\":"<<int(i.abort)<<",\"in_valid\":"<<int(i.valid)<<",\"out_ready\":"<<int(i.ready)<<",\"chroma\":"<<int(i.chroma)<<",\"scale\":"<<i.scale<<",\"in_id\":"<<i.id<<",\"coeff_hex\":\""<<hex_words(d.in_coefficients)<<"\",\"in_ready\":"<<int(d.original_in_ready)<<",\"out_valid\":"<<int(d.original_out_valid)<<",\"out_id\":"<<d.original_out_id<<",\"out_error\":"<<int(d.original_out_error)<<",\"out_hex\":\""<<hex_words(d.original_out_dequantized)<<"\"}\n";
    }
    void clear(){Inputs i=noise();i.rst=true;i.abort=false;i.valid=true;i.ready=true;step(i,"reset");}
    void finish(){while(m.state==1)step(noise(),"multiply_ignored_input");unsigned stalls=random32(rng)%4;while(stalls--){Inputs i=noise();i.ready=false;step(i,"held_output");}Inputs i=noise();i.ready=true;step(i,"accept_output");}
    void submit(Tile tile,unsigned scale,bool chroma,const char*tag){if(m.state!=0)throw std::runtime_error("test not idle");Inputs i=noise();i.tile=tile;i.scale=scale;i.chroma=chroma;i.valid=true;step(i,tag);finish();}
};
int main(int argc,char**argv){try{
    Verilated::commandArgs(argc,argv);if(argc!=3)throw std::runtime_error("seed and trace required");uint32_t seed=uint32_t(std::stoul(argv[1]));Bench b(seed,argv[2]);b.clear();
    Tile t{};
    // Every legal signed coefficient, at every raster position, in all six quantizer configurations.
    for(unsigned c=0;c<2;++c)for(unsigned s=0;s<3;++s)for(int v=-2048;v<=2048;++v){t.fill(v);b.submit(t,s,c!=0,"exhaustive_legal_value");}
    // Every input position rejects each out-of-range extreme, with and without chroma.
    for(unsigned n=0;n<64;++n)for(int v:{-32768,-2049,2049,32767}){t.fill(0);t[n]=v;b.submit(t,(n+unsigned(v&1))%3,(n&1)!=0,"invalid_coefficient");}
    for(unsigned c=0;c<2;++c){t.fill(0);b.submit(t,3,c!=0,"invalid_scale_zero");t.fill(2048);b.submit(t,3,c!=0,"invalid_scale_nonzero");}
    for(unsigned n=0;n<512;++n){for(auto&v:t)v=int32_t(random32(b.rng)%4097)-2048;b.submit(t,n%3,(n&1)!=0,"dense_random");}
    // Accepted nonzero data must retain the prior packed output at the acceptance edge;
    // interruption at every multiply group resets both hidden prefetch and public state.
    for(unsigned mode=0;mode<4;++mode)for(unsigned group=0;group<8;++group){b.clear();t.fill(0);t[group*8]=mode&1?-2048:2048;Inputs i=b.noise();i.valid=true;i.tile=t;i.scale=mode%3;i.chroma=(mode&1)!=0;b.step(i,"interrupt_accept");for(unsigned n=0;n<group;++n)b.step(b.noise(),"interrupt_advance");i=b.noise();i.rst=(mode&1)!=0;i.abort=(mode&1)==0;i.valid=true;i.ready=true;if(mode>=2){i.rst=true;i.abort=true;}b.step(i,"interrupt_group");++b.directed;t.fill(-1);b.submit(t,1,false,"post_interrupt_retry");}
    // A held valid result, IDLE collisions, and valid input during output acceptance.
    for(unsigned mode=0;mode<4;++mode){b.clear();t.fill(1);Inputs i=b.noise();i.valid=true;i.tile=t;i.scale=2;i.chroma=true;b.step(i,"hold_interrupt_accept");while(b.m.state==1)b.step(b.noise(),"hold_interrupt_advance");i=b.noise();i.ready=false;b.step(i,"hold_before_interrupt");i=b.noise();i.rst=(mode&1)!=0;i.abort=mode!=1;i.valid=true;i.ready=true;b.step(i,"hold_interrupt");++b.directed;}
    b.clear();t.fill(0);for(unsigned n=0;n<12;++n){Inputs i=b.noise();i.valid=n&1;i.tile=t;i.scale=n%4;i.ready=n&2;b.step(i,"idle_fastpath_collisions");}b.clear();
    b.d.final();b.trace.close();std::cout<<"{\"status\":\"TEST_PASS\",\"seed\":"<<seed<<",\"clock_edges\":"<<b.edges<<",\"public_samples\":"<<b.samples<<",\"packed_element_comparisons\":"<<b.comparisons<<",\"accepted_inputs\":"<<b.accepts<<",\"held_output_edges\":"<<b.held<<",\"reset_edges\":"<<b.resets<<",\"abort_edges\":"<<b.aborts<<",\"directed_interruptions\":"<<b.directed<<",\"legal_value_transactions\":24582}\n";return 0;
}catch(const std::exception&e){std::cerr<<"TEST_FAIL "<<e.what()<<"\n";return 1;}}
