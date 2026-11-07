#include "Vscratch_probe.h"
#include "Vscratch_probe___024root.h"
#include "verilated.h"
#include <cstdint>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>

struct Vector {
    uint8_t state=20, prefetch=1, tile_overlap=0, raw=0, sealed=1, offer=0, outstanding=0, error=0;
    uint8_t reset=0, abort_valid=0, index=0, cache_valid=15;
    uint32_t epoch=7, abort_epoch=7, blocks=2, block=0;
    uint32_t starts[4]={0,48,80,112}, cursors[4]={0,1,2,3}, counts[4]={0,2,3,4}, cache_address[4]={32,48,80,112};
};
static uint32_t rng;
static uint32_t next() { rng ^= rng << 13; rng ^= rng >> 17; rng ^= rng << 5; return rng; }
#define SET(field, value) do { r->scratch_probe__DOT__old_dut__DOT__##field=(value); r->scratch_probe__DOT__new_dut__DOT__##field=(value); } while(0)
#define GET(field) (r->scratch_probe__DOT__new_dut__DOT__##field)

int main(int argc, char** argv) {
    try {
        if(argc!=2) throw std::runtime_error("seed required");
        uint32_t seed=uint32_t(std::stoul(argv[1])); rng=seed;
        VerilatedContext context; context.randReset(0);
        Vscratch_probe top(&context); top.clk=0; top.eval();
        auto* r=top.rootp;
        uint64_t cases=0, valid_cases=0, suppressed=0, selected[4]={0,0,0,0}, raw_cases=0, boundary_cases=0;
        std::ofstream trace("probe-seed-"+std::to_string(seed)+".jsonl");
        if(!trace) throw std::runtime_error("trace open failed");
        auto check = [&](const Vector& v) {
            SET(state,v.state); SET(prefetch_mode,v.prefetch); SET(tile_overlap_mode,v.tile_overlap);
            SET(raw_mode,v.raw); SET(sealed,v.sealed); SET(prefetch_offer,v.offer); SET(outstanding,v.outstanding);
            SET(error,v.error); SET(active_epoch,v.epoch); SET(blocks,v.blocks); SET(output_block,v.block); SET(output_index,v.index);
            SET(raw_value,0); SET(cache_valid,v.cache_valid);
            for(unsigned b=0;b<4;++b) { SET(starts[b],v.starts[b]); SET(counts[b],v.counts[b]); SET(cache_address[b],v.cache_address[b]); }
            for(unsigned b=1;b<4;++b) SET(cursors[b-1],v.cursors[b]);
            top.reset=v.reset; top.abort_valid=v.abort_valid; top.abort_epoch=v.abort_epoch;
            top.eval();
            bool valid=false; unsigned segment=0; uint32_t address=0, word=0;
            bool cancel=v.reset || (v.abort_valid && v.abort_epoch==v.epoch);
            bool guard=v.prefetch && !(v.tile_overlap && !v.raw) && v.sealed && !v.offer && !v.outstanding && !cancel && v.error==0;
            auto miss=[&](unsigned b,uint32_t a){return !(v.cache_valid&(1u<<b)) || v.cache_address[b]!=(a&0x3fff0u);};
            if(guard && v.state==20 && !v.raw && ((uint32_t(v.block)+1)<v.blocks)) {
                word=32u+(v.block+1u)*2u;
                if(miss(0,word)) { valid=true; segment=0; address=word&0x3fff0u; }
                for(unsigned b=1;b<4;++b) {
                    word=v.starts[b]+v.cursors[b]*4u;
                    if(!valid && v.cursors[b]<v.counts[b] && miss(b,word)) {valid=true;segment=b;address=word&0x3fff0u;}
                }
            } else if(guard && v.state==22 && v.raw && v.block*64u+uint32_t(v.index)+1u<v.blocks*64u) {
                word=32u+(v.block*64u+uint32_t(v.index)+1u)*2u;
                if(miss(0,word)) {valid=true;segment=0;address=word&0x3fff0u;}
            }
            if(!top.probe_outputs_equal || !top.probe_internal_equal || GET(candidate_valid)!=valid || GET(candidate_segment)!=segment || GET(candidate_address)!=address || GET(candidate_word_address)!=word) {
                std::cerr<<"case "<<cases<<" outputeq="<<unsigned(top.probe_outputs_equal)<<" coneeq="<<unsigned(top.probe_internal_equal)<<" actual="<<unsigned(GET(candidate_valid))<<","<<unsigned(GET(candidate_segment))<<","<<GET(candidate_address)<<","<<GET(candidate_word_address)<<" expected="<<valid<<","<<segment<<","<<address<<","<<word<<"\n";
                throw std::runtime_error("actual RTL/reference mismatch");
            }
            trace<<"{\"case\":"<<cases<<",\"state\":"<<unsigned(v.state)<<",\"control\":["<<unsigned(v.prefetch)<<","<<unsigned(v.tile_overlap)<<","<<unsigned(v.raw)<<","<<unsigned(v.sealed)<<","<<unsigned(v.offer)<<","<<unsigned(v.outstanding)<<","<<unsigned(v.error)<<","<<unsigned(v.reset)<<","<<unsigned(v.abort_valid)<<"],\"epoch\":"<<v.epoch<<",\"abort_epoch\":"<<v.abort_epoch<<",\"blocks\":"<<v.blocks<<",\"block\":"<<v.block<<",\"index\":"<<unsigned(v.index)<<",\"cache_valid\":"<<unsigned(v.cache_valid)<<",\"starts\":[";
            for(unsigned b=0;b<4;++b) trace<<(b?",":"")<<v.starts[b];
            trace<<"],\"cursors\":[";for(unsigned b=1;b<4;++b)trace<<(b>1?",":"")<<v.cursors[b];
            trace<<"],\"counts\":[";for(unsigned b=0;b<4;++b)trace<<(b?",":"")<<v.counts[b];
            trace<<"],\"cache_address\":[";for(unsigned b=0;b<4;++b)trace<<(b?",":"")<<v.cache_address[b];
            trace<<"],\"actual_and_expected\":["<<valid<<","<<segment<<","<<address<<","<<word<<"]}\n";
            ++cases;
            if(valid){++valid_cases;++selected[segment];} else ++suppressed;
            if(v.raw)++raw_cases;
            for(unsigned b=1;b<4;++b)if(v.starts[b]>0xfffffff0u || v.cursors[b]>=0x40000000u) {++boundary_cases;break;}
        };
        // Exhaust every DC/AC miss combination under every gating control combination.
        for(unsigned eligibility=0;eligibility<16;++eligibility) {
            for(unsigned guards=0;guards<256;++guards) {
                Vector v;v.prefetch=(guards&1)?0:1;v.tile_overlap=(guards>>1)&1;v.sealed=(guards&4)?0:1;
                v.offer=(guards>>3)&1;v.outstanding=(guards>>4)&1;v.reset=(guards>>5)&1;v.abort_valid=(guards>>6)&1;v.error=(guards&128)?1:0;
                v.cache_valid=uint8_t(15u^eligibility);check(v);
            }
        }
        // Explicit cursor exhaustion, cacheline/truncation/wrap and raw last-sample boundaries.
        const uint32_t edges[]={0u,1u,15u,16u,0x3fff0u,0x40000u,0xfffffff0u,0xffffffffu};
        for(uint32_t a:edges)for(uint32_t c:edges)for(unsigned mask=0;mask<16;++mask) {
            Vector v;v.starts[1]=a;v.starts[2]=a+4u;v.starts[3]=a+8u;
            for(unsigned b=1;b<4;++b){v.cursors[b]=c;v.counts[b]=c==0xffffffffu?c:c+1u;v.cache_address[b]=((a+c*4u)&0x3fff0u);}
            v.cache_valid=uint8_t(15u^mask);check(v);
        }
        for(unsigned block: {0u,1u,65535u})for(unsigned idx:{0u,14u,15u,62u,63u})for(unsigned miss=0;miss<2;++miss) {
            Vector v;v.raw=1;v.tile_overlap=1;v.state=22;v.block=block;v.blocks=block+1u;v.index=uint8_t(idx);v.cache_valid=miss?14:15;check(v);
        }
        for(unsigned i=0;i<16384;++i) {
            Vector v;v.prefetch=uint8_t((next()&7)!=0);v.tile_overlap=uint8_t((next()&7)==0);v.raw=uint8_t(next()&1);v.sealed=uint8_t((next()&7)!=0);
            v.offer=uint8_t((next()&7)==0);v.outstanding=uint8_t((next()&7)==0);v.error=uint8_t((next()&15)==0);v.reset=uint8_t((next()&31)==0);v.abort_valid=uint8_t((next()&7)==0);
            v.abort_epoch=(next()&1)?v.epoch:v.epoch+1u;v.state=uint8_t((next()%8)==0?next()%30:(v.raw?22:20));v.blocks=(next()%65537u);v.block=next()%65536u;v.index=uint8_t(next()&63);v.cache_valid=uint8_t(next()&15);
            for(unsigned b=1;b<4;++b){v.starts[b]=next();v.cursors[b]=next();v.counts[b]=next();v.cache_address[b]=next()&0x3ffffu;}
            check(v);
        }
        if(valid_cases==0 || raw_cases==0 || boundary_cases==0)throw std::runtime_error("missing coverage");
        for(unsigned b=0;b<4;++b)if(selected[b]==0)throw std::runtime_error("priority branch not covered");
        trace.close();top.final();
        std::cout<<"{\"status\":\"TEST_PASS\",\"seed\":"<<seed<<",\"cases\":"<<cases<<",\"all_public_outputs_equal\":true,\"internal_cone_equal\":true,\"reference_equal\":true,\"valid_cases\":"<<valid_cases<<",\"suppressed_cases\":"<<suppressed<<",\"selected_segments\":["<<selected[0]<<","<<selected[1]<<","<<selected[2]<<","<<selected[3]<<"],\"raw_cases\":"<<raw_cases<<",\"wrap_boundary_cases\":"<<boundary_cases<<",\"clock_edges\":0}\n";
        return 0;
    }catch(const std::exception& e){std::cerr<<"TEST_FAIL "<<e.what()<<"\n";return 1;}
}
