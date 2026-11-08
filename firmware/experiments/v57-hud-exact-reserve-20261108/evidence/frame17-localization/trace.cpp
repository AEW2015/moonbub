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
static unsigned ordinal=0,target=0,seen7680=0;static bool inject=false;
extern "C" __declspec(dllimport) unsigned short __stdcall RtlCaptureStackBackTrace(unsigned long,unsigned long,void**,unsigned long*);
extern "C" __declspec(dllimport) void* __stdcall GetModuleHandleA(const char*);
void cu66_allocation_observer(size_t n){if(ordinal==17&&n==7680){++seen7680;void* frames[24];auto count=RtlCaptureStackBackTrace(0,24,frames,nullptr);auto base=reinterpret_cast<uintptr_t>(GetModuleHandleA(nullptr));std::cerr<<"ALLOCATION7680 frame="<<ordinal<<" allocation_index="<<seen7680<<" live="<<(owner?owner->live:0)<<" base="<<std::hex<<base<<std::dec<<"\n";for(unsigned i=0;i<count;i++)std::cerr<<"STACK "<<std::hex<<(reinterpret_cast<uintptr_t>(frames[i])-base+0x140000000ull)<<std::dec<<"\n";}}
void* cu66_test_malloc(size_t n){if(inject&&ordinal==17&&n==7680&&seen7680==target)return nullptr;return std::malloc(n);}
static size_t largest(){return inject&&ordinal==17&&seen7680==target?7168:116272;}

static size_t wire_held=0,min_free_all=SIZE_MAX,min_free_frame=SIZE_MAX,probe_calls=0;
static size_t probe(){const size_t used=wire_held+(owner?owner->live:0);const size_t available=used>116272?0:116272-used;min_free_all=std::min(min_free_all,available);min_free_frame=std::min(min_free_frame,available);++probe_calls;return available;}
int main(int argc,char**argv){try{
  cu66::need(argc==4,"sequence directory count andinject");target=std::stoul(argv[3]);inject=target!=0;std::string dir=argv[1];const auto count=std::stoul(argv[2]);cu66::need(count>=3&&count<=40,"count3..40");v34::Endpoint endpoint(98304);owner=&endpoint.arena;endpoint.arena.free_probe=probe;endpoint.arena.reserve=8192;endpoint.arena.largest_probe=largest;Bytes output(42276);
  auto transact=[&](const Bytes& req){auto n=endpoint.transact({req.data(),req.size()},output.data(),output.size());cu66::need(n>=36&&v34::u32(output.data()+28)==0,"native status");return n;};
  for(uint32_t fid=0;fid<count;fid++){ordinal=fid;
    std::string name="frame"+std::string(fid<10?"00":"0")+std::to_string(fid);auto prepare=file(dir+"/"+name+".prepare");auto golden=file(dir+"/"+name+".hud");
    auto gen=v34::u64(prepare.data()+12);auto rid=v34::u32(prepare.data()+24);wire_held=prepare.size();min_free_frame=SIZE_MAX;probe_calls=0;endpoint.arena.peak=endpoint.arena.live;
    auto reply_n=endpoint.transact({prepare.data(),prepare.size()},output.data(),output.size());cu66::need(reply_n>=36,"reply length");auto status=v34::u32(output.data()+28);const auto failure=endpoint.arena.last_failure;
    const long long post_margin=116272ll-static_cast<long long>(wire_held)-static_cast<long long>(endpoint.arena.peak)-8192ll;
    std::cout<<"RESERVE_FRAME frame="<<fid<<" status="<<status<<" wire="<<wire_held<<" native_peak="<<endpoint.arena.peak<<" live="<<endpoint.arena.live<<" min_callback_free="<<min_free_frame<<" min_postallocation_margin="<<post_margin<<" probes="<<probe_calls<<" failure_kind="<<failure.kind<<" requested="<<failure.requested<<" failure_live="<<failure.live<<" failure_free="<<failure.free<<" failure_largest="<<failure.largest<<" failure_probes="<<failure.probes<<"\n";
    if(status!=0){std::cout<<"RESERVE_SEQUENCE_REFUSED first_frame="<<fid<<" prior_accepted="<<(endpoint.gate->accepted()?endpoint.gate->accepted()->id:0xffffffffu)<<"\n";return 2;}
    wire_held=0;
    Bytes range(8);v34::put32(range.data()+4,21120);auto n=transact(request(3,gen,fid,rid,0,range));
    cu66::need(n==42276&&golden.size()==42240&&std::equal(golden.begin(),golden.end(),output.begin()+32),"actual HUD words");
    Bytes ack(20);v34::put32(ack.data(),21120);std::copy(endpoint.gate->status().tag.begin(),endpoint.gate->status().tag.end(),ack.begin()+4);
    transact(request(4,gen,fid,rid,1,ack));transact(request(5,gen,fid,rid,0,{}));
    cu66::need(endpoint.arena.failures==0,"arena allocation failure");
  }
  std::cout<<"RESERVE_SEQUENCE_PASS frames="<<count<<" maximum_request="<<endpoint.arena.maximum<<" min_free="<<min_free_all<<"\n"; return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<"\n";return 1;}}
