"""Strict static array source and conservative automatic materialization.

Planning uses structure only. Production binding gathers words but never computes
an arithmetic result. ``reference`` is an independent whole-source interpreter.
"""
import copy
from . import project as p, grid_kernel as g, mf01_grid as grid

SCHEMA = 'raveil.array-program/v1'
MAX_NODES = 128
MAX_PASSES = 128
MAX_SESSIONS = 128
MAX_WORK = 32768
MAX_PLANES = 65536
MASK = 0xffffffff
OPS = {'add': 2, 'mul': 2, 'max': 2, 'max_i32': 2, 'relu_i32': 1,
       'add_imm': 1, 'ge_imm': 1}


def _fields(value, fields, message):
    if type(value) is not dict or set(value) != set(fields):
        raise ValueError(message)


def _nodes(nodes, result, views):
    if type(nodes) is not list or not 1 <= len(nodes) <= MAX_NODES:
        raise ValueError('array map requires 1..128 nodes')
    seen = set()
    for node in nodes:
        if type(node) is not dict or type(node.get('op')) is not str:
            raise ValueError('invalid array node')
        op = node['op']
        if op != 'load' and op not in OPS:
            raise ValueError('unsupported array operation')
        fields = {'id', 'op'} | ({'view'} if op == 'load' else {'args'})
        if op in ('add_imm', 'ge_imm'):
            fields.add('imm')
        _fields(node, fields, 'invalid array node fields')
        name = node['id']
        if type(name) is not str or not name or len(name) > 128 or name in seen:
            raise ValueError('invalid or duplicate array node id')
        if op == 'load':
            if type(node['view']) is not str or node['view'] not in views:
                raise ValueError('unknown array view')
        else:
            args = node['args']
            if (type(args) is not list or len(args) != OPS[op] or
                    any(type(a) is not str or a not in seen for a in args)):
                raise ValueError('array nodes require dependency-ordered SSA')
        if 'imm' in node:
            grid.integer(node['imm'], 0, (1 << 22) - 1)
        seen.add(name)
    if type(result) is not str or result not in seen:
        raise ValueError('unknown array result')


def structure(value):
    _fields(value, {'schema', 'stages', 'outputs'}, 'invalid array program fields')
    if (value['schema'] != SCHEMA or type(value['stages']) is not list or
            not 1 <= len(value['stages']) <= 8 or type(value['outputs']) is not list or
            not 1 <= len(value['outputs']) <= 8):
        raise ValueError('array program requires 1..8 stages and outputs')
    stages = {}; deps = {}; total = 0; literal_words = 0
    for stage in value['stages']:
        _fields(stage, {'name', 'source'}, 'invalid array stage')
        if type(stage['name']) is not str:
            raise ValueError('array stage name must be text')
        name = p.name(stage['name'])
        if name in stages:
            raise ValueError('duplicate array stage')
        s = stage['source']
        if type(s) is not dict:
            raise ValueError('invalid array stage source')
        _fields(s, {'inputs', 'shape', 'boundary', 'kernel'} | ({'post'} if 'post' in s else set()),
                'invalid array stage fields (tiles are automatic)')
        if type(s['inputs']) is not list or not 1 <= len(s['inputs']) <= 8:
            raise ValueError('array stage requires 1..8 inputs')
        if type(s['shape']) is not list or len(s['shape']) != 2:
            raise ValueError('array output needs two dimensions')
        for size in s['shape']:
            grid.integer(size, 1, 64)
        g.boundary(s['boundary']); deps[name] = set()
        for item in s['inputs']:
            if type(item) is dict and 'from' in item:
                _fields(item, {'from'}, 'invalid array producer link')
                if type(item['from']) is not str:
                    raise ValueError('array producer must be text')
                deps[name].add(p.name(item['from']))
            else:
                literal_words += len(g.read_input(p.encoded(item))['words'])
        k = s['kernel']
        _fields(k, {'extent', 'fold', 'views', 'nodes', 'result'}, 'invalid array kernel')
        grid.integer(k['extent'], 1, 64)
        if type(k['fold']) is not str or k['fold'] not in ('sum', 'max'):
            raise ValueError('array fold requires sum or unsigned max')
        if type(k['views']) is not dict or not 1 <= len(k['views']) <= 8:
            raise ValueError('array requires 1..8 views')
        for vname, view in k['views'].items():
            if type(vname) is not str or not vname or len(vname) > 128:
                raise ValueError('invalid array view name')
            _fields(view, {'input', 'offset', 'row', 'column', 'step'}, 'invalid array view')
            grid.integer(view['input'], 0, len(s['inputs']) - 1)
            for key in ('offset', 'row', 'column', 'step'):
                if type(view[key]) is not list or len(view[key]) != 2:
                    raise ValueError('array view needs coordinate pair')
                for x in view[key]:
                    grid.integer(x, -63 if key == 'offset' else 0, 63)
        _nodes(k['nodes'], k['result'], k['views']); total += len(k['nodes'])
        if 'post' in s:
            _fields(s['post'], {'nodes', 'result'}, 'invalid array post map')
            _nodes(s['post']['nodes'], s['post']['result'], {'reduced'})
            total += len(s['post']['nodes'])
        stages[name] = s
    if total > MAX_NODES:
        raise ValueError('array exceeds 128 total source nodes')
    if any(type(n) is not str or n not in stages for n in value['outputs']):
        raise ValueError('unknown array output')
    if len(set(value['outputs'])) != len(value['outputs']):
        raise ValueError('duplicate array output')
    if any(not d <= stages.keys() for d in deps.values()):
        raise ValueError('unknown array producer')
    pending = set(stages); order = []
    while pending:
        ready = sorted(n for n in pending if not deps[n] & pending)
        if not ready:
            raise ValueError('cyclic array stages')
        order.append(ready[0]); pending.remove(ready[0])
    return stages, order, total, literal_words


