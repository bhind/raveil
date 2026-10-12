import copy,json,unittest
from unittest.mock import patch
from raveil import project as p,project_mf01_grid as a,project_dag_batch as b,fold_dag as d,mf01_grid as g
from tests import test_project_dag_batch as fixtures
from scripts.mf01_grid_affine_cases import matmul


class AffineGridWorkspaceTests(unittest.TestCase):
    save=fixtures.BatchTests.save
    fake=fixtures.BatchTests.fake
    def setUp(self):
        fixtures.BatchTests.setUp(self);self.value,self.expected=matmul(3,5,4,(2,3))
    def run_fixture(self):
        (self.project.root/'inputs/grid.json').write_bytes(p.encoded(self.value))
        with patch.object(d,'run',side_effect=self.fake):return a.run(self.project,'grid.json',self.kernel,self.build)
    def test_retile_and_differently_shaped_input_edit(self):
        first=self.run_fixture();self.assertEqual(first['output']['words'],self.expected)
        self.value['tile']=[3,2];second=self.run_fixture()
        self.assertEqual(a.compare(self.project,first['id'],second['id'])['changed_cells'],0)
        self.value['inputs'][1]['words'][0]^=1;third=self.run_fixture()
        with patch('subprocess.Popen',side_effect=AssertionError('must not execute')):
            self.assertEqual(a.compare(self.project,second['id'],third['id'])['changed_cells'],3)
            self.assertEqual(a.load(self.project,first['id'])['output']['words'],self.expected)
    def test_consistent_source_and_lowering_rewrite_cannot_rebind_old_execution(self):
        for field in ['vector','shape','input']:
            record=self.run_fixture();root=self.project.root/'grids'/record['id'];changed=copy.deepcopy(self.value)
            if field=='vector':changed['kernel']['views']['a']['row']=[0,0]
            elif field=='shape':changed['shape']=[2,5]
            else:changed['inputs'][1]['words'][0]^=1
            raw=p.encoded(changed);compiled=g.compile(changed)
            (root/'source.json').write_bytes(raw);(root/'lowered.json').write_bytes(p.encoded(compiled['batch']))
            (root/'plan.json').write_bytes(p.encoded(a._plan(record['id'],'grid.json',raw,compiled)))
            record['files']=b._inventory(root);payload=p.encoded(record)
            (root/'record.json').write_bytes(payload);(root/'record.sha256').write_text(p.digest(payload)+'\n')
            with self.subTest(field=field),self.assertRaisesRegex(ValueError,'captured batch differs'):a.load(self.project,record['id'])
