"""Standalone visible measured-output report; no network, server or dependencies."""
import html
import json
from pathlib import Path


def pixels(matrix):
    h=len(matrix);w=len(matrix[0])
    rectangles=''.join(f'<rect x="{c}" y="{r}" width="1" height="1" fill="rgb({v},{v},{v})"/>'
                       for r,row in enumerate(matrix) for c,v in enumerate(row))
    return f'<svg role="img" aria-label="integer image" viewBox="0 0 {w} {h}" shape-rendering="crispEdges">{rectangles}</svg>'


def write(root, summary, images):
    root=Path(root);sections=[]
    for case in summary['cases']:
        name=case['name'];output=case['outputs'];figures=[('入力',images[name])]
        for item in output:
            if item['name']=='gradient':continue
            figures.append(({'activated':'輪郭抽出＋活性化','pooled':'2×2縮小'}[item['name']],
                            [item['words'][r*item['columns']:(r+1)*item['columns']] for r in range(item['rows'])]))
        cells=''.join('<figure>'+pixels(matrix)+'<figcaption>'+label+'</figcaption></figure>' for label,matrix in figures)
        rows=''
        for label,key in [('RTL動作サイクル合計','rtl_active_cycles'),('RTL読み取り','reads'),('RTL書き込み','writes'),('QEMUセッション','sessions'),('ホスト全体時間・中央値（秒）','median_wall_seconds')]:
            values=[case[v][key] for v in ('scalar','fused')]
            rows+=f'<tr><th>{label}</th><td>{values[0]:,.3f}</td><td>{values[1]:,.3f}</td></tr>'
        sections.append(f'<section><h2>{html.escape(name)}</h2><div class="images">{cells}</div><table><tr><th>測定項目</th><th>融合なし</th><th>融合あり</th></tr>{rows}</table><p>CPU C -O3 計算のみ：{case["cpu_median_ns"]:,.0f} ns/画像。上のホスト全体時間とは測定範囲が異なります。</p></section>')
    data=json.dumps(summary,ensure_ascii=False).replace('<','\\u003c')
    page='''<!doctype html><html lang="ja"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Raveil 画像処理実験</title><style>
body{font:16px/1.65 system-ui,sans-serif;margin:auto;max-width:1040px;padding:32px;background:#f4f6f9;color:#192334}h1{font-size:30px}section{background:white;padding:24px;margin:24px 0;border-radius:12px}.images{display:flex;gap:20px;flex-wrap:wrap}figure{margin:0;flex:1;min-width:150px}svg{width:100%;max-width:260px;background:#111}table{border-collapse:collapse;width:100%;margin-top:24px}th,td{text-align:right;border-bottom:1px solid #ddd;padding:8px}th:first-child{text-align:left}.verdict{font-weight:bold;font-size:20px}details{margin-top:24px}pre{white-space:pre-wrap;overflow-wrap:anywhere}</style>
<h1>Raveil：画像を処理して、融合の効果を測る</h1><p>横方向の差分フィルタ → 正の値だけを残す → 2×2最大値で縮小。表示画像は検証済みの実際のQEMU／RTL出力です。</p>'''
    page+='<p class="verdict">'+html.escape(summary['disposition'])+'</p>'
    page+=''.join(sections)
    page+='''<p>サイクルは同一RTL・同じ合成メモリ待ちポリシー下のシミュレーション値です。各ジョブの開始後から最終書き込み応答までを合計し、起動・ホスト処理・ジョブ間の時間を含みません。読み書きはRTLの32bitメモリポートの転送で、DRAM帯域やシステム全体の転送ではありません。ホスト全体時間はCLI起動から証跡検証・終了までを含みます。実チップ性能・Groq優位性・新規性は示しません。</p><details><summary>測定データ</summary><pre id="data"></pre></details>'''
    page+='<script type="application/json" id="result">'+data+'</script><script>document.getElementById("data").textContent=JSON.stringify(JSON.parse(document.getElementById("result").textContent),null,2)</script></html>'
    (root/'report.html').write_text(page)
