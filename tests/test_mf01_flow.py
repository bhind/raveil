import copy,unittest
from raveil import mf01_flow as flow,mf01_grid as grid
from scripts.mf01_flow_cases import pair,diamond,eight,cases
from scripts.mf01_grid_generated import execute_host


class FlowTests(unittest.TestCase):
    def execute(self,value):
        plan=flow.compile(value);stages={s['name']:s['source'] for s in value['stages']};outputs={}
        for row in plan['stages']:
            source=flow.materialize(stages[row['name']],outputs);words=execute_host(grid.compile(source))
            outputs[row['name']]=dict(rows=row['shape'][0],columns=row['shape'][1],words=words)
        return [dict(name=name,**outputs[name]) for name in plan['outputs']]

    def test_direct_composed_formulas_and_author_order(self):
        for name,value,expected in cases():
            old=copy.deepcopy(value)
            with self.subTest(name=name):
                self.assertEqual(self.execute(value),expected);self.assertEqual(flow.reference(value),expected)
                shuffled=copy.deepcopy(value);shuffled['stages'].reverse()
                self.assertEqual(flow.compile(shuffled),flow.compile(value));self.assertEqual(value,old)
        self.assertEqual(flow.compile(diamond()[0])['sessions'],16)
        self.assertEqual(flow.compile(eight()[0])['jobs'],15)

    def test_every_stage_admitted_before_execution(self):
        for kind in ['missing','cycle','self','duplicate','output','duplicate-output','link-extra','link-bool','many','late-invalid','session-cap']:
            value,_=pair()
            if kind=='missing':value['stages'][0]['source']['inputs'][0]={'from':'absent'}
            elif kind=='cycle':value['stages'][1]['source']['inputs'][0]={'from':'second'}
            elif kind=='self':value['stages'][0]['source']['inputs'][0]={'from':'second'}
            elif kind=='duplicate':value['stages'].append(copy.deepcopy(value['stages'][0]))
            elif kind=='output':value['outputs']=['missing']
            elif kind=='duplicate-output':value['outputs']=['second','second']
            elif kind=='link-extra':value['stages'][0]['source']['inputs'][0]={'from':'first','offset':0}
            elif kind=='link-bool':value['stages'][0]['source']['inputs'][0]={'from':True}
            elif kind=='many':value['stages']*=5
            elif kind=='late-invalid':value['stages'][0]['source']['kernel']['nodes'][0]['view']='absent'
            else:
                value,_=diamond();value['stages'][-1]['source']['tile']=[2,3]
            with self.subTest(kind=kind),self.assertRaises(ValueError):flow.compile(value)

    def test_v1_link_shape_inference_and_original_preservation(self):
        value,_=eight();value['stages']=value['stages'][-2:];value['outputs']=['stage-1']
        second=value['stages'][0]['source'];second['schema']=grid.SCHEMA;second.pop('shape');second.pop('post')
        for view in second['kernel']['views'].values():view.pop('row');view.pop('column')
        self.assertEqual(flow.compile(value)['stages'][1]['shape'],[1,1])
        self.assertEqual(self.execute(value)[0]['words'],[15])
