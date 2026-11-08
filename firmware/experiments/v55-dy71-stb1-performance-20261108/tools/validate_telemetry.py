"""Validate one complete V45 retained export without combining separate attempts."""
import argparse
import json
import re
from pathlib import Path


def validate(raw):
    groups = {}
    for line in raw.decode('utf-8', errors='replace').splitlines():
        marker = re.search(r'\bDY45 (BEGIN|END) e=(\d+) a=(\d+) n=(\d+) hash=([0-9a-f]{8}) tx_loss=unknown$', line)
        row = re.search(r'\bDY45 e=(\d+) a=(\d+) i=(\d+) n=(\d+) (.*)$', line)
        if marker:
            kind, epoch, attempt, count, checksum = marker.groups()
            group = groups.setdefault((int(epoch), int(attempt)), {'begin': [], 'end': [], 'rows': [], 'order': []})
            group[kind.lower()].append((int(count), checksum))
            group['order'].append(kind.lower())
        elif row:
            epoch, attempt, index, count, payload = row.groups()
            group = groups.setdefault((int(epoch), int(attempt)), {'begin': [], 'end': [], 'rows': [], 'order': []})
            group['rows'].append((int(index), int(count), payload))
            group['order'].append('row')
    results = []
    for (epoch, attempt), group in sorted(groups.items()):
        errors = []
        if len(group['begin']) != 1 or len(group['end']) != 1:
            errors.append('missing or duplicated BEGIN/END')
        begin = group['begin'][0] if group['begin'] else None
        if begin and group['end'] != [begin]:
            errors.append('boundary count/checksum mismatch')
        checksum = 2166136261
        for _, _, payload in group['rows']:
            for byte in payload.encode('utf-8') + b'\n':
                checksum = ((checksum ^ byte) * 16777619) & 0xffffffff
        if begin:
            count, expected = begin
            if group['order'] != ['begin'] + ['row'] * count + ['end']:
                errors.append('boundary/row order mismatch')
            if [(i, n) for i, n, _ in group['rows']] != [(i, count) for i in range(count)]:
                errors.append('missing, duplicated, reordered or inconsistent row')
            if f'{checksum:08x}' != expected:
                errors.append('payload checksum mismatch')
        results.append({'epoch': epoch, 'attempt': attempt, 'complete': not errors,
                        'received_rows': len(group['rows']), 'errors': errors,
                        'underlying_tx_loss_count': None})
    return results


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('capture', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    results = validate(args.capture.read_bytes())
    result = {'exports': results, 'valid_attempts': [r for r in results if r['complete']]}
    text = json.dumps(result, indent=2) + '\n'
    if args.output:
        args.output.write_text(text, encoding='utf-8')
    print(text, end='')
    raise SystemExit(0 if result['valid_attempts'] else 1)


if __name__ == '__main__':
    main()
