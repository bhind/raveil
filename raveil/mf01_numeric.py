"""Source-only signed ordering legalization into the unchanged uint32 MF01 ISA."""
import copy

SIGNED_OPS = {'max_i32': 2, 'relu_i32': 1}


def lower(nodes, result, *, share_transforms=False):
    """Preserve public SSA names; compiler admission still enforces physical limits."""
    if type(nodes) is not list or not 1 <= len(nodes) <= 15:
        raise ValueError('one to fifteen source map nodes required')
    seen = set()
    for node in nodes:
        if type(node) is not dict:
            raise ValueError('invalid source node')
        op = node.get('op')
        if type(op) is not str or op not in {'load','add','mul','max','add_imm','ge_imm',*SIGNED_OPS}:
            raise ValueError('invalid source operation')
        fields = {'id','op'} | ({'view'} if op == 'load' else
                 {'args','imm'} if op in ('add_imm','ge_imm') else {'args'})
        name = node.get('id')
        if set(node) != fields or type(name) is not str or not name or name in seen:
            raise ValueError('invalid source node fields or identifier')
        args = node.get('args', [])
        arity = 0 if op == 'load' else SIGNED_OPS.get(op, 1 if 'imm' in node else 2)
        if type(args) is not list or len(args) != arity:
            raise ValueError('incorrect source arity')
        if any(type(arg) is not str or arg not in seen for arg in args):
            raise ValueError('source nodes must be in dependency order')
        if op == 'load' and (type(node['view']) is not str or not node['view']):
            raise ValueError('invalid source view')
        if 'imm' in node and (type(node['imm']) is not int or not 0 <= node['imm'] < 1 << 22):
            raise ValueError('source immediate must fit unsigned22 bits')
        seen.add(name)
    if type(result) is not str or result not in seen:
        raise ValueError('unknown source result')
    reserved = set(seen)
    emitted = []
    serial = 0
    sign = None
    biased = {}

    def emit(op, args, *, name=None, imm=None):
        nonlocal serial
        if name is None:
            while True:
                name = f'__mf01_numeric_{serial}'
                serial += 1
                if name not in reserved:
                    reserved.add(name)
                    break
        node = dict(id=name, op=op, args=args)
        if imm is not None:
            node['imm'] = imm
        emitted.append(node)
        return name

    def translated(name):
        if share_transforms and name in biased:
            return biased[name]
        value = emit('add', [name,sign])
        if share_transforms:
            biased[name] = value
        return value

    for node in nodes:
        op = node['op']
        if op not in SIGNED_OPS:
            emitted.append(copy.deepcopy(node))
            continue
        a = node['args'][0]
        if sign is None:
            # GE_U32(x, 0) is exactly one, independent of runtime input.
            one = emit('ge_imm', [a], imm=0)
            hi = emit('add_imm', [one], imm=32767)
            lo = emit('add_imm', [one], imm=65535)
            sign = emit('mul', [hi,lo])
        left = translated(a)
        right = sign if op == 'relu_i32' else translated(node['args'][1])
        selected = emit('max', [left,right])
        emit('add', [selected,sign], name=node['id'])
        if share_transforms:
            # T(T(selected)) = selected, even when the public result is also used.
            biased[node['id']] = selected
    return emitted
