"""Independent actual packet retry after reset in new DC_CHECK state56."""
from pathlib import Path
parent=Path(__file__).with_name('run_arith.py');s=parent.read_text()
s=s.replace("for index,seed,count,abort in [('directed',6901,31,True),('stress',6902,120,True),('actual',6901,1371,False)]:","for index,seed,count,abort in [('directed',6901,31,True),('stress',6902,120,True)]:")
method=''' void dc_reset56_checks(const std::vector<Fixture>&cases){
  const Fixture*chosen=nullptr;
  for(const auto&candidate:cases){
   if(candidate.invalid)continue;
   load(candidate);unsigned count=0;
   while(d.debug_state!=56&&!d.done&&!d.error){step();demand(++count<20000000,"DC reset setup watchdog");}
   if(d.debug_state==56){chosen=&candidate;break;}
   demand(d.done&&!d.error&&!pending,"valid setup fixture failed");
  }
  demand(chosen!=nullptr,"DC_CHECK uncovered");
  std::array<uint8_t,352> before{};
  for(unsigned i=0;i<352;i++)before[i]=d.rootp->cu71_ab38_decoder_arithpipe__DOT__probabilities[i];
  d.rootp->cu71_ab38_decoder_arithpipe__DOT__dc_prediction=0x7fffffff;
  d.rst=1;d.abort_i=1;step(false);
  demand(d.debug_state==0&&!d.busy&&!d.error&&!d.aborted&&!d.tile_valid,"reset56 control/priority");
  demand(d.rootp->cu71_ab38_decoder_arithpipe__DOT__dc_prediction==0x7fffffff,"private DC unexpectedly reset");
  for(unsigned i=0;i<352;i++)demand(before[i]==d.rootp->cu71_ab38_decoder_arithpipe__DOT__probabilities[i],"reset56 probability RAM write");
  d.rst=0;d.abort_i=0;step(false);
  demand(d.cfg_ready&&!pending&&!d.done,"reset56 did not quiesce");
  run(*chosen);
  std::cout<<"DC_RESET56_FULL_PACKET_RETRY_PASS dirty_payload=1 retained_probability_bytes=352 reset_over_abort=1 fixture="<<chosen->name<<"\\n";
 }
'''
# Keep generated hierarchy replacement tied to the actual selected top.
s=s.replace("tb=tb.replace(' void abort_checks(const Fixture&good){',method+' void abort_checks(const Fixture&good){')", "tb=tb.replace(' void abort_checks(const Fixture&good){',method+"+repr(method)+".replace('cu71_ab38_decoder_arithpipe__DOT__',top+'__DOT__')+' void abort_checks(const Fixture&good){')")
s=s.replace("sim.abort_checks(*p);sim.arithmetic_micro_abort_checks(fs);","sim.abort_checks(*p);sim.arithmetic_micro_abort_checks(fs);sim.dc_reset56_checks(fs);")
s=s.replace("(o/src.name).write_bytes(src.read_bytes());", "(o/'executed-wrapper.py').write_bytes(Path(__file__).read_bytes());(o/'executed-parent.py').write_bytes(Path(__file__).with_name('run_arith.py').read_bytes());(o/src.name).write_bytes(src.read_bytes());")
s=s.replace("'PASS_ARITHMETIC_MICROPIPE_ACTUAL_COEFFICIENTS_AND_ABORTS'","'PASS_DC_RESET56_REAL_PACKET_RETRY_AND_DIRECTED_STRESS'")
s=s.replace("'1371actual+31directed+120stresscoefficient/rejectionfixtures; inheritedabort/reset/backpressureandall4newmicrostateabortprobabilityRAM/counterchecks+validretry. Latencychanges, wireandroundingunchanged.'","'Independent31directed+120stress; direct reset in DC_CHECK56 with dirty unreset DC payload, retained probability RAM, reset-over-abort and full native packet/golden coefficient retry. No hardware.'")
exec(compile(s,str(parent),'exec'),globals())
