import copy,hashlib,random,unittest
from unittest.mock import patch
from raveil import mf01_grid as g,mf01_flow as flow,mf01_grid_plan as planner,project as p,project_mf01_grid as workspace,project_dag_batch as batch
from raveil.mf01_numeric import lower
from raveil.fold_evidence import loads
from scripts.mf01_numeric_cases import EDGES,MASK,pointwise,signed,cases as old_cases
from scripts.mf01_numeric_shared_cases import cases,chain,branch_nodes,branch_expected,branch_flow
from scripts.mf01_numeric_extra_cases import shared_sign_live_input
from tests import test_mf01_numeric as fixture,test_project_mf01_numeric as saved


class SharedNumericTests(unittest.TestCase):
    def test_previously_rejected_chain_and_real_branch_fit_without_limit_change(self):
        for name,value,expected in cases():
            with self.subTest(name=name):
                before=copy.deepcopy(value);compiled=g.compile(value)
                self.assertEqual(fixture.execute(value),expected);self.assertEqual(g.reference(value),expected)
                self.assertEqual(value,before)
                legacy={**value,'schema':g.SCHEMA_V4}
                with self.assertRaisesRegex(ValueError,'fifteen map nodes'):g.compile(legacy)
                for job in compiled['batch']['items'][0]['dag']['jobs']:
                    self.assertLessEqual(len(job['region']['nodes']),15)
        value,_=chain();self.assertEqual(len(lower(value['kernel']['nodes'],'activated')),17)
        self.assertEqual(len(lower(value['kernel']['nodes'],'activated',share_transforms=True)),14)

    def test_random_modular_branch_uses_original_and_translated_values(self):
        rng=random.Random(234)
        for _ in range(16):
            a=[signed(rng.getrandbits(32)) for _ in range(5)];b=[signed(rng.getrandbits(32)) for _ in range(7)]
            value,_=pointwise(a,b,tile=(5,7));value['schema']=g.SCHEMA_V5
            value['kernel']['nodes']=branch_nodes();value['kernel']['result']='answer'
            self.assertEqual(fixture.execute(value),[branch_expected(x,y) for x in a for y in b])
            self.assertTrue({n['id'] for n in value['kernel']['nodes']} <= {n['id'] for n in lower(value['kernel']['nodes'],'answer',share_transforms=True)})

    def test_generated_identifiers_do_not_capture_public_names(self):
        value,expected=chain();nodes=value['kernel']['nodes'];mapping={n['id']:f'__mf01_numeric_{i}' for i,n in enumerate(nodes)}
        for node in nodes:
            node['id']=mapping[node['id']]
            if 'args' in node:node['args']=[mapping[x] for x in node['args']]
        value['kernel']['result']=mapping['activated']
        self.assertEqual(fixture.execute(value),expected)

    def test_equal_operands_share_one_translation(self):
        value,_=pointwise(EDGES,[0],tile=(7,1));value['schema']=g.SCHEMA_V5
        value['kernel']['nodes'][-1]['args']=['a','a']
        self.assertEqual(len(lower(value['kernel']['nodes'],'x',share_transforms=True)),9)
        self.assertEqual(fixture.execute(value),[x&MASK for x in EDGES])

    def test_kernel_and_post_cache_are_isolated(self):
        value,_=chain();value['kernel']['extent']=3
        value['post']=dict(nodes=[dict(id='a',op='load',view='reduced'),dict(id='x',op='relu_i32',args=['a'])],result='x')
        expected=[max(0,signed((3*max(0,a,b))&MASK)) for a in EDGES for b in EDGES]
        self.assertEqual(fixture.execute(value),expected)
        self.assertEqual(g.reference(value),expected)

    def test_no_dead_public_nodes_are_removed_to_fit(self):
        value,_=chain();value['kernel']['nodes'] += [dict(id='unused1',op='add_imm',args=['a'],imm=1),dict(id='unused2',op='add_imm',args=['a'],imm=2)]
        with self.assertRaisesRegex(ValueError,'fifteen map nodes'):g.compile(value)
        with self.assertRaisesRegex(ValueError,'no admitted uniform tile'):planner.plan(value)

    def test_existing_allocator_still_rejects_live_register_overflow(self):
        value,_=pointwise([1],[2],tile=(1,1));value['schema']=g.SCHEMA_V5
        nodes=[dict(id=f'a{i}',op='load',view='a') for i in range(9)]
        # First use of a0 and a1 occurs only after the ninth simultaneous live load.
        nodes += [dict(id='s0',op='add',args=['a0','a1']),dict(id='s1',op='add',args=['a2','a3']),dict(id='s2',op='add',args=['a4','a5']),dict(id='s3',op='add',args=['a6','a7']),dict(id='s4',op='add',args=['a8','s0'])]
        value['kernel'].update(nodes=nodes,result='s4')
        with self.assertRaisesRegex(ValueError,'eight live registers'):g.compile(value)

    def test_v4_lowering_digest_unchanged(self):
        payload=p.encoded([g.compile(s) for _,s,_ in old_cases()]+[g.compile(shared_sign_live_input()[0])])
        self.assertEqual(hashlib.sha256(payload).hexdigest(),'f9bd173717bdf1ab9d1393ae869c02012660a4b77579c41685b4aae8d91293ac')

    def test_flow_and_partition_planner_preserve_v5(self):
        value,expected=chain((4,4));proposal=planner.plan(value)
        self.assertEqual(proposal['source']['schema'],g.SCHEMA_V5)
        self.assertEqual(fixture.execute(proposal['source']),expected)
        value,expected=branch_flow();self.assertEqual(flow.reference(value)[0]['words'],expected)