def bind(value, step, planes):
    """Bind an admitted plan pass to exact input words; no arithmetic evaluation."""
    rows, columns = step['shape']
    if 'gather' in step:
        recipe = step['gather']; s = next(x['source'] for x in value['stages'] if x['name'] == recipe['stage'])
        view = s['kernel']['views'][recipe['view']]
        item = s['inputs'][view['input']]
        operand = planes[step['args'][0]] if 'from' in item else item
        words = []
        for r in range(rows):
            for c in range(columns):
                coords = [view['offset'][a] + r * view['row'][a] + c * view['column'][a] +
                          recipe['k'] * view['step'][a] for a in range(2)]
                words.append(g.sample(operand, *coords, s['boundary']))
        operands = [dict(rows=rows, columns=columns, words=words)]
    else:
        operands = [planes[n] for n in step['args']]
    nodes = [dict(id=f'a{i}', op='load', view=f'v{i}') for i in range(len(operands))]
    result = 'a0'
    if step['op'] != 'load':
        node = dict(id='out', op=step['op'], args=[n['id'] for n in nodes])
        if 'imm' in step:
            node['imm'] = step['imm']
        nodes.append(node); result = 'out'
    return dict(schema=grid.SCHEMA_V5, inputs=[dict(schema=g.INPUT, **copy.deepcopy(o)) for o in operands],
                shape=[rows, columns], tile=[16, 16], boundary='zero',
                kernel=dict(extent=1, fold='sum', views={f'v{i}': dict(input=i, offset=[0, 0],
                            row=[1, 0], column=[0, 1], step=[0, 0]) for i in range(len(operands))},
                            nodes=nodes, result=result))


