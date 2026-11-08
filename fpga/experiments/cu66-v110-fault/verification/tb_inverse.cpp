#include "Vlocality_probe.h"
#include "Vlocality_probe___024root.h"
#include "Vlocality_probe_cu66_idct8x8.h"
static void locality_pre(Vlocality_probe&);
static void locality_post(Vlocality_probe&);
#include "historical_inverse.cpp"
#define OLD(n) r.locality_probe__DOT__old_dut__DOT__##n
#define NEW(n) r.locality_probe__DOT__new_dut__DOT__##n
#define BOTH(n,v) do {const auto z=(v);OLD(n)=z;NEW(n)=z;}while(0)
#define BOTH_IDCT(n,v) do {const auto z=(v);r.__PVT__locality_probe__DOT__old_dut__DOT__inverse->n=z;r.__PVT__locality_probe__DOT__new_dut__DOT__inverse->n=z;}while(0)
struct Meta {unsigned epoch=0,child=0,plane=0,scale=0,block=0,tile=0,cell=0;};
struct Oracle {
 std::array<std::array<uint16_t,64>,2> store{};std::array<Meta,2> meta{};unsigned index=0,token=0;
 uint64_t clocks=0,writes=0,guarded=0;std::array<unsigned,8> faults{};unsigned fault=0,bank=0,word=0;bool write=false;
 std::ofstream* trace=nullptr;std::string phase="prepared";
} oracle;
static unsigned qcell(unsigned p,unsigned t){return p? (t&2047U):((((t/90)/2)*45+(t%90)/2)&2047U);}
static Meta input_meta(const Vlocality_probe&d){return {d.in_epoch,d.in_child_epoch,d.in_plane,d.in_qscale,d.in_block,d.in_tile,d.in_qcell};}
static uint64_t digest(const std::array<std::array<uint16_t,64>,2>&s){uint64_t h=1469598103934665603ULL;for(const auto& b:s)for(unsigned v:b){h^=v;h*=1099511628211ULL;}return h;}
static void locality_pre(Vlocality_probe&d){
 // The standalone start is an admitted parent start; cancel includes either peer kill or external abort.
 d.verify_abort_packet=d.cancel&&((oracle.clocks&1U)!=0);
 d.verify_metadata_bad=d.in_plane>2||d.in_tile>=(d.in_plane==0?5400U:1350U)||d.in_qcell!=qcell(d.in_plane,d.in_tile);
 const int signed_value=int(d.in_value)-((d.in_value&32768U)?65536:0);
 d.verify_domain_bad=d.in_qscale==3||signed_value< -2048||signed_value>2048;
 d.eval();need(d.probe_state_equal,"preedge all inverse control/owner/intermediate state comparison");
 need(d.probe_fault_equal,"co-registered fault exact same-cycle status");
 need(d.probe_outputs_equal&&d.probe_stores_equal,"preedge whole-module/store comparison");
 need(d.probe_fill_index==oracle.index&&d.probe_next_token==oracle.token,"independent input position/token oracle");
 const Meta in=input_meta(d),old=oracle.meta[d.fill_bank];unsigned f=0;
 if(d.input_done&&oracle.index!=0)f=4;
 else if(d.in_valid&&d.in_ready){
  if(d.in_index!=oracle.index)f=1;
  else if(in.plane>2||in.tile>=(in.plane?1350U:5400U)||in.cell!=qcell(in.plane,in.tile)||
    (d.bank_state[d.fill_bank]==1&&(old.epoch!=in.epoch||old.child!=in.child||old.plane!=in.plane||old.scale!=in.scale||old.block!=in.block||old.tile!=in.tile||old.cell!=in.cell)))f=2;
  else if(in.scale==3||int16_t(d.in_value)<-2048||int16_t(d.in_value)>2048)f=3;
  else if(oracle.index==0&&oracle.token==0xffffffffU)f=7;
 }
 need(d.probe_fault==f,"independent malformed-input priority oracle");
 oracle.fault=f;oracle.bank=d.fill_bank;oracle.word=oracle.index;
 oracle.write=d.in_valid&&d.in_ready&&f==0;
 if(oracle.trace)*oracle.trace<<"{\"clock\":"<<oracle.clocks<<",\"phase\":\""<<oracle.phase<<"\",\"guards\":"<<(unsigned(d.reset)|unsigned(d.start)*2U|unsigned(d.cancel)*4U)<<",\"input_done\":"<<unsigned(d.input_done)<<",\"in_valid\":"<<unsigned(d.in_valid)<<",\"in_ready\":"<<unsigned(d.in_ready)<<",\"index\":"<<unsigned(d.in_index)<<",\"fill_index\":"<<oracle.index<<",\"bank\":"<<oracle.bank<<",\"value\":"<<unsigned(d.in_value)<<",\"fault\":"<<f<<",\"write\":"<<oracle.write;
 if(oracle.write){oracle.store[oracle.bank][oracle.word]=d.in_value;if(oracle.word==0){oracle.meta[oracle.bank]=in;++oracle.token;}oracle.index=(oracle.word+1)&63U;++oracle.writes;}
 if(f)++oracle.faults[f];
 if(d.reset||d.start||d.cancel){oracle.index=0;oracle.token=0;++oracle.guarded;}
 else if(f)oracle.index=0;
}
static void locality_post(Vlocality_probe&d){
 need(d.probe_state_equal,"postedge all inverse control/owner/intermediate state comparison");
 need(d.probe_fault_equal,"co-registered fault exact same-cycle status");
 need(d.probe_outputs_equal&&d.probe_stores_equal,"postedge whole-module/store comparison");
 for(unsigned b=0;b<2;++b)for(unsigned w=0;w<64;++w){const auto& view=b?d.probe_store1:d.probe_store0;const uint16_t actual=uint16_t(view[w/2]>>((w&1)*16));need(actual==oracle.store[b][w],"independent entire coefficient store incl inactive/held words");}
 if(d.error)oracle.index=0;
 if(oracle.trace)*oracle.trace<<",\"post_error\":"<<unsigned(d.error)<<",\"store_digest\":"<<digest(oracle.store)<<",\"equal\":true}\n";
 ++oracle.clocks;need(oracle.clocks<1000000,"finite focused-clock watchdog");
}
struct Prepared {unsigned bank=0,index=0,guard=0,plane=0,tile=0,scale=1;int value=17;bool valid=true,input_done=false;unsigned index_delta=0,mutate=0,next=100;};
int main(int argc,char**argv){try{
 need(argc==4,"seed trace boundary-file required");unsigned seed=unsigned(std::stoul(argv[1]));std::mt19937 rng(seed);std::ofstream trace(argv[2]);need(bool(trace),"trace open");oracle.trace=&trace;
 Vlocality_probe d;auto&r=*d.rootp;
 d.clk=0;d.reset=1;d.start=0;d.cancel=0;d.input_done=0;d.in_valid=0;d.in_epoch=0;d.in_child_epoch=0;d.in_plane=0;d.in_qscale=0;d.in_block=0;d.in_tile=0;d.in_qcell=0;d.in_index=0;d.in_value=0;d.out_ready=0;
 auto tick=[&](){d.clk=0;d.eval();locality_pre(d);d.clk=1;d.eval();locality_post(d);d.clk=0;d.eval();};tick();d.reset=0;
 auto run=[&](const Prepared&c){
  d.clk=0;d.reset=(c.guard&1)!=0;d.start=(c.guard&2)!=0;d.cancel=(c.guard&4)!=0;d.input_done=c.input_done;d.in_valid=c.valid;
  d.in_epoch=1001;d.in_child_epoch=1002;d.in_plane=c.plane;d.in_qscale=c.scale;d.in_block=13;d.in_tile=c.tile;d.in_qcell=qcell(c.plane,c.tile);d.in_index=(c.index+c.index_delta)&63U;d.in_value=uint16_t(c.value);d.out_ready=rng()%2;
  BOTH(running,1U);BOTH(finished_input,0U);BOTH(error,0U);BOTH(fault_o,0U);NEW(fault_pending_o)=0;BOTH(done,0U);BOTH(fill_bank,c.bank);BOTH(math_bank,c.bank^1U);BOTH(math_state,0U);BOTH(fill_index,c.index);BOTH(next_token,c.next);BOTH(bank_state[0],0U);BOTH(bank_state[1],0U);BOTH(bank_state[c.bank],c.index?1U:0U);
  Meta m=input_meta(d);oracle.meta[c.bank]=m;oracle.index=c.index;oracle.token=c.next;
  BOTH(epochs[c.bank],m.epoch);BOTH(child_epochs[c.bank],m.child);BOTH(planes[c.bank],m.plane);BOTH(scales[c.bank],m.scale);BOTH(blocks[c.bank],m.block);BOTH(tiles[c.bank],m.tile);BOTH(cells[c.bank],m.cell);
  switch(c.mutate){case 1:d.in_epoch^=1;break;case 2:d.in_child_epoch^=1;break;case 3:d.in_block^=1;break;case 4:d.in_qcell^=1;break;case 5:d.in_tile^=1;break;case 6:d.in_plane=3;break;default:break;}
  tick();
 };
 for(unsigned b=0;b<2;++b)for(unsigned w=0;w<64;++w){Prepared c;c.bank=b;c.index=w;c.value=int(rng()%4097)-2048;run(c);}
 for(unsigned p=0;p<3;++p)for(unsigned t=0;t<(p?1350U:5400U);++t){Prepared c;c.plane=p;c.tile=t;c.bank=t&1;c.index=t%64;c.value=int(rng()%4097)-2048;run(c);}
 for(unsigned b=0;b<2;++b)for(unsigned w=0;w<64;++w)for(unsigned g=0;g<8;++g){Prepared c;c.bank=b;c.index=w;c.guard=g;c.value=int(rng()%4097)-2048;run(c);}
 for(unsigned b=0;b<2;++b)for(unsigned idx:{0U,1U,63U})for(unsigned kind=0;kind<18;++kind){Prepared c;c.bank=b;c.index=idx;
  if(kind<7)c.mutate=kind;else if(kind==7)c.index_delta=1;else if(kind==8)c.scale=3;else if(kind==9)c.value=2049;else if(kind==10)c.value=-2049;else if(kind==11)c.next=0xffffffffU;else if(kind==12)c.input_done=true;else if(kind==13){c.input_done=true;c.index_delta=1;c.scale=3;}else if(kind==14){c.index_delta=1;c.mutate=4;c.value=2049;}else if(kind==15){c.mutate=4;c.scale=3;}else if(kind==16)c.valid=false;else c.tile=c.plane?1350:5400;
  run(c);
 }
 // Late arithmetic fail occurs after the valid input write in the source FSM.
 for(unsigned idx:{0U,63U}){
  Prepared c;c.index=idx;c.bank=0;run(c);
  d.reset=d.start=d.cancel=0;d.input_done=0;d.in_valid=1;d.in_index=idx;d.in_value=321;
  BOTH(running,1U);BOTH(finished_input,0U);BOTH(error,0U);BOTH(fault_o,0U);NEW(fault_pending_o)=0;BOTH(done,0U);BOTH(fill_bank,0U);BOTH(fill_index,idx);BOTH(bank_state[0],idx?1U:0U);BOTH(bank_state[1],3U);BOTH(math_bank,1U);BOTH(math_state,2U);BOTH(tokens[1],99U);
  // Verification-only prepared dequant response is produced through public
  // producer registers; it does not claim complete packet reachability.
  BOTH(dequant__DOT__state,2U);BOTH(dequant__DOT__out_id,98U);BOTH(dequant__DOT__out_error,0U);oracle.index=idx;oracle.meta[0]=input_meta(d);tick();need(d.error==5,"late dequant mismatch not reached");
 }
 unsigned concurrent_math_cases=0;
 for(unsigned math:{2U,3U,4U})for(unsigned idx:{0U,1U,63U})for(unsigned kind=0;kind<7;++kind){
  if(kind==4&&idx!=0)continue;
  if(kind==5&&idx!=1)continue;
  Prepared c;c.index=idx;c.bank=0;run(c);
  d.reset=d.start=d.cancel=0;d.input_done=0;d.in_valid=1;d.in_index=idx;d.in_value=321;
  BOTH(running,1U);BOTH(finished_input,0U);BOTH(error,0U);BOTH(fault_o,0U);NEW(fault_pending_o)=0;BOTH(done,0U);BOTH(fill_bank,0U);BOTH(fill_index,idx);BOTH(bank_state[0],idx?1U:0U);BOTH(bank_state[1],3U);BOTH(math_bank,1U);BOTH(math_state,math);BOTH(tokens[1],99U);
  if(math==2){BOTH(dequant__DOT__state,2U);BOTH(dequant__DOT__out_id,98U);BOTH(dequant__DOT__out_error,0U);}
  else {BOTH_IDCT(state,9U);BOTH_IDCT(out_id,98U);BOTH_IDCT(out_error,0U);}
  oracle.index=idx;oracle.meta[0]=input_meta(d);
  unsigned expected=math==2?5U:6U;
  if(kind==1){d.in_index=(idx+1)&63U;expected=1;}
  else if(kind==2){d.in_qcell^=1;expected=2;}
  else if(kind==3){d.in_value=2049;expected=3;}
  else if(kind==4){BOTH(next_token,0xffffffffU);oracle.token=0xffffffffU;expected=7;}
  else if(kind==5){d.input_done=1;expected=4;}
  else if(kind==6){d.in_qscale=3;expected=idx?2U:3U;}
  tick();need(d.error==expected,"exact input-vs-concurrent arithmetic fault priority");++concurrent_math_cases;
 }
 const auto prepared_clocks=oracle.clocks,prepared_writes=oracle.writes,prepared_guards=oracle.guarded;const auto prepared_faults=oracle.faults;
 d.final();trace<<"{\"model_start\":\"historical-real-interface\"}\n";oracle=Oracle{};oracle.trace=&trace;oracle.phase="historical";
 char* oldargv[]={argv[0],argv[3],argv[1]};need(historical_inverse_main(3,oldargv)==0,"existing inverse boundary suite failed");
 std::cout<<"{\"status\":\"TEST_PASS\",\"seed\":"<<seed<<",\"concurrent_math_cases\":"<<concurrent_math_cases<<",\"prepared_clocks\":"<<prepared_clocks<<",\"prepared_writes\":"<<prepared_writes<<",\"guarded_clocks\":"<<prepared_guards<<",\"historical_clocks\":"<<oracle.clocks<<",\"historical_writes\":"<<oracle.writes<<",\"word_count\":128,\"coefficient_bits\":2048,\"late_same_edge_write_fail_cases\":2,\"prepared_faults\":[";for(unsigned i=0;i<8;++i){if(i)std::cout<<',';std::cout<<prepared_faults[i];}std::cout<<"]}\n";return 0;
 }catch(const std::exception&e){std::cerr<<"TEST_FAIL "<<e.what()<<'\n';return 1;}}
