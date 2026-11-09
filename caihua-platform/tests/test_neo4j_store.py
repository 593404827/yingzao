import json,unittest
from unittest.mock import patch
from backend import neo4j_store as neo

class Neo4jStoreTests(unittest.TestCase):
 def test_graph_filters_retired_records_and_preserves_evidence(self):
  meta={'meta':{'entries':77},'corpus':[{'sid':'CH-028'}]}
  a={'id':'a','attributes':[{'value':'三分之一'}]};b={'id':'b','attributes':[],'active':False}
  edge={'id':'r','source':'a','target':'b','evidence':[{'quote':'原文'}]}
  response=[[[json.dumps(meta)]],[[json.dumps(a)],[json.dumps(b)]],[[json.dumps(edge)]]]
  with patch.object(neo,'query',return_value=response):
   g=neo.graph();self.assertEqual(len(g['nodes']),1);self.assertFalse(g['edges'])
   full=neo.graph(True);self.assertEqual(full['edges'][0]['evidence'],edge['evidence'])
 def test_conflicting_revision_does_not_claim_success(self):
  before={'id':'e','source':'a','target':'b','predicate':'使用色彩','status':'候选'}
  with patch.object(neo,'query',side_effect=[[[[json.dumps(before),0]]],[[],[]]]) as call:
   with self.assertRaises(ValueError):neo.apply_change('edge','e',{'status':'待确认'},'test','change')
   statements=call.call_args.args[0]
   self.assertIn('WITH DISTINCT c',statements[1][0])
   self.assertNotIn('WITH count(r)',statements[1][0])
 def test_transaction_errors_are_not_ignored(self):
  from io import BytesIO
  with patch('urllib.request.urlopen',return_value=BytesIO(json.dumps({'errors':[{'code':'X','message':'failed'}]}).encode())):
   with self.assertRaises(RuntimeError):neo.query([('RETURN 1',{})])
