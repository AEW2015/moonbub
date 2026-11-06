"""Replay actual KEY/P/P with explicit +1-cycle IDCT manifest, no DUT edits."""
from pathlib import Path
reference=Path(__file__).with_name('run_syncsafe.py')
s=reference.read_text()
for old,new in [("d/'syncsafe-math-v002/sources.json'","d/'validpipe-v003/sources.json'"),
                ("d/'syncsafe-math-v002/derivation.json'","d/'validpipe-v003/derivation.json'")]:
    assert old in s
    s=s.replace(old,new)
exec(compile(s,str(reference),'exec'),globals())
