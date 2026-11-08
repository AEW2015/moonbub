#include "hud.hpp"
#include <fstream>
#include <sstream>
#include <iostream>
#include <vector>
#include <string>
static std::vector<uint8_t> read(const std::string&p){std::ifstream f(p,std::ios::binary);if(!f)throw std::runtime_error("open "+p);return {std::istreambuf_iterator<char>(f),{}};}
static uint16_t u16(const std::vector<uint8_t>&b,size_t i){return uint16_t(b.at(2*i))|(uint16_t(b.at(2*i+1))<<8);}
int main(int argc,char**argv){try{if(argc!=2)throw std::runtime_error("index required");std::string index=argv[1],dir=index.substr(0,index.find_last_of("/\\")+1);std::ifstream f(index);std::string line;unsigned cases=0,accepted=0,rejected=0;uint64_t compared=0;
while(std::getline(f,line)){if(line.empty())continue;std::stringstream ss(line);std::vector<std::string>v;std::string x;while(std::getline(ss,x,'\t'))v.push_back(x);if(v.size()!=7)throw std::runtime_error("seven TSV fields");auto packet=read(dir+v[1]);auto ref=v[2]=="-"?std::vector<uint8_t>{}:read(dir+v[2]);auto want=v[3]=="-"?std::vector<uint8_t>{}:read(dir+v[3]);unsigned w=std::stoul(v[4]),h=std::stoul(v[5]);bool success=v[6]=="1";
cu66_port::Arena arena(262144);cu66_port::Scope scope(arena);cu66::Patch reference;reference.rect={0,0,uint16_t(w),uint16_t(h)};if(!ref.empty()){reference.words.resize(ref.size()/2);for(size_t i=0;i<reference.words.size();i++)reference.words[i]=u16(ref,i);}bool did=false;std::string reason;
try{auto output=cu66::decode_patch({packet.data(),packet.size()},ref.empty()?nullptr:&reference,w,h);did=true;if(!success)throw std::runtime_error("unexpected accept "+v[0]);if(output.size()*2!=want.size())throw std::runtime_error("output size");for(size_t i=0;i<output.size();i++){if(output[i]!=u16(want,i))throw std::runtime_error("word mismatch "+v[0]);compared++;}}
catch(const cu66_port::Error&e){reason=e.what();if(success)throw std::runtime_error("unexpected reject "+v[0]+": "+reason);}
for(size_t i=0;i<reference.words.size();i++)if(reference.words[i]!=u16(ref,i))throw std::runtime_error("mutated reference");if(did)accepted++;else rejected++;cases++;std::cout<<"CASE_PASS name="<<v[0]<<" accepted="<<did<<" peak="<<arena.peak<<" maximum="<<arena.maximum<<" allocations="<<arena.allocations<<" reason="<<reason<<"\n";
}
std::cout<<"NATIVE_PASS cases="<<cases<<" accepted="<<accepted<<" rejected="<<rejected<<" words_compared="<<compared<<" reference_unchanged=1\n";return 0;}catch(const std::exception&e){std::cerr<<"FAIL "<<e.what()<<"\n";return 1;}}
