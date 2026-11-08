// Semantic regression only: actual final V44 endpoint, historical native corpus.
#include "C:/moon/publish/firmware/experiments/v47-dy71-hud-order-20261107/native/endpoint.hpp"
#include <fstream>
#include <iterator>
#include <iostream>
#include <sstream>
#include <iomanip>

using Bytes=std::vector<uint8_t>;
static Bytes read(const std::string&p){std::ifstream f(p,std::ios::binary);if(!f)throw std::runtime_error(p);return Bytes{std::istreambuf_iterator<char>(f),{}};}
static uint32_t call(v34::Endpoint&e,uint8_t op,uint32_t f,uint32_t ref,uint32_t arg,const Bytes&payload,Bytes&out){
 Bytes req(36+payload.size());std::memcpy(req.data(),"HC70",4);req[4]=1;req[5]=op;v34::put32(req.data()+8,payload.size());v34::put64(req.data()+12,f+1);v34::put32(req.data()+20,f);v34::put32(req.data()+24,ref);v34::put32(req.data()+28,arg);std::copy(payload.begin(),payload.end(),req.begin()+32);v34::put32(req.data()+req.size()-4,cu66::crc32(cu66::View(req.data(),req.size()-4)));e.transact(cu66::View(req.data(),req.size()),out.data(),out.size());return v34::u32(out.data()+28);
}
int main(int argc,char**argv){
 if(argc!=2){return 2;}
 std::ifstream manifest(argv[1]);if(!manifest){return 3;}
 std::string scene,line,active;std::unique_ptr<v34::Endpoint> endpoint;unsigned frames=0;size_t peak=0;
 while(std::getline(manifest,line)){
  std::istringstream row(line);std::string path,expected;unsigned frame;row>>scene>>frame>>path>>expected;if(!row){return 4;}
  if(scene!=active){endpoint=std::make_unique<v34::Endpoint>(1024*1024);active=scene;}
  auto packet=read(path);auto ref=v34::u32(packet.data()+12);auto nb=v34::u32(packet.data()+68);Bytes hu(packet.begin()+76+nb,packet.end()-4),out(42276);
  auto code=call(*endpoint,1,frame,ref,(packet[5]&1)?1:0,hu,out);if(code!=0){std::cerr<<"PREPARE_FAIL "<<scene<<" "<<frame<<" code"<<code<<"\n";return 5;}
  Bytes tag(out.begin()+56,out.begin()+72);Bytes readarg(8);v34::put32(readarg.data()+4,21120);
  if(call(*endpoint,3,frame,ref,0,readarg,out)!=0){return 6;}
  cu66::SHA256 sha;sha.update(cu66::View(out.data()+32,42240));auto digest=sha.finish();std::ostringstream text;for(auto v:digest){text<<std::hex<<std::setw(2)<<std::setfill('0')<<unsigned(v);}
  if(text.str()!=expected){std::cerr<<"GOLDEN_FAIL "<<scene<<" "<<frame<<"\n";return 7;}
  Bytes ack(20);v34::put32(ack.data(),21120);std::copy(tag.begin(),tag.end(),ack.begin()+4);
  if(call(*endpoint,4,frame,ref,1,ack,out)!=0||call(*endpoint,5,frame,ref,0,{},out)!=0){return 8;}
  peak=std::max(peak,endpoint->arena.peak);++frames;
 }
 auto key=read("C:/moon/maintenance/streaming-verification-20261107/three-frame-fixtures/frame0.cu66");auto nb=v34::u32(key.data()+68);Bytes original(key.begin()+76+nb,key.end()-4);unsigned invalid=0;
 for(unsigned which=0;which<3;++which){
  auto hu=original;
  if(which==0){hu[18]^=1;}
  if(which==1){auto length=v34::u32(hu.data()+54);hu[106+5]=255;v34::put32(hu.data()+106+length-4,cu66::crc32(cu66::View(hu.data()+106,length-4)));}
  if(which==2){hu[106+12]^=1;}
  v34::put32(hu.data()+hu.size()-4,cu66::crc32(cu66::View(hu.data(),hu.size()-4)));
  v34::Endpoint bad(1024*1024);Bytes out(42276);auto code=call(bad,1,0,0xffffffffu,1,hu,out);
  if(code==0||bad.gate->candidate_ready()||bad.gate->accepted()){std::cerr<<"MALFORMED_ACCEPTED "<<which<<"\n";return 9;}++invalid;
 }
 std::cout<<"NATIVE_CORPUS_GOLDEN_PASS frames"<<frames<<" words"<<size_t(frames)*21120<<" semantic_host_cap1048576 peak"<<peak<<" malformed_rejections"<<invalid<<"\n";
}