class SharedSavedTests(unittest.TestCase):
    save=saved.NumericWorkspaceTests.save
    fake=saved.NumericWorkspaceTests.fake
    execute=saved.NumericWorkspaceTests.execute
    def setUp(self):
        saved.NumericWorkspaceTests.setUp(self);self.value,self.expected=shared_sign_live_input()

    def test_old_and_new_proofs_revalidate_and_compare(self):
        old=self.execute();self.value['schema']=g.SCHEMA_V5;new=self.execute()
        with patch('subprocess.Popen',side_effect=AssertionError('saved read executed')):
            self.assertEqual(workspace.compare(self.project,old['id'],new['id'])['changed_cells'],0)
            self.assertEqual(workspace.load(self.project,old['id']),old)
            self.assertEqual(workspace.load(self.project,new['id']),new)

    def test_resealed_version_change_cannot_reuse_old_children(self):
        record=self.execute();root=self.project.root/'grids'/record['id']
        self.value['schema']=g.SCHEMA_V5;raw=p.encoded(self.value);compiled=g.compile(self.value)
        (root/'source.json').write_bytes(raw);(root/'lowered.json').write_bytes(p.encoded(compiled['batch']))
        (root/'plan.json').write_bytes(p.encoded(workspace._plan(record['id'],'grid.json',raw,compiled)))
        record['files']=batch._inventory(root);payload=p.encoded(record)
        (root/'record.json').write_bytes(payload);(root/'record.sha256').write_text(p.digest(payload)+'\n')
        with patch('subprocess.Popen',side_effect=AssertionError('saved read executed')),self.assertRaisesRegex(ValueError,'captured batch differs'):
            workspace.load(self.project,record['id'])

    def test_rejection_creates_no_attempt(self):
        self.value,_=chain();self.value['kernel']['nodes'] += [dict(id='u1',op='add',args=['a','b']),dict(id='u2',op='add',args=['a','b'])]
        with patch('subprocess.Popen',side_effect=AssertionError('invalid source executed')),self.assertRaises(ValueError):self.execute()
        self.assertNotIn('grids',self.project.workspace.ls('/'))
