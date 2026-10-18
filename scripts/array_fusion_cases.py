"""Owned functional acceptance inputs and independent source-level formulas."""
import copy
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from raveil import array_program as a
from scripts.array_program_cases import cases as original_cases, src, program, literal, view, load, output


def cases():
    selected = {'long-expression', 'pointwise-17-19', 'gemm-3-5-3',
                'stencil-zero', 'stencil-clamp', 'stencil-wrap', 'wrapped-fold-post',
                'signed-modular-threshold', 'fanout-join'}
    for name, value, expected in original_cases():
        if name in selected:
            value = copy.deepcopy(value); value['schema'] = a.SCHEMA_V2
            yield name, value, expected
    for m, n, k in [(17, 19, 64), (32, 32, 8)]:
        left = [(i % 17 - 8) & a.MASK for i in range(m * k)]
        right = [(i % 13 - 6) & a.MASK for i in range(k * n)]
        s = src(m, n, [0] * (m * n)); s['inputs'] = [literal(m, k, left), literal(k, n, right)]
        s['kernel'] = dict(extent=k, fold='sum', views={
            'a': view(0, column=(0, 0), step=(0, 1)),
            'b': view(1, row=(0, 0), step=(1, 0))},
            nodes=[load('a', 'a'), load('b', 'b'), dict(id='z', op='mul', args=['a', 'b'])], result='z')
        value = program(s); value['schema'] = a.SCHEMA_V2
        expected = [sum(left[r*k+t] * right[t*n+c] for t in range(k)) & a.MASK
                    for r in range(m) for c in range(n)]
        yield f'gemm-{m}-{n}-{k}', value, [output('answer', m, n, expected)]
    nodes = [load()]; previous = 'x'
    for i in range(23):
        name = f'n{i}'; nodes.append(dict(id=name, op='add_imm', args=[previous], imm=1)); previous = name
    words = [(i * 123457) & a.MASK for i in range(4096)]
    value = program(src(64, 64, words, nodes)); value['schema'] = a.SCHEMA_V2
    yield 'long-map-64-64', value, [output('answer', 64, 64, [(x + 23) & a.MASK for x in words])]
    first = src(2, 3, range(6), nodes); second = src(3, 2, range(6))
    second['inputs'] = [{'from': 'first'}]; second['kernel']['views']['v'] = view(row=(0, 1), column=(1, 0))
    value = dict(schema=a.SCHEMA_V2, stages=[dict(name='first', source=first), dict(name='transpose', source=second)],
                 outputs=['first', 'transpose'])
    yield 'mixed-block-transpose', value, [output('first', 2, 3, range(23, 29)), output('transpose', 3, 2, [23, 26, 24, 27, 25, 28])]


if __name__ == '__main__':
    import argparse, json
    from pathlib import Path
    parser = argparse.ArgumentParser(description='Write one editable v2 source to a fresh file.')
    parser.add_argument('name', choices=[n for n, _, _ in cases()]); parser.add_argument('output', type=Path)
    args = parser.parse_args(); value = next(v for n, v, _ in cases() if n == args.name)
    with args.output.open('x') as stream:
        json.dump(value, stream, indent=2); stream.write('\n')
