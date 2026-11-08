#include "native/hud.hpp"
#include <fstream>
#include <sstream>
#include <iostream>
#include <iomanip>
#include <chrono>
#include <cassert>
static std::vector<uint8_t> unhex(const std::string&s){std::vector<uint8_t>b;for(size_t i=0;i<s.size();i+=2)b.push_back(uint8_t(std::stoul(s.substr(i,2),nullptr,16)));return b;}
int main(int argc,char**argv){assert(argc==2);std::ifstream f(argv[1]);assert(f);std::string line;
 while(std::getline(f,line)){std::istringstream row(line);std::string name,hex,expected;unsigned count,max;row>>name>>count>>max>>hex>>expected;assert(row);auto b=unhex(hex);cu66_port::Arena arena(98304);std::string result;
  {cu66_port::Scope scope(arena);try{cu66::Reader reader({b.data(),b.size()});auto out=cu66::huffman(reader,count,max);reader.end();std::ostringstream text;text<<"OK:";for(auto x:out)text<<std::hex<<std::setw(2)<<std::setfill('0')<<unsigned(x);result=text.str();if(expected!="-")assert(result=="OK:"+expected);}catch(const std::exception&e){result="ERR:"+std::string(e.what());if(expected!="-"){std::cerr<<name<<" unexpectedlyfailed "<<result<<"\n";return 3;}}}
  assert(arena.live==0);std::cout<<name<<"\t"<<result<<"\t"<<arena.peak<<"\t"<<arena.allocations<<"\n";
 }
}