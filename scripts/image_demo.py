"""Owned integer image workload and independent oracle for EXP-0013."""
import copy
import struct
from raveil import array_program as compiler


def validate(image):
    if type(image) is not list or not 2 <= len(image) <= 64 or len(image) % 2:
        raise ValueError('image needs an even height in 2..64')
    if type(image[0]) is not list or not 2 <= len(image[0]) <= 64 or len(image[0]) % 2:
        raise ValueError('image needs an even width in 2..64')
    width = len(image[0])
    if any(type(row) is not list or len(row) != width or
           any(type(v) is not int or not 0 <= v <= 255 for v in row) for row in image):
        raise ValueError('image needs rectangular uint8 integer pixels')
    return len(image), width


def reference(image):
    """Signed horizontal difference, positive activation, 2x2 maximum pooling.

    Does not use source nodes, compiler, backend or gathered operands.
    """
    height, width = validate(image)
    gradient = [[image[r][min(c+1, width-1)]-image[r][max(c-1, 0)]
                 for c in range(width)] for r in range(height)]
    activated = [[max(0, pixel) for pixel in row] for row in gradient]
    pooled = [[max(activated[r+dr][c+dc] for dr in (0, 1) for dc in (0, 1))
               for c in range(0, width, 2)] for r in range(0, height, 2)]
    return [dict(name=name, rows=len(matrix), columns=len(matrix[0]),
                 words=[v & 0xffffffff for row in matrix for v in row])
            for name, matrix in [('gradient', gradient), ('activated', activated), ('pooled', pooled)]]


def source(image, fused=True):
    height, width = validate(image)
    if type(fused) is not bool: raise ValueError('fused must be bool')
    def view(index=0, offset=(0, 0), row=(1, 0), column=(0, 1)):
        return dict(input=index, offset=list(offset), row=list(row), column=list(column), step=[0, 0])
    def load(name): return dict(id=name, op='load', view=name)
    def stage(name, inputs, shape, views, nodes):
        return dict(name=name, source=dict(inputs=inputs, shape=shape, boundary='clamp',
                    kernel=dict(extent=1, fold='sum', views=views, nodes=nodes, result=nodes[-1]['id'])))
    gradient = stage('gradient', [dict(schema='raveil.grid-input/v2', rows=height, columns=width,
                                      words=[p for row in image for p in row]),
                                 dict(schema='raveil.grid-input/v2', rows=1, columns=1, words=[0xffffffff])],
                     [height, width], dict(left=view(offset=(0, -1)), right=view(offset=(0, 1)),
                                          negative=view(1, row=(0, 0), column=(0, 0))),
                     [load('left'), load('right'), load('negative'),
                      dict(id='negated', op='mul', args=['left', 'negative']),
                      dict(id='difference', op='add', args=['right', 'negated'])])
    activated = stage('activated', [{'from': 'gradient'}], [height, width], {'x': view()},
                      [load('x'), dict(id='positive', op='relu_i32', args=['x'])])
    views = {f'p{i}': view(offset=offset, row=(2, 0), column=(0, 2))
             for i, offset in enumerate(((0, 0), (0, 1), (1, 0), (1, 1)))}
    pooled = stage('pooled', [{'from': 'activated'}], [height//2, width//2], views,
                   [*[load(f'p{i}') for i in range(4)],
                    dict(id='a', op='max', args=['p0', 'p1']),
                    dict(id='b', op='max', args=['p2', 'p3']),
                    dict(id='result', op='max', args=['a', 'b'])])
    value = dict(schema=compiler.SCHEMA_V2 if fused else compiler.SCHEMA,
                 stages=[gradient, activated, pooled], outputs=['gradient', 'activated', 'pooled'])
    compiler.compile(value)
    return value


def cases():
    # Public deterministic generated data; no external image/data dependency.
    yield 'blocks-16', [[220 if (3 <= r < 13 and 3 <= c < 7) or
                        (9 <= r < 13 and 3 <= c < 13) else 20 for c in range(16)] for r in range(16)]
    yield 'diagonal-24', [[240 if abs(r-c) < 3 or (r-12)**2+(c-12)**2 < 20 else 10
                         for c in range(24)] for r in range(24)]
    yield 'texture-16x24', [[(r*37+c*19+(r*c)%71) % 256 for c in range(24)] for r in range(16)]


def trace_metrics(raw, device):
    """Metrics from a separately validated successful runtime trace.

    Caller must validate the complete parent/RTL evidence first. Cycles start at
    the existing harness's first post-start loop; the final write response finishes
    this RTL on the same edge. Reset/start edges and host gaps are excluded.
    """
    if not raw or len(raw) % 24: raise ValueError('empty or truncated trace')
    if (device.get('schema') != 'raveil.fold-device/v1' or device.get('success') != 1 or
            device.get('fault') != 0 or device.get('cancelled') != 0):
        raise ValueError('metrics require successful RTL execution')
    reads = writes = responses = 0; previous = -1; pending = None; last = None
    for row in struct.iter_unpack('<6I', raw):
        kind, cycle, write, address, value, error = row
        if cycle <= previous or write not in (0, 1) or error: raise ValueError('invalid trace order/status')
        previous = cycle
        if kind == 0:
            if pending is not None: raise ValueError('overlapping request')
            pending = (write, address); writes += write; reads += 1-write
        elif kind == 1:
            if pending != (write, address): raise ValueError('unmatched response')
            pending = None; responses += 1
        else: raise ValueError('unknown event')
        last = row
    if pending is not None or last[0] != 1 or last[2] != 1: raise ValueError('no final write completion')
    if (reads, writes, reads+writes, responses) != tuple(device.get(k) for k in ('reads','writes','accepted','completed')):
        raise ValueError('trace/receipt counts differ')
    return dict(rtl_active_cycles=last[1]+1, reads=reads, writes=writes,
                transactions=reads+writes, interface_payload_bytes=4*(reads+writes))


def pgm(image):
    h, w = validate(image)
    return f'P5\n{w} {h}\n255\n'.encode()+bytes(v for row in image for v in row)


def read_pgm(raw):
    # Deliberately one explicit P5 subset; no external decoder dependency.
    import re
    match = re.match(rb'P5\n([0-9]+) ([0-9]+)\n255\n', raw)
    if not match: raise ValueError('use P5 with width height and max255 on separate lines')
    w, h = map(int, match.groups()); data = raw[match.end():]
    if not 2 <= h <= 64 or not 2 <= w <= 64 or len(data) != h*w:
        raise ValueError('invalid PGM dimensions or length')
    image = [list(data[r*w:(r+1)*w]) for r in range(h)]; validate(image)
    return image
