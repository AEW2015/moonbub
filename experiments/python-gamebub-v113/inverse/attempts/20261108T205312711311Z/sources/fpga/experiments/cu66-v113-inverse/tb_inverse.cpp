#include "Vcu66_inverse_stream_v91j.h"
#include "Vcu66_inverse_stream_v91j___024root.h"
#include "verilated.h"
#include <array>
#include <cstdint>
#include <deque>
#include <fstream>
#include <iostream>
#include <optional>
#include <random>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
static void need(bool b,const std::string&s){if(!b)throw std::runtime_error(s);}
static std::vector<uint8_t> unhex(const std::string&s){if(s=="-")return {};std::vector<uint8_t> v;for(size_t n=0;n<s.size();n+=2)v.push_back(uint8_t(std::stoul(s.substr(n,2),nullptr,16)));return v;}
static int i32(const std::vector<uint8_t>&v,unsigned n){uint32_t a=0;for(unsigned i=0;i<4;++i)a|=uint32_t(v[n*4+i])<<(8*i);return int32_t(a);}
static int sb(uint32_t a,unsigned w){a&=(1U<<w)-1;return a&(1U<<(w-1))?int(int64_t(a)-(int64_t(1)<<w)):int(a);}
template<class W>static int packed(const W&v,unsigned n,unsigned w){unsigned at=n*w,i=at/32,s=at%32;uint64_t a=v[i];if(s+w>32)a|=uint64_t(v[i+1])<<32;return sb(uint32_t(a>>s),w);}
struct Case{std::string name;unsigned error,plane,scale;std::vector<uint8_t> coef,dq,res;};
static std::vector<Case> load(const std::string&p){std::ifstream f(p);need(bool(f),"goldens open");std::vector<Case> v;std::string l;while(std::getline(f,l)){std::istringstream i(l);Case c;std::string a,b,d;i>>c.name>>c.error>>c.plane>>c.scale>>a>>b>>d;need(!i.fail(),"goldens row");c.coef=unhex(a);c.dq=unhex(b);c.res=unhex(d);v.push_back(c);}return v;}
struct Job{const Case*c;unsigned token,tile;};
struct Held{std::array<unsigned,11> a;bool operator==(const Held&o)const{return a==o.a;}};
class Bench{
public:
 Vcu66_inverse_stream_v91j d;std::mt19937 rng;uint64_t cycle=0,total_inputs=0,total_outputs=0,total_commits=0,overlap=0,full=0,latency_max=0;unsigned high=0,owner=0,offered=0,emitted=0,launches=0,dqs=0;bool hold=false;std::optional<Held> held;std::vector<Job> jobs;std::deque<uint64_t> commits;uint64_t expected_commits=0;
 explicit Bench(unsigned s):rng(s){d.clk=0;d.reset=1;d.start=d.cancel=d.input_done=d.in_valid=0;d.fault_ack_i=0;d.in_epoch=d.in_child_epoch=d.in_plane=d.in_qscale=d.in_block=d.in_tile=d.in_qcell=d.in_index=d.in_value=d.in_metadata_bad=d.in_domain_bad=0;tick();d.reset=0;tick();}
 auto& r(){return *d.rootp;}
 Held tuple(){return {{d.out_epoch,d.out_child_epoch,d.out_token,d.out_plane,d.out_qscale,d.out_block,d.out_tile,d.out_qcell,d.out_index,d.out_value,owner}};}
 void flags(){int v=int16_t(d.in_value);d.in_metadata_bad=d.in_plane>2||d.in_tile>=(d.in_plane?1350:5400)||d.in_qcell!=(d.in_plane?(d.in_tile&2047):(((d.in_tile/90)/2)*45+(d.in_tile%90)/2));d.in_domain_bad=d.in_qscale==3||v < -2048||v>2048;}
 bool tick(){d.clk=0;d.out_ready=!hold&&rng()%4!=0;flags();d.eval();bool kill=d.reset||d.start||d.cancel||d.error;bool take=d.in_valid&&d.in_ready;
 if(kill){held.reset();commits.clear();}else{
  if(held)need(d.out_valid&&tuple()==*held,"held final/ordinary tuple changed");
  held=d.out_valid&&!d.out_ready?std::optional<Held>(tuple()):std::nullopt;
  if(take){++total_inputs;commits.push_back(cycle+2);}
  if(d.dbg_launch){need(launches<jobs.size(),"unexpected launch");const Job&j=jobs[launches++];need(j.c->error==0&&d.dbg_token==j.token,"launch token");for(unsigned n=0;n<64;++n)need(packed(d.dbg_coefficients,n,16)==int16_t(unsigned(j.c->coef[2*n])|(unsigned(j.c->coef[2*n+1])<<8)),"coefficient golden "+j.c->name);}
  if(d.dbg_dequant){need(dqs<jobs.size(),"unexpected DQ");const Job&j=jobs[dqs++];need(d.dbg_token==j.token,"DQ token");for(unsigned n=0;n<64;++n)need(packed(d.dbg_dequantized,n,20)==i32(j.c->dq,n),"DQ golden "+j.c->name);}
  if(d.out_valid&&d.out_ready){unsigned ji=emitted/64,ix=emitted%64;need(ji<jobs.size(),"extra residual");const Job&j=jobs[ji];need(d.out_epoch==77&&d.out_child_epoch==88&&d.out_token==j.token&&d.out_plane==j.c->plane&&d.out_qscale==j.c->scale&&d.out_block==j.tile+17&&d.out_tile==j.tile&&d.out_index==ix,"residual identity/order");need(sb(d.out_value,24)==i32(j.c->res,ix),"residual golden "+j.c->name);++emitted;++total_outputs;}
 }
 if(!kill&&!commits.empty()&&commits.front()==cycle){++expected_commits;commits.pop_front();++total_commits;}
 d.clk=1;d.eval();++cycle;need(cycle<3000000,"clock watchdog");
 if(d.reset||d.start)expected_commits=0;
 if(!d.error)need(r().cu66_inverse_stream_v91j__DOT__count_commits==expected_commits,"independent accept E+2 commit ledger");else commits.clear();
 high=std::max(high,unsigned(r().cu66_inverse_stream_v91j__DOT__result_occupancy));
 if(d.out_valid&&d.math_state!=0)++overlap;
 if(r().cu66_inverse_stream_v91j__DOT__result_occupancy==2)++full;
 d.clk=0;d.eval();return take;
 }
 void begin(){need(!d.busy,"begin without drain");++owner;d.start=1;d.input_done=d.in_valid=0;jobs.clear();offered=emitted=launches=dqs=0;tick();d.start=0;}
 void feed(const Case&c,unsigned tile=0,unsigned count=64){jobs.push_back({&c,++offered,tile});d.in_epoch=77;d.in_child_epoch=88;d.in_plane=c.plane;d.in_qscale=c.scale;d.in_block=tile+17;d.in_tile=tile;d.in_qcell=c.plane?tile:(((tile/90)/2)*45+(tile%90)/2);
 for(unsigned ix=0;ix<count&&!d.error;++ix){d.in_valid=1;d.in_index=ix;d.in_value=uint16_t(unsigned(c.coef[ix*2])|(unsigned(c.coef[ix*2+1])<<8));for(unsigned w=0;;++w){need(w<30000,"input watchdog");if(tick()||d.error)break;}}
 d.in_valid=0;
 }
 void finish(unsigned err=0){d.input_done=1;uint64_t b=cycle;for(unsigned w=0;w<30000&&!d.done&&!d.error;++w)tick();latency_max=std::max(latency_max,cycle-b);d.input_done=0;need(d.error==err,"terminal error expected "+std::to_string(err)+" got "+std::to_string(d.error));if(!err)need(d.done&&emitted==jobs.size()*64&&launches==jobs.size()&&dqs==jobs.size(),"EOF before complete residual drain");need(!d.busy,"terminal private drain");}
 void cancel(bool rst=false){d.in_valid=d.input_done=0;if(rst)d.reset=1;else d.cancel=1;tick();d.reset=d.cancel=0;hold=false;for(unsigned n=0;n<160;++n){tick();need(!d.out_valid&&!d.busy&&!d.done,"old result after cancel/reset");}}
};
int main(int argc,char**argv){try{need(argc==3,"usage boundary.tsv seed");unsigned seed=unsigned(std::stoul(argv[2]));auto cases=load(argv[1]);Bench b(seed);unsigned rows=0,directed=0;const Case* ac=nullptr;
 for(const auto&c:cases){b.begin();b.feed(c);b.finish(c.error);++rows;if(!c.error&&c.name.find("ac")!=std::string::npos)ac=&c;}
 need(ac,"AC golden absent");
 // Multiple jobs, finite full queue, then cancellation with both slots owned.
 for(bool rst:{false,true}){b.begin();b.hold=true;b.feed(*ac,0);b.feed(*ac,1);b.feed(*ac,2);b.feed(*ac,3);for(unsigned n=0;n<400;++n)b.tick();need(b.high==2&&!b.d.in_ready&&b.d.count_completed_tiles==0,"finite results and bank backpressure");b.cancel(rst);++directed;}
 // Ordered queue drain and actual computation while an older output is held.
 b.begin();b.hold=true;b.feed(*ac,0);b.feed(*ac,1);for(unsigned n=0;n<400;++n)b.tick();need(b.d.out_valid&&b.d.count_launches==2,"second math under held first result");b.hold=false;b.feed(*ac,2);b.feed(*ac,3);b.finish();++directed;
 // Final coefficient EOF is deferred through real validate/commit edges.
 b.begin();b.feed(*ac);b.hold=true;b.d.input_done=1;for(unsigned n=0;n<400;++n)b.tick();need(!b.d.done&&b.d.out_valid,"held final output lost EOF ownership");b.hold=false;while(b.emitted<63)b.tick();b.hold=true;for(unsigned n=0;n<15;++n){b.tick();need(!b.d.done&&b.d.out_index==63,"held final tuple EOF");}b.hold=false;b.finish();++directed;
 for(unsigned count:{1U,7U,63U}){b.begin();b.feed(*ac,0,count);b.finish(4);b.cancel();++directed;}
 // Kill in accept, validate, commit, arithmetic, held result. Synchronous reset
 // and cancel both quarantine every old private owner before repeated IDs retry.
 for(unsigned phase=0;phase<7;++phase)for(bool rst:{false,true}){b.begin();b.hold=true;if(phase<3){b.feed(*ac,0,1);for(unsigned n=0;n<phase;++n)b.tick();}else{b.feed(*ac);for(unsigned n=0;n<(phase-3)*45;++n)b.tick();}b.cancel(rst);b.begin();b.feed(*ac);b.finish();++directed;}
 // Input priority and flags are interpreted from the accepted tuple, even while
 // live metadata/value pins subsequently change in the validation interval.
 for(unsigned kind=0;kind<4;++kind){b.begin();b.feed(*ac,0,1);for(unsigned n=0;n<3;++n)b.tick();b.d.in_valid=1;b.d.in_index=kind==0?3:1;b.d.in_qcell=kind==1?1:0;b.d.in_value=kind>=2?2049:0;if(kind==3)b.d.in_index=3;while(!b.tick()){}b.d.in_valid=0;b.d.in_index=0;b.d.in_qcell=0;b.d.in_value=0;for(unsigned n=0;n<3;++n)b.tick();need(b.d.error==(kind==0||kind==3?1U:kind==1?2U:3U),"snapshot fault priority");b.cancel();++directed;}
 need(b.overlap>0&&b.high==2,"overlap/full coverage absent");std::cout<<"{\"status\":\"TEST_PASS\",\"seed\":"<<seed<<",\"boundary_cases\":"<<rows<<",\"directed_checks\":"<<directed<<",\"cycles\":"<<b.cycle<<",\"accepted_inputs\":"<<b.total_inputs<<",\"committed_inputs\":"<<b.total_commits<<",\"residual_samples\":"<<b.total_outputs<<",\"max_result_occupancy\":"<<b.high<<",\"math_and_offered_output_cycles\":"<<b.overlap<<",\"full_result_cycles\":"<<b.full<<",\"max_eof_response_cycles\":"<<b.latency_max<<"}\n";return 0;
}catch(const std::exception&e){std::cerr<<"TEST_FAIL "<<e.what()<<"\n";return 1;}}
