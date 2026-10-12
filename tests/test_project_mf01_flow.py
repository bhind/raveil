import copy,json,os,shutil,unittest
from unittest.mock import patch
from raveil import project as p,project_mf01_flow as a,project_mf01_grid as g,project_dag_batch as b,fold_dag as d
from tests import test_project_dag_batch as fixtures
from scripts.mf01_flow_cases import pair,eight


class FlowWorkspaceTests(unittest.TestCase):
    save=fixtures.BatchTests.save
    fake=fixtures.BatchTests.fake
    def setUp(self):
        fixtures.BatchTests.setUp(self);self.source,self.expected=pair();self.save_source()
    def save_source(self):(self.project.root/'inputs/flow.json').write_bytes(p.encoded(self.source))
    def execute(self,callback=None):
        with patch.object(d,'run',side_effect=callback or self.fake):return a.run(self.project,'flow.json',self.kernel,self.build)
    def reseal(self,record):
        root=self.project.root/'flows'/record['id'];record['files']=b._inventory(root);raw=p.encoded(record)
        (root/'record.json').write_bytes(raw);(root/'record.sha256').write_text(p.digest(raw)+'\n')

    def test_preview_edits_saved_revalidation_and_common_snapshots(self):
        before=p.tree(self.project.root);preview=a.check(self.project,'flow.json')
        self.assertEqual(preview['order'],['first','second']);self.assertEqual(before,p.tree(self.project.root))
        first=self.execute();self.assertEqual(first['outputs'],self.expected)
        self.source['stages'][1]['source']['inputs'][0]['words'][0]=1;self.save_source();second=self.execute()
        with patch('subprocess.Popen',side_effect=AssertionError('saved read must not execute')):
            self.assertEqual(a.load(self.project,first['id'])['outputs'],self.expected)
            self.assertEqual(len(a.history(self.project)),2);self.assertGreater(a.compare(self.project,first['id'],second['id'])['changed_cells'],0)

    def test_failed_middle_stops_all_later_stages_and_preserves_frozen_source(self):
        self.source,_=eight();self.save_source();calls=[]
        def execute(*args):
            (self.project.root/'inputs/flow.json').write_text('changed');i=len(calls);calls.append(i)
            return self.fake(*args,failed=0 if i==2 else None)
        record=self.execute(execute)
        self.assertEqual(record['status'],'incomplete');self.assertIsNone(record['outputs']);self.assertEqual(len(calls),3)
        self.assertEqual(len(record['children']),3);self.assertEqual(a.load(self.project,record['id']),record)
        with self.assertRaises(ValueError):a.compare(self.project,record['id'],record['id'])

    def test_bad_later_source_rejected_before_attempt(self):
        self.source['stages'][0]['source']['kernel']['nodes'][0]['view']='missing';self.save_source()
        with patch.object(g,'run',side_effect=AssertionError('must not execute')),self.assertRaises(ValueError):a.run(self.project,'flow.json',self.kernel,self.build)
        self.assertNotIn('flows',self.project.workspace.ls('/'))

    def test_coordinated_rebind_to_inline_input_does_not_rebind_child_proof(self):
        record=self.execute();root=self.project.root/'flows'/record['id']
        value=json.loads((root/'source.json').read_text());value['stages'][0]['source']['inputs'][0]=dict(schema='raveil.grid-input/v2',rows=5,columns=6,words=[0]*30)
        raw=p.encoded(value);(root/'source.json').write_bytes(raw)
        plan=json.loads((root/'plan.json').read_text());plan['source_sha256']=p.digest(raw);plan['preview']=a.flow.compile(value)
        (root/'plan.json').write_bytes(p.encoded(plan));self.reseal(record)
        with self.assertRaisesRegex(ValueError,'producer binding'):a.load(self.project,record['id'])

    def test_rehashed_output_prefix_identity_and_extra_child_reject(self):
        for kind in ['float-output','prefix','name','extra','executable']:
            self.source,_=eight();self.source['stages']=self.source['stages'][-1:];self.source['outputs']=['stage-0'];self.save_source()
            record=self.execute();root=self.project.root/'flows'/record['id']
            if kind=='float-output':record['outputs'][0]['words'][0]=float(record['outputs'][0]['words'][0])
            elif kind=='prefix':record['children'].append(copy.deepcopy(record['children'][0]))
            elif kind=='name':record['children'][0]['name']='different'
            elif kind=='extra':(root/'children/01').mkdir()
            else:
                (root/'kernel.elf').write_bytes(b'changed kernel');plan=json.loads((root/'plan.json').read_text());plan['kernel_sha256']=p.digest(b'changed kernel');(root/'plan.json').write_bytes(p.encoded(plan))
            self.reseal(record)
            with self.subTest(kind=kind),self.assertRaises(ValueError):a.load(self.project,record['id'])

    def test_wrong_but_valid_child_never_supplies_next_stage(self):
        original=g.run;calls=[]
        def substitute(project,input_file,kernel,build):
            calls.append(input_file);path=project.root/'inputs'/input_file
            value=json.loads(path.read_text());value['inputs'][0]['words']=[0]*len(value['inputs'][0]['words']);path.write_bytes(p.encoded(value))
            return original(project,input_file,kernel,build)
        with patch.object(g,'run',side_effect=substitute),self.assertRaisesRegex(ValueError,'producer binding'):self.execute()
        self.assertEqual(len(calls),1);self.assertEqual(a.history(self.project)[0]['status'],'unsealed')

    def test_artifact_budget_and_publish_collision_leave_parent_unsealed(self):
        self.source,_=eight();self.source['stages']=self.source['stages'][-1:];self.source['outputs']=['stage-0'];self.save_source()
        inventory=b._inventory
        def capped(root):
            if root.parent.name=='flows':raise ValueError('tree exceeds byte limit')
            return inventory(root)
        with patch.object(b,'_inventory',side_effect=capped),self.assertRaisesRegex(ValueError,'byte limit'):self.execute()
        link=os.link
        def collision(src,dst):
            if '/flows/' in str(dst) and '/children/' not in str(dst):raise FileExistsError('parent exists')
            return link(src,dst)
        with patch.object(a.os,'link',side_effect=collision),self.assertRaises(FileExistsError):self.execute()
        self.assertEqual([row['status'] for row in a.history(self.project)],['unsealed']*2)

    def test_different_valid_executable_rejected_before_downstream(self):
        original=g.run;calls=[];other=self.kernel.parent/'other.elf';other.write_bytes(b'different valid fixture kernel')
        def substitute(project,input_file,kernel,build):
            calls.append(input_file);return original(project,input_file,other,build)
        with patch.object(g,'run',side_effect=substitute),self.assertRaisesRegex(ValueError,'executables differ'):self.execute()
        self.assertEqual(len(calls),1);self.assertEqual(a.history(self.project)[0]['status'],'unsealed')

    def test_removed_successful_suffix_and_unused_failure_reject(self):
        record=self.execute();root=self.project.root/'flows'/record['id']
        record['children'].pop();shutil.rmtree(root/'children/01');self.reseal(record)
        with self.assertRaisesRegex(ValueError,'ended before'):a.load(self.project,record['id'])
        self.source,_=eight();self.source['stages']=self.source['stages'][-2:];self.source['outputs']=['stage-0'];self.save_source();calls=[]
        def fail_unused(*args):
            i=len(calls);calls.append(i);return self.fake(*args,failed=0 if i==1 else None)
        record=self.execute(fail_unused)
        self.assertEqual(len(calls),2);self.assertIsNone(record['outputs']);self.assertEqual(record['status'],'incomplete')

    def test_parent_interrupt_before_and_after_publish(self):
        self.source,_=eight();self.source['stages']=self.source['stages'][-1:];self.source['outputs']=['stage-0'];self.save_source()
        link=os.link
        def before(src,dst):
            if '/flows/' in str(dst) and '/children/' not in str(dst):raise KeyboardInterrupt()
            return link(src,dst)
        with patch.object(a.os,'link',side_effect=before),self.assertRaises(KeyboardInterrupt):self.execute()
        def after(src,dst):
            result=link(src,dst)
            if '/flows/' in str(dst) and '/children/' not in str(dst):raise KeyboardInterrupt()
            return result
        with patch.object(a.os,'link',side_effect=after):record=self.execute()
        self.assertEqual(record['status'],'succeeded');self.assertEqual(a.load(self.project,record['id']),record)

    def test_interrupt_or_uncertain_cleanup_is_unsealed(self):
        for error in [KeyboardInterrupt(),b.f.CleanupUncertain('uncertain writer')]:
            with patch.object(g,'run',side_effect=error),self.assertRaises(type(error)):a.run(self.project,'flow.json',self.kernel,self.build)
        self.assertEqual([r['status'] for r in a.history(self.project)],['unsealed']*2)
