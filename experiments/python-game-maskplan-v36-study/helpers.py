from pathlib import Path
import hashlib, importlib.util, sys
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]

def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    sys.modules[name] = value
    spec.loader.exec_module(value)
    return value

old = module('maskplan36_frozen35', HERE.parent/'python-game-aligned-v35-study/helpers.py')
model = module('maskplan36_model', HERE/'model.py')

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def pins():
    paths = {ROOT/p for p in old.pins()}
    paths |= {HERE/name for name in ('helpers.py','model.py','benchmark.py')}
    return {p.relative_to(ROOT).as_posix(): sha(p) for p in sorted(paths)}
