#include "Vv129_dense_owned_queue.h"
#include "verilated.h"
#include <cstdint>
#include <deque>
#include <iostream>
#include <random>
#include <stdexcept>
#include <string>

struct Token { uint32_t frame, child; uint16_t block; uint8_t index; int16_t value; };
struct Stim {
    bool reset=false,kill=false,arm=false,quiet=true,debt=true,finish=false;
    bool valid=false,context=true,ready=false;
    uint32_t arm_frame=0x80000001U,arm_child=0x10001U;
    uint16_t arm_block=0;
    Token token{0x80000001U,0x10001U,0,0,0};
};

class Bench {
    Vv129_dense_owned_queue d;
    bool active=false,fault=false;
    uint32_t frame=0,child=0;
    uint16_t block=0;
    std::deque<Token> queue;
public:
    uint64_t clocks=0, push_count=0,pop_count=0,simultaneous=0,full_bubble=0;
    uint64_t bad_full=0,bad_accepted=0,pop_on_fault=0,stalls=0,kill_flush=0;
    uint64_t finish_fenced=0,finishes=0,arm_fenced=0,wraps=0;
    void step(const Stim &s) {
        d.reset=s.reset; d.kill=s.kill; d.arm_valid=s.arm; d.arm_frame_epoch=s.arm_frame;
        d.arm_child_epoch=s.arm_child; d.arm_first_block=s.arm_block;
        d.child_quiescent=s.quiet; d.memory_debt_empty=s.debt; d.finish_valid=s.finish;
        d.in_valid=s.valid; d.in_frame_epoch=s.token.frame; d.in_child_epoch=s.token.child;
        d.in_block=s.token.block; d.in_index=s.token.index; d.in_value=uint16_t(s.token.value);
        d.publication_context_ready=s.context; d.out_ready=s.ready;
        d.clk=0; d.eval();
        const bool ar=!active&&!fault&&queue.empty()&&s.quiet&&s.debt&&!s.reset&&!s.kill;
        const bool ir=active&&!fault&&queue.size()<2&&!s.reset&&!s.kill;
        const bool ov=active&&!fault&&!queue.empty()&&s.context&&!s.reset&&!s.kill;
        const bool fr=active&&!fault&&queue.empty()&&!s.valid&&s.quiet&&s.debt&&!s.reset&&!s.kill;
        auto need=[](bool ok,const char *why){if(!ok)throw std::runtime_error(why);};
        need(bool(d.arm_ready)==ar && bool(d.in_ready)==ir && bool(d.out_valid)==ov && bool(d.finish_ready)==fr,
             "ready/valid mismatch");
        need(bool(d.active)==active && bool(d.owner_fault)==fault && unsigned(d.occupancy)==queue.size(),"control mismatch");
        if(active)need(d.acquisition_block==block,"acquisition cursor mismatch");
        if(ov) {
            const Token &x=queue.front();
            need(d.out_frame_epoch==x.frame && d.out_child_epoch==x.child && d.out_block==x.block &&
                 d.out_index==x.index && uint16_t(d.out_value)==uint16_t(x.value),"output tuple mismatch");
        }
        const bool bad=active&&s.valid&&(s.token.frame!=frame || s.token.child!=child || s.token.block!=block);
        const bool push=s.valid&&ir, pop=ov&&s.ready;
        if(s.arm&&!ar)++arm_fenced;
        if(s.finish&&!fr)++finish_fenced;
        if(ov&&!s.ready)++stalls;
        if(queue.size()==2&&s.valid&&pop&&!ir)++full_bubble;
        if(bad&&queue.size()==2)++bad_full;
        if(bad&&push)++bad_accepted;
        if(bad&&pop)++pop_on_fault;
        if(push)++push_count;
        if(pop)++pop_count;
        if(push&&pop&&!bad)++simultaneous;
        if((s.reset||s.kill)&&!queue.empty())++kill_flush;
        if(s.reset||s.kill) {active=false;fault=false;queue.clear();}
        else if(s.arm&&ar) {active=true;fault=false;frame=s.arm_frame;child=s.arm_child;block=s.arm_block;queue.clear();}
        else if(active&&bad) {active=false;fault=true;queue.clear();}
        else if(s.finish&&fr) {active=false;queue.clear();++finishes;}
        else if(active) {
            if(pop)queue.pop_front();
            if(push) {queue.push_back(s.token);if(s.token.index==63){if(block==0xffffU)++wraps;block=uint16_t(block+1U);}}
        }
        d.clk=1;d.eval();d.clk=0;d.eval();++clocks;
    }
    bool is_active()const{return active;}
    bool is_faulted()const{return fault;}
    uint32_t frame_id()const{return frame;}
    uint32_t child_id()const{return child;}
    uint16_t next_block()const{return block;}
};

