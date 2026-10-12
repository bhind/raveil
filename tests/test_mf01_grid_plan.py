import copy,io,json,tempfile,unittest
from contextlib import redirect_stdout,redirect_stderr
from pathlib import Path
from unittest.mock import patch
from raveil import mf01_grid as g,mf01_grid_plan as planner,project as p
from raveil.cli import main
from scripts.mf01_grid_affine_cases import matmul,cases


class TilePlannerTests(unittest.TestCase):
    def test_previously_rejected_matmul_selects_admitted_partition(self):
        value,expected=matmul(17,19,64);before=copy.deepcopy(value)
        with self.assertRaisesRegex(ValueError,'324'):g.compile(value)
        proposal=planner.plan(value)
        self.assertEqual(proposal['selected'],dict(tile=[5,5],sessions=16,packed_input_words=9216))
        self.assertEqual(proposal['admitted'],1);self.assertEqual(proposal['searched'],256)
        self.assertEqual(sum(proposal['rejected'].values()),255)
        self.assertEqual(g.reference(proposal['source']),expected);self.assertEqual(value,before)
    def test_matmul_choice_matches_independent_exhaustive_geometry(self):
        for m,n,k in [(1,17,64),(3,5,2),(64,64,1),(17,19,64),(23,20,64),(8,32,32),(16,16,20),(64,64,64)]:
            value,_=matmul(m,n,k)
            feasible=[]
            for rows in range(1,17):
                for columns in range(1,17):
                    nr,nc=(m+rows-1)//rows,(n+columns-1)//columns
                    if nr*nc<=16 and min(rows,m)*k<=324 and min(columns,n)*k<=324:
                        feasible.append((nr*nc,k*(m*nc+n*nr),rows*columns,rows,columns))
            with self.subTest(shape=(m,n,k)):
                if not feasible:
                    with self.assertRaisesRegex(ValueError,'no admitted'):planner.plan(value)
                else:
                    choice=min(feasible);proposal=planner.plan(value)
                    self.assertEqual(proposal['admitted'],len(feasible))
                    self.assertEqual(proposal['selected'],dict(tile=list(choice[-2:]),sessions=choice[0],packed_input_words=choice[1]))
    def test_owned_sources_preserve_semantics_and_plan_is_deterministic(self):
        for name,value,expected in cases():
            with self.subTest(name=name):
                proposal=planner.plan(value)
                self.assertEqual(g.reference(proposal['source']),expected)
                self.assertEqual(planner.plan(value),proposal)
                changed=copy.deepcopy(value);changed['tile']=proposal['source']['tile'];self.assertEqual(changed,proposal['source'])
    def test_invalid_source_never_becomes_an_executable_proposal(self):
        value,_=matmul(3,5,2)
        for tile in ([True,2],[0,2],[17,2],[2.0,2],[],None):
            bad=copy.deepcopy(value);bad['tile']=tile
            with self.subTest(tile=tile),self.assertRaises(ValueError):planner.plan(bad)
        for mutation in ('unknown-field','bad-node','negative-stride','wrong-dimension'):
            bad=copy.deepcopy(value)
            if mutation=='unknown-field':bad['unexpected']=1
            elif mutation=='bad-node':bad['kernel']['nodes']=[None]
            elif mutation=='negative-stride':bad['kernel']['views']['a']['row']=[-1,0]
            else:bad['inputs'][0]['rows']+=1
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):planner.plan(bad)


class PlannerWorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.project=p.Project(p.init_project(Path(self.temp.name)/'project'))
        self.source,_=matmul(17,19,64);self.path=self.project.root/'inputs/source.json';self.path.write_bytes(p.encoded(self.source))
    def test_readonly_preview_and_explicit_new_source(self):
        before=p.tree(self.project.root)
        with patch('subprocess.Popen',side_effect=AssertionError('planning must not execute')):
            first=planner.propose(self.project,'source.json')
            self.assertEqual(p.tree(self.project.root),before)
            saved=planner.propose(self.project,'source.json','selected.json')
        self.assertEqual(saved['input_sha256'],p.digest(self.path.read_bytes()))
        self.assertEqual(json.loads((self.project.root/'inputs/selected.json').read_text()),first['source'])
        self.assertEqual(json.loads(self.path.read_text()),self.source)
        self.assertFalse((self.project.root/'grids').exists())
        with self.assertRaises(FileExistsError):planner.propose(self.project,'source.json','selected.json')
    def test_confined_paths_symlinks_and_duplicate_json(self):
        for filename in ('../escape.json','a/b.json','x',None):
            with self.subTest(filename=filename),self.assertRaises(ValueError):planner.propose(self.project,filename)
        target=Path(self.temp.name)/'outside.json';target.write_text('unchanged')
        (self.project.root/'inputs/link.json').symlink_to(target)
        with self.assertRaises(ValueError):planner.propose(self.project,'link.json')
        with self.assertRaises(FileExistsError):planner.propose(self.project,'source.json','link.json')
        self.assertEqual(target.read_text(),'unchanged')
        with self.assertRaises(ValueError):planner.propose(self.project,'source.json','../escape.json')
        self.path.write_text('{"schema":1,"schema":2}')
        with self.assertRaises(ValueError):planner.propose(self.project,'source.json','new.json')
        self.assertFalse((self.project.root/'inputs/new.json').exists())
    def test_cli_and_impossible_workload_leave_no_attempt(self):
        out=io.StringIO()
        with patch('subprocess.Popen',side_effect=AssertionError('must not execute')),redirect_stdout(out):
            code=main(['project','grid-plan','--project',str(self.project.root),'--input','source.json','--output','chosen.json'])
        self.assertEqual(code,0);self.assertEqual(json.loads(out.getvalue())['selected']['tile'],[5,5])
        impossible,_=matmul(64,64,64);self.path.write_bytes(p.encoded(impossible));before=p.tree(self.project.root)
        with self.assertRaisesRegex(ValueError,'no admitted'):planner.propose(self.project,'source.json','impossible.json')
        self.assertEqual(before,p.tree(self.project.root))
