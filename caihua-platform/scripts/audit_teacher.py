"""Compare teacher concerns to active graph; never declare all 229 resolved."""
from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));from backend import storage
raw=json.loads((ROOT/'data/raw/graph.original.json').read_text());g=storage.graph();nm={n['id']:n for n in g['nodes']};rows=[]
def add(topic,previous,current,result,reason):rows.append({'topic':topic,'previous':previous,'current':current,'result':result,'reason':reason})
z=[n for n in g['nodes'] if n['name']=='赭笔'];related=[e for e in g['edges'] if e['predicate']=='使用工具' and nm[e['target']]['name']=='笔' and e['sid'] in ['CH-009','CH-031','CH-045']];colors=[e for e in g['edges'] if e['predicate']=='使用色彩' and nm[e['target']]['name']=='赭' and e['sid'] in ['CH-009','CH-031','CH-045']]
add('赭笔整体被当作工具','旧版在 CH-009/031/045 合并为赭笔工具实体',f'当前赭笔有效实体 {len(z)}；笔的使用工具关系 {len(related)} 条；赭色关系 {len(colors)} 条','本轮修正','遵循用户明确拆分要求；旧实体及三条旧关系撤回，原文不改。赭色不等同特定矿物颜料。')
for name in ['诸华间杂','内施五彩诸华','五彩诸华']:
 bad=[n for n in g['nodes'] if n['name']==name and 'CH-028' in n['sids']];add('CH-028 '+name,'截图中作为技法或纹样整体提取',f'当前对应实体 {len(bad)} 个','当前未复现该旧错误' if not bad else '仍需复核','当前用诸华作为纹样、五彩设色作为设色方法；不把间杂直接当独立技法。')
p=[n for n in g['nodes'] if n['group']=='纹样及其要素'];bad=[(n['name'],a['predicate'],a['value']) for n in p for a in n['attributes'] if a['predicate'] in ['品第','等级','等第']];add('纹样没有品第','老师指出纹样无品第',str(bad) if bad else '当前有效纹样属性中无品第/等级/等第','当前检查通过' if not bad else '仍需复核','列举种类数与价值等级区分。')
r=[e for e in g['edges'] if e['sid']=='CH-028' and e['predicate']=='对晕'];add('空缘与外缘道对晕','截图质疑对象关系不完整',f'当前直接对晕关系 {len(r)} 条','本轮补齐','保留对晕技法，同时补齐空缘→对晕→外缘道；不跨构件配对。')
wrong=[e for e in g['edges'] if e['sid']=='CH-028' and e['predicate'] in ['包含部位','包含区域'] and nm[e['source']]['name'] in ['外棱','梁外棱四周','栱外棱四周'] and '缘道' in nm[e['target']]['name']];add('外棱四周不宜包含缘道','截图质疑层级关系',f'该模式有效关系 {len(wrong)} 条','当前检查通过' if not wrong else '仍需复核','当前部位统一在施作对象/构件部位下，未保留截图中的包含区域层级。')
n=next(n for n in g['nodes'] if n['name']=='空缘宽度减外缘道三分之一规定');add('减与三分之一如何记录','截图要求补充运算和比例',json.dumps([(a['predicate'],a['value']) for a in n['attributes']],ensure_ascii=False),'部分修正、解释仍待确认','本轮记录运算词=减、原文比例=三分之一；原文与题解的最终比例解释不擅自裁定。')
for name in ['梁栿缘道宽度二分规定','枓栱缘道宽度一分规定']:
 n=next(n for n in g['nodes'] if n['name']==name);rel=[e for e in g['edges'] if e['source']==n['id']];add('尺寸主语与量值：'+name,'截图提出保留对象与尺寸值分离',json.dumps([{'relation':e['predicate'],'target':nm[e['target']]['name'],'scope':e['qualifiers'].get('scope','')} for e in rel],ensure_ascii=False),'本轮修正','约束对象改为缘道，构件写入范围；不将被测对象误作参照对象，分°不当厘米。')
issue_file=ROOT/'data/reports/关系类别越界_待复核.json'
if issue_file.exists():
 for x in json.loads(issue_file.read_text()):
  add('关系类别越界 '+x['sid']+' / '+x['id'],x['subject']+'→'+x['predicate']+'→'+x['object'],'目标子类为'+x['actual_subtype']+'，预期'+x['expected'],'本轮新增待确认','保留原模型候选与证据，不自动更改为另一种关系；默认回答排除。')
# Audit all earlier issue rows as lineage checks; status remains historical, not fresh semantic endorsement.
ledger=json.loads((ROOT/'data/raw/audit_229.json').read_text());trail=[]
for item in ledger:
 sid=item['条目'];ns=[n for n in g['nodes'] if sid in n['sids']];es=[e for e in g['edges'] if e['sid']==sid];trail.append({'id':item['问题编号'],'sid':sid,'question':item['原问题'],'historical_status':item['审核状态'],'previous_decision':item['处理与修改建议'],'current_entity_count':len(ns),'current_relation_count':len(es),'current_pending_relation_count':sum(e['status']=='待确认' for e in es),'scope':'条目级回查计数，不等于该问题已重新通过专家审核'})
report={'checks':rows,'historical_issues':trail,'corrections':storage.history(),'note':'本次对截图关注点和赭笔做具体核对；229项建立逐项可追踪索引，未将全部问题冒称本轮语义审核通过。'}
(ROOT/'data/reports/teacher_review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));lines=['# 老师意见与当前知识表达回查','',report['note'],'']
for x in rows:lines += ['## '+x['topic'],'','原问题：'+x['previous'],'','当前：'+x['current'],'','结论：'+x['result'],'','处理说明：'+x['reason'],'']
(ROOT/'data/reports/老师意见回查.md').write_text('\n'.join(lines));print(json.dumps({'active_nodes':g['meta']['node_count'],'active_relations':g['meta']['relation_count'],'checks':len(rows),'historical_issues':len(trail),'zhebi_active':len(z)},ensure_ascii=False))
