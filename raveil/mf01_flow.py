"""Bounded composition of admitted whole-grid computations.

Links carry committed grid values between existing sessions; they grant no guest
capability and do not turn stage scheduling into a hardware-performance claim.
"""
import copy
from . import mf01_grid as grid,project as p

SCHEMA='raveil.mf01-flow/v1'


def materialize(source,outputs):
    result=copy.deepcopy(source)
    result['inputs']=[dict(schema='raveil.grid-input/v2',**copy.deepcopy(outputs[item['from']]))
                      if type(item) is dict and set(item)=={'from'} else copy.deepcopy(item)
                      for item in source['inputs']]
    return result


def structure(value):
    if (type(value) is not dict or set(value)!={'schema','stages','outputs'} or value['schema']!=SCHEMA or
        type(value['stages']) is not list or not 1<=len(value['stages'])<=8 or
        type(value['outputs']) is not list or not 1<=len(value['outputs'])<=8):
        raise ValueError('flow requires1..8 named stages and outputs')
    stages={};dependencies={}
    for stage in value['stages']:
        if type(stage) is not dict or set(stage)!={'name','source'} or type(stage['name']) is not str:
            raise ValueError('invalid flow stage')
        name=p.name(stage['name']);source=stage['source']
        if name in stages:raise ValueError('duplicate flow stage')
        if type(source) is not dict or type(source.get('inputs')) is not list or not 1<=len(source['inputs'])<=2:
            raise ValueError('flow stage requires grid source inputs')
        stages[name]=source;dependencies[name]=set()
        for item in source['inputs']:
            if type(item) is dict and 'from' in item:
                if set(item)!={'from'} or type(item['from']) is not str:raise ValueError('invalid flow link')
                dependencies[name].add(p.name(item['from']))
    for name in value['outputs']:
        if type(name) is not str or name not in stages:raise ValueError('unknown flow output')
    if len(set(value['outputs']))!=len(value['outputs']):raise ValueError('duplicate flow output')
    if any(not deps<=stages.keys() for deps in dependencies.values()):raise ValueError('unknown flow producer')
    pending=set(stages);order=[]
    while pending:
        ready=sorted(name for name in pending if not dependencies[name]&pending)
        if not ready:raise ValueError('cyclic flow dependencies')
        # One stable serial schedule. Authoring order does not grant execution order.
        name=ready[0];pending.remove(name);order.append(name)
    return stages,dependencies,order


def compile(value):
    stages,dependencies,order=structure(value)
    placeholders={};plan=[];sessions=jobs=0
    for name in order:
        source=materialize(stages[name],placeholders);lowered=grid.compile(source)
        shape=[lowered['rows'],lowered['columns']]
        count=len(lowered['batch']['items']);job_count=sum(len(item['dag']['jobs']) for item in lowered['batch']['items'])
        sessions+=count;jobs+=job_count
        if sessions>16 or jobs>128:raise ValueError('flow exceeds16 sessions or128 jobs')
        placeholders[name]=dict(rows=shape[0],columns=shape[1],words=[0]*(shape[0]*shape[1]))
        plan.append(dict(name=name,dependencies=sorted(dependencies[name]),shape=shape,sessions=count,jobs=job_count))
    return dict(order=order,stages=plan,outputs=list(value['outputs']),sessions=sessions,jobs=jobs)


def reference(value):
    plan=compile(value);stages={s['name']:s['source'] for s in value['stages']};outputs={}
    for stage in plan['stages']:
        name=stage['name'];source=materialize(stages[name],outputs);r,c=stage['shape']
        outputs[name]=dict(rows=r,columns=c,words=grid.reference(source))
    return [dict(name=name,**outputs[name]) for name in plan['outputs']]
