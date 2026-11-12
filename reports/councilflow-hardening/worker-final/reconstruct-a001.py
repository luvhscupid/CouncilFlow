import ast, hashlib, json
from pathlib import Path
src=Path('tests/test_contracts.py').read_text(encoding='utf-8')
expected='a6776471d5010b15a88f86b9b2e96a635b2c718b2ef731b32d4e92c1f97fc333'
tree=ast.parse(src)
node=next(n for cls in tree.body if isinstance(cls,ast.ClassDef) for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='test_plan_criteria_preserve_multiline_text_but_reject_other_controls')
lines=src.splitlines(keepends=True)
del lines[node.lineno-1:node.end_lineno]
src=''.join(lines).replace('\n\n    def test_original_plan_and_final_acceptance_cannot_be_weakened','\n    def test_original_plan_and_final_acceptance_cannot_be_weakened',1)
start=src.index('    def test_published_json_message_examples_match_current_contract(self):')
end=src.index('    def test_plan_artifact_acceptance_is_checked_not_only_packet(self):',start)
prefix,suffix=src[:start],src[end:]
method=('    def test_published_json_message_examples_match_current_contract(self):\n'
        '        examples = ROOT / "docs" / "CouncilFlow-Full-Plan" / "examples"\n'
        '        for name in ("job.assign.json", "job.report.json"):\n'
        '            with self.subTest(name=name):\n'
        '                packet = c.loads((examples / name).read_bytes())\n'
        '                c.validate_message(packet)\n')
for gap in range(4):
 candidate=(prefix+method+'\n'*gap+suffix).encode('utf-8')
 digest=hashlib.sha256(candidate).hexdigest()
 print(json.dumps({'gap':gap,'sha256':digest,'matches':digest==expected}))
 if digest==expected:
  out=Path('reports/councilflow-hardening/worker-final/reconstructed/A001/tests/test_contracts.py')
  out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(candidate);break
