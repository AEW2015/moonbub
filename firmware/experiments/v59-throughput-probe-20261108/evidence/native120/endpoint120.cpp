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
int main(int argc,char**argv){try{
  cu66::need(argc==3,"sequence directory and count");std::string dir=argv[1];const auto count=std::stoul(argv[2]);cu66::need(count>=3&&count<=120,"count3..120");v34::Endpoint endpoint(98304);Bytes output(42276);
  auto transact=[&](const Bytes& req){auto n=endpoint.transact({req.data(),req.size()},output.data(),output.size());cu66::need(n>=36&&v34::u32(output.data()+28)==0,"native status");return n;};
  for(uint32_t fid=0;fid<count;fid++){
    std::string name="frame"+std::string(fid<10?"00":fid<100?"0":"")+std::to_string(fid);auto prepare=file(dir+"/"+name+".prepare");auto golden=file(dir+"/"+name+".hud");
    auto gen=v34::u64(prepare.data()+12);auto rid=v34::u32(prepare.data()+24);transact(prepare);
    Bytes range(8);v34::put32(range.data()+4,21120);auto n=transact(request(3,gen,fid,rid,0,range));
    cu66::need(n==42276&&golden.size()==42240&&std::equal(golden.begin(),golden.end(),output.begin()+32),"actual HUD words");
    Bytes ack(20);v34::put32(ack.data(),21120);std::copy(endpoint.gate->status().tag.begin(),endpoint.gate->status().tag.end(),ack.begin()+4);
    transact(request(4,gen,fid,rid,1,ack));transact(request(5,gen,fid,rid,0,{}));
    cu66::need(endpoint.arena.failures==0,"arena allocation failure");
  }
  unsigned faults=0;
  for(uint32_t target=0;target<count;target++){
    v34::Endpoint isolated(98304);Bytes local(42276);
    auto call=[&](const Bytes& req,uint32_t expected){auto n=isolated.transact({req.data(),req.size()},local.data(),local.size());cu66::need(n>=36&&v34::u32(local.data()+28)==expected,"fault reply");};
    auto commit=[&](const Bytes& prep){auto gen=v34::u64(prep.data()+12);auto fid=v34::u32(prep.data()+20);auto rid=v34::u32(prep.data()+24);Bytes ack(20);v34::put32(ack.data(),21120);std::copy(isolated.gate->status().tag.begin(),isolated.gate->status().tag.end(),ack.begin()+4);call(request(4,gen,fid,rid,1,ack),0);call(request(5,gen,fid,rid,0,{}),0);};
    for(uint32_t fid=0;fid<target;fid++){auto prep=file(dir+"/frame"+std::string(fid<10?"00":fid<100?"0":"")+std::to_string(fid)+".prepare");call(prep,0);commit(prep);}
    auto prep=file(dir+"/frame"+std::string(target<10?"00":target<100?"0":"")+std::to_string(target)+".prepare");
    auto before=isolated.gate->accepted();Bytes accepted;
    if(before)for(const auto&patch:before->patches)for(auto w:patch.words){accepted.push_back(uint8_t(w));accepted.push_back(uint8_t(w>>8));}
    auto malformed=prep;malformed.back()^=1;bool threw=false;try{isolated.transact({malformed.data(),malformed.size()},local.data(),local.size());}catch(const std::exception&){threw=true;}
    cu66::need(threw&&isolated.gate->accepted()==before&&!isolated.gate->candidate_ready(),"malformed HC rollback");faults++;
    malformed=prep;malformed[malformed.size()-5]^=1;v34::put32(malformed.data()+malformed.size()-4,cu66::crc32({malformed.data(),malformed.size()-4}));call(malformed,4);
    cu66::need(isolated.gate->accepted()==before&&!isolated.gate->candidate_ready(),"HUD late-failure rollback");Bytes after;
    if(before)for(const auto&patch:before->patches)for(auto w:patch.words){after.push_back(uint8_t(w));after.push_back(uint8_t(w>>8));}
    cu66::need(accepted==after,"accepted words mutated");before.reset();faults++;
    v34::put64(prep.data()+12,v34::u64(prep.data()+12)+1000);v34::put32(prep.data()+prep.size()-4,cu66::crc32({prep.data(),prep.size()-4}));call(prep,0);commit(prep);
    cu66::need(isolated.gate->accepted()->id==target&&isolated.arena.failures==0,"new generation recovery");
  }
  std::cout<<"{\"frames\":"<<count<<",\"HUD_words\":"<<count*21120<<",\"arena_cap\":98304,\"arena_peak\":"<<endpoint.arena.peak<<",\"allocation_failures\":"<<endpoint.arena.failures<<",\"malformed_and_late_failure_checks\":"<<faults<<",\"recovery_checks\":"<<count<<"}\n";return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<"\n";return 1;}}
