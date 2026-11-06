"""Actual pin-model native KEY/P, one source change only, no selected DUT edits."""
from pathlib import Path
reference=Path(__file__).with_name('run_syncsafe.py');s=reference.read_text()
for old,new in [("d/'syncsafe-math-v002/sources.json'","d/'tag-equality-v001/sources.json'"),("d/'syncsafe-math-v002/derivation.json'","d/'tag-equality-v001/derivation.json'")]:
 assert old in s;s=s.replace(old,new)
exec(compile(s,str(reference),'exec'),globals())
