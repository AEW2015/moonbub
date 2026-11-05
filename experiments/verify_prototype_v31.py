#!/usr/bin/env python3
"""Offline V31 retained arithmetic/log/source verification, no tool install."""
from pathlib import Path
import hashlib,json,subprocess,sys
ROOT=Path(__file__).resolve().parent.parent
def main():
    m=json.loads((ROOT/'docs/prototype-v31-provenance.json').read_text())
    assert m['schema']=='gamebub-v31-provenance'
    for p,h in {**m['file_sha256'],**m['frozen_v30_sha256']}.items():
        q=Path(p);assert not q.is_absolute() and '..' not in q.parts
        assert hashlib.sha256((ROOT/q).read_bytes()).hexdigest()==h,p
    r=subprocess.run([sys.executable,str(ROOT/m['rtl_helper'])],capture_output=True,text=True)
    if r.returncode:sys.stderr.write(r.stdout+r.stderr);r.check_returncode()
    for p,h in m['file_sha256'].items():assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h,p
    print(json.dumps(dict(inventory_files=len(m['file_sha256']),frozen_v30_files=len(m['frozen_v30_sha256']),
                          rtl_replay=json.loads(r.stdout),ESP32_firmware_changed=False,physical_30fps_proven=False),indent=2))
if __name__=='__main__':main()
