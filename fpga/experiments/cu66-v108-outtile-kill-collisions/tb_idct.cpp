#include "Vidct_probe.h"
#include "Vidct_probe___024root.h"
#include "verilated.h"
#include <array>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <random>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
static void need(bool x,const std::string&m){if(!x)throw std::runtime_error(m);}
struct Case{unsigned id=0,error=0;std::array<uint32_t,40> data{};std::array<uint32_t,48> expected{};};
template<size_t N>static void unhex(const std::string&s,std::array<uint32_t,N>&out){need(s.size()==N*8,"hex width");for(unsigned i=0;i<N;++i)out[i]=uint32_t(std::stoul(s.substr(s.size()-8*(i+1),8),nullptr,16));}
static std::vector<Case> read_cases(const std::string&path){std::ifstream f(path);need(bool(f),"open vectors");std::vector<Case> all;std::string a,b;Case c;while(f>>c.id>>a>>b>>c.error){unhex(a,c.data);unhex(b,c.expected);all.push_back(c);}need(all.size()==4303,"fixture count");return all;}
template<size_t N>static uint64_t bits(const VlWide<N>&v,unsigned at,unsigned width){const unsigned w=at/32,s=at%32;uint64_t x=uint64_t(v[w])>>s;if(s+width>32)x|=uint64_t(v[w+1])<<(32-s);if(s+width>64)x|=uint64_t(v[w+2])<<(64-s);return x&((uint64_t(1)<<width)-1);}
static int64_t signed_bits(uint64_t x,unsigned width){return x&(uint64_t(1)<<(width-1))?int64_t(x)-int64_t(uint64_t(1)<<width):int64_t(x);}
static bool dc_only(const Case&c){if(c.data[0]>>20)return false;for(unsigned i=1;i<40;++i)if(c.data[i])return false;return true;}
static bool zero(const Case&c){for(auto x:c.data)if(x)return false;return true;}
class Bench{public:
 Vidct_probe d;std::mt19937 rng;std::ofstream trace;uint64_t clocks=0,muls=0,outputs=0;unsigned states=0;std::array<uint32_t,40> accepted_source{};bool source_owned=false;uint64_t source_owner_checks=0,idle_noise_edges=0;
 uint64_t expected_written=0,poison_words=0,public_word_checks=0,exposed_word_commits=0,kill_payload_collisions=0,clear_edges=0;
 std::mt19937 poison_rng;
 void check_words(){need(d.verify_written==expected_written,"independent exact public-word written-mask owner");for(unsigned word=0;word<64;++word){const auto p=bits(d.verify_payload,word*24,24);const auto o=bits(d.out_tile,word*24,24);need(o==((expected_written>>word&1U)?p:0U),"every public invalid/partial word visibility");++public_word_checks;}}
 void poison_hidden(){auto&r=*d.rootp;for(unsigned word=0;word<64;++word)if(!(expected_written>>word&1U)){const uint32_t noise=poison_rng()&0xffffffU;switch(word){
 case 0:r.idct_probe__DOT__candidate__DOT__output_words__BRA__0__KET____DOT__payload=noise;break;
 case 1:r.idct_probe__DOT__candidate__DOT__output_words__BRA__1__KET____DOT__payload=noise;break;
 case 2:r.idct_probe__DOT__candidate__DOT__output_words__BRA__2__KET____DOT__payload=noise;break;
 case 3:r.idct_probe__DOT__candidate__DOT__output_words__BRA__3__KET____DOT__payload=noise;break;
 case 4:r.idct_probe__DOT__candidate__DOT__output_words__BRA__4__KET____DOT__payload=noise;break;
 case 5:r.idct_probe__DOT__candidate__DOT__output_words__BRA__5__KET____DOT__payload=noise;break;
 case 6:r.idct_probe__DOT__candidate__DOT__output_words__BRA__6__KET____DOT__payload=noise;break;
 case 7:r.idct_probe__DOT__candidate__DOT__output_words__BRA__7__KET____DOT__payload=noise;break;
 case 8:r.idct_probe__DOT__candidate__DOT__output_words__BRA__8__KET____DOT__payload=noise;break;
 case 9:r.idct_probe__DOT__candidate__DOT__output_words__BRA__9__KET____DOT__payload=noise;break;
 case 10:r.idct_probe__DOT__candidate__DOT__output_words__BRA__10__KET____DOT__payload=noise;break;
 case 11:r.idct_probe__DOT__candidate__DOT__output_words__BRA__11__KET____DOT__payload=noise;break;
 case 12:r.idct_probe__DOT__candidate__DOT__output_words__BRA__12__KET____DOT__payload=noise;break;
 case 13:r.idct_probe__DOT__candidate__DOT__output_words__BRA__13__KET____DOT__payload=noise;break;
 case 14:r.idct_probe__DOT__candidate__DOT__output_words__BRA__14__KET____DOT__payload=noise;break;
 case 15:r.idct_probe__DOT__candidate__DOT__output_words__BRA__15__KET____DOT__payload=noise;break;
 case 16:r.idct_probe__DOT__candidate__DOT__output_words__BRA__16__KET____DOT__payload=noise;break;
 case 17:r.idct_probe__DOT__candidate__DOT__output_words__BRA__17__KET____DOT__payload=noise;break;
 case 18:r.idct_probe__DOT__candidate__DOT__output_words__BRA__18__KET____DOT__payload=noise;break;
 case 19:r.idct_probe__DOT__candidate__DOT__output_words__BRA__19__KET____DOT__payload=noise;break;
 case 20:r.idct_probe__DOT__candidate__DOT__output_words__BRA__20__KET____DOT__payload=noise;break;
 case 21:r.idct_probe__DOT__candidate__DOT__output_words__BRA__21__KET____DOT__payload=noise;break;
 case 22:r.idct_probe__DOT__candidate__DOT__output_words__BRA__22__KET____DOT__payload=noise;break;
 case 23:r.idct_probe__DOT__candidate__DOT__output_words__BRA__23__KET____DOT__payload=noise;break;
 case 24:r.idct_probe__DOT__candidate__DOT__output_words__BRA__24__KET____DOT__payload=noise;break;
 case 25:r.idct_probe__DOT__candidate__DOT__output_words__BRA__25__KET____DOT__payload=noise;break;
 case 26:r.idct_probe__DOT__candidate__DOT__output_words__BRA__26__KET____DOT__payload=noise;break;
 case 27:r.idct_probe__DOT__candidate__DOT__output_words__BRA__27__KET____DOT__payload=noise;break;
 case 28:r.idct_probe__DOT__candidate__DOT__output_words__BRA__28__KET____DOT__payload=noise;break;
 case 29:r.idct_probe__DOT__candidate__DOT__output_words__BRA__29__KET____DOT__payload=noise;break;
 case 30:r.idct_probe__DOT__candidate__DOT__output_words__BRA__30__KET____DOT__payload=noise;break;
 case 31:r.idct_probe__DOT__candidate__DOT__output_words__BRA__31__KET____DOT__payload=noise;break;
 case 32:r.idct_probe__DOT__candidate__DOT__output_words__BRA__32__KET____DOT__payload=noise;break;
 case 33:r.idct_probe__DOT__candidate__DOT__output_words__BRA__33__KET____DOT__payload=noise;break;
 case 34:r.idct_probe__DOT__candidate__DOT__output_words__BRA__34__KET____DOT__payload=noise;break;
 case 35:r.idct_probe__DOT__candidate__DOT__output_words__BRA__35__KET____DOT__payload=noise;break;
 case 36:r.idct_probe__DOT__candidate__DOT__output_words__BRA__36__KET____DOT__payload=noise;break;
 case 37:r.idct_probe__DOT__candidate__DOT__output_words__BRA__37__KET____DOT__payload=noise;break;
 case 38:r.idct_probe__DOT__candidate__DOT__output_words__BRA__38__KET____DOT__payload=noise;break;
 case 39:r.idct_probe__DOT__candidate__DOT__output_words__BRA__39__KET____DOT__payload=noise;break;
 case 40:r.idct_probe__DOT__candidate__DOT__output_words__BRA__40__KET____DOT__payload=noise;break;
 case 41:r.idct_probe__DOT__candidate__DOT__output_words__BRA__41__KET____DOT__payload=noise;break;
 case 42:r.idct_probe__DOT__candidate__DOT__output_words__BRA__42__KET____DOT__payload=noise;break;
 case 43:r.idct_probe__DOT__candidate__DOT__output_words__BRA__43__KET____DOT__payload=noise;break;
 case 44:r.idct_probe__DOT__candidate__DOT__output_words__BRA__44__KET____DOT__payload=noise;break;
 case 45:r.idct_probe__DOT__candidate__DOT__output_words__BRA__45__KET____DOT__payload=noise;break;
 case 46:r.idct_probe__DOT__candidate__DOT__output_words__BRA__46__KET____DOT__payload=noise;break;
 case 47:r.idct_probe__DOT__candidate__DOT__output_words__BRA__47__KET____DOT__payload=noise;break;
 case 48:r.idct_probe__DOT__candidate__DOT__output_words__BRA__48__KET____DOT__payload=noise;break;
 case 49:r.idct_probe__DOT__candidate__DOT__output_words__BRA__49__KET____DOT__payload=noise;break;
 case 50:r.idct_probe__DOT__candidate__DOT__output_words__BRA__50__KET____DOT__payload=noise;break;
 case 51:r.idct_probe__DOT__candidate__DOT__output_words__BRA__51__KET____DOT__payload=noise;break;
 case 52:r.idct_probe__DOT__candidate__DOT__output_words__BRA__52__KET____DOT__payload=noise;break;
 case 53:r.idct_probe__DOT__candidate__DOT__output_words__BRA__53__KET____DOT__payload=noise;break;
 case 54:r.idct_probe__DOT__candidate__DOT__output_words__BRA__54__KET____DOT__payload=noise;break;
 case 55:r.idct_probe__DOT__candidate__DOT__output_words__BRA__55__KET____DOT__payload=noise;break;
 case 56:r.idct_probe__DOT__candidate__DOT__output_words__BRA__56__KET____DOT__payload=noise;break;
 case 57:r.idct_probe__DOT__candidate__DOT__output_words__BRA__57__KET____DOT__payload=noise;break;
 case 58:r.idct_probe__DOT__candidate__DOT__output_words__BRA__58__KET____DOT__payload=noise;break;
 case 59:r.idct_probe__DOT__candidate__DOT__output_words__BRA__59__KET____DOT__payload=noise;break;
 case 60:r.idct_probe__DOT__candidate__DOT__output_words__BRA__60__KET____DOT__payload=noise;break;
 case 61:r.idct_probe__DOT__candidate__DOT__output_words__BRA__61__KET____DOT__payload=noise;break;
 case 62:r.idct_probe__DOT__candidate__DOT__output_words__BRA__62__KET____DOT__payload=noise;break;
 case 63:r.idct_probe__DOT__candidate__DOT__output_words__BRA__63__KET____DOT__payload=noise;break;
 default:throw std::runtime_error("private word index");}++poison_words;}d.eval();need(d.probe_equal,"arbitrary masked private payload became public");check_words();}
 explicit Bench(unsigned seed,const std::string&path):rng(seed),trace(path),poison_rng(seed^0x10800000U){need(bool(trace),"trace open");d.clk=0;d.rst=1;d.abort_frame=0;d.in_valid=0;d.in_id=0;d.out_ready=0;for(unsigned i=0;i<40;++i)d.in_tile[i]=0;tick();d.rst=0;}
 void tick(){
  d.clk=0;d.eval();need(d.probe_equal,"whole IDCT preedge mismatch");check_words();poison_hidden();unsigned state=d.verify_state;states|=1U<<state;
  std::array<uint64_t,8> expected{},samples{},basis{};const bool kill=d.rst||d.abort_frame,mul=state==1||state==3||state==5||state==7;
  for(unsigned lane=0;lane<8;++lane){samples[lane]=bits(d.verify_samples,lane*24,24);basis[lane]=bits(d.verify_basis,lane*14,14);expected[lane]=kill?0:mul?(uint64_t(signed_bits(samples[lane],24)*signed_bits(basis[lane],14))&((uint64_t(1)<<38)-1)):bits(d.verify_products,lane*38,38);}
  if(state!=0&&!kill){need(source_owned,"owned IDCT state without accepted source");for(unsigned i=0;i<40;++i)need(d.verify_source_tile[i]==accepted_source[i],"accepted source tile changed during work/hold");++source_owner_checks;}
  if(kill)source_owned=false;
  else if(state==0&&d.in_valid&&d.in_ready){for(unsigned i=0;i<40;++i)accepted_source[i]=d.in_tile[i];source_owned=true;}
  else if(state==9&&d.out_valid&&d.out_ready)source_owned=false;
  const uint32_t cycles=kill?0:state==0&&d.in_valid&&d.in_ready?0:state!=0&&state!=9?d.active_cycles+1:d.active_cycles;
  trace<<"{\"clock\":"<<clocks<<",\"state\":"<<state<<",\"k\":"<<unsigned(d.verify_k)<<",\"group\":"<<unsigned(d.verify_group)<<",\"kill\":"<<kill<<",\"mul\":"<<mul<<",\"rst\":"<<unsigned(d.rst)<<",\"abort\":"<<unsigned(d.abort_frame)<<",\"in_valid\":"<<unsigned(d.in_valid)<<",\"in_ready\":"<<unsigned(d.in_ready)<<",\"out_ready\":"<<unsigned(d.out_ready)<<",\"samples\":[";
  for(unsigned i=0;i<8;++i){if(i)trace<<',';trace<<signed_bits(samples[i],24);}trace<<"],\"basis\":[";for(unsigned i=0;i<8;++i){if(i)trace<<',';trace<<signed_bits(basis[i],14);}trace<<"]";
  uint64_t writes=0;
  if(state==8)writes=~uint64_t(0);
  else if(state==4&&d.verify_k==7)for(unsigned row=0;row<8;++row)for(unsigned col=2U*d.verify_group;col<2U*d.verify_group+2;++col)writes|=uint64_t(1)<<(row*8+col);
  need(d.verify_payload_write==writes,"independent original group/DC payload write schedule");
  bool input_bad=false,input_zero=true;for(unsigned word=0;word<64;++word){const int64_t value=signed_bits(bits(d.in_tile,word*20,20),20);input_bad|=value>522240||value< -522240;input_zero&=value==0;}
  const bool clear=kill||(state==0&&d.in_valid&&d.in_ready&&(input_bad||input_zero));
  if(kill&&writes)++kill_payload_collisions;
  if(clear){expected_written=0;++clear_edges;}else{exposed_word_commits+=uint64_t(__builtin_popcountll(writes&~expected_written));expected_written|=writes;}
  d.clk=1;d.eval();need(d.probe_equal,"whole IDCT postedge mismatch");check_words();need(d.active_cycles==cycles,"independent active cycle oracle");
  if(d.verify_state!=0){need(source_owned,"postedge owned state without source");for(unsigned i=0;i<40;++i)need(d.verify_source_tile[i]==accepted_source[i],"accepted source tile capture/binding");++source_owner_checks;}
  bool public_zero_after=true;for(unsigned word=0;word<64;++word)public_zero_after&=bits(d.out_tile,word*24,24)==0;
  trace<<",\"written_mask_after\":"<<d.verify_written<<",\"payload_write_mask\":"<<writes<<",\"public_zero_after\":"<<(public_zero_after?"true":"false");
  trace<<",\"products\":[";for(unsigned i=0;i<8;++i){const auto actual=bits(d.verify_products,i*38,38);need(actual==expected[i],"signed24x14 product oracle");if(i)trace<<',';trace<<signed_bits(actual,38);}trace<<"],\"cycles\":"<<d.active_cycles<<",\"next_state\":"<<unsigned(d.verify_state)<<"}\n";
  if(mul&&!kill){++muls;}
  d.clk=0;d.eval();need(d.probe_equal,"whole IDCT falling evaluation mismatch");check_words();++clocks;need(clocks<2000000,"clock watchdog");
 }
 void send(const Case&c){need(d.in_ready,"input not ready");for(unsigned i=0;i<40;++i)d.in_tile[i]=c.data[i];d.in_id=c.id;d.in_valid=1;d.out_ready=0;tick();d.in_valid=0;}
 void run(const Case&c){
  send(c);unsigned work=0;
  while(!d.out_valid){need(++work<=130,"tile watchdog");d.in_valid=rng()&1;d.in_id=rng();for(unsigned i=0;i<40;++i)d.in_tile[i]=rng();tick();}
  need(d.out_id==c.id&&d.out_error==c.error,"golden metadata/error");for(unsigned i=0;i<48;++i)need(d.out_tile[i]==c.expected[i],"golden residual mismatch id"+std::to_string(c.id));
  const unsigned expected_cycles=c.error||zero(c)?0:dc_only(c)?4:128;need(d.active_cycles==expected_cycles,"shortcut/full active cycle count");
  for(unsigned stall=0,n=rng()%7;stall<n;++stall){d.in_valid=1;d.out_ready=0;tick();need(d.out_valid&&d.out_id==c.id&&d.active_cycles==expected_cycles,"held output metadata/cycles");for(unsigned i=0;i<48;++i)need(d.out_tile[i]==c.expected[i],"held output changed");}
  d.in_valid=0;d.out_ready=1;tick();d.out_ready=0;++outputs;need(d.in_ready,"output did not release");
 }
 void flush(unsigned guards){d.rst=guards&1;d.abort_frame=(guards&2)!=0;tick();need(!d.out_valid&&!d.out_error&&d.active_cycles==0,"kill did not clear");d.rst=0;d.abort_frame=0;d.in_valid=0;d.clk=0;d.eval();need(d.in_ready,"kill did not idle");}
};
int main(int argc,char**argv){try{
 need(argc==4,"usage vectors seed trace");const auto all=read_cases(argv[1]);const unsigned seed=unsigned(std::stoul(argv[2]));Bench b(seed,argv[3]);const Case*ac=nullptr,*dc=nullptr;
 for(const auto&c:all)if(!c.error&&!zero(c)){if(dc_only(c)&&!dc)dc=&c;if(!dc_only(c)&&!ac)ac=&c;}
 need(ac&&dc,"missing general/DC vectors");unsigned directed=0,abort_mask=0;unsigned boundary_cases=0,boundary_groups=0,boundary_guards=0,boundary_matrix=0,boundary_retries=0;
 for(unsigned n=0;n<1024;++n){b.d.in_valid=0;b.d.in_id=b.rng();for(unsigned i=0;i<40;++i)b.d.in_tile[i]=b.rng();b.tick();++b.idle_noise_edges;}
 for(unsigned state=0;state<10;++state)for(unsigned guards=1;guards<=3;++guards){
  b.flush(1);if(state!=0){b.send(state>=5&&state<=8?*dc:*ac);unsigned watchdog=0;while(b.d.verify_state!=state){need(++watchdog<=130,"abort state unreachable");b.tick();}}
  b.d.in_valid=1;for(unsigned i=0;i<40;++i)b.d.in_tile[i]=b.rng();b.flush(guards);abort_mask|=1U<<state;b.run(*ac);++directed;
 }
 for(const auto&c:all){for(unsigned n=b.rng()%3;n;--n)b.tick();b.run(c);}
 // All original fixtures finish before this additional matrix; their RNG sequence is unchanged.
 for(unsigned group=0;group<4;++group)for(unsigned guards=1;guards<=3;++guards){
  b.flush(1);b.send(*ac);unsigned watchdog=0;
  while(!(b.d.verify_state==4&&b.d.verify_k==7&&b.d.verify_group==group)){need(++watchdog<=130,"final-pass write boundary unreachable");b.tick();}
  uint64_t selected=0;for(unsigned row=0;row<8;++row)for(unsigned col=group*2;col<group*2+2;++col)selected|=uint64_t(1)<<(row*8+col);
  b.d.clk=0;b.d.eval();need(b.d.verify_payload_write==selected&&__builtin_popcountll(selected)==16,"target actual sixteen-word AC write collision");
  const uint64_t old_collisions=b.kill_payload_collisions,old_outputs=b.outputs;
  b.d.in_valid=1;b.d.in_id=b.rng();for(unsigned i=0;i<40;++i)b.d.in_tile[i]=b.rng();b.flush(guards);
  need(b.kill_payload_collisions==old_collisions+1&&b.d.verify_written==0,"targeted kill must hide every concurrently written word");
  for(unsigned i=0;i<48;++i)need(b.d.out_tile[i]==0,"targeted kill public output zero even invalid");
  ++boundary_cases;boundary_groups|=1U<<group;boundary_guards|=1U<<(guards-1);boundary_matrix|=1U<<(group*3+guards-1);
  b.run(*ac);need(b.outputs==old_outputs+1,"targeted kill good golden retry did not complete");++boundary_retries;
 }
 need(boundary_cases==12&&boundary_groups==15&&boundary_guards==7&&boundary_matrix==4095&&boundary_retries==12,"all twelve AC write-boundary kill/golden-retry cases");
 need(abort_mask==1023&&b.states==1023,"all FSM states coverage");need(b.poison_words>1000&&b.kill_payload_collisions>=3&&b.exposed_word_commits>1000,"arbitrary hidden-word/kill collision/exposure coverage");
 std::cout<<"{\"status\":\"TEST_PASS\",\"seed\":"<<seed<<",\"tiles\":"<<all.size()<<",\"directed_abort_reset_cases\":"<<directed<<",\"abort_state_mask\":"<<abort_mask<<",\"states\":"<<b.states<<",\"source_owner_checks\":"<<b.source_owner_checks<<",\"idle_noise_edges\":"<<b.idle_noise_edges<<",\"clock_edges\":"<<b.clocks<<",\"masked_private_word_poisons\":"<<b.poison_words<<",\"all_cycle_public_word_checks\":"<<b.public_word_checks<<",\"exposed_word_commits\":"<<b.exposed_word_commits<<",\"kill_payload_write_collisions\":"<<b.kill_payload_collisions<<",\"clear_edges\":"<<b.clear_edges<<",\"multiply_edges\":"<<b.muls<<",\"completed_tiles\":"<<b.outputs<<",\"write_boundary_collision_cases\":"<<boundary_cases<<",\"write_boundary_group_mask\":"<<boundary_groups<<",\"write_boundary_guard_mask\":"<<boundary_guards<<",\"write_boundary_matrix_mask\":"<<boundary_matrix<<",\"write_boundary_good_retries\":"<<boundary_retries<<"}\n";b.d.final();return 0;
}catch(const std::exception&e){std::cerr<<"IDCT_PREFETCH_FAIL "<<e.what()<<'\n';return 1;}}
