"""Versioned, structurally admitted whole-stage fusion; no host result arithmetic.

V1 plans remain the compatibility path. V2 selects a complete grid stage when
its actual backend admission and session/output costs beat scalar materialization.
Source evaluation work has a separate finite bound; fewer output planes do not
make the arithmetic disappear.
"""
import copy

from . import array_program as a, grid_kernel as g, mf01_grid as grid
from . import mf01_grid_plan as tile_planner

POLICY = 'whole-stage-then-single-output-blocks/v1'
MAX_SCALAR_EVALUATIONS = 1048576


def bind(value, step, planes):
    if value['schema'] != a.SCHEMA_V2:
        raise ValueError('fused passes require array-program/v2')
    if step['op'] == 'block':
        return _bind_block(value, step, planes)
    source = next(s['source'] for s in value['stages'] if s['name'] == step['stage'])
    inputs = []
    for item in source['inputs']:
        if 'from' in item:
            data = planes[step['producers'][item['from']]]
            inputs.append(dict(schema=g.INPUT, **copy.deepcopy(data)))
        else:
            inputs.append(copy.deepcopy(item))
    return dict(copy.deepcopy(source), schema=grid.SCHEMA_V5,
                inputs=inputs, tile=list(step['tile']))


def _cost(compiled, bound):
    jobs = [j for item in compiled['batch']['items'] for j in item['dag']['jobs']]
    return dict(sessions=len(compiled['layout']), jobs=len(jobs),
                work_words=sum(j['region']['shape'][0] * j['region']['shape'][1] for j in jobs),
                packed_input_words=sum(sum(j['region']['lengths']) for j in jobs),
                bound_input_words=sum(len(i['words']) for i in bound['inputs']))


def _fused(value, name, source, results, planes):
    # These are structural limits of the existing grid-v5 frontend. All source
    # fields, including unused declarations, were already checked by structure().
    if (len(source['inputs']) > 2 or len(source['kernel']['nodes']) > 15 or
            ('post' in source and len(source['post']['nodes']) > 15)):
        return None
    producers = {item['from']: results[item['from']] for item in source['inputs'] if 'from' in item}
    step = dict(op='fused', stage=name, shape=list(source['shape']),
                args=sorted(set(producers.values())), producers=producers, tile=[16, 16])
    bound = bind(value, step, planes)
    try:
        compiled = grid.compile(bound)
    except ValueError:
        try:
            selected = tile_planner.plan(bound)['source']
            step['tile'] = selected['tile']
            bound = selected
            compiled = grid.compile(bound)
        except ValueError:
            return None
    step.update(_cost(compiled, bound))
    return step


def _scalar_stage(name, source, results, emit):
    kernel = source['kernel']; accumulator = None
    for index in range(kernel['extent']):
        refs = {}
        for node in kernel['nodes']:
            if node['op'] == 'load':
                item = source['inputs'][kernel['views'][node['view']]['input']]
                args = [results[item['from']]] if 'from' in item else []
                ref = emit(source['shape'], 'load', args,
                           gather=dict(stage=name, view=node['view'], k=index))
            else:
                ref = emit(source['shape'], node['op'], [refs[n] for n in node['args']],
                           **({'imm': node['imm']} if 'imm' in node else {}))
            refs[node['id']] = ref
        term = refs[kernel['result']]
        accumulator = term if accumulator is None else emit(
            source['shape'], 'add' if kernel['fold'] == 'sum' else 'max', [accumulator, term])
    if 'post' in source:
        refs = {}
        for node in source['post']['nodes']:
            args = [accumulator] if node['op'] == 'load' else [refs[n] for n in node['args']]
            refs[node['id']] = emit(source['shape'], node['op'], args,
                                   **({'imm': node['imm']} if 'imm' in node else {}))
        accumulator = refs[source['post']['result']]
    return accumulator


def _bind_block(value, step, planes):
    operands = []
    for spec in step['inputs']:
        if 'plane' in spec:
            operands.append(dict(schema=g.INPUT, **copy.deepcopy(planes[spec['plane']])))
        else:
            request = dict(op='load', shape=step['shape'], args=spec['args'], gather=spec['gather'])
            operands.append(a.bind(value, request, planes)['inputs'][0])
    return dict(schema=grid.SCHEMA_V5, inputs=operands, shape=list(step['shape']),
                tile=[16, 16], boundary='zero', kernel=dict(extent=1, fold='sum',
                views={f'v{i}': dict(input=i, offset=[0, 0], row=[1, 0], column=[0, 1],
                                    step=[0, 0]) for i in range(len(operands))},
                nodes=copy.deepcopy(step['nodes']), result=step['result']))


