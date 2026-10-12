"""Checked rectangular assembly of named row-major uint32 tile results."""

def assemble(outputs,layout,rows,columns):
    if type(rows) is not int or type(columns) is not int or not 1<=rows<=64 or not 1<=columns<=64:
        raise ValueError('invalid output dimensions')
    if len(outputs)!=len(layout):raise ValueError('missing output tiles')
    values=[None]*(rows*columns)
    for output,tile in zip(outputs,layout):
        if (any(type(tile.get(k)) is not int for k in ('row','column','rows','columns')) or
            tile['row']<0 or tile['column']<0 or tile['rows']<1 or tile['columns']<1 or
            tile['row']+tile['rows']>rows or tile['column']+tile['columns']>columns):
            raise ValueError('tile rectangle out of bounds')
        if output['name']!=tile['name'] or output['shape']!=[tile['rows'],tile['columns']]:raise ValueError('tile identity differs')
        if len(output['words'])!=tile['rows']*tile['columns']:raise ValueError('tile length differs')
        for r in range(tile['rows']):
            for c in range(tile['columns']):
                index=(tile['row']+r)*columns+tile['column']+c
                if not 0<=index<len(values) or values[index] is not None:raise ValueError('tile overlap/bounds')
                values[index]=output['words'][r*tile['columns']+c]
    if any(v is None for v in values):raise ValueError('tile gap')
    return values
