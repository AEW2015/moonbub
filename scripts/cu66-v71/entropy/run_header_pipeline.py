"""Run existing real entropy campaign with the two explicit header states."""
from pathlib import Path
parent=Path(__file__).with_name('run_arith.py')
s=parent.read_text()
s=s.replace('ARITHMETIC_MICRO_ABORT_PASS','HEADER_PREFIX_MICRO_ABORT_PASS')
s=s.replace('PASS_ARITHMETIC_MICROPIPE_ACTUAL_COEFFICIENTS_AND_ABORTS','PASS_HEADER_PIPE_ACTUAL_COEFFICIENTS_AND_NEW_STATE_ABORTS')
s=s.replace('1371actual+31directed+120stresscoefficient/rejectionfixtures; inheritedabort/reset/backpressureandall4newmicrostateabortprobabilityRAM/counterchecks+validretry. Latencychanges, wireandroundingunchanged.',
'''1371actual+31directed+120stress; two appended header-state abort/probability/counter/retry checks and inherited reset/backpressure. Header latency+2, modular arithmetic and wire bytes unchanged; targeted header-error and direct-reset gates separate.''')
s=s.replace("(o/src.name).write_bytes(src.read_bytes());", "(o/'executed-parent.py').write_bytes(Path(__file__).with_name('run_arith.py').read_bytes());(o/'executed-wrapper.py').write_bytes(Path(__file__).read_bytes());(o/src.name).write_bytes(src.read_bytes());")
exec(compile(s,str(parent),'exec'),globals())
