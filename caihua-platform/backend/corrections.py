"""Versioned, reversible corrections. Source snapshot never overwritten."""
import copy,hashlib,json

def corrected_graph(raw):
 g=copy.deepcopy(raw); nodes={n['id']:n for n in g['nodes']};log=[]
 for n in nodes.values():n.setdefault('active',True)
 for e in g['edges']:e.setdefault('active',True)
 def record(subject,before,after,reason):log.append({'subject':subject,'before':copy.deepcopy(before),'after':copy.deepcopy(after),'reason':reason,'version':'2026-11-08-portable-v1'})
 def add_node(name,group,subtype,mentions):
  existing=next((n for n in nodes.values() if n['name']==name and n['group']==group and n.get('active')),None)
  if existing:return existing
  nid='FIX-E-'+hashlib.sha256((name+group).encode()).hexdigest()[:16];n={'id':nid,'name':name,'group':group,'subtype':subtype,'sids':sorted({m['sid'] for m in mentions}),'mentions':copy.deepcopy(mentions),'attributes':[],'active':True};nodes[nid]=n;return n
 def add_edge(source,target,predicate,sid,evidence,reason,qualifiers=None):
  id='FIX-R-'+hashlib.sha256((source+target+predicate+sid).encode()).hexdigest()[:16]
  e={'id':id,'source':source,'target':target,'predicate':predicate,'sid':sid,'kind':'relations','status':'本轮原文核验','evidence':copy.deepcopy(evidence),'qualifiers':qualifiers or {},'audit_note':reason,'active':True};g['edges'].append(e);record(id,None,e,reason);return e
 zhe=next((n for n in nodes.values() if n['name']=='赭笔' and n['group']=='绘制与加工工具'),None)
 if zhe:
  pen=add_node('笔','绘制与加工工具','绘制工具',zhe['mentions']);color=add_node('赭','色彩','色彩',zhe['mentions'])
  before=copy.deepcopy(zhe);zhe['active']=False;zhe['review_note']='按用户明确复核要求拆为笔与赭色；赭色不直接等同特定矿物颜料。';record(zhe['id'],before,zhe,zhe['review_note'])
  for e in list(g['edges']):
   if e['target']==zhe['id'] and e['predicate']=='使用工具':
    before=copy.deepcopy(e);e['active']=False;record(e['id'],before,e,'撤回把赭笔整体当作工具的关系')
    reason='依据本轮用户要求，将赭笔拆为工具“笔”与色彩“赭”；原文保留，不确认具体颜料矿物。'
    add_edge(e['source'],pen['id'],'使用工具',e['sid'],e.get('evidence',[]),reason,e.get('qualifiers'))
    add_edge(e['source'],color['id'],'使用色彩',e['sid'],e.get('evidence',[]),reason,e.get('qualifiers'))
  for n in nodes.values():
   if n['id']!=zhe['id'] and '赭笔' in n['name']:
    before=copy.deepcopy(n);n['name']=n['name'].replace('赭笔','赭色').replace('旁赭色','以赭色旁描并');record(n['id'],before,n,'步骤/规定采用语义名称，原文证据仍保留赭笔写法')
 # CH028: retain original words, no computed final ratio while source/interpretation conflict remains.
 for n in nodes.values():
  if 'CH-028' in n['sids'] and n['subtype']=='定量规定':
   if '减外缘道三分之一' in n['name']:
    ev=n['mentions'][0].get('evidence',[])
    for pred,val in [('运算词','减'),('原文比例','三分之一')]:
     if not any(a['predicate']==pred for a in n['attributes']):
      a={'id':'FIX-A-'+hashlib.sha256((n['id']+pred).encode()).hexdigest()[:16],'kind':'attributes','sid':'CH-028','source':n['id'],'target':None,'predicate':pred,'value':val,'status':'本轮原文核验','evidence':copy.deepcopy(ev),'qualifiers':{},'audit_note':'仅记录原文运算与比例，不据此裁定争议中的最终宽度比。'};n['attributes'].append(a);record(a['id'],None,a,a['audit_note'])
   if '宽度二分规定' in n['name'] or '宽度一分规定' in n['name']:
    target=next(x for x in nodes.values() if x['name']=='外缘道' and 'CH-028' in x['sids']);which='梁栿' if '二分' in n['name'] else '枓栱'
    for e in g['edges']:
     if e['sid']=='CH-028' and e['source']==n['id']:
      if e['predicate']=='约束对象':
       before=copy.deepcopy(e);e['target']=target['id'];e['qualifiers']['scope']=which+'的缘道宽度';e['status']='本轮原文核验';record(e['id'],before,e,'尺寸约束落到缘道宽度，并保留对应构件范围')
      elif e['predicate']=='参照对象':
       before=copy.deepcopy(e);e['active']=False;record(e['id'],before,e,'绝对尺寸中的被测缘道不是相对尺寸的参照对象，撤回混用关系')
 space=next(n for n in nodes.values() if n['name']=='空缘' and 'CH-028' in n['sids']);outer=next(n for n in nodes.values() if n['name']=='外缘道' and 'CH-028' in n['sids'])
 c=next(x for x in g['corpus'] if x['sid']=='CH-028');quote='外留空缘，与外缘道对晕';start=c['text'].index(quote);ev=[{'source_sid':'CH-028','source_field':'text','quote':quote,'start':start,'end':start+len(quote),'span_valid':True}]
 add_edge(space['id'],outer['id'],'对晕','CH-028',ev,'按老师所提对象关系补齐空缘与外缘道对晕；未展开到梁、栱的交叉配对。')
 # Flag schema-role mismatches rather than silently promoting model candidates.
 rules={'使用色彩':('group','色彩'),'使用材料':('group','材料与颜料'),'使用工具':('group','绘制与加工工具'),'采用设色方法':('subtype','设色方法'),'采用技法':('subtype','技法')}
 for e in g['edges']:
  if e.get('active') and e['predicate'] in rules:
   key,expected=rules[e['predicate']];target=nodes[e['target']]
   if target[key]!=expected:
    before=copy.deepcopy(e);e['status']='待确认';e['audit_note']='本轮规则回查：'+e['predicate']+' 的目标为 '+target['subtype']+'，与预期 '+expected+' 不一致；不能直接改名或自动确认。';record(e['id'],before,e,e['audit_note'])
 g['nodes']=list(nodes.values());g['corrections']=log;g['meta']['version']='可迁移平台初版 / 复核修订 2026-11-08';g['meta']['node_count']=sum(n['active'] for n in g['nodes']);g['meta']['relation_count']=sum(e['active'] for e in g['edges']);g['meta']['attribute_count']=sum(len(n['attributes']) for n in g['nodes'] if n['active']);return g
