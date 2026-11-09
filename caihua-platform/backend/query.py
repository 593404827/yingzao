QUESTIONS=[('五彩遍装会用到哪些颜色？','colors','五彩遍装'),('碾玉装关联哪些知识？','neighbors','碾玉装'),('有哪些装饰制度？','systems',''),('青绿叠晕棱间装如何用色？','context','青绿叠晕棱间装'),('杂间装有哪些组合做法？','context','杂间装'),('丹粉刷饰在原文中怎么说？','context','丹粉刷饰'),('立刷和横刷谁先谁后？','order','立刷'),('刷白铅粉要刷几遍？','attributes','刷白铅粉'),('横刷使用什么材料？','material','横刷'),('还有哪些知识待确认？','pending','')]
def allowed(a,level):return level=='pending' or (a.get('status') in ['已核验','本轮原文核验'] if level=='verified' else a.get('status')!='待确认')
def search(g,text):
 aliases={'赭笔':['笔','赭'],'赭色':['赭']}; names=aliases.get(text,[text]);return [n for n in g['nodes'] if any(t in n['name'] for t in names)]
def run(g,params):
 i=params.get('preset');text=str(params.get('text','')).strip();level=params.get('level','all')
 if i is not None:
  i=int(i)
  if i not in range(len(QUESTIONS)):raise ValueError('预设问题编号无效')
  question,kind,name=QUESTIONS[i]
 else:
  hits=sorted((n['name'] for n in g['nodes'] if n['name'] in text),key=len,reverse=True);name=hits[0] if hits else text;question=text
  kind='colors' if any(x in text for x in ['颜色','色彩','用色']) else 'neighbors'
 roots=[n for n in g['nodes'] if n['name']==name];ids={n['id'] for n in roots};edges=[e for e in g['edges'] if allowed(e,level)];nm={n['id']:n for n in g['nodes']};paths=[];rows=[];sources=[]
 if kind=='systems':
  roots=[n for n in g['nodes'] if n['subtype']=='装饰制度'];resultedges=[];summary=f'检索到 {len(roots)} 个装饰制度候选名称（含简称、组合做法，非平行制度种类数）。'
 elif kind=='pending':
  resultedges=[e for e in g['edges'] if e['status']=='待确认'];summary=f'待确认关系 {len(resultedges)} 条；既有挂起断言 {len(g["suspended"])} 条。'
 elif kind=='context':
  sids={s for n in roots for s in n['sids']};sources=[c for c in g['corpus'] if c['sid'] in sids];resultedges=[e for e in edges if e['sid'] in sids];summary='返回该名称出现条目的原文及候选关系；同条共现不自动等于归属关系。'
 elif kind=='attributes':
  rows=[a for n in roots for a in n['attributes'] if a['predicate']=='施作遍数' and allowed(a,level)];resultedges=[];summary='；'.join(name+'：'+str(a['value']) for a in rows) or '当前筛选下没有记录。'
 elif kind=='colors':
  for a in edges:
   if a['source'] in ids and a['predicate']=='使用色彩' and nm[a['target']]['group']=='色彩':paths.append([a])
   if a['source'] in ids and a['predicate'] in ['采用技法','采用设色方法','包含步骤']:
    for b in edges:
     if b['source']==a['target'] and b['sid']==a['sid'] and b['predicate']=='使用色彩' and nm[b['target']]['group']=='色彩':paths.append([a,b])
  seen=set();resultedges=[]
  for p in paths:
   for e in p:
    if e['id'] not in seen:resultedges.append(e);seen.add(e['id'])
  colors=sorted({nm[p[-1]['target']]['name'] for p in paths});summary=(name+'可检索到：'+'、'.join(colors)+'。请结合每条路径的部位、技法与备选条件理解。') if colors else '当前筛选下没有完整用色路径，不等于原典未记载。'
 else:
  resultedges=[e for e in edges if (e['source'] in ids or e['target'] in ids) and (kind!='material' or e['predicate']=='使用材料') and (kind!='order' or e['predicate']=='先于')];summary=f'检索到 {len(resultedges)} 条关系。'
 nodeids={n['id'] for n in roots}|{x for e in resultedges for x in [e['source'],e['target']]}
 return {'question':question,'kind':kind,'summary':summary,'root_ids':[n['id'] for n in roots],'nodes':[n for n in g['nodes'] if n['id'] in nodeids],'edges':resultedges,'attributes':rows,'paths':paths,'sources':sources,'suspended':g['suspended'] if kind=='pending' else []}
