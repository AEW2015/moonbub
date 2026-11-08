// Actual native HC70 evidence mode and rollback regression; no hardware.
#include "../native/endpoint.hpp"
#include <array>
#include <cassert>
#include <fstream>
#include <iterator>
#include <iostream>
static std::vector<uint8_t> load(const std::string&p){std::ifstream f(p,std::ios::binary);assert(f);return {std::istreambuf_iterator<char>(f),{}};}
static uint32_t call(v34::Endpoint&e,uint8_t op,uint64_t gen,uint32_t fid,uint32_t ref,uint32_t arg,const std::vector<uint8_t>&payload,std::array<uint8_t,1060>&out){
 std::vector<uint8_t>w(payload.size()+36);std::memcpy(w.data(),"HC70",4);w[4]=1;w[5]=op;v34::put32(w.data()+8,payload.size());v34::put64(w.data()+12,gen);v34::put32(w.data()+20,fid);v34::put32(w.data()+24,ref);v34::put32(w.data()+28,arg);std::copy(payload.begin(),payload.end(),w.begin()+32);v34::put32(w.data()+w.size()-4,cu66::crc32({w.data(),w.size()-4}));e.transact({w.data(),w.size()},out.data(),out.size());return v34::u32(out.data()+28);
}
static std::vector<uint8_t> hu(const std::vector<uint8_t>&w){return {w.begin()+32,w.end()-4};}
int main(int argc,char**argv){assert(argc==2);std::string root=argv[1];auto key=hu(load(root+"/prepare0.bin"));auto delta=hu(load(root+"/prepare1.bin"));std::array<uint8_t,1060>out{};
 for(uint32_t mode:{1u,2u}){
  v34::Endpoint e(98304);assert(call(e,1,1,0,0xffffffffu,1,key,out)==0);assert((out[33]&1)!=0&&(out[33]&32)==0);std::vector<uint8_t>ack(20);v34::put32(ack.data(),21120);std::copy(out.begin()+56,out.begin()+72,ack.begin()+4);
  assert(call(e,5,1,0,0xffffffffu,0,{},out)!=0); // Writer assertion is mandatory.
  for(uint32_t invalid:{0u,3u})assert(call(e,4,1,0,0xffffffffu,invalid,ack,out)!=0);
  auto bad=ack;v34::put32(bad.data(),21119);assert(call(e,4,1,0,0xffffffffu,mode,bad,out)!=0);
  bad=ack;bad[4]^=1;assert(call(e,4,1,0,0xffffffffu,mode,bad,out)!=0);
  assert(call(e,4,2,0,0xffffffffu,mode,ack,out)!=0);assert(call(e,4,1,1,0xffffffffu,mode,ack,out)!=0);assert(call(e,4,1,0,0,mode,ack,out)!=0);
  assert(!e.gate->candidate_transferred());assert(call(e,4,1,0,0xffffffffu,mode,ack,out)==0);assert(bool(out[33]&32)==(mode==2));assert((out[33]&15)==15);
  assert(call(e,4,1,0,0xffffffffu,mode,ack,out)==0); // Same evidence retry is idempotent.
  assert(call(e,4,1,0,0xffffffffu,mode==2?1:2,ack,out)!=0);assert(bool(out[33]&32)==(mode==2));
  assert(call(e,5,1,0,0xffffffffu,0,{},out)==0);assert(out[32]==3);assert(bool(out[33]&32)==(mode==2));auto accepted=e.gate->accepted();assert(accepted&&accepted->id==0);
  // Provisional P frame can be acknowledged then aborted without cache mutation.
  assert(call(e,1,2,1,0,0,delta,out)==0);assert((out[33]&32)==0);std::copy(out.begin()+56,out.begin()+72,ack.begin()+4);
  assert(call(e,4,2,1,0,2,ack,out)==0);assert(call(e,6,2,1,0,0,{},out)==0);assert((out[33]&63)==16);assert(e.gate->accepted().get()==accepted.get());assert(e.gate->status().external_completion_evidence==0);assert(call(e,5,2,1,0,0,{},out)!=0);
  assert(call(e,1,2,1,0,0,delta,out)==2);assert(e.gate->accepted().get()==accepted.get());
  std::cout<<"PASS HC70 mode="<<mode<<" identity_count_tag_reject retry evidence_no_relabel abort_rollback stale_generation\n";
 }
}

