#!/usr/bin/env python3
"""Reproducible source-coordinate falsification, optional coupled execution.

The expected formula is built with the source, without calling the grid oracle,
packer, MF01 interpreter or admission functions. Rejected partitions are retained
as rejections, never silently counted as successful comparisons. Signed mode also
records independent counterfactuals and selects only numerically sensitive cases.
"""
import argparse,copy,collections,json,random,sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from raveil import mf01_grid as g,fold_dag as d,project as p
from raveil.grid_assembly import assemble

MASK=(1<<32)-1


def generated(seed,count,numeric="unsigned"):
    if numeric not in {"unsigned","signed32"}:raise ValueError("unknown numerical mode")
    signed_mode=numeric=="signed32"
    rng=random.Random(seed)
    edges=[0,1,2,127,128,65535,1<<31,MASK-1,MASK]
    binary={'add':lambda a,b:(a+b)&MASK,'mul':lambda a,b:(a*b)&MASK,'max':max}
    for index in range(count):
        # The first twelve form all boundary/fold/post combinations.
        boundary=['zero','clamp','wrap'][index%3]
        fold=['sum','max'][(index//3)%2];post=(index//6)%2==1
        rows,cols=rng.randint(1,8),rng.randint(1,8);extent=rng.randint(1,4)
        inputs=[]
        for _ in range(1+(index//12)%2):
            h,w=rng.randint(1,9),rng.randint(1,9)
            inputs.append(dict(schema='raveil.grid-input/v2',rows=h,columns=w,
                               words=[rng.choice(edges) if rng.randrange(2) else rng.getrandbits(32) for _ in range(h*w)]))
        views={}
        for vi,name in enumerate(['a','b']):
            views[name]=dict(input=vi%len(inputs),offset=[rng.randint(-4,4) for _ in range(2)],
                             row=[rng.randint(0,2) for _ in range(2)],column=[rng.randint(0,2) for _ in range(2)],step=[rng.randint(0,2) for _ in range(2)])
        op=['add','mul','max'][rng.randrange(3)];bias=rng.choice([0,1,127,(1<<22)-1]);threshold=rng.choice([0,1,128,65535,(1<<22)-1])
        if signed_mode:op='max_i32'
        tail=rng.randrange(3);nodes=[dict(id=n,op='load',view=n) for n in ['a','b']]
        nodes.append(dict(id='x',op=op,args=['a','b']));result='x'
        if tail:
            nodes.append(dict(id='y',op='add_imm' if tail==1 else 'ge_imm',args=['x'],imm=bias if tail==1 else threshold));result='y'
        value=dict(schema=g.SCHEMA_V3 if post else g.SCHEMA_V2,inputs=inputs,shape=[rows,cols],tile=[rows,cols],boundary=boundary,
                   kernel=dict(extent=extent,fold=fold,views=views,nodes=nodes,result=result))
        post_kind=rng.randrange(3)
        if post:
            pn=[dict(id='r',op='load',view='reduced')]
            if post_kind==0:pn.append(dict(id='p',op='mul',args=['r','r']))
            elif post_kind==1:pn.append(dict(id='p',op='add_imm',args=['r'],imm=bias))
            else:pn.append(dict(id='p',op='ge_imm',args=['r'],imm=threshold))
            value['post']=dict(nodes=pn,result='p')
        if signed_mode:
            value['schema']=g.SCHEMA_V4
            if tail==2:nodes[-1]=dict(id='y',op='relu_i32',args=['x'])
            if post:
                pn.append(dict(id='activated',op='relu_i32',args=['p']))
                value['post']['result']='activated'
        outside=set()
        def sample(name,r,c,k,zero_input=None):
            v=views[name];src=inputs[v['input']];h,w=src['rows'],src['columns']
            i=v['offset'][0]+r*v['row'][0]+c*v['column'][0]+k*v['step'][0]
            j=v['offset'][1]+r*v['row'][1]+c*v['column'][1]+k*v['step'][1]
            if i<0 or j<0 or i>=h or j>=w:outside.add((name,r,c,k))
            if v['input']==zero_input:return 0
            if boundary=='zero' and (i<0 or j<0 or i>=h or j>=w):return 0
            if boundary=='clamp':i,j=min(max(i,0),h-1),min(max(j,0),w-1)
            if boundary=='wrap':i,j=i%h,j%w
            return src['words'][i*w+j]
        expected=[]
        if signed_mode:
            def signed(word):return word if word<(1<<31) else word-(1<<32)
            def formula(disable=frozenset(),zero_input=None):
                words=[]
                for r in range(rows):
                    for c in range(cols):
                        terms=[]
                        for k in range(extent):
                            a,b=(sample(n,r,c,k,zero_input) for n in ['a','b'])
                            word=max(a,b) if 'kernel-max' in disable else max(signed(a),signed(b))&MASK
                            if tail==1:word=(word+bias)&MASK
                            if tail==2 and 'kernel-relu' not in disable:word=max(0,signed(word))
                            terms.append(word)
                        total=sum(terms)&MASK if fold=='sum' else max(terms)
                        if post:
                            if post_kind==0:total=(total*total)&MASK
                            elif post_kind==1:total=(total+bias)&MASK
                            else:total=int(total>=threshold)
                            if 'post-relu' not in disable:total=max(0,signed(total))
                        words.append(total)
                return words
            expected=formula()
            replacements={'kernel-max'}|({'kernel-relu'} if tail==2 else set())|({'post-relu'} if post else set())
            counterfactual=formula(replacements)
            diagnostics=dict(counterfactual=counterfactual,
                signed_changed_cells=sum(a!=b for a,b in zip(expected,counterfactual)),
                operation_changed_cells={name:sum(a!=b for a,b in zip(expected,formula({name}))) for name in sorted(replacements)},
                input_changed_cells=[sum(a!=b for a,b in zip(expected,formula(zero_input=i))) for i in range(len(inputs))],
                outside_samples=len(outside))
        for r in range(0 if signed_mode else rows):
            for c in range(cols):
                terms=[binary[op](sample('a',r,c,k),sample('b',r,c,k)) for k in range(extent)]
                if tail==1:terms=[(word+bias)&MASK for word in terms]
                if tail==2:terms=[int(word>=threshold) for word in terms]
                total=sum(terms)&MASK if fold=='sum' else max(terms)
                if post:
                    if post_kind==0:total=(total*total)&MASK
                    elif post_kind==1:total=(total+bias)&MASK
                    else:total=int(total>=threshold)
                expected.append(total)
        tiles=[[rows,cols],[max(1,(rows+3)//4),max(1,(cols+3)//4)],
               [rng.randint(1,8),rng.randint(1,8)]]
        case=dict(index=index,source=value,expected=expected,tiles=[list(t) for t in dict.fromkeys(tuple(t) for t in tiles)])
        if signed_mode:case['numeric_diagnostics']=diagnostics
        yield case


def execute_host(compiled):
    outputs=[]
    for item in compiled['batch']['items']:
        state=d.State(item['dag'])
        for index in range(len(item['dag']['jobs'])):
            job,reads,writes=state.resolve(index)
            assert reads.bit_count()+writes.bit_count()<=4
            words=d.reference(job['region'],job['inputs']);state.commit(index,writes,words,True)
        final=state.final();assert final['available']
        outputs.append(dict(name=item['name'],shape=item['dag']['jobs'][-1]['region']['shape'],words=final['output']))
    return assemble(outputs,compiled['layout'],compiled['rows'],compiled['columns'])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed',type=int,default=226);parser.add_argument('--count',type=int,default=1000)
    parser.add_argument('--numeric',choices=['unsigned','signed32'],default='unsigned')
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--kernel',type=Path);parser.add_argument('--build',type=Path)
    args=parser.parse_args()
    if bool(args.kernel)!=bool(args.build):parser.error('--kernel and --build must be used together')
    if not 1<=args.count<=10000:parser.error('--count must be 1..10000')
    if args.kernel and args.count<24:parser.error('coupled mode requires at least 24 generated sources')
    root=args.output.resolve();root.mkdir(parents=True,exist_ok=False)
    counts=collections.Counter();rejected=collections.Counter();coverage=collections.Counter();selected={};rows=[]
    for case in generated(args.seed,args.count,args.numeric):
        original=copy.deepcopy(case['source']);admitted=0;record=dict(index=case['index'],partitions=[])
        for tile in case['tiles']:
            value={**case['source'],'tile':tile};counts['partitions']+=1
            try:compiled=g.compile(value)
            except ValueError as error:
                if str(error) not in {'tile input rectangle exceeds324 words','grid needs more than sixteen independent tiles'}:
                    (root/'failure.json').write_bytes(p.encoded(dict(case=case,tile=tile,error=str(error))))
                    raise AssertionError('unexpected admission rejection: '+str(error)) from error
                rejected[str(error)]+=1;record['partitions'].append(dict(tile=tile,rejected=str(error)));continue
            admitted+=1;actual=execute_host(compiled)
            if actual!=case['expected']:
                (root/'failure.json').write_bytes(p.encoded(dict(case=case,tile=tile,actual=actual)))
                raise AssertionError(f"differential mismatch at source {case['index']} tile {tile}")
            counts['admitted_partitions']+=1;counts['compared_words']+=len(actual)
            record['partitions'].append(dict(tile=tile,words=len(actual)))
            key=(value['boundary'],value['kernel']['fold'],'post' if 'post' in value else 'plain',str(len(value['inputs'])))
            distinct=len(set(case['expected']))
            diagnostics=case.get('numeric_diagnostics')
            eligible=diagnostics is None or (diagnostics['signed_changed_cells']>0 and diagnostics['outside_samples']>0 and all(diagnostics['input_changed_cells']))
            score=(int(eligible),int(distinct>1),-len(compiled['layout']),distinct,len(case['expected']),-case['index'])
            if key not in selected or score>selected[key]['score']:
                selected[key]=dict(index=case['index'],source=value,expected=case['expected'],score=score,numeric_diagnostics=diagnostics)
        assert case['source']==original,'compilation modified source'
        counts['sources']+=1;counts['sources_with_admission' if admitted else 'sources_without_admission']+=1
        if admitted:
            coverage[f"{original['boundary']}/{original['kernel']['fold']}/{'post' if 'post' in original else 'plain'}"]+=1
            for node in original['kernel']['nodes']+original.get('post',{}).get('nodes',[]):coverage['op/'+node['op']]+=1
            coverage['inputs/'+str(len(original['inputs']))]+=1
        rows.append(dict(**case,results=record['partitions']))
    # No all-rejected run can be green, even if every error names a known bound.
    if not counts['admitted_partitions']:raise AssertionError('no admitted partition was compared')
    required={(mode,fold,post,str(n)) for mode in ['zero','clamp','wrap'] for fold in ['sum','max'] for post in ['plain','post'] for n in [1,2]}
    if args.count>=24 and set(selected)!=required:raise AssertionError('missing declared source categories: '+str(sorted(required-set(selected))))
    if args.numeric=='signed32' and args.count>=24 and any(not case['score'][0] for case in selected.values()):
        raise AssertionError('missing signed-sensitive boundary/input representatives; increase count')
    if args.kernel and any(len(set(case['expected']))<2 for case in selected.values()):
        raise AssertionError('coupled selection lacks nonconstant outputs; increase count')
    observed_signed={name for case in selected.values() if case['numeric_diagnostics']
                     for name,cells in case['numeric_diagnostics']['operation_changed_cells'].items() if cells}
    if args.numeric=='signed32' and args.count>=24 and observed_signed!={'kernel-max','kernel-relu','post-relu'}:
        raise AssertionError('missing observable signed operation placement; increase count')
    # Full sources and expected outputs make every seed case replayable.
    (root/'cases.json').write_bytes(p.encoded(rows))
    summary=dict(evidence_class='host-generated-coordinate-differential',seed=args.seed,numeric=args.numeric,observable_signed_placements=sorted(observed_signed),counts=dict(counts),rejected=dict(rejected),coverage=dict(coverage),selection={ '/'.join(key):dict(index=v['index'],tile=v['source']['tile'],distinct_words=len(set(v['expected'])),numeric_diagnostics=v['numeric_diagnostics']) for key,v in sorted(selected.items())},actual=[])
    (root/'host-summary.json').write_bytes(p.encoded(summary));print(json.dumps(summary),flush=True)
    if args.kernel:
        from raveil import project_mf01_grid as a,project_dag_batch as b
        project=p.Project(p.init_project(root/'workspace'))
        for key,case in sorted(selected.items()):
            (project.root/'inputs/grid.json').write_bytes(p.encoded(case['source']))
            record=a.run(project,'grid.json',args.kernel,args.build)
            assert record['status']=='succeeded' and record['output']['words']==case['expected']
            child_project=p.Project(project.root/'grids'/record['id']/'child');batch=b.load(child_project,record['batch_id'])
            with patch('subprocess.Popen',side_effect=AssertionError('saved read spawned process')):
                assert a.load(project,record['id'])['output']['words']==case['expected']
            result=dict(category='/'.join(key),index=case['index'],id=record['id'],words=len(case['expected']),distinct_words=len(set(case['expected'])),sessions=len(batch['children']),jobs=sum(c['processed'] for c in batch['children']),numeric_diagnostics=case['numeric_diagnostics'])
            summary['actual'].append(result);print('PASS actual',json.dumps(result),flush=True)
        summary['actual_evidence_class']=a.CLASS
    (root/'summary.json').write_bytes(p.encoded(summary))


if __name__=='__main__':main()
