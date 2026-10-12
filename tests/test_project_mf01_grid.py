import copy,json,os,unittest
from unittest.mock import patch
from raveil import project as p,project_mf01_grid as a,project_dag_batch as b,fold_dag as d
from tests import test_project_dag_batch as fixtures
from scripts.mf01_grid_cases import make


class GridWorkspaceTests(unittest.TestCase):
    save=fixtures.BatchTests.save
    fake=fixtures.BatchTests.fake
    def setUp(self):
        fixtures.BatchTests.setUp(self)
        self.source=make(3,5,(2,3));self.save_source()
    def save_source(self):(self.project.root/'inputs/grid.json').write_bytes(p.encoded(self.source))
    def run_fixture(self,callback=None):
        with patch.object(d,'run',side_effect=callback or self.fake):return a.run(self.project,'grid.json',self.kernel,self.build)
    def reseal(self,r):
        root=self.project.root/'grids'/r['id'];r['files']=b._inventory(root);raw=p.encoded(r);(root/'record.json').write_bytes(raw);(root/'record.sha256').write_text(p.digest(raw)+'\n')
    def test_readonly_preview_and_saved_input_program_edits(self):
        before=p.tree(self.project.root);self.assertEqual(len(a.check(self.project,'grid.json')['layout']),4);self.assertEqual(before,p.tree(self.project.root))
        first=self.run_fixture();old=copy.deepcopy(first['output']['words'])
        self.source['inputs'][0]['words'][0]=7;self.save_source();second=self.run_fixture()
        self.source['kernel']['nodes'].append(dict(id='bias',op='add_imm',args=['a'],imm=1));self.source['kernel']['result']='bias';self.save_source();third=self.run_fixture()
        with patch('subprocess.Popen',side_effect=AssertionError('must not execute')):
            self.assertEqual(a.load(self.project,first['id'])['output']['words'],old);self.assertEqual(len(a.history(self.project)),3)
            self.assertEqual(a.compare(self.project,first['id'],second['id'])['changed_cells'],1)
            self.assertEqual(a.compare(self.project,second['id'],third['id'])['changed_cells'],15)
    def test_frozen_source_and_incomplete_parent(self):
        calls=[]
        def execute(*args):
            (self.project.root/'inputs/grid.json').write_text('changed');index=len(calls);calls.append(args);return self.fake(*args,failed=0 if index==1 else None)
        r=self.run_fixture(execute);self.assertEqual(len(calls),2);self.assertEqual(r['status'],'incomplete');self.assertIsNone(r['output'])
        self.assertEqual(a.load(self.project,r['id']),r)
        with self.assertRaises(ValueError):a.compare(self.project,r['id'],r['id'])
    def test_rehashed_source_lowering_layout_output_and_child_id_reject(self):
        for case in ['source','lowered','layout','word','child-id']:
            r=self.run_fixture();root=self.project.root/'grids'/r['id']
            if case=='source':
                path=root/'source.json';v=json.loads(path.read_text());v['inputs'][0]['words'][0]=5;path.write_bytes(p.encoded(v))
            elif case=='lowered':
                path=root/'lowered.json';v=json.loads(path.read_text());v['items'][0]['dag']['jobs'][0]['inputs'][0][0]=5;path.write_bytes(p.encoded(v))
            elif case=='layout':
                path=root/'plan.json';v=json.loads(path.read_text());v['layout'][0]['row']=-1;path.write_bytes(p.encoded(v))
            elif case=='word':r['output']['words'][0]=float(r['output']['words'][0])
            else:r['batch_id']='missing'
            self.reseal(r)
            with self.subTest(case=case),self.assertRaises(ValueError):a.load(self.project,r['id'])
    def test_interrupts_cleanup_uncertainty_and_no_overwrite(self):
        for error in [KeyboardInterrupt(),b.f.CleanupUncertain('unknown writer')]:
            with patch.object(b,'run',side_effect=error),self.assertRaises(type(error)):a.run(self.project,'grid.json',self.kernel,self.build)
        self.assertEqual([r['status'] for r in a.history(self.project)],['unsealed']*2)
        original=os.link
        def publish(src,dst):
            if '/grids/' in str(dst) and '/child/' not in str(dst):raise FileExistsError('no overwrite')
            return original(src,dst)
        with patch.object(a.os,'link',side_effect=publish),self.assertRaises(FileExistsError):self.run_fixture()
    def test_oracle_mismatch_never_publishes_grid(self):
        with patch.object(a.grid,'reference',return_value=[0]*15),self.assertRaisesRegex(ValueError,'oracle'):self.run_fixture()
        self.assertEqual(a.history(self.project)[0]['status'],'unsealed')