int main(int argc,char **argv) {
    Verilated::commandArgs(argc,argv);
    if(argc!=2)return 2;
    try {
        const unsigned seed=unsigned(std::stoul(argv[1])); std::mt19937 rng(seed); Bench b; Stim s;
        s.reset=true;b.step(s);s.reset=false;s.arm=true;s.arm_block=0xffff;b.step(s);s.arm=false;
        s.valid=true;s.token={s.arm_frame,s.arm_child,0xffff,62,42};b.step(s);
        s.token.index=63;b.step(s);
        s.token.block=0;s.token.index=0;s.ready=true;b.step(s); // full/pop bubble
        b.step(s); // simultaneous one-slot pop/push
        s.ready=false;s.token.index=1;b.step(s); // full
        s.token.child^=0x80000000U;b.step(s); // bad while full and stalled
        s.valid=false;s.kill=true;b.step(s);s.kill=false;s.arm=true;s.arm_block=0;b.step(s);s.arm=false;
        s.valid=true;s.token={s.arm_frame,s.arm_child,0,1,7};b.step(s);
        s.token.child^=0x80000000U;s.ready=true;b.step(s); // good head retires on bad offer edge
        s.valid=false;s.kill=true;b.step(s);s.kill=false;s.arm=true;s.debt=false;b.step(s); // fenced arm
        s.debt=true;b.step(s);s.arm=false;s.valid=true;s.ready=false;s.token={s.arm_frame,s.arm_child,0,2,8};b.step(s);
        s.valid=false;s.ready=true;s.debt=false;b.step(s);s.ready=false;s.finish=true;b.step(s); // debt fence
        s.debt=true;s.quiet=false;b.step(s);s.quiet=true;b.step(s);s.finish=false;
        for(unsigned n=0;n<60000;++n) {
            Stim x; x.reset=(rng()%997==0);x.kill=b.is_faulted() ? (rng()%3!=0) : (rng()%211==0);
            x.quiet=(rng()%8!=0);x.debt=(rng()%7!=0);x.context=(rng()%5!=0);x.ready=(rng()%3!=0);
            x.arm=!b.is_active()&&!b.is_faulted()&&(rng()%3!=0);
            x.arm_frame=rng();x.arm_child=rng();x.arm_block=uint16_t(rng());
            x.finish=b.is_active()&&(rng()%51==0);x.valid=b.is_active()&&(rng()%4!=0);
            x.token={b.frame_id(),b.child_id(),b.next_block(),uint8_t(rng()%64),int16_t(rng())};
            if(x.valid&&rng()%12==0)x.token.child^=0x80000000U;
            if(x.valid&&rng()%29==0)x.token.frame^=0x80000000U;
            if(x.valid&&rng()%31==0)x.token.block^=0x8000U;
            b.step(x);
        }
        if(!b.push_count||!b.pop_count||!b.simultaneous||!b.full_bubble||!b.bad_full||!b.bad_accepted||
           !b.pop_on_fault||!b.stalls||!b.kill_flush||!b.finish_fenced||!b.finishes||!b.arm_fenced||!b.wraps)
            throw std::runtime_error("directed or randomized coverage incomplete");
        std::cout << "{\"type\":\"v129_dense_queue_verdict\",\"status\":\"TEST_PASS\",\"seed\":"<<seed
          <<",\"clocks\":"<<b.clocks<<",\"pushes\":"<<b.push_count<<",\"pops\":"<<b.pop_count
          <<",\"simultaneous\":"<<b.simultaneous<<",\"full_recovery_bubbles\":"<<b.full_bubble
          <<",\"bad_while_full\":"<<b.bad_full<<",\"bad_accepted\":"<<b.bad_accepted
          <<",\"good_pop_on_fault_edge\":"<<b.pop_on_fault<<",\"held_stalls\":"<<b.stalls
          <<",\"kill_flushes\":"<<b.kill_flush<<",\"finish_fenced\":"<<b.finish_fenced
          <<",\"finishes\":"<<b.finishes<<",\"arm_fenced\":"<<b.arm_fenced
          <<",\"block_wraps\":"<<b.wraps<<"}\n"; return 0;
    } catch(const std::exception &e) {std::cerr<<"V129_DENSE_FAIL "<<e.what()<<'\n';return 1;}
}