def compile(value):
    stages, order, total, literal_words = structure(value)
    steps = []; results = {}; sessions = work = 0

    def emit(shape, op, args, **extra):
        nonlocal sessions, work
        rows, cols = shape; sessions += ((rows + 15) // 16) * ((cols + 15) // 16)
        work += rows * cols
        if len(steps) >= MAX_PASSES or sessions > MAX_SESSIONS or work > MAX_WORK:
            raise ValueError('array exceeds pass/session/work budget')
        identity = f'p{len(steps):03d}'
        steps.append(dict(id=identity, shape=list(shape), op=op, args=list(args), **extra))
        return identity

    for name in order:
        s = stages[name]; k = s['kernel']; accumulator = None
        for index in range(k['extent']):
            refs = {}
            for node in k['nodes']:
                if node['op'] == 'load':
                    item = s['inputs'][k['views'][node['view']]['input']]
                    args = [results[item['from']]] if 'from' in item else []
                    ref = emit(s['shape'], 'load', args, gather=dict(stage=name, view=node['view'], k=index))
                else:
                    ref = emit(s['shape'], node['op'], [refs[a] for a in node['args']],
                               **({'imm': node['imm']} if 'imm' in node else {}))
                refs[node['id']] = ref
            term = refs[k['result']]
            accumulator = term if accumulator is None else emit(s['shape'], 'add' if k['fold'] == 'sum' else 'max', [accumulator, term])
        if 'post' in s:
            refs = {}
            for node in s['post']['nodes']:
                args = [accumulator] if node['op'] == 'load' else [refs[a] for a in node['args']]
                refs[node['id']] = emit(s['shape'], node['op'], args,
                                       **({'imm': node['imm']} if 'imm' in node else {}))
            accumulator = refs[s['post']['result']]
        results[name] = accumulator
    last = {s['id']: i for i, s in enumerate(steps)}
    for i, s in enumerate(steps):
        for ref in s['args']:
            last[ref] = i
    outputs = [dict(name=n, producer=results[n]) for n in value['outputs']]
    for o in outputs:
        last[o['producer']] = len(steps)
    planes = {}; sizes = {}; peak = literal_words
    for i, s in enumerate(steps):
        size = s['shape'][0] * s['shape'][1]
        # Conservative logical workspace: retained planes, packed operands, result.
        packing = (1 if 'gather' in s else len(s['args'])) * size
        peak = max(peak, literal_words + sum(sizes.values()) + packing + size)
        if peak > MAX_PLANES:
            raise ValueError('array exceeds logical plane-word budget')
        grid.compile(bind(value, s, planes))  # Existing backend admission is authoritative.
        planes[s['id']] = dict(rows=s['shape'][0], columns=s['shape'][1], words=[0] * size)
        sizes[s['id']] = size
        s['release'] = sorted(n for n in sizes if last[n] == i)
        for n in s['release']:
            del sizes[n]; del planes[n]
    return dict(order=order, source_nodes=total, passes=steps, outputs=outputs,
                sessions=sessions, work_words=work, peak_plane_words=peak)


def publish(plan, planes):
    return [dict(name=o['name'], **copy.deepcopy(planes[o['producer']])) for o in plan['outputs']]


def commit(planes, step, output):
    planes[step['id']] = output
    for name in step['release']:
        del planes[name]


def reference(value):
    """Original-coordinate, scalar SSA interpreter; never consumes compiled passes."""
    stages, order, _, _ = structure(value); outputs = {}

    def evaluate(nodes, result, load):
        values = {}
        for node in nodes:
            op = node['op']; args = [values[a] for a in node.get('args', [])]
            if op == 'load': word = load(node['view'])
            elif op == 'add': word = args[0] + args[1]
            elif op == 'mul': word = args[0] * args[1]
            elif op == 'max': word = max(args)
            elif op == 'max_i32': word = max(a if a < 0x80000000 else a - 0x100000000 for a in args)
            elif op == 'relu_i32': word = max(0, args[0] if args[0] < 0x80000000 else args[0] - 0x100000000)
            elif op == 'add_imm': word = args[0] + node['imm']
            elif op == 'ge_imm': word = int(args[0] >= node['imm'])
            values[node['id']] = word & MASK
        return values[result]

    for name in order:
        s = stages[name]; kernel = s['kernel']; rows, columns = s['shape']; words = []
        inputs = [outputs[item['from']] if 'from' in item else item for item in s['inputs']]
        for row in range(rows):
            for col in range(columns):
                accumulator = 0
                for k in range(kernel['extent']):
                    def sample(vname):
                        v = kernel['views'][vname]; data = inputs[v['input']]
                        r = v['offset'][0] + row * v['row'][0] + col * v['column'][0] + k * v['step'][0]
                        c = v['offset'][1] + row * v['row'][1] + col * v['column'][1] + k * v['step'][1]
                        h, w = data['rows'], data['columns']
                        if s['boundary'] == 'zero' and not (0 <= r < h and 0 <= c < w):
                            return 0
                        if s['boundary'] == 'clamp': r, c = min(h-1, max(0, r)), min(w-1, max(0, c))
                        if s['boundary'] == 'wrap': r, c = r % h, c % w
                        return data['words'][r*w+c]
                    term = evaluate(kernel['nodes'], kernel['result'], sample)
                    accumulator = ((accumulator + term) & MASK) if kernel['fold'] == 'sum' else max(accumulator, term)
                if 'post' in s:
                    post = s['post']; accumulator = evaluate(post['nodes'], post['result'], lambda _: accumulator)
                words.append(accumulator)
        outputs[name] = dict(rows=rows, columns=columns, words=words)
    return [dict(name=n, **outputs[n]) for n in value['outputs']]
