import json,re,hashlib
from pathlib import Path
root=Path(r'E:\Saint\PROJECTS\CouncilFlow-main')
plan=json.loads((root/'reports/councilflow-hardening/planner/plan.json').read_text(encoding='utf-8'))
current={x['id']:x['criterion'] for x in plan['acceptance'] if x['id'].startswith('E')}
frozen=(root/'docs/gate3/CouncilFlow-Gate3-v0.2/02-GATE3-v0.2-FROZEN.md').read_text(encoding='utf-8')
c3=(root/'docs/gate3/CouncilFlow-Gate3-v0.2/06-COUNCIL-APPROVED-ERRATUM-C3.md').read_text(encoding='utf-8')
def body(text, header):
 m=re.search(r'(?m)^'+re.escape(header)+r'\s*$',text)
 if not m:return None
 rest=text[m.end():]
 end=re.search(r'(?m)^#{1,3} ',rest)
 return rest[:end.start()].strip('\n') if end else rest.strip('\n')
rows=[]
for n in range(1,11):
 k=f'E{n}'
 if n==4:
  h='E4 — Custom-agent loading'; e=h+'\n'+body(c3,'## '+h)
 else:
  m=re.search(rf'(?m)^### (E{n} — .+)$',frozen); h=m.group(1); e=h+'\n'+body(frozen,'### '+h)
 a=current.get(k)
 rows.append({'id':k,'exact_text_match':a==e,'actual_sha256':hashlib.sha256((a or '').encode()).hexdigest(),'expected_sha256':hashlib.sha256(e.encode()).hexdigest(),'actual':a,'expected':e})
p=root/'reports/councilflow-hardening/tester-final/criteria-check.json'; p.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print([(r['id'],r['exact_text_match']) for r in rows])
