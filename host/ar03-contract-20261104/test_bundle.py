#!/usr/bin/env python3
"""Focused source-binding and read-only verification tests."""
import hashlib, importlib.util, json, subprocess, sys, tempfile
from pathlib import Path

sys.dont_write_bytecode=True
SCRIPT=Path(__file__).with_name('build_bundle.py').resolve()
spec=importlib.util.spec_from_file_location('ar03_bundle',SCRIPT)
mod=importlib.util.module_from_spec(spec);sys.modules[spec.name]=mod;spec.loader.exec_module(mod)

def tree_hashes(root):
    return {p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob('*')) if p.is_file()}

def main():
    source=Path(sys.argv[1]).resolve(); plan=Path(sys.argv[2]).resolve(); bundle=Path(sys.argv[3]).resolve()
    rel=mod.SOURCE_INPUTS[0]; expected=mod.git_blob(source,mod.SOURCE_COMMIT,rel)
    with tempfile.TemporaryDirectory(prefix='ar03-source-binding-') as td:
        candidate=Path(td)/Path(rel).name
        candidate.write_bytes(expected)
        mod.require_bound_bytes(candidate,expected,rel)
        candidate.write_bytes(expected+b'\n')
        try: mod.require_bound_bytes(candidate,expected,rel)
        except SystemExit as exc:
            assert 'source binding mismatch' in str(exc)
        else: raise AssertionError('modified pinned input was accepted')
    before=tree_hashes(bundle)
    json_files=sorted(bundle.rglob('*.json'))
    assert json_files
    for path in json_files:
        raw=path.read_bytes()
        assert b'\r' not in raw and raw.endswith(b'\n'), f'noncanonical JSON newlines: {path.name}'
        json.loads(raw.decode('utf-8'))
    source_before={rel:hashlib.sha256((source/rel).read_bytes()).hexdigest() for rel in mod.SOURCE_INPUTS}
    cmd=[sys.executable,str(SCRIPT),'--source',str(source),'--plan-repo',str(plan),'--out',str(bundle),'--verify-only']
    run=subprocess.run(cmd,capture_output=True,text=True,check=True)
    after=tree_hashes(bundle)
    source_after={rel:hashlib.sha256((source/rel).read_bytes()).hexdigest() for rel in mod.SOURCE_INPUTS}
    assert before==after, 'verify-only modified bundle content'
    assert source_before==source_after, 'verify-only modified pinned source input'
    print(json.dumps({'passed':True,'modified_input_rejected':True,'verify_only_read_only':True,
        'bundle_files_unchanged':len(before),'source_inputs_unchanged':len(source_before),'canonical_json_lf_files':len(json_files),'verify_only_stdout':run.stdout.strip()},sort_keys=True))
if __name__=='__main__':main()
