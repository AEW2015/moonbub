#!/usr/bin/env python3
"""Read-only reversible derivations from selected V126v3 and terminal auditor."""
import argparse,json,sys
from pathlib import Path
sys.dont_write_bytecode=True
from prepare import ROOT,HERE,records
PAIRS=[('scripts/cu66-v126/audit_functional_v3.py','scripts/cu66-v127/audit_functional.py','c7efaad7328ad5bc5754ba332420e6006bf76652da660e7d01ae55777f655d42'),('scripts/cu66-v126/audit_terminal.py','scripts/cu66-v127/audit_terminal.py','e103bd96d4c049442f9a10e14e75fa905085b152fd9491d3a1e64c2de5c94739')]
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');a=ap.parse_args()
 result=dict(schema='v127-independent-auditor-derivation-v1',old_integrity_check_calls_removed=0,sources=records(PAIRS));p=HERE/'audit-derivation.json'
 if a.write:p.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
 else:assert json.loads(p.read_text())==result
 print('V127_AUDITOR_DERIVATIONS_PREPARED_NOT_RUN',[(Path(r['candidate']).name,len(r['edits']))for r in result['sources']])
if __name__=='__main__':main()
