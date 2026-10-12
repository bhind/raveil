import copy,random,unittest
from raveil import mf01_grid as g,fold_dag as d
from raveil.grid_assembly import assemble
from scripts.mf01_grid_affine_cases import grid,view,source,matmul,cases
from scripts.mf01_grid_cases import cases as v1_cases


class AffineGridTests(unittest.TestCase):
    def compare(self,value,expected=None):
        compiled=g.compile(value);outputs=[]
        for item in compiled['batch']['items']:
            job=item['dag']['jobs'][0]
            outputs.append(dict(name=item['name'],shape=job['region']['shape'],words=d.reference(job['region'],job['inputs'])))
        actual=assemble(outputs,compiled['layout'],compiled['rows'],compiled['columns'])
        self.assertEqual(actual,g.reference(value))
        if expected is not None:self.assertEqual(actual,expected)
        return compiled
    def test_owned_programs_and_direct_formulas(self):
        for name,value,expected in cases():
            with self.subTest(name=name):self.compare(value,expected)
    def test_random_rectangular_matmul(self):
        rng=random.Random(222)
        for _ in range(50):
            m,n,k=[rng.randint(1,20) for _ in range(3)]
            value,expected=matmul(m,n,k,(6,6));self.compare(value,expected)
    def test_v1_identity_mapping_compatibility_and_source_unchanged(self):
        for _,value in v1_cases():
            old=copy.deepcopy(value);v2=copy.deepcopy(value);v2['schema']=g.SCHEMA_V2;v2['shape']=[value['inputs'][0]['rows'],value['inputs'][0]['columns']]
            for v in v2['kernel']['views'].values():v.update(row=[1,0],column=[0,1])
            self.assertEqual(g.compile(value),g.compile(v2));self.assertEqual(value,old)
    def test_mixed_views_same_input_and_inactive_dimensions(self):
        a=grid(3,5)
        value=source([a],(4,3),(2,2),{'a':view(0,(1,0),(0,1)),'b':view(0,(0,1),(1,0),offset=(-1,2))},
                     [dict(id='a',op='load',view='a'),dict(id='b',op='load',view='b'),dict(id='x',op='add',args=['a','b'])],'x',boundary='wrap')
        expected=[(a['words'][(r%3)*5+c]+a['words'][((c-1)%3)*5+(r+2)%5])&0xffffffff for r in range(4) for c in range(3)]
        self.compare(value,expected)
        value=source([grid(1,1)],(1,1),(1,1),{'a':view(0,(63,63),(63,63),(63,63))},[dict(id='a',op='load',view='a')],'a')
        job=self.compare(value)['batch']['items'][0]['dag']['jobs'][0]
        self.assertEqual(job['region']['views']['a'],[0,0,0,0,0]);self.assertEqual(job['region']['lengths'],[1,0])
    def test_exact_input_ceiling_and_invalid_v2_fields(self):
        value,_=matmul(6,6,54,(6,6));self.assertEqual(g.compile(value)['batch']['items'][0]['dag']['jobs'][0]['region']['lengths'],[324,324])
        value,_=matmul(13,13,25,(13,13))
        with self.assertRaisesRegex(ValueError,'324'):g.compile(value)
        value,_=matmul(3,5,2,(2,3))
        changes=[(['shape'],[True,5]),(['shape'],[0,5]),(['shape'],[65,5]),(['shape'],[3.0,5]),(['shape'],[1]),(['kernel','views','a','row'],[-1,0]),(['kernel','views','a','column'],[0,True]),(['kernel','views','a','step'],[64,0]),(['kernel','views','a','row'],[0]),(['schema'],g.SCHEMA)]
        for path,new in changes:
            bad=copy.deepcopy(value);target=bad
            for key in path[:-1]:target=target[key]
            target[path[-1]]=new
            with self.subTest(path=path),self.assertRaises(ValueError):g.compile(bad)
        for key in ['shape','unknown']:
            bad=copy.deepcopy(value)
            if key=='shape':del bad[key]
            else:bad[key]=1
            with self.assertRaises(ValueError):g.compile(bad)
        bad=copy.deepcopy(value);del bad['kernel']['views']['a']['row']
        with self.assertRaises(ValueError):g.compile(bad)
        bad=copy.deepcopy(value);bad['shape']=[17,1];bad['tile']=[1,1]
        with self.assertRaisesRegex(ValueError,'sixteen'):g.compile(bad)
