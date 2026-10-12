import copy,unittest
from unittest.mock import patch
from raveil.fold_evidence import loads
from raveil import project as p,project_mf01_grid as a,project_dag_batch as b,fold_dag as d,mf01_grid as g
from tests import test_project_dag_batch as fixtures
from scripts.mf01_numeric_cases import pointwise,EDGES,cases


class NumericWorkspaceTests(unittest.TestCase):
    save=fixtures.BatchTests.save
    fake=fixtures.BatchTests.fake
    def setUp(self):
        fixtures.BatchTests.setUp(self);self.value,self.expected=pointwise(EDGES,EDGES,tile=(7,7))
    def execute(self):
        (self.project.root/'inputs/grid.json').write_bytes(p.encoded(self.value))
        with patch.object(d,'run',side_effect=self.fake):return a.run(self.project,'grid.json',self.kernel,self.build)
    def test_saved_source_preserves_signed_operation_and_detects_numeric_edit(self):
        first=self.execute();self.assertEqual(first['output']['words'],self.expected)
        self.value['kernel']['nodes'][-1]['op']='max';second=self.execute()
        with patch('subprocess.Popen',side_effect=AssertionError('saved inspection executed')):
            self.assertGreater(a.compare(self.project,first['id'],second['id'])['changed_cells'],0)
            self.assertEqual(a.load(self.project,first['id']),first)
        old=loads((self.project.root/'grids'/first['id']/'source.json').read_bytes())
        self.assertEqual(old['kernel']['nodes'][-1]['op'],'max_i32')
    def test_rehashed_numerical_semantics_cannot_reuse_child(self):
        record=self.execute();root=self.project.root/'grids'/record['id'];value=copy.deepcopy(self.value)
        value['kernel']['nodes'][-1]['op']='max';raw=p.encoded(value);compiled=g.compile(value)
        (root/'source.json').write_bytes(raw);(root/'lowered.json').write_bytes(p.encoded(compiled['batch']))
        (root/'plan.json').write_bytes(p.encoded(a._plan(record['id'],'grid.json',raw,compiled)))
        record['files']=b._inventory(root);payload=p.encoded(record)
        (root/'record.json').write_bytes(payload);(root/'record.sha256').write_text(p.digest(payload)+'\n')
        with self.assertRaisesRegex(ValueError,'captured batch differs'):a.load(self.project,record['id'])
    def test_lowered_capacity_rejection_creates_no_attempt(self):
        previous='x'
        for i in range(6):
            name=f'next{i}';self.value['kernel']['nodes'].append(dict(id=name,op='add_imm',args=[previous],imm=1));previous=name
        self.value['kernel']['result']=previous
        with patch('subprocess.Popen',side_effect=AssertionError('rejection executed')),self.assertRaises(ValueError):self.execute()
        self.assertNotIn('grids',self.project.workspace.ls('/'))
