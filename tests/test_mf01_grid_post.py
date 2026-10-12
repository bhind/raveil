import copy,unittest
from raveil import mf01_grid as g,fold_dag as d,mf01_grid_plan as planner
from raveil.grid_assembly import assemble
from scripts.mf01_grid_post_cases import with_post,cases
from scripts.mf01_grid_affine_cases import matmul


class PostMapTests(unittest.TestCase):
    def execute(self,value):
        compiled=g.compile(value);outputs=[]
        for item in compiled['batch']['items']:
            dag=item['dag'];state=d.State(dag)
            self.assertEqual(len(dag['jobs']),2);self.assertEqual(dag['output'],'result')
            for i in range(2):
                job,reads,writes=state.resolve(i);expected=d.reference(job['region'],job['inputs'])
                self.assertLessEqual(reads.bit_count()+writes.bit_count(),4);state.commit(i,writes,expected,True)
            final=state.final();self.assertTrue(final['available'])
            outputs.append(dict(name=item['name'],shape=dag['jobs'][-1]['region']['shape'],words=final['output']))
        return assemble(outputs,compiled['layout'],compiled['rows'],compiled['columns'])
    def test_owned_formulas_and_fold_then_map_order(self):
        for name,value,expected in cases():
            with self.subTest(name=name):
                self.assertEqual(self.execute(value),expected);self.assertEqual(g.reference(value),expected)
        value,_=matmul(2,2,2,(2,2));post=with_post(value)
        wrong=copy.deepcopy(value);wrong['kernel']['nodes'].append(dict(id='biased',op='add_imm',args=['x'],imm=7));wrong['kernel']['result']='biased'
        self.assertNotEqual(g.reference(post),g.reference(wrong))
    def test_one_and_two_chunk_reference_boundaries(self):
        for name,value,_ in cases():
            if not name.startswith('words-'):continue
            dag=g.compile(value)['batch']['items'][0]['dag'];plan=d.compile_plan(dag)
            chunks=1 if name=='words-128' else 2
            self.assertEqual(plan['chunks'],[chunks,chunks]);self.assertEqual(len(d.read_slots(plan,1))+chunks,2*chunks)
            self.assertTrue(set(plan['slots'][0]).isdisjoint(plan['slots'][1]))
    def test_failed_producer_or_post_never_exposes_final(self):
        value,_=matmul(3,5,4,(2,3));dag=g.compile(with_post(value))['batch']['items'][0]['dag']
        state=d.State(dag);job,_,write=state.resolve(0);state.commit(0,write,d.reference(job['region'],job['inputs']),False)
        self.assertIsNone(state.resolve(1));self.assertFalse(state.final()['available'])
        state=d.State(dag)
        for i in range(2):
            job,_,write=state.resolve(i);state.commit(i,write,d.reference(job['region'],job['inputs']),i==0)
        self.assertTrue(state.available(0));self.assertFalse(state.final()['available'])
    def test_version_post_program_and_immediate_rejections(self):
        value,_=matmul(3,5,4,(2,3));post=with_post(value)
        for kind in ['missing','extra','none','node-none','unknown-view','imm-bool','imm-large','undefined','too-many','old-version']:
            bad=copy.deepcopy(post)
            if kind=='missing':del bad['post']
            elif kind=='extra':bad['post']['extra']=0
            elif kind=='none':bad['post']=None
            elif kind=='node-none':bad['post']['nodes']=[None]
            elif kind=='unknown-view':bad['post']['nodes'][0]['view']='other'
            elif kind=='imm-bool':bad['post']['nodes'][1]['imm']=True
            elif kind=='imm-large':bad['post']['nodes'][1]['imm']=1<<22
            elif kind=='undefined':bad['post']['result']='missing'
            elif kind=='too-many':bad['post']['nodes']*=8
            else:bad['schema']=g.SCHEMA_V2
            with self.subTest(kind=kind),self.assertRaises(ValueError):g.compile(bad)
    def test_planner_preserves_post_and_counts_only_source_packing(self):
        value,expected=matmul(17,19,64);post=with_post(value);before=copy.deepcopy(post)
        proposal=planner.plan(post)
        self.assertEqual(proposal['selected'],dict(tile=[5,5],sessions=16,packed_input_words=9216))
        self.assertEqual(proposal['source']['post'],post['post']);self.assertEqual(post,before)
        self.assertEqual(g.reference(proposal['source']),[(v+7)&0xffffffff for v in expected])
