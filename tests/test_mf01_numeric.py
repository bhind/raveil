import copy,random,unittest
from raveil import mf01_grid as g,fold_dag as d,mf01_grid_plan as planner,mf01_flow as flow,mf01_flow_plan as flow_plan
from raveil.grid_assembly import assemble
from scripts.mf01_numeric_cases import cases,pointwise,EDGES,signed,gemm_bias_relu,MASK


def execute(value):
    compiled=g.compile(value);outputs=[]
    for item in compiled['batch']['items']:
        state=d.State(item['dag'])
        for i in range(len(item['dag']['jobs'])):
            job,_,writes=state.resolve(i)
            assert all(n['op'] not in ('max_i32','relu_i32') for n in job['region']['nodes'])
            state.commit(i,writes,d.reference(job['region'],job['inputs']),True)
        outputs.append(dict(name=item['name'],shape=item['dag']['jobs'][-1]['region']['shape'],words=state.final()['output']))
    return assemble(outputs,compiled['layout'],compiled['rows'],compiled['columns'])


class NumericTests(unittest.TestCase):
    def test_edges_partitions_and_post_fold_order(self):
        for name,value,expected in cases():
            with self.subTest(name=name):
                before=copy.deepcopy(value)
                self.assertEqual(execute(value),expected);self.assertEqual(g.reference(value),expected)
                self.assertEqual(value,before)
    def test_deterministic_full_word_pairs(self):
        rng=random.Random(229)
        for _ in range(24):
            a=[signed(rng.getrandbits(32)) for _ in range(9)];b=[signed(rng.getrandbits(32)) for _ in range(11)]
            value,expected=pointwise(a,b,tile=(5,6))
            self.assertEqual(execute(value),expected);self.assertEqual(g.reference(value),expected)
    def test_generated_names_cannot_capture_later_user_identifiers(self):
        value,expected=pointwise(EDGES,EDGES)
        nodes=value['kernel']['nodes'];nodes[0]['id']='__mf01_numeric_0';nodes[2]['args'][0]='__mf01_numeric_0'
        nodes[2]['id']='__mf01_numeric_1';value['kernel']['result']='__mf01_numeric_1'
        self.assertEqual(execute(value),expected)
    def test_malformed_original_programs_reject(self):
        base,_=pointwise(EDGES,EDGES)
        for change in [lambda n:n.update(args=['a']),lambda n:n.update(args=['a',True]),lambda n:n.update(args=['a',[]]),
                       lambda n:n.update(args=['a','x']),lambda n:n.update(id='a'),lambda n:n.update(op='min_i32'),
                       lambda n:n.update(imm=0),lambda n:n.update(op=[]),lambda n:n.update(id=[])]:
            value=copy.deepcopy(base);change(value['kernel']['nodes'][-1])
            with self.subTest(node=value['kernel']['nodes'][-1]),self.assertRaises(ValueError):g.compile(value)
        for result in [None,[],True,'missing']:
            value=copy.deepcopy(base);value['kernel']['result']=result
            with self.assertRaises(ValueError):g.compile(value)
        for nodes in [None,[],[None]]:
            value=copy.deepcopy(base);value['kernel']['nodes']=nodes
            with self.assertRaises(ValueError):g.compile(value)
    def test_resource_limits_apply_after_expansion(self):
        value,_=pointwise(EDGES,EDGES);previous='x'
        for i in range(6):
            name=f'next{i}';value['kernel']['nodes'].append(dict(id=name,op='add_imm',args=[previous],imm=1));previous=name
        value['kernel']['result']=previous
        with self.assertRaisesRegex(ValueError,'fifteen map nodes'):g.compile(value)
        with self.assertRaisesRegex(ValueError,'no admitted uniform tile'):planner.plan(value)
    def test_old_versions_reject_signed_nodes_and_keep_unsigned_max(self):
        value,_=pointwise(EDGES,EDGES)
        value['schema']=g.SCHEMA_V2
        with self.assertRaises(ValueError):g.compile(value)
        value['kernel']['nodes'][-1]['op']='max'
        self.assertEqual(execute(value),[max(x&MASK,y&MASK) for x in EDGES for y in EDGES])
        value['schema']=g.SCHEMA_V3
        value['post']=dict(nodes=[dict(id='r',op='load',view='reduced'),dict(id='x',op='relu_i32',args=['r'])],result='x')
        with self.assertRaises(ValueError):g.compile(value)
    def test_unsigned_fold_and_threshold_remain_explicit(self):
        value,_=pointwise([-3,-1],[-2])
        value['kernel']['fold']='max';value['kernel']['extent']=2
        self.assertEqual(execute(value),[(-2)&MASK,(-1)&MASK])
        value['kernel']['nodes'].append(dict(id='threshold',op='ge_imm',args=['x'],imm=1));value['kernel']['result']='threshold'
        self.assertEqual(execute(value),[1,1])
    def test_signed_gemm_bias_relu_and_flow_plan(self):
        value,expected=gemm_bias_relu();before=copy.deepcopy(value)
        proposal=flow_plan.plan(value);result=flow.reference(proposal['source'])
        self.assertEqual(result,[dict(name='activation',rows=3,columns=5,words=expected)])
        self.assertEqual(value,before);self.assertEqual(proposal['sessions'],2)
        self.assertIn(0,expected);self.assertTrue(any(x>0 for x in expected))
        outputs={}
        for name in flow.compile(value)['order']:
            stage=next(s for s in value['stages'] if s['name']==name);material=flow.materialize(stage['source'],outputs)
            outputs[name]=dict(rows=3,columns=5,words=execute(material))
        self.assertEqual(outputs['activation']['words'],expected)
