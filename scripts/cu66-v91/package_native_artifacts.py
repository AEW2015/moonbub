#!/usr/bin/env python3
"""Package exact native audit artifacts without duplicating frozen input blobs."""
import gzip
import hashlib
import json
from pathlib import Path
import tarfile

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT/'experiments/python-gamebub-v91'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    archive=AREA/'native-artifacts.tar.gz'
    members,aliases={},{}
    with archive.open('wb') as raw, gzip.GzipFile(filename='',fileobj=raw,mode='wb',mtime=0) as gz:
        with tarfile.open(fileobj=gz,mode='w') as tar:
            for attempt in sorted((AREA/'native-attempts').iterdir()):
                if not attempt.is_dir(): continue
                paths=sorted(list((attempt/'sources').rglob('*'))+list(attempt.glob('native-*.bin')))
                for path in paths:
                    if not path.is_file(): continue
                    name=str(path.relative_to(AREA)); digest=sha(path)
                    if path.suffix=='.gz' and 'sources' in path.parts:
                        original=ROOT/path.relative_to(attempt/'sources')
                        assert original.is_file() and sha(original)==digest
                        aliases[name]=dict(path=str(original.relative_to(ROOT)),sha256=digest)
                    else:
                        info=tar.gettarinfo(str(path),arcname=name)
                        info.mtime=0;info.uid=info.gid=0;info.uname=info.gname='';info.mode=0o644
                        with path.open('rb') as data: tar.addfile(info,data)
                        members[name]=digest
    with tarfile.open(archive,'r:gz') as tar:
        for name,digest in members.items():
            assert hashlib.sha256(tar.extractfile(name).read()).hexdigest()==digest
    index=dict(schema='cu66-v91-native-artifact-storage-v1',archive=archive.name,
               archive_sha256=sha(archive),members=members,existing_frozen_aliases=aliases,
               scope='Exact source snapshots/binaries archived for Git; duplicate frozen gzip snapshots resolve to already-tracked fixtures. Local unpacked copies are ignored, not removed.')
    (AREA/'native-artifact-storage.json').write_text(json.dumps(index,indent=2)+'\n')
    print('PACKAGED',len(members),'members',len(aliases),'aliases',archive.stat().st_size,'bytes')


if __name__=='__main__':main()
