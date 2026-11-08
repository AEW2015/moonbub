#include "endpoint.hpp"
#include <fstream>
#include <iostream>
using Bytes=std::vector<uint8_t>;
Bytes file(const std::string&p){std::ifstream f(p,std::ios::binary);cu66::need(bool(f),"open");return {std::istreambuf_iterator<char>(f),{}};}
Bytes request(uint8_t op,uint64_t gen,uint32_t fid,uint32_t rid,uint32_t arg,const Bytes&payload){
  Bytes b(36+payload.size());std::memcpy(b.data(),"HC70",4);b[4]=1;b[5]=op;
  v34::put32(b.data()+8,payload.size());v34::put64(b.data()+12,gen);v34::put32(b.data()+20,fid);v34::put32(b.data()+24,rid);v34::put32(b.data()+28,arg);
  std::copy(payload.begin(),payload.end(),b.begin()+32);v34::put32(b.data()+b.size()-4,cu66::crc32({b.data(),b.size()-4}));return b;
}
static cu66_port::Arena* owner=nullptr;
static size_t wire_held=0,min_free_all=SIZE_MAX,min_free_frame=SIZE_MAX,probe_calls=0;
static unsigned frame=0,mode=0,component=99,planned=0,components=0,max_post=0,late_fixed=0;static bool begun=false;
static bool constrained(){return begun&&((mode==1&&frame==17&&component==1)||(mode==2&&frame==17)||(mode==3));}
void* v58_test_malloc(size_t n){return constrained()&&n>7168?nullptr:std::malloc(n);}
void v58_note_allocation(size_t element,size_t n){if(begun){max_post=std::max(max_post,unsigned(n));if(element==2&&n>=7680)++late_fixed;}else if(element==2&&n>=7680){const size_t wanted[4]={15360,11520,7680,7680};cu66::need(planned<4&&n==wanted[planned],"preplan order");++planned;}if(n>=7168)std::cout<<"ALLOC frame="<<frame<<" begun="<<begun<<" component="<<component<<" element="<<element<<" bytes="<<n<<" live="<<(owner?owner->live:0)<<"\n";}
void v58_component_begin(unsigned i){if(PREPLANNED)cu66::need(planned==4,"four private outputs before transients");begun=true;component=i;++components;}
static size_t probe(){const size_t used=wire_held+(owner?owner->live:0);const size_t free=used>116272?0:116272-used;min_free_all=std::min(min_free_all,free);min_free_frame=std::min(min_free_frame,free);++probe_calls;return free;}
static size_t largest(){return constrained()?7168:116272;}
int main(int argc,char**argv){try{
  cu66::need(argc==4,"sequence directory count mode");mode=std::stoul(argv[3]);std::string dir=argv[1];const auto count=std::stoul(argv[2]);cu66::need(count>=3&&count<=40,"count3..40");v34::Endpoint endpoint(98304);owner=&endpoint.arena;endpoint.arena.free_probe=probe;endpoint.arena.reserve=8192;endpoint.arena.largest_probe=largest;Bytes output(42276);
  auto transact=[&](const Bytes& req){auto n=endpoint.transact({req.data(),req.size()},output.data(),output.size());cu66::need(n>=36&&v34::u32(output.data()+28)==0,"native status");return n;};
  for(uint32_t fid=0;fid<count;fid++){frame=fid;begun=false;component=99;planned=0;components=0;max_post=0;late_fixed=0;
    std::string name="frame"+std::string(fid<10?"00":"0")+std::to_string(fid);auto prepare=file(dir+"/"+name+".prepare");auto golden=file(dir+"/"+name+".hud");
    auto gen=v34::u64(prepare.data()+12);auto rid=v34::u32(prepare.data()+24);wire_held=prepare.size();min_free_frame=SIZE_MAX;probe_calls=0;endpoint.arena.peak=endpoint.arena.live;
    auto reply_n=endpoint.transact({prepare.data(),prepare.size()},output.data(),output.size());cu66::need(reply_n>=36,"reply length");auto status=v34::u32(output.data()+28);const auto failure=endpoint.arena.last_failure;
    const long long post_margin=116272ll-static_cast<long long>(wire_held)-static_cast<long long>(endpoint.arena.peak)-8192ll;
    std::cout<<"RESERVE_FRAME frame="<<fid<<" status="<<status<<" wire="<<wire_held<<" native_peak="<<endpoint.arena.peak<<" live="<<endpoint.arena.live<<" min_callback_free="<<min_free_frame<<" min_postallocation_margin="<<post_margin<<" probes="<<probe_calls<<" failure_kind="<<failure.kind<<" requested="<<failure.requested<<" failure_live="<<failure.live<<" failure_free="<<failure.free<<"\n";
    if(status!=0){std::cout<<"RESERVE_SEQUENCE_REFUSED first_frame="<<fid<<" prior_accepted="<<(endpoint.gate->accepted()?endpoint.gate->accepted()->id:0xffffffffu)<<"\n";return 2;}
    std::cout<<"PLAN frame="<<fid<<" planned="<<planned<<" components="<<components<<" late_fixed="<<late_fixed<<" max_post="<<max_post<<"\n";if(PREPLANNED)cu66::need(planned==4&&components==4&&late_fixed==0,"allocation lifetime plan");begun=false;wire_held=0;
    Bytes range(8);v34::put32(range.data()+4,21120);auto n=transact(request(3,gen,fid,rid,0,range));
    cu66::need(n==42276&&golden.size()==42240&&std::equal(golden.begin(),golden.end(),output.begin()+32),"actual HUD words");
    Bytes ack(20);v34::put32(ack.data(),21120);std::copy(endpoint.gate->status().tag.begin(),endpoint.gate->status().tag.end(),ack.begin()+4);
    transact(request(4,gen,fid,rid,1,ack));transact(request(5,gen,fid,rid,0,{}));
    cu66::need(endpoint.arena.failures==0,"arena allocation failure");
  }
  std::cout<<"RESERVE_SEQUENCE_PASS frames="<<count<<" min_free="<<min_free_all<<"\n"; return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<"\n";return 1;}}
