#include "codec.hpp"
#include <chrono>
#include <iostream>
#include <sys/resource.h>
using namespace cu66;
using Clock=std::chrono::steady_clock;
static bool read32(uint32_t &value) {
  char bytes[4];std::cin.read(bytes,4);if(std::cin.gcount()==0)return false;
  need(std::cin.gcount()==4,"EC94 helper framing");value=0;
  for(unsigned i=0;i<4;++i)value|=uint32_t(uint8_t(bytes[i]))<<(8*i);
  return true;
}
static void write32(uint32_t value) {for(unsigned i=0;i<4;++i)std::cout.put(char(value>>(8*i)));}
template<class T> static void array_json(const T &values) {
  std::cout<<'[';for(size_t i=0;i<values.size();++i) {if(i)std::cout<<',';std::cout<<values[i];}std::cout<<']';
}
static void metrics(const cu94::DecodeStats &s) {
#define METRIC(name) std::cout<<",\"" #name "\":";array_json(s.name);
  METRIC(ab_decisions) METRIC(ab_renorm) METRIC(literal_bits) METRIC(ans_symbols)
  METRIC(ans_renorm_bytes) METRIC(model_tables) METRIC(model_entries) METRIC(ans_lanes)
#undef METRIC
}
static uint64_t elapsed(Clock::time_point start) {return uint64_t(std::chrono::duration_cast<std::chrono::nanoseconds>(Clock::now()-start).count());}
int main() {try {
  uint32_t blocks,length;
  while(read32(blocks)) {
    need(read32(length)&&blocks>=1&&blocks<=5400&&length>=46&&length<=46+128*blocks,"EC94 helper bounds");
    Bytes source(length);std::cin.read(reinterpret_cast<char*>(source.data()),length);need(size_t(std::cin.gcount())==length,"EC94 helper truncation");
    auto start=Clock::now();auto values=decode_ab38(source,blocks,1);uint64_t source_decode=elapsed(start);
    start=Clock::now();auto prepared=cu94::prepare(values);uint64_t preparation=elapsed(start);
    need(prepared.ab.packet==source,"EC94 exact frozen AB re-encoding");need(cu88::decode_br88(prepared.br.packet,blocks,1)==values,"EC94 frozen BR decode parity");
    std::array<cu94::Choices,9> choices{};
    for(unsigned i=0;i<8;++i) {choices[i].fill(i);}choices[8]=cu94::local_choices(prepared);
    std::array<unsigned,9> selectors{};for(unsigned i=0;i<9;++i)selectors[i]=cu94::wire_selector(choices[i]);
    std::array<Bytes,9> candidates;std::array<std::string,9> hashes;std::array<cu94::DecodeStats,9> decoded_stats;
    start=Clock::now();for(unsigned i=0;i<9;++i)candidates[i]=cu94::assemble(prepared,choices[i]);uint64_t assembly=elapsed(start);
    start=Clock::now();for(unsigned i=0;i<9;++i)hashes[i]=hex(sha256(candidates[i]));uint64_t hashing=elapsed(start);
    start=Clock::now();for(unsigned i=0;i<9;++i) {
      need(cu94::decode_ec94(candidates[i],blocks,1,&decoded_stats[i])==values,"EC94 native coefficient parity");
      if(!candidates[i][5])for(unsigned context=0;context<4;++context) {
        const auto &expected=prepared.metrics[choices[i][context]];const auto &actual=decoded_stats[i];
        need(actual.ab_decisions[context]==expected.ab_decisions[context]&&actual.ab_renorm[context]==expected.ab_renorm[context]&&actual.literal_bits[context]==expected.literal_bits[context]&&actual.ans_symbols[context]==expected.ans_symbols[context]&&actual.ans_renorm_bytes[context]==expected.ans_renorm_bytes[context]&&actual.model_tables[context]==expected.model_tables[context]&&actual.model_entries[context]==expected.model_entries[context]&&actual.ans_lanes[context]==expected.ans_lanes[context],"EC94 decoder metrics parity");
      }
    }
    uint64_t validation=elapsed(start);Bytes coefficients;for(auto value:values)cu85::put16(coefficients,uint16_t(value));
    std::cout<<"{\"blocks\":"<<blocks<<",\"old_bytes\":"<<source.size()<<",\"coefficient_sha256\":\""<<hex(sha256(coefficients))<<"\",\"source_raw_fallback\":"<<(prepared.source_raw_fallback?"true":"false")<<",\"source_decode_ns\":"<<source_decode<<",\"prepare_ns\":"<<preparation<<",\"assemble_ns\":"<<assembly<<",\"hash_ns\":"<<hashing<<",\"generation_ns\":"<<(source_decode+preparation+assembly+hashing)<<",\"validate_ns\":"<<validation;
    std::cout<<",\"method_stream_bytes\":[";
    for(unsigned method=0;method<8;++method) {if(method)std::cout<<',';std::array<size_t,4> sizes{};for(unsigned c=0;c<4;++c)sizes[c]=prepared.streams[method][c].size();array_json(sizes);}
    std::cout<<"],\"methods\":[";
    for(unsigned method=0;method<8;++method) {if(method)std::cout<<',';std::cout<<"{\"method\":"<<method;metrics(prepared.metrics[method]);std::cout<<'}';}
    std::cout<<"],\"masks\":[";
    for(unsigned i=0;i<9;++i) {
      const auto &packet=candidates[i];if(i)std::cout<<',';
      std::cout<<"{\"requested_selector\":"<<selectors[i]<<",\"wire_selector\":"<<unsigned(packet[6])<<",\"raw\":"<<(packet[5]?"true":"false")<<",\"bytes\":"<<packet.size()<<",\"sha256\":\""<<hashes[i]<<"\",\"methods\":[";
      for(unsigned context=0;context<4;++context) {if(context)std::cout<<',';std::cout<<choices[i][context];}std::cout<<']';metrics(decoded_stats[i]);std::cout<<'}';
    }
    std::cout<<"]}"<<std::endl;
    for(const auto &packet:candidates) {write32(uint32_t(packet.size()));std::cout.write(reinterpret_cast<const char*>(packet.data()),std::streamsize(packet.size()));}std::cout.flush();
  }
  struct rusage usage{};need(getrusage(RUSAGE_SELF,&usage)==0,"EC94 native RSS query");std::cerr<<"EC94_NATIVE_PEAK_RSS_KIB "<<usage.ru_maxrss<<'\n';return 0;
} catch(const std::exception &error) {std::cerr<<"EC94_HELPER_FAIL "<<error.what()<<std::endl;return 1;}}
