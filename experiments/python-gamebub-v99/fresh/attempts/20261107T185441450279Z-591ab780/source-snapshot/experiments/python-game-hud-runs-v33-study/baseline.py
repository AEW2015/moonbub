"""Read-only imports of the frozen v32 and earlier protocol implementations."""
from pathlib import Path
import importlib.util,sys
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('hud33_frozen32',HERE.parent/'python-game-hud-v32-study/model.py')
old=importlib.util.module_from_spec(spec);sys.modules[spec.name]=old;spec.loader.exec_module(old)
p,h=old.p,old.h
