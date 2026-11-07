#include "codec.hpp"
#include <chrono>
#include <iostream>
#include <sys/resource.h>
using namespace cu66;
using Clock=std::chrono::steady_clock;
static bool read32(uint32_t &value) {
  char bytes[4];std::cin.read(bytes,4);if(std::cin.gcount()==0)return false;
  need(std::cin.gcount()==4,"EC93 helper framing");value=0;
  for(unsigned i=0;i<4;++i)value|=uint32_t(uint8_t(bytes[i]))<<(8*i);
  return true;
}
static void write32(uint32_t value) {for(unsigned i=0;i<4;++i)std::cout.put(char(value>>(8*i)));}
template<class T> static void array_json(const T &values) {
  std::cout<<'[';for(size_t i=0;i<values.size();++i) {if(i)std::cout<<',';std::cout<<values[i];}std::cout<<']';
}
static void metrics(const cu93::DecodeStats &s) {
  std::cout<<",\"ab_decisions\":";array_json(s.ab_decisions);std::cout<<",\"ab_renorm\":";array_json(s.ab_renorm);
  std::cout<<",\"plain_bits\":";array_json(s.plain_bits);std::cout<<",\"group_headers\":";array_json(s.group_headers);
  std::cout<<",\"arithmetic_inits\":";array_json(s.arithmetic_inits);
}
static uint64_t elapsed(Clock::time_point start) {return uint64_t(std::chrono::duration_cast<std::chrono::nanoseconds>(Clock::now()-start).count());}
int main() {try {
  uint32_t blocks,length;
  while(read32(blocks)) {
    need(read32(length)&&blocks>=1&&blocks<=5400&&length>=46&&length<=46+128*blocks,"EC93 helper bounds");
    Bytes source(length);std::cin.read(reinterpret_cast<char*>(source.data()),length);need(size_t(std::cin.gcount())==length,"EC93 helper truncation");
    auto start=Clock::now();auto values=decode_ab38(source,blocks,1);uint64_t source_decode=elapsed(start);
    start=Clock::now();auto prepared=cu93::prepare(values);uint64_t preparation=elapsed(start);
    need(prepared.ab.packet==source,"EC93 exact frozen AB re-encoding");need(cu88::decode_br88(prepared.br.packet,blocks,1)==values,"EC93 frozen BR decode parity");
    std::array<unsigned,5> selectors{0,85,170,255,cu93::local_selector(prepared)};
    std::array<Bytes,5> candidates;std::array<std::string,5> hashes;std::array<cu93::DecodeStats,5> decoded_stats;
    start=Clock::now();for(unsigned i=0;i<5;++i)candidates[i]=cu93::assemble(prepared,selectors[i]);uint64_t assembly=elapsed(start);
    start=Clock::now();for(unsigned i=0;i<5;++i)hashes[i]=hex(sha256(candidates[i]));uint64_t hashing=elapsed(start);
    start=Clock::now();for(unsigned i=0;i<5;++i) {
      need(cu93::decode_ec93(candidates[i],blocks,1,&decoded_stats[i])==values,"EC93 native coefficient parity");
      if(!candidates[i][5])for(unsigned context=0;context<4;++context) {
        const auto &expected=prepared.metrics[(selectors[i]>>(2*context))&3];const auto &actual=decoded_stats[i];
        need(actual.ab_decisions[context]==expected.ab_decisions[context]&&actual.ab_renorm[context]==expected.ab_renorm[context]&&actual.plain_bits[context]==expected.plain_bits[context]&&actual.group_headers[context]==expected.group_headers[context]&&actual.arithmetic_inits[context]==expected.arithmetic_inits[context],"EC93 decoder metrics parity");
      }
    }
    uint64_t validation=elapsed(start);Bytes coefficients;for(auto value:values)cu85::put16(coefficients,uint16_t(value));
    std::cout<<"{\"blocks\":"<<blocks<<",\"old_bytes\":"<<source.size()<<",\"coefficient_sha256\":\""<<hex(sha256(coefficients))<<"\",\"source_raw_fallback\":"<<(prepared.source_raw_fallback?"true":"false")<<",\"source_decode_ns\":"<<source_decode<<",\"prepare_ns\":"<<preparation<<",\"assemble_ns\":"<<assembly<<",\"hash_ns\":"<<hashing<<",\"generation_ns\":"<<(source_decode+preparation+assembly+hashing)<<",\"validate_ns\":"<<validation;
    std::cout<<",\"method_stream_bytes\":[";
    for(unsigned method=0;method<4;++method) {if(method)std::cout<<',';std::array<size_t,4> sizes{};for(unsigned c=0;c<4;++c)sizes[c]=prepared.streams[method][c].size();array_json(sizes);}
    std::cout<<"],\"suffix_histogram_run_dc_level_lsb_position_zero_one\":[";
    for(unsigned type=0;type<2;++type) {if(type)std::cout<<',';std::cout<<'[';for(unsigned p=0;p<24;++p) {if(p)std::cout<<',';array_json(prepared.suffix_histogram[type][p]);}std::cout<<']';}
    std::cout<<"],\"methods\":[";
    for(unsigned method=0;method<4;++method) {if(method)std::cout<<',';std::cout<<"{\"method\":"<<method;metrics(prepared.metrics[method]);std::cout<<'}';}
    std::cout<<"],\"masks\":[";
    for(unsigned i=0;i<5;++i) {
      const auto &packet=candidates[i];if(i)std::cout<<',';
      std::cout<<"{\"requested_selector\":"<<selectors[i]<<",\"wire_selector\":"<<unsigned(packet[6])<<",\"raw\":"<<(packet[5]?"true":"false")<<",\"bytes\":"<<packet.size()<<",\"sha256\":\""<<hashes[i]<<"\",\"methods\":[";
      for(unsigned context=0;context<4;++context) {if(context)std::cout<<',';std::cout<<((selectors[i]>>(2*context))&3);}std::cout<<']';metrics(decoded_stats[i]);std::cout<<'}';
    }
    std::cout<<"]}"<<std::endl;
    for(const auto &packet:candidates) {write32(uint32_t(packet.size()));std::cout.write(reinterpret_cast<const char*>(packet.data()),std::streamsize(packet.size()));}std::cout.flush();
  }
  struct rusage usage{};need(getrusage(RUSAGE_SELF,&usage)==0,"EC93 native RSS query");std::cerr<<"EC93_NATIVE_PEAK_RSS_KIB "<<usage.ru_maxrss<<'\n';return 0;
} catch(const std::exception &error) {std::cerr<<"EC93_HELPER_FAIL "<<error.what()<<std::endl;return 1;}}
