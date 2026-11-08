#include "decoder.hpp"
#include <fstream>
#include <iostream>
#include <string>
using namespace cu66;
Bytes read_file(const std::string&p){std::ifstream f(p,std::ios::binary);need(bool(f),"packet open");return Bytes(std::istreambuf_iterator<char>(f),{});}
void write_file(const std::string&p,const Bytes&b){std::ofstream f(p,std::ios::binary);need(bool(f),"golden output open");f.write(reinterpret_cast<const char*>(b.data()),b.size());need(bool(f),"golden output complete");}
int main(int argc,char**argv){try{need(argc==3,"package output");Decoder d;for(unsigned i=0;i<12;++i){char n[32];std::snprintf(n,sizeof n,"frame%03u.cu66",i);auto f=d.receive(read_file(std::string(argv[1])+"/"+n));need(f->id==i,"frame identity");Bytes planes,hud;for(const auto&p:f->planes)planes.insert(planes.end(),p.begin(),p.end());for(const auto&p:f->hud){auto w=word_bytes(p.words);hud.insert(hud.end(),w.begin(),w.end());}auto display=word_bytes(f->display);need(planes.size()==518400&&hud.size()==42240&&display.size()==691200,"golden dimensions");std::string base=std::string(argv[2])+"/frame"+std::to_string(i);write_file(base+".canonical.u16",planes);write_file(base+".hud",hud);write_file(base+".rgb565",display);std::cout<<"GOLDEN id="<<i<<" yuv="<<hex(sha256(planes))<<" hud="<<hex(sha256(hud))<<" display="<<hex(sha256(display))<<"\n";}return 0;}catch(const std::exception&e){std::cerr<<e.what()<<"\n";return 1;}}
