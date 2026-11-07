#include "Vrans_symbol.h"
#include "verilated.h"
#include "verilated_vcd_c.h"
#include <array>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <memory>
#include <random>
#include <stdexcept>
#include <string>
#include <vector>

static constexpr uint32_t LOWER=1u<<23;
static uint64_t checks=0;
static void need(bool value,const std::string &message) {
  ++checks;if(!value)throw std::runtime_error(message);
}
static uint32_t word(std::istream &in,unsigned bytes=4) {
  uint32_t out=0;
  for(unsigned i=0;i<bytes;++i) {int c=in.get();need(c!=EOF,"vector truncation");out|=uint32_t(c)<<(8*i);}
  return out;
}
struct Field {uint32_t q,lane,state,cursor;};
struct Case {
  unsigned scale,lanes,models;
  std::array<uint32_t,4> initial;
  std::array<std::array<unsigned,16>,2> frequencies;
  std::vector<uint8_t> bytes;
  std::vector<Field> fields;
};
struct Sample {
  bool cfg,init,input,output;unsigned q,lane;uint32_t state,cursor;
};
struct Sim {
  Vrans_symbol dut;
  std::unique_ptr<VerilatedVcdC> trace;
  uint64_t clocks=0;
  explicit Sim(const std::string &wave="") {
    if(!wave.empty()) {trace=std::make_unique<VerilatedVcdC>();dut.trace(trace.get(),3);trace->open(wave.c_str());}
    dut.rst=1;tick();dut.rst=0;
  }
  ~Sim() {dut.final();if(trace)trace->close();}
  Sample tick() {
    dut.clk=0;dut.eval();if(trace)trace->dump(2*clocks);
    Sample s{bool(dut.cfg_ready),bool(dut.init_ready),bool(dut.byte_ready),bool(dut.out_valid),
             dut.out_symbol,dut.out_lane,dut.out_state,dut.bytes_consumed};
    dut.clk=1;dut.eval();if(trace)trace->dump(2*clocks+1);++clocks;
    return s;
  }
  void reset(bool abort=false) {
    dut.cfg_valid=0;dut.init_valid=0;dut.start=0;dut.byte_valid=0;dut.out_ready=0;
    if(abort)dut.abort_job=1;else dut.rst=1;
    tick();dut.abort_job=0;dut.rst=0;dut.eval();
    need(!dut.out_valid&&!dut.done&&!dut.error&&dut.symbols_emitted==0&&dut.bytes_consumed==0,"reset/abort did not clear ownership");
  }
  bool load(const Case &c) {
    dut.cfg_scale=c.scale;dut.start_lanes=c.lanes;dut.start_models=c.models;
    dut.start_symbols=uint32_t(c.fields.size());dut.start_bytes=uint32_t(c.bytes.size());
    for(unsigned model=0;model<c.models;++model) {
      unsigned cumulative=0;
      for(unsigned symbol=0;symbol<16;++symbol) {
        dut.cfg_valid=1;dut.cfg_addr=model*16+symbol;dut.cfg_frequency=c.frequencies[model][symbol];dut.cfg_cumulative=cumulative;
        auto s=tick();need(s.cfg,"table preload backpressured unexpectedly");cumulative+=c.frequencies[model][symbol];
        if(dut.error) {dut.cfg_valid=0;return false;}
      }
    }
    dut.cfg_valid=0;
    for(unsigned lane=0;lane<c.lanes&&lane<4;++lane) {
      dut.init_valid=1;dut.init_lane=lane;dut.init_state=c.initial[lane];
      auto s=tick();need(s.init,"state preload backpressured unexpectedly");
      if(dut.error) {dut.init_valid=0;return false;}
    }
    dut.init_valid=0;dut.start=1;tick();dut.start=0;
    return !dut.error;
  }
};
struct Timing {uint64_t cycles,input_stalls,output_stalls;std::array<unsigned,3> refills{};};
static Timing run(Sim &sim,const Case &c,bool stalled,unsigned seed,bool expected_error=false) {
  auto &d=sim.dut;std::mt19937 random(seed);size_t input=0,output=0;bool pending=false,held=false;
  Sample held_value{};uint32_t prior_cursor=0;uint64_t begin=sim.clocks;Timing timing{};
  uint64_t watchdog=1000+64*c.fields.size()+32*c.bytes.size();
  while(!d.done&&!d.error) {
    need(sim.clocks-begin<watchdog,"RTL finite watchdog");
    if(!pending&&input<c.bytes.size()&&(!stalled||random()%3!=0))pending=true;
    d.byte_valid=pending;d.byte_data=input<c.bytes.size()?c.bytes[input]:0;
    d.out_ready=!stalled||random()%4!=0;
    auto sample=sim.tick();
    if(held)need(sample.output&&sample.q==held_value.q&&sample.lane==held_value.lane&&sample.state==held_value.state&&sample.cursor==held_value.cursor,"output changed while held");
    held=sample.output&&!d.out_ready;held_value=sample;
    if(sample.input&&!pending)++timing.input_stalls;
    if(sample.output&&!d.out_ready)++timing.output_stalls;
    if(sample.input&&pending) {++input;pending=false;}
    if(sample.output&&d.out_ready) {
      need(output<c.fields.size(),"extra RTL symbol");
      if(!expected_error) {
        const auto &gold=c.fields[output];
        need(sample.q==gold.q&&sample.lane==gold.lane&&sample.state==gold.state&&sample.cursor==gold.cursor,"RTL field/state/cursor mismatch at "+std::to_string(output));
      }
      unsigned refill=sample.cursor-prior_cursor;need(refill<=2,"more than two refills");++timing.refills[refill];prior_cursor=sample.cursor;++output;
    }
  }
  timing.cycles=sim.clocks-begin;
  if(expected_error)need(d.error&&!d.done,"malformed stream did not fail closed");
  else {
    need(d.done&&!d.error&&output==c.fields.size()&&input==c.bytes.size(),"RTL terminal totals");
    need(d.symbols_emitted==output&&d.bytes_consumed==input,"RTL counters differ from observed handshakes");
    need(timing.cycles==4*c.fields.size()+c.bytes.size()+timing.input_stalls+timing.output_stalls,"cycle conservation");
  }
  d.byte_valid=0;d.out_ready=0;return timing;
}
static void failure(Sim &s,const Case &c,const std::string &name) {
  s.reset();bool accepted=s.load(c);
  if(accepted)run(s,c,false,1,true);
  need(s.dut.error&&!s.dut.done,"negative case accepted: "+name);
  std::cout<<"{\"type\":\"negative\",\"name\":\""<<name<<"\",\"code\":"<<unsigned(s.dut.error_code)<<"}\n";
}
int main(int argc,char **argv) {try {
  Verilated::commandArgs(argc,argv);Verilated::traceEverOn(true);
  need(argc==3,"usage: binary vectors.bin waveform-prefix");std::ifstream input(argv[1],std::ios::binary);
  need(bool(input),"cannot read vector file");need(word(input)==0x34395652u,"vector magic");unsigned count=word(input);need(count>0&&count<256,"vector count bound");
  std::vector<Case> cases;
  for(unsigned n=0;n<count;++n) {
    Case c;c.scale=word(input);c.lanes=word(input);c.models=word(input);unsigned fields=word(input),bytes=word(input);
    need(fields<=65536&&bytes<=2*fields,"test vector finite bound");
    for(auto &v:c.initial)v=word(input);
    for(auto &m:c.frequencies)for(auto &v:m)v=word(input,2);
    for(unsigned i=0;i<bytes;++i)c.bytes.push_back(uint8_t(word(input,1)));
    for(unsigned i=0;i<fields;++i)c.fields.push_back({word(input),word(input),word(input),word(input)});
    cases.push_back(std::move(c));
  }
  need(input.peek()==EOF,"extra vector file data");unsigned rows=0;std::array<uint64_t,3> all_refills{};
  unsigned wave_case=0;while(wave_case<cases.size()&&cases[wave_case].fields.empty())++wave_case;
  for(unsigned n=0;n<cases.size();++n)for(unsigned mode=0;mode<3;++mode) {
    const auto &c=cases[n];std::string wave=n==wave_case&&mode<2?std::string(argv[2])+"-mode"+std::to_string(mode)+".vcd":"";
    Sim sim(wave);uint64_t config_begin=sim.clocks;need(sim.load(c),"valid model/state preload rejected");uint64_t config_cycles=sim.clocks-config_begin;
    auto timing=run(sim,c,mode!=0,9400+mode);
    for(unsigned k=0;k<3;++k)all_refills[k]+=timing.refills[k];
    std::cout<<"{\"type\":\"case\",\"case\":"<<n<<",\"mode\":"<<mode<<",\"seed\":"<<9400+mode<<",\"scale\":"<<c.scale<<",\"lanes\":"<<c.lanes<<",\"models\":"<<c.models<<",\"symbols\":"<<c.fields.size()<<",\"renorm_bytes\":"<<c.bytes.size()<<",\"config_cycles\":"<<config_cycles<<",\"decode_cycles\":"<<timing.cycles<<",\"input_stalls\":"<<timing.input_stalls<<",\"output_stalls\":"<<timing.output_stalls<<"}\n";++rows;
  }
  Case empty{};empty.scale=10;empty.lanes=2;empty.models=1;empty.initial.fill(LOWER);for(auto &m:empty.frequencies)m[0]=1024;
  Sim sim;Case bad=empty;bad.scale=7;failure(sim,bad,"unsupported_scale");
  bad=empty;--bad.frequencies[0][0];failure(sim,bad,"table_sum");
  bad=empty;bad.initial[0]=LOWER-1;failure(sim,bad,"initial_below_lower");
  bad=empty;bad.initial[0]=0x80000000u;failure(sim,bad,"initial_upper_bound");
  bad=empty;bad.initial[0]=LOWER+1;failure(sim,bad,"nonterminal_empty_state");
  bad=empty;bad.lanes=3;failure(sim,bad,"unsupported_lanes");
  unsigned negative=6;const Case *refill_case=nullptr;
  for(const auto &c:cases)if(!c.bytes.empty()&&c.fields.size()>1) {refill_case=&c;break;}
  need(refill_case!=nullptr,"missing refill vector");
  bad=*refill_case;bad.bytes.pop_back();failure(sim,bad,"truncated_refill");++negative;
  bad=*refill_case;bad.bytes.push_back(0);failure(sim,bad,"trailing_refill");++negative;
  for(unsigned kind=0;kind<3;++kind) {
    sim.reset();need(sim.load(*refill_case),"abort setup");auto &d=sim.dut;size_t at=0;bool reached=false;
    for(unsigned wait=0;wait<100000;++wait) {
      d.byte_valid=kind==1?0:at<refill_case->bytes.size();d.byte_data=at<refill_case->bytes.size()?refill_case->bytes[at]:0;d.out_ready=kind==0?0:1;
      d.clk=0;d.eval();
      if((kind==0&&d.out_valid)||(kind==1&&d.byte_ready)||(kind==2&&wait==1)) {reached=true;break;}
      auto sample=sim.tick();if(sample.input&&d.byte_valid)++at;need(!d.error&&!d.done,"cancel checkpoint was not reached");
    }
    need(reached,"abort checkpoint timeout");sim.reset(kind!=2);need(sim.load(*refill_case),"abort retry rejected");run(sim,*refill_case,true,9490+kind);
    std::cout<<"{\"type\":\"recovery\",\"kind\":"<<kind<<",\"status\":\"PASS\"}\n";
  }
  std::cout<<"{\"type\":\"verdict\",\"status\":\"TEST_PASS\",\"checks\":"<<checks<<",\"vectors\":"<<cases.size()<<",\"rows\":"<<rows<<",\"negative\":"<<negative<<",\"recoveries\":3,\"refill_histogram\":["<<all_refills[0]<<','<<all_refills[1]<<','<<all_refills[2]<<"]}\n";return 0;
} catch(const std::exception &error) {std::cerr<<"RTL_TEST_FAIL "<<error.what()<<'\n';return 1;}}
