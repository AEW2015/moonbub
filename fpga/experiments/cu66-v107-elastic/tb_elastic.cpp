#include "Vcu66_coefficient_elastic.h"
#include "verilated.h"
#include <array>
#include <cstdint>
#include <deque>
#include <fstream>
#include <iostream>
#include <random>
#include <stdexcept>
#include <string>
#include <vector>
static void require(bool ok,const std::string&s){if(!ok)throw std::runtime_error(s);}
struct Token {
 uint32_t epoch,child;unsigned plane,scale,block,tile,cell,index,value;
 bool operator==(const Token&o)const{return epoch==o.epoch&&child==o.child&&plane==o.plane&&scale==o.scale&&block==o.block&&tile==o.tile&&cell==o.cell&&index==o.index&&value==o.value;}
};
struct Event {bool push,pop,done;};
class Bench {
public:
 Vcu66_coefficient_elastic d;std::mt19937 rng;std::deque<Token> queue;
 bool active=false,sealed=false,pending_final=false;
 uint64_t cycles=0,pushes=0,pops=0,discarded=0,done_edges=0,stalls=0,replacements=0,flushes=0,final_stalls=0;
 std::ofstream transcript;
 explicit Bench(unsigned seed,const char*path):rng(seed),transcript(path){require(bool(transcript),"trace open");d.clk=0;d.reset=1;d.start=0;d.cancel=0;d.input_done=0;d.in_valid=0;d.out_ready=0;tick();d.reset=0;}
 Token token(){auto n=[&](){return unsigned(rng());};return {n(),n(),n()%4,n()%4,n()%65536,n()%8192,n()%2048,n()%64,n()%65536};}
 Token input()const{return {d.in_epoch,d.in_child_epoch,d.in_plane,d.in_qscale,d.in_block,d.in_tile,d.in_qcell,d.in_index,d.in_value};}
 Token output()const{return {d.out_epoch,d.out_child_epoch,d.out_plane,d.out_qscale,d.out_block,d.out_tile,d.out_qcell,d.out_index,d.out_value};}
 void offer(const Token&t){d.in_epoch=t.epoch;d.in_child_epoch=t.child;d.in_plane=t.plane;d.in_qscale=t.scale;d.in_block=t.block;d.in_tile=t.tile;d.in_qcell=t.cell;d.in_index=t.index;d.in_value=t.value;}
 Event tick(){
  d.clk=0;d.eval();const bool kill=d.reset||d.start||d.cancel;
  require(bool(d.out_valid)==(active&&!kill&&!queue.empty()),"output validity/ownership mismatch");
  require(queue.size()<=1,"independent queue occupancy bound");
  if(d.out_valid)require(output()==queue.front(),"entire130-bit tuple mismatch");
  const bool fence=active&&!kill&&sealed&&!pending_final&&queue.empty();
  require(bool(d.output_done)==fence,"done fence before drain/late/missing");
  const bool capacity=queue.empty()||bool(d.out_ready);
  require(bool(d.in_ready)==(active&&!kill&&(!sealed||pending_final)&&capacity),"producer backpressure/fence mismatch");
  require(bool(d.occupied)==(!queue.empty()||pending_final),"stage occupancy mismatch");
  Event e{bool(d.in_valid&&d.in_ready),bool(d.out_valid&&d.out_ready),bool(d.output_done)};
  const Token offered=input();
  if(kill){discarded+=queue.size();queue.clear();active=d.start&&!d.reset&&!d.cancel;sealed=false;pending_final=false;++flushes;require(!e.push&&!e.pop&&!e.done,"flush leaked handshake");}
  else{
   stalls+=d.out_valid&&!d.out_ready;done_edges+=e.done;replacements+=e.push&&e.pop;
   if(e.pop){queue.pop_front();++pops;}
   if(e.push){queue.push_back(offered);++pushes;if(pending_final)pending_final=false;}
   if(active&&d.input_done&&!sealed){sealed=true;pending_final=d.in_valid&&!e.push;if(pending_final)++final_stalls;}
  }
  if(e.push||e.pop||kill||e.done)transcript<<"{\"edge\":"<<cycles<<",\"push\":"<<e.push<<",\"pop\":"<<e.pop<<",\"done\":"<<e.done<<",\"kill\":"<<kill<<",\"epoch\":"<<offered.epoch<<",\"child\":"<<offered.child<<",\"index\":"<<offered.index<<",\"value\":"<<offered.value<<",\"depth\":"<<queue.size()<<"}\n";
  d.clk=1;d.eval();d.clk=0;d.eval();++cycles;require(cycles<5000000,"finite clock watchdog");return e;
 }
 void begin(){d.in_valid=0;d.input_done=0;d.out_ready=0;d.start=1;tick();d.start=0;}
 void frame(unsigned length,unsigned timing,bool sticky){
  begin();std::vector<Token> words;for(unsigned i=0;i<length;++i)words.push_back(token());
  unsigned at=0,delivered=0,delay=1+rng()%7;bool pending=false,done_sent=false;
  for(unsigned watchdog=0;watchdog<10000;++watchdog){
   if(!pending&&at<length&&rng()%4!=0)pending=true;
   if(pending){offer(words[at]);}d.in_valid=pending;d.out_ready=rng()%4!=0;
   if(timing==2&&at==length&&!done_sent)d.out_ready=0;
   bool finish=false;
   if(timing==0)finish=(pending&&at+1==length)||(length==0);
   else if(at==length){if(delay) --delay;else finish=true;}
   d.input_done=(!done_sent&&finish)||(sticky&&done_sent);
   if(d.input_done)done_sent=true;
   d.clk=0;d.eval();if(d.out_valid&&d.out_ready){require(delivered<words.size()&&output()==words[delivered],"independent frame transcript reordering");++delivered;}
   Event e=tick();if(e.push){++at;pending=false;}
   if(e.done){require(done_sent&&at==length&&delivered==length,"done lost finalword or accepted extra token");
    d.in_valid=0;for(unsigned hold=0;hold<7;++hold){d.input_done=sticky;d.out_ready=rng()%2;require(tick().done,"done pulse not retained");}
    return;
   }
  }
  throw std::runtime_error("frame progress watchdog");
 }
 void cancellation(unsigned mask,unsigned phase){
  begin();Token a=token(),b=token();offer(a);d.in_valid=1;d.out_ready=0;
  if(phase>0){require(tick().push,"cancel setup input missing");d.in_valid=0;}
  if(phase==2){offer(b);d.in_valid=1;d.input_done=1;tick();require(pending_final,"stalled final-offer setup");}
  if(phase==3){d.input_done=1;tick();d.input_done=0;d.out_ready=1;tick();require(d.output_done,"done-state cancel setup");}
  d.reset=mask&1;d.start=(mask&2)!=0;d.cancel=(mask&4)!=0;tick();
  d.reset=d.start=d.cancel=0;d.in_valid=0;d.input_done=0;d.out_ready=1;
  for(unsigned i=0;i<4;++i){Event e=tick();require(!e.pop&&!e.done,"stale cancelled tuple/fence");}
  frame(2,0,false);
 }
};
int main(int argc,char**argv){try{
 require(argc==3,"seed transcript required");unsigned seed=unsigned(std::stoul(argv[1]));Bench b(seed,argv[2]);
 for(unsigned mask=1;mask<8;++mask)for(unsigned phase=0;phase<4;++phase)b.cancellation(mask,phase);
 for(unsigned timing=0;timing<3;++timing)for(bool sticky:{false,true})
  for(unsigned length:{0U,1U,2U,63U,64U,65U,128U})for(unsigned repeat=0;repeat<16;++repeat)b.frame(length,timing,sticky);
 for(unsigned n=0;n<512;++n)b.frame(b.rng()%257,b.rng()%3,b.rng()%2);
 require(b.pushes==b.pops+b.discarded+b.queue.size(),"accepted tuple conservation");
 require(b.final_stalls>0&&b.replacements>1000&&b.stalls>1000&&b.flushes>1000,"adversarial coverage floor");
 std::cout<<"{\"status\":\"TEST_PASS\",\"seed\":"<<seed<<",\"edges\":"<<b.cycles<<",\"pushes\":"<<b.pushes<<",\"pops\":"<<b.pops<<",\"discarded\":"<<b.discarded<<",\"done_edges\":"<<b.done_edges<<",\"held_edges\":"<<b.stalls<<",\"simultaneous_replace\":"<<b.replacements<<",\"flushes\":"<<b.flushes<<",\"stalled_final_fences\":"<<b.final_stalls<<"}\n";
 b.d.final();return 0;
 }catch(const std::exception&e){std::cerr<<"TEST_FAIL "<<e.what()<<'\n';return 1;}}
