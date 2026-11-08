#!/usr/bin/env python3
"""Compose disjoint V105 recipes in both orders; reject ambiguous edits."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RECIPES = {
    'admission': 'fpga/experiments/cu66-v105-admission/edit-recipe.json',
    'memory': 'fpga/experiments/cu66-v105-memory/edit-proof.json',
}
TARGET = 'fpga/experiments/cu66-v105-composed/cs88_admission_v91i2a.sv'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def apply(text, edits):
    for edit in edits:
        assert edit['expected_occurrences'] == 1
        assert text.count(edit['before']) == 1, ('nonunique/missing anchor', edit['name'])
        text = text.replace(edit['before'], edit['after'], 1)
    return text


def main():
    recipes, pins, originals = {}, {}, []
    for name, path in RECIPES.items():
        raw = (ROOT / path).read_bytes()
        recipe = json.loads(raw)
        assert recipe['schema'] == 'v105-edit-recipe-v1'
        original = recipe.get('original_path', recipe.get('originalpath'))
        original_hash = recipe.get('original_sha256', recipe.get('originalhash'))
        candidate = recipe.get('candidate_path', recipe.get('candidatepath'))
        candidate_hash = recipe.get('candidate_sha256', recipe.get('candidatehash'))
        before, after = [(ROOT / p).read_bytes() for p in (original, candidate)]
        assert sha(before) == original_hash and sha(after) == candidate_hash
        assert apply(before.decode(), recipe['edits']).encode() == after
        recipes[name] = recipe
        originals.append(before)
        pins[name] = dict(recipe=path, recipe_sha256=sha(raw), original=original,
                          original_sha256=original_hash, candidate=candidate,
                          candidate_sha256=candidate_hash, edits=len(recipe['edits']))
    assert originals[0] == originals[1], 'different original sources'
    orders = []
    texts = []
    for order in [('admission', 'memory'), ('memory', 'admission')]:
        text = originals[0].decode()
        for name in order:
            text = apply(text, recipes[name]['edits'])
        texts.append(text)
        orders.append(dict(order=order, sha256=sha(text.encode())))
    assert texts[0] == texts[1], 'edit orders diverge'
    # Preserve the exact original module interface, including widths and names.
    header = lambda text: text[:text.index(');') + 2]
    assert header(texts[0]) == header(originals[0].decode())
    dest = ROOT / TARGET
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(texts[0])
    result = dict(schema='v105-both-order-composition-v1', status='PASS',
                  recipes=pins, orders=orders, both_orders_identical=True,
                  module_header_byte_identical=True, candidate=TARGET,
                  candidate_sha256=sha(dest.read_bytes()),
                  composer=dict(path=str(Path(__file__).relative_to(ROOT)),
                                sha256=sha(Path(__file__).read_bytes())),
                  scope='Exact source composition only; separate focused and integrated RTL tests required.')
    path = ROOT / 'experiments/python-gamebub-v105/composition.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print('V105_COMPOSE_PASS', result['candidate_sha256'])


if __name__ == '__main__':
    main()
