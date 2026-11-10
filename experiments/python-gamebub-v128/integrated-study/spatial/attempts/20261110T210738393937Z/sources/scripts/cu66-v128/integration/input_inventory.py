#!/usr/bin/env python3
"""Enumerate all explicitly selected V128 pre-run inputs without EDA or source writes."""
import hashlib,importlib.util,json,sys
from pathlib import Path
sys.dont_write_bytecode=True
from contract import ROOT,files as integration_files,load

def module(path,name):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def input_paths():
 raw=module(ROOT/'scripts/cu66-v128/raw/qualify.py','v128_raw_input_inventory')
 pad=module(ROOT/'scripts/cu66-v128/padding/qualify.py','v128_pad_input_inventory')
 paths=set(integration_files()+raw.input_files()+pad.verify())
 paths.add(Path(__file__).resolve())
 for directory in ['scripts/cu66-v128/integration','scripts/cu66-v128/raw','scripts/cu66-v128/padding']:
  base=ROOT/directory;paths.update(p for p in base.rglob('*')if p.is_file()and p.suffix in ('.py','.json')and '__pycache__'not in p.parts)
 qualified=ROOT/'experiments/python-gamebub-v120/handoff.json';paths.add(qualified)
 paths.update(ROOT/meta['path']for meta in load(qualified)['source_origins'].values())
 paths.add(ROOT/'experiments/python-gamebub-v120/audit/baseline.json')
 # Old selected receipt pins recursively bind their own archived artifacts at every
 # normal contract check. This inventory enumerates the direct selected inputs;
 # it does not relabel historical executions or freeze future output files.
 assert all(p.is_file()for p in paths)
 return sorted(paths)

if __name__=='__main__':
 paths=input_paths();print(json.dumps({'status':'PREPARED_INPUT_INVENTORY_NOT_RTL_RUN','source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()for p in paths}},indent=2,sort_keys=True))
