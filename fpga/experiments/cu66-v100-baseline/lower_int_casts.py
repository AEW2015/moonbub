#!/usr/bin/env python3
"""Lexical compatibility adapter: int'(packed_integer) -> $signed(32'(...)).

This adapter preserves original files and all ports. It only handles the int
casts inventoried in the frozen component, whose operands are packed integer
arithmetic. It does not lower integer, typedef, real, unpacked-array, assertions,
or other SystemVerilog constructs. Generated output requires paired RTL tests.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil


def tokens(text):
    index = 0
    while index < len(text):
        c = text[index]
        if c.isspace():
            index += 1
            continue
        if text.startswith('//', index):
            end = text.find('\n', index + 2)
            index = len(text) if end < 0 else end
            continue
        if text.startswith('/*', index):
            end = text.find('*/', index + 2)
            if end < 0:
                raise ValueError('unterminated comment')
            index = end + 2
            continue
        if c == '"':
            index += 1
            while index < len(text):
                if text[index] == '\\':
                    index += 2
                elif text[index] == '"':
                    index += 1
                    break
                else:
                    index += 1
            else:
                raise ValueError('unterminated string')
            continue
        start = index
        if c.isalpha() or c in '_$':
            index += 1
            while index < len(text) and (text[index].isalnum() or text[index] in '_$'):
                index += 1
        elif c == '\\':
            while index < len(text) and not text[index].isspace():
                index += 1
        else:
            index += 1
        yield text[start:index], start, index


def lower(text):
    stream = list(tokens(text))
    replacements = []
    inventory = []
    for index in range(len(stream) - 2):
        if [x[0] for x in stream[index:index + 3]] != ['int', "'", '(']:
            continue
        depth = 1
        end_index = index + 3
        while end_index < len(stream) and depth:
            depth += (stream[end_index][0] == '(') - (stream[end_index][0] == ')')
            end_index += 1
        if depth:
            raise ValueError('unbalanced int cast')
        begin = stream[index][1]
        opening = stream[index + 2][1]
        closing = stream[end_index - 1][1]
        # Keep all intervening comments/whitespace, so diagnostics retain line
        # numbers. Inserting a wrapper after the original closing parenthesis
        # also handles nested casts without overlapping source substitutions.
        replacements.extend([(begin, stream[index][2], '$signed(32'),
                             (closing + 1, closing + 1, ')')])
        inventory.append(dict(line=text.count('\n', 0, begin) + 1,
                              expression=text[opening + 1:closing]))
    for begin, end, replacement in sorted(replacements, reverse=True):
        text = text[:begin] + replacement + text[end:]
    return text, inventory


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', required=True, type=Path)
    parser.add_argument('--source-root', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    spec = json.loads(args.manifest.read_text())
    args.output.mkdir(parents=True, exist_ok=False)
    receipt = dict(schema='v100-int-cast-compatibility-overlay-v1',
                   original_manifest_sha256=hashlib.sha256(args.manifest.read_bytes()).hexdigest(),
                   adapter_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), files={},
                   transform="int'(packed integer expression) -> $signed(32'(same expression))",
                   semantic_status='PAIRED_RTL_VERIFICATION_REQUIRED', original_sources_modified=False)
    for name in spec['rtl_sources'] + spec['include_headers']:
        source = args.source_root / name
        original = source.read_bytes()
        original_sha = hashlib.sha256(original).hexdigest()
        if original_sha != spec['source_sha256'][name]:
            raise ValueError('original input hash mismatch: ' + name)
        lowered, casts = lower(original.decode())
        target = args.output / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(lowered)
        receipt['files'][name] = dict(original_sha256=original_sha,
                                    generated_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
                                    changed=bool(casts), casts=casts)
    (args.output / 'adapter-receipt.json').write_text(json.dumps(receipt, indent=2, sort_keys=True) + '\n')
    print(json.dumps(dict(output=str(args.output), int_casts=sum(len(x['casts']) for x in receipt['files'].values()),
                          receipt=str(args.output / 'adapter-receipt.json'))))


if __name__ == '__main__':
    main()
