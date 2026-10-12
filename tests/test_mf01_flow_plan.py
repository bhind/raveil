import copy,itertools,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from raveil import mf01_flow as flow,mf01_flow_plan as planner,project as p
from scripts.mf01_flow_cases import diamond,eight
from scripts.mf01_flow_plan_cases import rescue,impossible


def geometry(m,n,k):
    result=[]
    for tr,tc in itertools.product(range(1,17),repeat=2):
        shapes=[(min(tr,m-r),min(tc,n-c)) for r in range(0,m,tr) for c in range(0,n,tc)]
        if len(shapes)>16 or any(h*k>324 or k*w>324 for h,w in shapes):continue
        result.append((len(shapes),sum(h*k+k*w for h,w in shapes),tr*tc,tr,tc))
    return result


class FlowPlanTests(unittest.TestCase):
    def test_rescues_invalid_requested_tiles_and_matches_independent_geometry(self):
        value,expected=rescue();old=copy.deepcopy(value)
        with self.assertRaises(ValueError):flow.compile(value)
        proposal=planner.plan(value);a=geometry(3,50,8);b=geometry(3,9,50)
        optimum=min((x[0]+y[0],x[1]+y[1]) for x in a for y in b)
        self.assertEqual((proposal['sessions'],proposal['packed_input_words']),optimum)
        self.assertEqual(optimum,(6,1246));self.assertEqual([row['tile'] for row in proposal['stages']],[[3,13],[3,5]])
        self.assertEqual(flow.reference(proposal['source'])[0]['words'],expected);self.assertEqual(value,old)
        for stage in proposal['source']['stages']:
            original=next(s for s in old['stages'] if s['name']==stage['name']);stage=copy.deepcopy(stage)
            stage['source']['tile']=original['source']['tile'];self.assertEqual(stage,original)

    def test_diamond_links_author_order_and_value_independence(self):
        value,expected=diamond();proposal=planner.plan(value)
        self.assertEqual(proposal['sessions'],4);self.assertEqual(proposal['packed_input_words'],197)
        self.assertEqual(flow.reference(proposal['source']),expected)
        changed=copy.deepcopy(value);changed['stages'].reverse();changed['stages'][0]['source']['inputs'][0]['words'][0]^=123
        other=planner.plan(changed);self.assertEqual(other['stages'],proposal['stages'])
        self.assertEqual([s['name'] for s in other['source']['stages']],[s['name'] for s in changed['stages']])

    def test_v1_linked_shape_inference_and_mismatch(self):
        from scripts.mf01_grid_cases import make
        a=make(1,1,(1,1));b=make(2,1,(2,1));c=make(1,1,(1,1));c['inputs']=[{'from':'a'}]
        value=dict(schema=flow.SCHEMA,stages=[dict(name='c',source=c),dict(name='a',source=a)],outputs=['c'])
        proposal=planner.plan(value);self.assertEqual(proposal['sessions'],2)
        self.assertEqual(flow.compile(proposal['source'])['stages'][-1]['shape'],[1,1])
        value['stages'].append(dict(name='b',source=b));value['stages'][0]['source']['inputs'].append({'from':'b'})
        with self.assertRaisesRegex(ValueError,'dimensions must agree'):planner.plan(value)

    def test_unachievable_aggregate_and_bad_requested_types_reject(self):
        with self.assertRaisesRegex(ValueError,'exceeds16'):planner.plan(impossible())
        for bad in [True,0,17,1.0]:
            value,_=rescue();value['stages'][0]['source']['tile'][0]=bad
            with self.subTest(value=bad),self.assertRaises(ValueError):planner.plan(value)
        value,_=rescue();value['stages'][1]['source']['inputs'][0]={'from':'second'}
        with self.assertRaisesRegex(ValueError,'cyclic'):planner.plan(value)

    def test_readonly_new_output_and_no_execution(self):
        with tempfile.TemporaryDirectory() as tmp:
            project=p.Project(p.init_project(Path(tmp)/'work'));value,_=rescue();raw=p.encoded(value)
            source=project.root/'inputs/flow.json';source.write_bytes(raw);before=p.tree(project.root)
            with patch('subprocess.Popen',side_effect=AssertionError('planner executed')):
                preview=planner.propose(project,'flow.json');self.assertEqual(p.tree(project.root),before)
                saved=planner.propose(project,'flow.json','selected.json');self.assertEqual(saved['source'],preview['source'])
                self.assertEqual(source.read_bytes(),raw);self.assertNotIn('flows',project.workspace.ls('/'))
                with self.assertRaises(FileExistsError):planner.propose(project,'flow.json','selected.json')
                with self.assertRaises(ValueError):planner.propose(project,'flow.json','../escape.json')
                (project.root/'inputs/link.json').symlink_to(source)
                with self.assertRaises((ValueError,OSError)):planner.propose(project,'link.json')

    def test_infeasible_output_is_not_written_and_duplicate_json_rejects(self):
        with tempfile.TemporaryDirectory() as tmp:
            project=p.Project(p.init_project(Path(tmp)/'work'));path=project.root/'inputs/flow.json';path.write_bytes(p.encoded(impossible()))
            with self.assertRaises(ValueError):planner.propose(project,'flow.json','selected.json')
            self.assertFalse((project.root/'inputs/selected.json').exists());self.assertNotIn('flows',project.workspace.ls('/'))
            path.write_text('{"schema":"raveil.mf01-flow/v1","schema":"x"}')
            with self.assertRaises(ValueError):planner.propose(project,'flow.json')
