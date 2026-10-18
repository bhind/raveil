"""Prepare admitted array literals from matrices; never execute or overwrite input."""
import copy
import csv
import io
import os
from pathlib import Path
import re
from uuid import uuid4

from . import array_program as array, project as p, project_array as a, project_fold as f
from .workspace import NativeWorkspace

CSV_LIMIT = 128*1024
DECIMAL = re.compile(r'[+-]?[0-9]{1,10}\Z')


def literal(matrix, dtype='u32'):
    """Encode explicit integer data; signed input is a bit-pattern conversion."""
    if dtype not in ('u32', 'i32') or type(dtype) is not str:
        raise ValueError('dtype must be u32 or i32')
    if type(matrix) is not list or not 1 <= len(matrix) <= 64:
        raise ValueError('matrix requires 1..64 rows')
    if type(matrix[0]) is not list or not 1 <= len(matrix[0]) <= 64:
        raise ValueError('matrix requires 1..64 columns')
    columns = len(matrix[0]); words = []
    low, high = (0, 0xffffffff) if dtype == 'u32' else (-(1<<31), (1<<31)-1)
    for row in matrix:
        if type(row) is not list or len(row) != columns:
            raise ValueError('matrix must be rectangular lists of integers')
        for value in row:
            if type(value) is not int or not low <= value <= high:
                raise ValueError('matrix value is outside '+dtype+' integer range')
            words.append(value & 0xffffffff)
    return dict(schema='raveil.grid-input/v2', rows=len(matrix), columns=columns, words=words)


def read_csv(raw, dtype='u32'):
    """Headerless UTF-8 (optional BOM), comma-separated decimal integers only."""
    if type(raw) is not bytes or len(raw) > CSV_LIMIT:
        raise ValueError('CSV must be bounded bytes (maximum 128 KiB)')
    rows = []
    try:
        for row in csv.reader(io.StringIO(raw.decode('utf-8-sig'), newline=''), strict=True):
            if len(rows) >= 64 or not 1 <= len(row) <= 64:
                raise ValueError('CSV requires 1..64 rows and columns; no blank rows')
            values = []
            for cell in row:
                token = cell.strip()
                if not DECIMAL.fullmatch(token):
                    raise ValueError('CSV requires decimal integers; no header or empty cells')
                values.append(int(token, 10))
            rows.append(values)
    except (UnicodeError, csv.Error) as error:
        raise ValueError('invalid UTF-8 integer CSV') from error
    literal(rows, dtype)
    return rows


def replace_literal(program, stage, slot, matrix, dtype='u32'):
    """Copy a valid source, replace one literal, then admit the entire program.

    Operand dimensions follow the matrix. Computation shapes/views stay unchanged;
    existing zero/clamp/wrap rules apply if data dimensions differ.
    """
    data = literal(matrix, dtype)
    stages, _, _, _ = array.structure(program)
    if type(stage) is not str or stage not in stages:
        raise ValueError('unknown array stage')
    inputs = stages[stage]['inputs']
    if type(slot) is not int or not 0 <= slot < len(inputs):
        raise ValueError('slot must index an existing stage input (zero based)')
    if 'from' in inputs[slot]:
        raise ValueError('cannot replace a producer-linked input; select a literal slot')
    value = copy.deepcopy(program)
    target = next(item for item in value['stages'] if item['name'] == stage)
    target['source']['inputs'][slot] = data
    array.compile(value)
    return value


def import_csv(project, input_file, output_file, stage, slot, csv_file, dtype='u32'):
    """Publish one complete, new input JSON by exclusive link. Never replace."""
    source_raw, source, _ = a._input(project.root/'inputs', input_file)
    output_file = f._filename(output_file)
    # Validate containment and reject existing files/directories/symlinks early.
    if output_file in NativeWorkspace(project.root/'inputs').ls('/'):
        raise ValueError('output input file already exists; choose a new name')
    csv_file = Path(csv_file).absolute()
    raw = NativeWorkspace(csv_file.parent).read_text(csv_file.name, maximum=CSV_LIMIT).encode()
    matrix = read_csv(raw, dtype)
    value = replace_literal(source, stage, slot, matrix, dtype)
    payload = p.encoded(value)
    if len(payload) > 4*1024*1024:
        raise ValueError('prepared array source exceeds 4 MiB')
    target = project.root/'inputs'/output_file
    pending = target.parent/('.array-import-'+uuid4().hex+'.pending')
    created = []
    try:
        p.write_new(pending, payload, created)
        os.link(pending, target, follow_symlinks=False)
    finally:
        # Clean only our own pending inode; a published final file is never removed.
        if created:
            try:
                info = pending.lstat()
                if (info.st_dev, info.st_ino) == created[0][1]: pending.unlink()
            except FileNotFoundError: pass
    data = literal(matrix, dtype)
    return dict(schema='raveil.array-input-import/v1', input_file=input_file, output_file=output_file,
                stage=stage, slot=slot, dtype=dtype, rows=data['rows'], columns=data['columns'],
                source_sha256=p.digest(source_raw), csv_sha256=p.digest(raw), output_sha256=p.digest(payload),
                evidence_class='host input preparation and static admission; no execution')
