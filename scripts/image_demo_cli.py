#!/usr/bin/env python3
"""Prepare an owned image workload, or display a verified saved image result."""
import argparse
import json
from pathlib import Path
import sys
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root))
if (root/'app/engine').is_dir():sys.path.insert(0,str(root/'app/engine'))
from raveil import project as p,project_array as a
from scripts.image_demo import source,read_pgm,reference
from scripts.image_demo_report import pixels


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);commands=parser.add_subparsers(dest='command',required=True)
    prepare=commands.add_parser('prepare');prepare.add_argument('--image',type=Path,required=True);prepare.add_argument('--output',type=Path,required=True)
    view=commands.add_parser('view');view.add_argument('--project',type=Path,required=True);view.add_argument('--id',required=True);view.add_argument('--output',type=Path,required=True)
    args=parser.parse_args(argv)
    try:
        if args.command=='prepare':
            if args.image.stat().st_size>8192:raise ValueError('PGM too large')
            image=read_pgm(args.image.read_bytes());value=source(image)
            with args.output.open('xb') as handle:handle.write(p.encoded(value))
        else:
            project=p.Project(args.project);record=a.load(project,args.id)
            if record['status']!='succeeded':raise ValueError('result is incomplete')
            value=json.loads((project.root/'arrays'/record['id']/'source.json').read_bytes())
            operand=value['stages'][0]['source']['inputs'][0];w=operand['columns'];h=operand['rows']
            image=[operand['words'][r*w:(r+1)*w] for r in range(h)]
            if value!=source(image,value['schema']=='raveil.array-program/v2') or record['outputs']!=reference(image):
                raise ValueError('saved program is not the specified image pipeline')
            figures=[('入力',image)]
            for output in record['outputs']:
                if output['name']=='gradient':continue
                figures.append((output['name'],[output['words'][r*output['columns']:(r+1)*output['columns']] for r in range(output['rows'])]))
            page='<!doctype html><meta charset="utf-8"><title>Raveil image result</title><style>body{font-family:system-ui;max-width:960px;margin:40px auto}section{display:flex;gap:24px}figure{flex:1;margin:0}svg{width:100%;image-rendering:pixelated}</style><h1>検証済みの画像処理結果</h1><p>保存済みQEMU／RTL出力。新しい実行は行っていません。</p><section>'
            page+=''.join('<figure>'+pixels(matrix)+'<figcaption>'+name+'</figcaption></figure>' for name,matrix in figures)+'</section>'
            with args.output.open('x') as handle:handle.write(page)
        print(str(args.output));return 0
    except (OSError,ValueError,KeyError,IndexError) as error:parser.exit(2,str(error)+'\n')


if __name__=='__main__':raise SystemExit(main())
