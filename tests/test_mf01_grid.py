import copy,random,unittest
from raveil import mf01_grid as g,fold_dag as d
from raveil.grid_assembly import assemble
from scripts.mf01_grid_cases import make,cases


class GridCompilerTests(unittest.TestCase):
    def compare(self,value):
        compiled=g.compile(value);outputs=[]
        for item in compiled['batch']['items']:
            j=item['dag']['jobs'][0];outputs.append(dict(name=item['name'],shape=j['region']['shape'],words=d.reference(j['region'],j['inputs'])))
        self.assertEqual(assemble(outputs,compiled['layout'],compiled['rows'],compiled['columns']),g.reference(value))
    def test_all_owned_programs_and_boundaries(self):
        for name,value in cases():
            with self.subTest(name=name):self.compare(value)
    def test_324_halo_and_inactive_stride_canonicalization(self):
        value=next(v for n,v in cases() if n=='maximum324-halo');j=g.compile(value)['batch']['items'][0]['dag']['jobs'][0]
        self.assertEqual(j['region']['lengths'],[324,0]);self.assertEqual(j['region']['views']['a'],[0,0,0,1,5])
        value['tile']=[1,10];value['inputs'][0]['columns']=10;value['inputs'][0]['words'].append(3)
        with self.assertRaisesRegex(ValueError,'324'):g.compile(value)
    def test_random_shapes_views_tiles_against_untiled_oracle(self):
        rng=random.Random(221)
        for _ in range(100):
            rows,columns=rng.randint(1,16),rng.randint(1,16);value=make(rows,columns,(8,8),rng.choice(['zero','clamp','wrap']),True)
            value['kernel']['extent']=rng.randint(1,3);value['kernel']['fold']=rng.choice(['sum','max'])
            value['kernel']['views']={name:dict(input=i,offset=[rng.randint(-2,2),rng.randint(-2,2)],step=[rng.randint(0,1),rng.randint(0,1)]) for i,name in enumerate(['a','b'])}
            value['kernel']['nodes']=[dict(id='a',op='load',view='a'),dict(id='b',op='load',view='b'),dict(id='x',op=rng.choice(['add','max','mul']),args=['a','b'])];value['kernel']['result']='x';self.compare(value)
    def test_admission_invalid_types_fields_extents_and_programs(self):
        source=make()
        changes=[(['tile'],[True,8]),(['boundary'],'other'),(['kernel','extent'],0),(['kernel','views','a','offset'],[-64,0]),(['kernel','views','a','step'],[-1,0]),(['kernel','views','a','input'],1),(['kernel','nodes'],[None]),(['kernel','result'],'missing')]
        for path,value in changes:
            bad=copy.deepcopy(source);target=bad
            for key in path[:-1]:target=target[key]
            target[path[-1]]=value
            with self.subTest(path=path),self.assertRaises(ValueError):g.compile(bad)
        bad=make(64,64,(8,8))
        with self.assertRaisesRegex(ValueError,'sixteen'):g.compile(bad)
        bad=make(two=True);bad['inputs'][1]['columns']+=1;bad['inputs'][1]['words'] += [0]*7
        with self.assertRaisesRegex(ValueError,'agree'):g.compile(bad)
    def test_lowering_does_not_mutate_source(self):
        for _,source in cases():
            before=copy.deepcopy(source);g.compile(source);self.assertEqual(source,before)
