#!/usr/bin/env python3
"""Read-only reversible focused-runner derivation; preserves inherited check bodies."""
import argparse,json,sys
from pathlib import Path
sys.dont_write_bytecode=True
from prepare import ROOT,HERE,records
PAIRS=[('scripts/cu66-v126/producer/qualify.py','scripts/cu66-v127/owner/qualify.py','362f9bb6f4cc0f9437044a464c08b7b151718e4de2fd5af4ab049491ce922fae')]
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');a=ap.parse_args()
 result=dict(schema='v127-focused-runner-derivation-v1',old_Cpp_require_checks_removed=0,all_inherited_replay_oracles_retained=True,sources=records(PAIRS));p=HERE/'focused-runner-derivation.json'
 if a.write:p.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
 else:assert json.loads(p.read_text())==result
 print('V127_FOCUSED_RUNNER_DERIVATION_PREPARED_NOT_RUN',len(result['sources']))
if __name__=='__main__':main()
