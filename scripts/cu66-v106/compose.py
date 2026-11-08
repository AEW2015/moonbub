#!/usr/bin/env python3
"""Compose exact V106 lookup and storage recipes in both orders."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RECIPES = {
    'math': 'fpga/experiments/cu66-v106-math/lut/cu66_inverse_stream_v91j.recipe.json',
    'storage': 'fpga/experiments/cu66-v106-locality/edit-proof.json',
}
TARGET = 'fpga/experiments/cu66-v106-composed/lut-storage/cu66_inverse_stream_v91j.sv'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def apply(text, edits):
    for edit in edits:
        assert edit['expected_occurrences'] == 1 and text.count(edit['before']) == 1, edit['name']
        text = text.replace(edit['before'], edit['after'], 1)
    return text


def main():
    recipes, refs, originals = {}, {}, []
    for name, path in RECIPES.items():
        raw = (ROOT / path).read_bytes()
        r = json.loads(raw)
        assert r['schema'] == 'v106-edit-recipe-v1'
        before = (ROOT / r['original_path']).read_bytes()
        after = (ROOT / r['candidate_path']).read_bytes()
        assert digest(before) == r['original_sha256'] and digest(after) == r['candidate_sha256']
        assert apply(before.decode(), r['edits']).encode() == after
        originals.append(before)
        recipes[name] = r
        refs[name] = dict(path=path, sha256=digest(raw), candidate=r['candidate_path'],
                          candidate_sha256=digest(after))
    assert originals[0] == originals[1]
    outputs, orders = [], []
    for order in [('math', 'storage'), ('storage', 'math')]:
        result = originals[0].decode()
        for name in order:
            result = apply(result, recipes[name]['edits'])
        outputs.append(result)
        orders.append(dict(order=order, sha256=digest(result.encode())))
    assert outputs[0] == outputs[1]
    header = lambda t: t[:t.index(');') + 2]
    assert header(outputs[0]) == header(originals[0].decode())
    path = ROOT / TARGET
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(outputs[0])
    proof = dict(schema='v106-both-order-composition-v1', status='PASS',
                 recipes=refs, orders=orders, both_orders_identical=True,
                 module_header_byte_identical=True, candidate=TARGET,
                 candidate_sha256=digest(path.read_bytes()),
                 composer=dict(path=str(Path(__file__).relative_to(ROOT)),
                               sha256=digest(Path(__file__).read_bytes())),
                 scope='Exact source composition only; independent focused and complete pipeline tests required.')
    (ROOT / 'experiments/python-gamebub-v106/composition.json').write_text(json.dumps(proof, indent=2, sort_keys=True) + '\n')
    print('V106_COMPOSITION_PASS', proof['candidate_sha256'])


if __name__ == '__main__':
    main()
