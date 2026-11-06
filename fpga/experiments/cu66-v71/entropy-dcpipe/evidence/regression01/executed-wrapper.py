"""Real coefficient/reject cases and direct abort in the appended DC state."""
from pathlib import Path
parent=Path(__file__).with_name('run_arith.py');s=parent.read_text()
s=s.replace('ARITHMETIC_MICRO_ABORT_PASS','DC_SUM_MICRO_ABORT_PASS')
s=s.replace('PASS_ARITHMETIC_MICROPIPE_ACTUAL_COEFFICIENTS_AND_ABORTS','PASS_DC_SUM_PIPE_ACTUAL_COEFFICIENTS_AND_NEW_STATE_ABORT')
s=s.replace('1371actual+31directed+120stresscoefficient/rejectionfixtures; inheritedabort/reset/backpressureandall4newmicrostateabortprobabilityRAM/counterchecks+validretry. Latencychanges, wireandroundingunchanged.',
'''1371actual+31directed+120stress; one appended DC-state abort/probability/counter/retry check and inherited reset/backpressure. DC latency+1/nonraw block; exact signed math, wire bytes and entropy updates unchanged. Direct reset/arithmetic review separate.''')
s=s.replace("(o/src.name).write_bytes(src.read_bytes());", "(o/'executed-parent.py').write_bytes(Path(__file__).with_name('run_arith.py').read_bytes());(o/'executed-wrapper.py').write_bytes(Path(__file__).read_bytes());(o/src.name).write_bytes(src.read_bytes());")
exec(compile(s,str(parent),'exec'),globals())
