"""Check Git's staged bytes against a development snapshot index."""
from pathlib import Path
import argparse, ast, hashlib, json, subprocess
root = Path(__file__).resolve().parents[2]
p = argparse.ArgumentParser()
p.add_argument('--index', required=True)
args = p.parse_args()
index = json.loads((root / args.index).read_text())
files = index['files']
queries = ''.join(':' + name + '\n' for name in files).encode()
result = subprocess.run(['git', 'cat-file', '--batch'], cwd=root, input=queries, stdout=subprocess.PIPE, check=True)
data = result.stdout
cursor = 0
python_files = 0
for name, expected in files.items():
    end = data.index(b'\n', cursor)
    header = data[cursor:end].split()
    assert len(header) == 3 and header[1] == b'blob', (name, header)
    size = int(header[2])
    blob = data[end+1:end+1+size]
    assert hashlib.sha256(blob).hexdigest() == expected, name
    cursor = end+1+size+1
    if name.endswith('.py'):
        ast.parse(blob.decode('utf-8-sig'), filename=name)
        python_files += 1
assert cursor == len(data)
check = subprocess.run(['git', '-c', 'core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol',
                        'diff', '--cached', '--check', '--', 'scripts/cu66-v71', 'docs/cu66-v71'],
                       cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
assert check.returncode == 0, (check.stdout + check.stderr).decode(errors='replace')[:4000]
print(json.dumps(dict(status='PASS_STAGED_BLOB_BYTES_PYTHON_PARSE_AND_SCRIPT_DOC_WHITESPACE',
                      blobs=len(files), python_files=python_files, hardware=False)))
