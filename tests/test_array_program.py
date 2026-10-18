"""Host compiler/interpreter UT; no QEMU/RTL execution evidence."""
import copy
import random
import unittest
from unittest.mock import patch
from raveil import array_program as a, mf01_grid as grid
from tests.test_mf01_numeric import execute as execute_grid


def literal(rows=2, columns=3, words=None):
    return dict(schema='raveil.grid-input/v2', rows=rows, columns=columns,
                words=list(range(rows*columns)) if words is None else words)


def source(rows=2, columns=3, nodes=None):
    nodes = nodes or [dict(id='x', op='load', view='v'), dict(id='y', op='add_imm', args=['x'], imm=3)]
    return dict(inputs=[literal(rows, columns)], shape=[rows, columns], boundary='zero',
                kernel=dict(extent=1, fold='sum', views={'v': dict(input=0, offset=[0,0], row=[1,0], column=[0,1], step=[0,0])},
                            nodes=nodes, result=nodes[-1]['id']))


def program(s=None):
    return dict(schema=a.SCHEMA, stages=[dict(name='answer', source=s or source())], outputs=['answer'])


def execute(value):
    plan=a.compile(value); planes={}
    for step in plan['passes']:
        src=a.bind(value,step,planes)
        words=execute_grid(src)
        a.commit(planes,step,dict(rows=step['shape'][0],columns=step['shape'][1],words=words))
    return a.publish(plan,planes)


def chain(count, rows=1, columns=1):
    nodes=[dict(id='n0',op='load',view='v')]
    nodes.extend(dict(id=f'n{i}',op='add_imm',args=[f'n{i-1}'],imm=1) for i in range(1,count))
    return program(source(rows,columns,nodes))


def gemm(m=3,n=4,k=5):
    s=source(m,n);s['inputs']=[literal(m,k),literal(k,n)]
    s['kernel'].update(extent=k,views={
        'left':dict(input=0,offset=[0,0],row=[1,0],column=[0,0],step=[0,1]),
        'right':dict(input=1,offset=[0,0],row=[0,0],column=[0,1],step=[1,0])},
        nodes=[dict(id='a',op='load',view='left'),dict(id='b',op='load',view='right'),dict(id='c',op='mul',args=['a','b'])],result='c')
    return program(s)


