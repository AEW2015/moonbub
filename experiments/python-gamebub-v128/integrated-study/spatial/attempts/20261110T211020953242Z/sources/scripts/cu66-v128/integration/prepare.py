#!/usr/bin/env python3
"""Read-only reversible full-runner preparation; optionally reconstruct into a new directory."""
import argparse,ast,hashlib,json
from pathlib import Path
from contract import ROOT,HERE,verify_derivation

def function_text(source,name):
 tree=ast.parse(source);node=next(x for x in tree.body if isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef))and x.name==name)
 return ast.get_source_segment(source,node)

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--reconstruct',type=Path);args=ap.parse_args();recipe=verify_derivation();checks={}
 required={'spatial.py':['memory','derive','semantic_events'],'live_guard/qualify.py':['sha','load','rel','write','module','verify_derivation','proof','memory'],'collect_final.py':['stage']}
 for entry in recipe['sources']:
  before=(ROOT/entry['original']).read_text();after=(ROOT/entry['candidate']).read_text();name=str(Path(entry['candidate']).relative_to(HERE.relative_to(ROOT)))
  for f in required.get(name,[]):assert function_text(before,f)==function_text(after,f);checks[name+':'+f]=True
  if args.reconstruct:
   out=args.reconstruct.resolve()/name;assert not out.exists();text=before
   for e in entry['edits']:assert text.count(e['before'])==e['count'];text=text.replace(e['before'],e['after'])
   assert hashlib.sha256(text.encode()).hexdigest()==entry['candidate_sha256'];out.parent.mkdir(parents=True,exist_ok=True);out.write_text(text)
 print(json.dumps(dict(status='V128_RUNNERS_PREPARED_NOT_RUN',runner_count=len(recipe['sources']),unchanged_helper_count=len(checks),unchanged_helpers=sorted(checks)),sort_keys=True))
if __name__=='__main__':main()
