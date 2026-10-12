import copy,unittest
from unittest.mock import patch
from raveil import project as p,project_mf01_grid as a,project_dag_batch as b,fold_dag as d,mf01_grid as g
from tests import test_project_dag_batch as fixtures
from scripts.mf01_grid_affine_cases import matmul
from scripts.mf01_grid_post_cases import with_post


class PostWorkspaceTests(unittest.TestCase):
    save=fixtures.BatchTests.save
    fake=fixtures.BatchTests.fake
    def setUp(self):
        fixtures.BatchTests.setUp(self);value,self.expected=matmul(3,5,4,(2,3));self.value=with_post(value)
    def run_fixture(self,failed=None):
        (self.project.root/'inputs/grid.json').write_bytes(p.encoded(self.value))
        with patch.object(d,'run',side_effect=lambda *args:self.fake(*args,failed=failed)):
            return a.run(self.project,'grid.json',self.kernel,self.build)
    def test_edit_post_preserves_old_source_and_all_cells_change(self):
        first=self.run_fixture();self.assertEqual(first['output']['words'],[(x+7)&0xffffffff for x in self.expected])
        self.value['post']['nodes'][1]['imm']=8;second=self.run_fixture()
        with patch('subprocess.Popen',side_effect=AssertionError('saved inspection cannot execute')):
            self.assertEqual(a.compare(self.project,first['id'],second['id'])['changed_cells'],15)
            self.assertEqual(a.load(self.project,first['id']),first)
    def test_either_failed_stage_suppresses_grid(self):
        for stage in [0,1]:
            record=self.run_fixture(stage)
            self.assertEqual(record['status'],'incomplete');self.assertIsNone(record['output'])
            self.assertEqual(a.load(self.project,record['id']),record)
    def test_rewritten_post_plan_and_lowering_cannot_reuse_old_child(self):
        record=self.run_fixture();root=self.project.root/'grids'/record['id'];value=copy.deepcopy(self.value)
        value['post']['nodes'][1]['imm']=8;raw=p.encoded(value);compiled=g.compile(value)
        (root/'source.json').write_bytes(raw);(root/'lowered.json').write_bytes(p.encoded(compiled['batch']))
        (root/'plan.json').write_bytes(p.encoded(a._plan(record['id'],'grid.json',raw,compiled)))
        record['files']=b._inventory(root);payload=p.encoded(record)
        (root/'record.json').write_bytes(payload);(root/'record.sha256').write_text(p.digest(payload)+'\n')
        with self.assertRaisesRegex(ValueError,'captured batch differs'):a.load(self.project,record['id'])