def _block(value, segment, output, renamed, planes):
    inputs = []; prefix = []; nodes = []; refs = {}; args = set()

    def slot(spec):
        if spec not in inputs:
            inputs.append(spec)
        if len(inputs) > 2:
            raise ValueError('block needs more than two inputs')
        return inputs.index(spec)

    def read(ref):
        if ref in refs:
            return refs[ref]
        producer = renamed[ref]; args.add(producer)
        index = slot(dict(plane=producer)); identity = f'e{index}'
        node = dict(id=identity, op='load', view=f'v{index}')
        if node not in prefix:
            prefix.append(node)
        return identity

    for i, raw in enumerate(segment):
        identity = f'n{i}'
        if raw['op'] == 'load':
            if 'gather' in raw:
                producers = [renamed[n] for n in raw['args']]; args.update(producers)
                index = slot(dict(gather=copy.deepcopy(raw['gather']), args=producers))
            else:
                producer = renamed[raw['args'][0]] if raw['args'][0] not in refs else None
                if producer is None:
                    # Identity of an in-block value: retain a real arithmetic
                    # node rather than remove a declared operation.
                    nodes.append(dict(id=identity, op='add_imm', args=[refs[raw['args'][0]]], imm=0))
                    refs[raw['id']] = identity
                    continue
                args.add(producer); index = slot(dict(plane=producer))
            node = dict(id=identity, op='load', view=f'v{index}')
        else:
            node = dict(id=identity, op=raw['op'], args=[read(n) for n in raw['args']])
            if 'imm' in raw:
                node['imm'] = raw['imm']
        nodes.append(node); refs[raw['id']] = identity
    step = dict(op='block', shape=list(segment[0]['shape']), args=sorted(args),
                inputs=inputs, nodes=prefix + nodes, result=refs[output],
                scalar_passes=len(segment))
    source = _bind_block(value, step, planes)
    step.update(_cost(grid.compile(source), source))
    return step


def _coalesce(value, original, results):
    """Greedy contiguous blocks with one externally observable result.

    No arithmetic is dropped or duplicated. Multiple live outputs force a cut;
    existing grid admission decides instruction/register/packing feasibility.
    Stage outputs are cuts even when not requested, preserving stage boundaries.
    """
    last = {step['id']: i for i, step in enumerate(original)}
    for i, step in enumerate(original):
        for ref in step['args']:
            last[ref] = i
    for ref in results.values():
        last[ref] = len(original)
    renamed = {}; planes = {}; combined = []; index = 0
    while index < len(original):
        if len(combined) >= a.MAX_PASSES:
            raise ValueError('array exceeds pass/session/work budget')
        first = original[index]; chosen = None; end = index + 1; output = first['id']
        if first['op'] != 'fused':
            # Grid-v5 accepts at most fifteen source nodes. Prefix loads may
            # consume some of those slots and actual signed lowering can add more.
            for limit in range(index + 2, min(len(original), index + 15) + 1):
                segment = original[index:limit]
                if (any(s['op'] == 'fused' or s['shape'] != first['shape'] for s in segment) or
                        any(s['id'] in results.values() for s in segment[:-1])):
                    break
                visible = [s['id'] for s in segment if last[s['id']] >= limit]
                if len(visible) > 1:
                    continue
                result = visible[0] if visible else segment[-1]['id']
                try:
                    candidate = _block(value, segment, result, renamed, planes)
                except ValueError:
                    continue
                chosen, end, output = candidate, limit, result
        if chosen is None:
            chosen = copy.deepcopy(first)
            chosen['args'] = [renamed[n] for n in first['args']]
            if first['op'] == 'fused':
                chosen['producers'] = {n: renamed[ref] for n, ref in first['producers'].items()}
        chosen['id'] = f'p{len(combined):03d}'
        renamed[output] = chosen['id']
        rows, columns = chosen['shape']
        planes[chosen['id']] = dict(rows=rows, columns=columns, words=[0] * (rows * columns))
        combined.append(chosen); index = end
    return combined, {name: renamed[ref] for name, ref in results.items()}


