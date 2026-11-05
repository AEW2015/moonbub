from pathlib import Path
import hashlib,importlib.util,json,sys,zlib
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
def module(name,path):
 s=importlib.util.spec_from_file_location(name,path);v=importlib.util.module_from_spec(s);sys.modules[name]=v;s.loader.exec_module(v);return v
old=module('stream48_frozen_direct43_helpers',HERE.parent/'python-game-direct-rx-v43-study/helpers.py');f,m=old.f,old.m
block=module('stream48_block44',HERE.parent/'python-game-block-rx-v44-study/decoder.py');sym=module('stream48_symmetric45',HERE.parent/'python-game-symmetric-inverse-v45-study/model.py')
load,sha,digest=old.load,old.sha,old.digest
raw=old.raw
