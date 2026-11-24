"""validate_sequence keeps its exact first error after being split into rule groups.

sequence-split-golden.json was generated with the unsplit validate_sequence from
main (bdda379). This test rebuilds the same seeded mutations of the shared contract
fixtures (drop, swap, duplicate, edit or delete a field) and requires the same
result for each: "ok", or the same (code, field, message) of the first failure.
Each case also stores the SHA-256 of its input, so a changed generator is caught
instead of silently comparing different inputs.
"""
import copy
import hashlib
import json
from pathlib import Path
import random
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_contracts as fixtures
import test_tester_selection as selection

c = fixtures.c
GOLDEN = Path(__file__).resolve().parent / "fixtures" / "sequence-split-golden.json"
POOL = [None, "X", 0, 1, 2, True, "M1", "M2", "M3", "M5", "M5b", "failed", "blocked", "passed",
        "rework", "accept", "reject", "worker", "tester", "reviewer", "manager", "A2", [], {}]
MUTATIONS_PER_BASE = 220


def _leaves(value, path=()):
    if isinstance(value, dict):
        for key, item in value.items():
            yield from _leaves(item, path + (key,))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _leaves(item, path + (index,))
    yield path


def _mutate(rng, messages):
    messages = copy.deepcopy(messages)
    operation, count = rng.randrange(5), len(messages)
    index = rng.randrange(count)
    if operation == 0:
        del messages[index]
    elif operation == 1:
        other = rng.randrange(count)
        messages[index], messages[other] = messages[other], messages[index]
    elif operation == 2:
        messages.insert(rng.randrange(count + 1), copy.deepcopy(messages[index]))
    else:
        path = rng.choice([p for p in _leaves(messages[index]) if p])
        parent = messages[index]
        for key in path[:-1]:
            parent = parent[key]
        if operation == 3:
            parent[path[-1]] = rng.choice(POOL)
        elif isinstance(parent, dict):
            del parent[path[-1]]
    return messages


def cases():
    rng = random.Random(20261124)
    bases = [fixtures.sequence(), selection.base_chain(), selection.chain_with_reviewer_citing("M5")]
    for base in bases:
        yield base
        for number in range(MUTATIONS_PER_BASE):
            once = _mutate(rng, base)
            yield _mutate(rng, once) if number % 3 == 2 else once


def outcome(module, messages):
    try:
        module.validate_sequence(copy.deepcopy(messages))
        return "ok"
    except module.ContractError as error:
        return [error.code, error.field, str(error)]


def digest(messages):
    return hashlib.sha256(json.dumps(messages, sort_keys=True).encode("utf-8")).hexdigest()


class SequenceSplitTests(unittest.TestCase):
    def test_first_error_unchanged_for_every_case(self):
        golden = json.loads(GOLDEN.read_text(encoding="utf-8"))
        generated = list(cases())
        self.assertEqual(len(generated), len(golden))
        for number, (messages, expected) in enumerate(zip(generated, golden)):
            with self.subTest(case=number):
                self.assertEqual(digest(messages), expected["input_sha256"], "case generator changed")
                self.assertEqual(outcome(c, messages), expected["result"])

    def test_golden_covers_many_rules(self):
        golden = json.loads(GOLDEN.read_text(encoding="utf-8"))
        codes = {case["result"][0] for case in golden if case["result"] != "ok"}
        self.assertGreaterEqual(len(codes), 15)
        self.assertIn("ok", [case["result"] for case in golden])


if __name__ == "__main__":
    if sys.argv[1:2] == ["--write"]:
        # Write with the unsplit function, e.g. a copy of main's contracts.py importable as argv[2].
        reference = __import__(sys.argv[2])
        GOLDEN.write_text(json.dumps([{"input_sha256": digest(m), "result": outcome(reference, m)} for m in cases()],
                                     indent=0) + "\n", encoding="utf-8", newline="\n")
    else:
        unittest.main()
