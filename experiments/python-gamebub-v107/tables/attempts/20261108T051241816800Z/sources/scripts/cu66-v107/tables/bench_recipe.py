from pathlib import Path
p=Path('fpga/experiments/cu66-v107-tables/tb_admission.cpp');s=p.read_text();old=Path('fpga/experiments/cu66-v105-memory/tb_modes.cpp').read_text()
# Retain the actual V105 cases/oracle, adapting only names, initial storage
# hierarchy and coordinate/cache preparation for the later full production body.
a=old.index('static bool hidden(');b=old.index('int main(',a);helpers=old[a:b].replace('hidden(','mode_hidden(').replace('struct Case','struct ModeCase')
body=old[old.index('int main('):]
body=body.replace('int main(int argc,char** argv){try{','static uint64_t prepared_mode_ports(unsigned seed) {')
body=body.replace(' need(argc==3,"seed and trace path required");const unsigned seed=unsigned(std::stoul(argv[1]));std::mt19937 rng(seed);',' std::mt19937 rng(seed);')
body=body.replace('Vmode_probe','Vadmission_probe').replace('std::ofstream trace(argv[2])','std::ofstream trace("mode-ports.jsonl")')
body=body.replace('need(','require(').replace('hidden(','mode_hidden(').replace('const Case&','const ModeCase&').replace('Case c','ModeCase c')
body=body.replace('d.probe_outputs_equal','!d.mismatch')
body=body.replace('OLD(modes)','r.admission_probe__DOT__original__DOT__modes').replace('NEW(modes)','r.admission_probe__DOT__candidate__DOT__mode_store__DOT__words')
body=body.replace('BOTH(scales[i],i%3U);','r.admission_probe__DOT__original__DOT__scale_store__DOT__words[i]=i%3U;r.admission_probe__DOT__candidate__DOT__scale_store__DOT__words[i]=i%3U;')
init='BOTH(lookup_mode,3U);BOTH(lookup_scale,2U);unsigned held=3,cases=0,reads=0,writes=0,guarded=0;'
prime='''unsigned prime=0;while(modes[prime]!=3U)++prime;
 BOTH(state,26U);BOTH(coord_valid,0U);d.lookup_req=1;d.lookup_tile=prime;d.lookup_cell=0;
 d.clk=0;d.eval();d.clk=1;d.eval();require(!d.mismatch&&d.lookup_mode==3,"prime known held mode via real lookup");d.clk=0;d.eval();d.lookup_req=0;
 unsigned held=3,cases=0,reads=0,writes=0,guarded=0;'''
assert init in body;body=body.replace(init,prime)
needle='  BOTH(state,c.state);'
coord='''  const unsigned cell=c.p?c.t:(c.t/180U)*45U+(c.t%90U)/2U;
  BOTH(coord_valid,1U);BOTH(coord_cell,cell);BOTH(coord_pair_base,c.p?0U:(c.t/180U)*45U);BOTH(coord_y_column,c.p?0U:c.t%90U);BOTH(coord_y_odd,c.p?0U:(c.t/90U)%2U);
'''
assert needle in body;body=body.replace(needle,coord+needle)
needle=' scan();\n for(unsigned i=0;i<8100;++i){require('
extra=''' for(uint32_t high:{0x80000000U,0xffffe000U})for(unsigned index:{0U,1U,4095U,8099U}){ModeCase c;c.state=31;c.index=high+index;c.addr=index;run(c);}
 scan();
 for(unsigned i=0;i<8100;++i){require('''
assert needle in body;body=body.replace(needle,extra)
body=body.replace('cases+1','cases+2')
last=' d.final();return 0;\n }catch(const std::exception& e){std::cerr<<"TEST_FAIL "<<e.what()<<\'\\n\';return 1;}}'
assert last in body;body=body.replace(last,' d.final();return cases+2;\n}')
macros='''\n#define OLD(n) r.admission_probe__DOT__original__DOT__##n
#define NEW(n) r.admission_probe__DOT__candidate__DOT__##n
#define BOTH(n,v) do {const auto z=(v);OLD(n)=z;NEW(n)=z;}while(0)
'''
pos=s.index('int main(int argc,char **argv)');s=s[:pos]+macros+helpers+body+'\n'+s[pos:]
s=s.replace('const auto scale_prepared_edges=prepared_scale_ports();','const auto mode_prepared_edges=prepared_mode_ports(seed);const auto scale_prepared_edges=prepared_scale_ports();')
s=s.replace('<<",\\\"scale_prepared_edges\\\":"<<scale_prepared_edges','<<",\\\"mode_prepared_edges\\\":"<<mode_prepared_edges<<",\\\"scale_prepared_edges\\\":"<<scale_prepared_edges')
assert s.count('mode_prepared_edges')==3;p.write_text(s)