def compile(value):
    stages, order, total, literal_words = a.structure(value)
    scalar_evaluations = sum(
        s['shape'][0] * s['shape'][1] * (
            s['kernel']['extent'] * len(s['kernel']['nodes']) + s['kernel']['extent'] - 1 +
            len(s.get('post', {}).get('nodes', []))) for s in stages.values())
    if scalar_evaluations > MAX_SCALAR_EVALUATIONS:
        raise ValueError('array exceeds scalar-evaluation budget')

    # Structural zero inputs ensure planning never depends on runtime words.
    structural = copy.deepcopy(value)
    for stage in structural['stages']:
        for item in stage['source']['inputs']:
            if 'from' not in item:
                item['words'] = [0] * len(item['words'])
    steps = []; results = {}; placeholders = {}; choices = []

    def emit(shape, op, args, **extra):
        identity = f'p{len(steps):03d}'
        steps.append(dict(id=identity, shape=list(shape), op=op, args=list(args), **extra))
        return identity

    for name in order:
        source = stages[name]; rows, columns = source['shape']; kernel = source['kernel']
        count = kernel['extent'] * len(kernel['nodes']) + kernel['extent'] - 1 + len(source.get('post', {}).get('nodes', []))
        scalar_sessions = count * ((rows + 15) // 16) * ((columns + 15) // 16)
        candidate = _fused(structural, name, source, results, placeholders)
        if candidate is not None and (candidate['sessions'], candidate['work_words'], 1) <= (
                scalar_sessions, count * rows * columns, count):
            extra = {k: v for k, v in candidate.items() if k not in ('shape', 'op', 'args')}
            result = emit(source['shape'], 'fused', candidate['args'], **extra)
            mode = 'fused'
        else:
            result = _scalar_stage(name, source, results, emit)
            mode = 'scalar'
        results[name] = result
        placeholders[result] = dict(rows=rows, columns=columns, words=[0] * (rows * columns))
        choices.append(dict(stage=name, mode=mode, scalar_passes=count, scalar_sessions=scalar_sessions))

    steps, results = _coalesce(structural, steps, results)
    if len(steps) > a.MAX_PASSES:
        raise ValueError('array exceeds pass/session/work budget')
    last = {s['id']: i for i, s in enumerate(steps)}
    for i, step in enumerate(steps):
        for ref in step['args']:
            last[ref] = i
    outputs = [dict(name=n, producer=results[n]) for n in value['outputs']]
    for output in outputs:
        last[output['producer']] = len(steps)
    planes = {}; sizes = {}; peak = literal_words; sessions = jobs = work = packed = 0
    for i, step in enumerate(steps):
        source = a.bind(structural, step, planes)
        cost = _cost(grid.compile(source), source)
        if step['op'] in ('fused', 'block') and any(step[k] != v for k, v in cost.items()):
            raise ValueError('fused structural cost differs')
        sessions += cost['sessions']; jobs += cost['jobs']; work += cost['work_words']
        packed += cost['packed_input_words']
        if sessions > a.MAX_SESSIONS or work > a.MAX_WORK:
            raise ValueError('array exceeds pass/session/work budget')
        size = step['shape'][0] * step['shape'][1]
        # Logical live storage: original literals + retained planes + full bound
        # input copies + tile/job packing + job results + assembled output. Not RSS.
        peak = max(peak, literal_words + sum(sizes.values()) + cost['bound_input_words'] +
                   cost['packed_input_words'] + cost['work_words'] + size)
        if peak > a.MAX_PLANES:
            raise ValueError('array exceeds logical plane-word budget')
        planes[step['id']] = dict(rows=step['shape'][0], columns=step['shape'][1], words=[0] * size)
        sizes[step['id']] = size
        step['release'] = sorted(n for n in sizes if last[n] == i)
        for n in step['release']:
            del planes[n]; del sizes[n]
    return dict(policy=POLICY, order=order, source_nodes=total, passes=steps, outputs=outputs,
                sessions=sessions, jobs=jobs, work_words=work, peak_plane_words=peak,
                packed_input_words=packed, scalar_evaluations=scalar_evaluations, stages=choices)