class ArrayCompilerTests(unittest.TestCase):
    def assert_program(self,value,expected=None):
        before=copy.deepcopy(value); actual=execute(value)
        self.assertEqual(actual,a.reference(value));self.assertEqual(value,before)
        if expected is not None:self.assertEqual(actual[0]['words'],expected)
        return actual

    def test_long_chain_and_full_128_node_boundary(self):
        for count in (16,40,128):
            value=chain(count); self.assert_program(value,[count-1])
            self.assertEqual(len(a.compile(value)['passes']),count)
        with self.assertRaises(ValueError):a.compile(chain(129))
        s=chain(16)['stages'][0]['source'];old=dict(schema=grid.SCHEMA_V5,tile=[16,16],**s)
        with self.assertRaises(ValueError):grid.compile(old)

    def test_nine_live_values_split_without_relaxing_registers(self):
        nodes=[dict(id=f'n{i}',op='load',view='v') for i in range(9)]
        prev='n0'
        for i in range(1,9):
            nodes.append(dict(id=f's{i}',op='add',args=[prev,f'n{i}']));prev=f's{i}'
        s=source(1,1,nodes);s['inputs'][0]['words']=[7]
        self.assert_program(program(s),[63])
        plan=a.compile(program(s));self.assertTrue(all(not x['release'] for x in plan['passes'][:8]))

    def test_gemm_shape_changes_and_transpose(self):
        for m,n,k in [(1,1,1),(3,4,5),(17,3,2)]:
            v=gemm(m,n,k)
            expected=[sum((r*k+t)*(t*n+c) for t in range(k))&a.MASK for r in range(m) for c in range(n)]
            self.assert_program(v,expected)
        s=source(3,2,[dict(id='x',op='load',view='v')]);s['inputs']=[literal(2,3)]
        s['kernel']['views']['v'].update(row=[0,1],column=[1,0])
        self.assert_program(program(s),[0,3,1,4,2,5])

    def test_boundaries_sparse_sampling_broadcast_and_large_shape(self):
        for mode,expected in [('zero',[0,0,0,0,0,0]),('clamp',[0,2,2,3,5,5]),('wrap',[3,3,3,0,0,0])]:
            s=source(2,3,[dict(id='x',op='load',view='v')]);s['boundary']=mode
            s['kernel']['views']['v'].update(offset=[-1,-3],row=[63,0],column=[0,63])
            self.assert_program(program(s),expected)
        s=source(64,64,[dict(id='x',op='load',view='v')]);s['inputs']=[literal(1,1,[17])]
        s['kernel']['views']['v'].update(row=[0,0],column=[0,0])
        self.assert_program(program(s),[17]*4096)
        self.assertEqual(a.compile(program(s))['sessions'],16)

    def test_all_numeric_ops_and_wrapping_before_signed_compare(self):
        values=[0,1,0x7fffffff,0x80000000,0xffffffff]
        for op in a.OPS:
            s=source(1,5);s['inputs'][0]['words']=values
            node=dict(id='z',op=op,args=['x'] if a.OPS[op]==1 else ['x','y'])
            if op in ('add_imm','ge_imm'):node['imm']=(1<<22)-1
            s['kernel']['nodes'].append(node);s['kernel']['result']='z'
            self.assert_program(program(s))
        s=source(1,1);s['inputs'][0]['words']=[0x7fffffff]
        s['kernel']['nodes'][-1]['imm']=1
        s['kernel']['nodes'].append(dict(id='r',op='relu_i32',args=['y']));s['kernel']['result']='r'
        self.assert_program(program(s),[0])

    def test_fold_unsigned_max_and_post_after_complete_sum(self):
        s=source(1,1,[dict(id='x',op='load',view='v')]);s['inputs']=[literal(1,2,[0xffffffff,2])]
        s['kernel']['extent']=2;s['kernel']['views']['v']['step']=[0,1]
        s['post']=dict(nodes=[dict(id='r',op='load',view='reduced'),dict(id='z',op='relu_i32',args=['r'])],result='z')
        self.assert_program(program(s),[1])  # ReLU per term would produce 2.
        s.pop('post');s['kernel']['fold']='max';self.assert_program(program(s),[0xffffffff])
        s['kernel']['extent']=64;s['kernel']['views']['v']['step']=[0,0]
        self.assert_program(program(s),[0xffffffff]);self.assertEqual(len(a.compile(program(s))['passes']),127)

    def test_stage_fanout_join_multiple_outputs_and_order(self):
        v=program(); base=copy.deepcopy(v['stages'][0]);base['name']='base'
        left=dict(name='left',source=source());left['source']['inputs']=[{'from':'base'}]
        right=copy.deepcopy(left);right['name']='right';right['source']['kernel']['nodes'][-1]['imm']=7
        join=dict(name='join',source=source());join['source']['inputs']=[{'from':'left'},{'from':'right'}]
        join['source']['kernel']['views']['w']=dict(input=1,offset=[0,0],row=[1,0],column=[0,1],step=[0,0])
        join['source']['kernel'].update(nodes=[dict(id='x',op='load',view='v'),dict(id='y',op='load',view='w'),dict(id='z',op='add',args=['x','y'])],result='z')
        v.update(stages=[join,right,base,left],outputs=['join','base'])
        out=self.assert_program(v);self.assertEqual(out[0]['words'],[16,18,20,22,24,26])
        plan=a.compile(v);v['stages'].reverse();self.assertEqual(a.compile(v),plan)
        self.assertEqual(len(out),2)

    def test_structure_plan_independent_of_words_and_mutations(self):
        v=gemm();plan=a.compile(v)
        for operand in v['stages'][0]['source']['inputs']:operand['words']=[a.MASK]*len(operand['words'])
        self.assertEqual(a.compile(v),plan)
        step=plan['passes'][0];bound=a.bind(v,step,{})
        bound['inputs'][0]['words'][0]=0
        self.assertEqual(v['stages'][0]['source']['inputs'][0]['words'][0],a.MASK)

    def test_lifetimes_bound_every_operand_and_pin_only_requested_outputs(self):
        v=gemm();plan=a.compile(v);live=set()
        for step in plan['passes']:
            self.assertTrue(set(step['args'])<=live);live.add(step['id'])
            for ref in step['release']:live.remove(ref)
        self.assertEqual(live,{o['producer'] for o in plan['outputs']})
        v=chain(128);self.assertLessEqual(a.compile(v)['peak_plane_words'],4)

    def test_resource_boundaries_and_preflight_backend_admission(self):
        v=chain(8,64,64);plan=a.compile(v)
        self.assertEqual(plan['sessions'],128);self.assertEqual(plan['work_words'],32768)
        with self.assertRaises(ValueError):a.compile(chain(9,64,64))
        v=chain(65);v['stages'][0]['source']['kernel']['extent']=2
        with self.assertRaises(ValueError):a.compile(v)
        v=program();peak=a.compile(v)['peak_plane_words']
        with patch.object(a,'MAX_PLANES',peak):a.compile(v)
        with patch.object(a,'MAX_PLANES',peak-1),self.assertRaises(ValueError):a.compile(v)
        with patch.object(grid,'compile',side_effect=ValueError('backend rejection')),self.assertRaisesRegex(ValueError,'backend rejection'):a.compile(v)
        # Real global plane limit: sixteen retained literal 64x64 grids exceed it with any result.
        s=source(1,1);s['inputs']=[literal(64,64) for _ in range(8)]
        v=program(s);v['stages'].append(dict(name='second',source=copy.deepcopy(s)))
        with self.assertRaisesRegex(ValueError,'plane'):a.compile(v)

    def test_all_declared_nodes_stages_and_inputs_are_validated(self):
        v=program();v['stages'].append(dict(name='unused',source=source()))
        self.assertEqual(len(a.compile(v)['passes']),4)
        v['stages'][1]['source']['kernel']['nodes'][-1]['op']='division'
        with self.assertRaises(ValueError):a.compile(v)
        v=program();s=v['stages'][0]['source'];s['inputs']*=8
        self.assert_program(v);s['inputs'].append(literal())
        with self.assertRaises(ValueError):a.compile(v)

    def test_strict_types_fields_topology_views_immediates(self):
        changes=[lambda v:v.update(schema='unknown'),lambda v:v.update(outputs=['answer','answer']),
                 lambda v:v.update(outputs=[[]]),lambda v:v.update(stages=[]),lambda v:v.update(extra=0)]
        schanges=[lambda s:s.update(tile=[1,1]),lambda s:s.update(shape=[True,2]),lambda s:s.update(shape=[65,1]),
                  lambda s:s.update(boundary=[]),lambda s:s.update(inputs=[{'from':'missing'}]),
                  lambda s:s.update(inputs=[{'from':'answer'}]),lambda s:s.update(inputs=[{'from':[]}]),
                  lambda s:s['kernel'].update(extent=0),lambda s:s['kernel'].update(fold=[]),
                  lambda s:s['kernel']['views']['v'].update(step=[-1,0]),lambda s:s['kernel']['views']['v'].update(input=True),
                  lambda s:s['kernel'].update(result=[]),lambda s:s['kernel'].update(nodes=[None]),
                  lambda s:s['kernel']['nodes'][-1].update(imm=True),lambda s:s['kernel']['nodes'][-1].update(imm=1<<22),
                  lambda s:s['kernel']['nodes'][-1].update(args=['missing']),lambda s:s['kernel']['nodes'][-1].update(id='x'),
                  lambda s:s['kernel']['nodes'][0].update(view='missing'),lambda s:s['kernel']['nodes'][-1].update(op=[]),
                  lambda s:s['inputs'][0].update(words=[True]*6),lambda s:s.update(post={'nodes':[dict(id='p',op='load',view='v')],'result':'p'})]
        for change in changes:
            v=program();change(v)
            with self.subTest(value=v),self.assertRaises(ValueError):a.compile(v)
        for change in schanges:
            v=program();change(v['stages'][0]['source'])
            with self.subTest(value=v),self.assertRaises(ValueError):a.compile(v)
        for value in [None,[],True,{'schema':a.SCHEMA}]:
            with self.assertRaises(ValueError):a.compile(value)

    def test_deterministic_generated_combinations(self):
        rng=random.Random(235)
        for index in range(60):
            rows,columns=rng.randrange(1,5),rng.randrange(1,5)
            s=source(rows,columns);s['inputs'][0]['words']=[rng.getrandbits(32) for _ in range(rows*columns)]
            s['boundary']=rng.choice(['zero','clamp','wrap']);k=s['kernel'];k['extent']=rng.randrange(1,4);k['fold']=rng.choice(['sum','max'])
            k['views']['v'].update(offset=[rng.randrange(-2,3),rng.randrange(-2,3)],step=[0,1])
            for i in range(2,rng.randrange(4,12)):
                op=rng.choice(list(a.OPS));args=[rng.choice(k['nodes'])['id'] for _ in range(a.OPS[op])]
                n=dict(id=f'n{i}',op=op,args=args)
                if op.endswith('_imm'):n['imm']=rng.randrange(1<<22)
                k['nodes'].append(n)
            k['result']=k['nodes'][-1]['id']
            if index%2:s['post']=dict(nodes=[dict(id='r',op='load',view='reduced'),dict(id='p',op='relu_i32',args=['r'])],result='p')
            with self.subTest(index=index):self.assert_program(program(s))

    def test_owned_common_input_examples(self):
        import json
        from pathlib import Path
        paths=sorted((Path(__file__).resolve().parents[1]/'examples/array-program').glob('*.json'))
        self.assertEqual({p.name for p in paths}, {'pointwise.json', 'gemm.json', 'stencil.json',
            'long-expression.json', 'fused-gemm.json', 'fused-long-map.json', 'fused-stages.json', 'import-gemm.json'})
        for path in paths:
            with self.subTest(example=path.name):self.assert_program(json.loads(path.read_text()))

    def test_eight_stage_output_and_total_post_node_limits(self):
        v=program();v['stages']=[dict(name=f's{i}',source=source(1,1)) for i in range(8)]
        v['outputs']=[s['name'] for s in v['stages']];self.assertEqual(len(self.assert_program(v)),8)
        v['stages'].append(dict(name='s8',source=source(1,1)))
        with self.assertRaises(ValueError):a.compile(v)
        v=chain(128);v['stages'][0]['source']['post']=dict(nodes=[dict(id='r',op='load',view='reduced')],result='r')
        with self.assertRaisesRegex(ValueError,'total source nodes'):a.compile(v)

    def test_reference_does_not_consume_compiler_or_gather(self):
        v=gemm();expected=a.reference(v)
        with patch.object(a,'compile',side_effect=AssertionError()),patch.object(a,'bind',side_effect=AssertionError()),patch.object(a.g,'sample',side_effect=AssertionError()):
            self.assertEqual(a.reference(v),expected)
