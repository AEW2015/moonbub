#!/usr/bin/env python3
"""Prepare a dual actual-ingress wrapper without changing public interfaces."""
import json
import re
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
OLD = ROOT / 'fpga/experiments/cu66-v128-raw/br88_packet_ingress_sync_v91h.sv'
NEW = HERE / 'br88_packet_ingress_sync_v91h.sv'


def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    old = OLD.read_text()
    renamed = old.replace('module br88_packet_ingress_sync_v91h #(', 'module header_index_baseline #(', 1)
    header = old[old.index(') (') + 3:old.index('\n);')]
    ports, direction, typ = [], None, None
    for token in header.split(','):
        t = token.strip()
        match = re.match(r'^(input|output)\s+(.+)$', t, re.S)
        if match:
            direction, t = match.group(1), match.group(2).strip()
            m = re.match(r'^(logic(?:\s+signed)?(?:\s*\[[^]]+\])?)\s+(.+)$', t, re.S)
            assert m, t
            typ, t = m.group(1), m.group(2).strip()
        assert re.fullmatch(r'\w+', t), t
        ports.append((direction, typ, t))
    top = 'module header_index_pair (\n' + ',\n'.join(f'    {d} {t} {n}' for d,t,n in ports)
    top += ',\n    output logic pair_equal\n);\n'
    for direction, typ, name in ports:
        if direction == 'output': top += f'    {typ} old_{name};\n'
    for module, prefix, instance in [('header_index_baseline', 'old_', 'reference'),
                                     ('br88_packet_ingress_sync_v91h', '', 'candidate')]:
        top += f'    {module} {instance} (\n'
        top += ',\n'.join(f'        .{n}({prefix if d == "output" else ""}{n})' for d,t,n in ports)
        top += '\n    );\n'
    top += '    always_comb pair_equal =\n'
    top += ' &&\n'.join(f'        (old_{n} == {n})' for d,t,n in ports if d == 'output') + ';\nendmodule\n'
    (HERE/'header_index_baseline.sv').write_text(renamed)
    (HERE/'header_index_pair.sv').write_text(top)
    (HERE/'manifest.json').write_text(json.dumps(dict(baseline_sha256=sha(OLD), candidate_sha256=sha(NEW),
        renamed_sha256=sha(HERE/'header_index_baseline.sv'), wrapper_sha256=sha(HERE/'header_index_pair.sv'),
        output_count=sum(d=='output' for d,t,n in ports), scope='Pair of actual selected ingress RTL modules; all public output values compared every evaluation.'), indent=2,sort_keys=True)+'\n')


if __name__ == '__main__': main()
