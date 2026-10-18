#!/usr/bin/env python3
"""HTML scorecard report of this website system: index.html in the scorecard-data worktree (--data), from weeks/ and latest.json.

Self-contained (inline CSS, no external assets). Committed files carry no timestamp, so they change only when a number
changes; with --out DIR --stamp, a copy with the generation time (America/New_York) and run link is written to DIR
for the workflow artifact. Also prints a Markdown summary for GITHUB_STEP_SUMMARY with --summary FILE.
"""
import argparse, datetime as dt, html, json, os
from pathlib import Path
from zoneinfo import ZoneInfo

ET = ZoneInfo('America/New_York')
CSS = """
:root{--ink:#1f2933;--muted:#6b7785;--line:#e3e8ee;--bg:#f7f9fb;--card:#fff;--accent:#2457a6;--bad:#b42318;--good:#1a7f37;--soft:#eef3fb}
*{box-sizing:border-box}body{margin:0;font:14px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;color:var(--ink);background:var(--bg)}
header{background:#14213d;color:#fff;padding:24px 32px}header h1{margin:0;font-size:22px;font-weight:600}header p{margin:4px 0 0;color:#c9d3e3}
main{padding:24px 32px;max-width:1400px}a{color:var(--accent)}.muted{color:var(--muted)}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;margin:0 0 24px}
.card{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:14px 16px}.card .k{font-size:12px;color:var(--muted);text-transform:uppercase;letter-spacing:.04em}.card .v{font-size:24px;font-weight:600;margin-top:2px}
.tablewrap{overflow-x:auto;background:var(--card);border:1px solid var(--line);border-radius:8px}
table{border-collapse:collapse;width:100%;font-variant-numeric:tabular-nums}th,td{padding:8px 12px;border-bottom:1px solid var(--line);text-align:right;white-space:nowrap}
th:first-child,td:first-child{text-align:left;position:sticky;left:0;background:var(--card)}thead th{background:#f1f4f8;font-weight:600;font-size:12px}
thead th.sofar{background:#fff7e0}td.sofar{background:#fffcf2}tr.group td{background:var(--soft);font-weight:600;color:#14213d;text-align:left}
td.r12,th.r12{background:#f4f7fb;border-left:2px solid var(--line)}.bad{color:var(--bad);font-weight:600}.zero{color:#a5b0bc}
.tag{display:inline-block;font-size:11px;padding:1px 6px;border-radius:10px;background:#fde9a8;color:#7a5b00;margin-left:4px}
footer{padding:16px 32px 32px;color:var(--muted);font-size:12px}
"""


def esc(v):
    return html.escape(str(v))


def num(v, digits=0):
    if v is None:
        return '<span class="zero">–</span>'
    if isinstance(v, (int, float)) and v == 0:
        return '<span class="zero">0</span>'
    return f'{v:.{digits}f}' if isinstance(v, float) or digits else str(v)


def pct(v):
    return '<span class="zero">–</span>' if v is None else (f'<span class="bad">{v*100:.0f}%</span>' if v > 0 else '<span class="zero">0%</span>')


def load(root):
    weeks = [json.loads(p.read_text()) for p in sorted((root / 'weeks').glob('20*-W*.json'))]
    latest = json.loads((root / 'latest.json').read_text()) if (root / 'latest.json').exists() else None
    return weeks, latest


def page(title, subtitle, body, stamp, run_url):
    foot = 'Generated ' + (f'{stamp} ET' if stamp else 'by the scorecard workflow') + (f' · <a href="{esc(run_url)}">workflow run</a>' if run_url else '')
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title><style>{CSS}</style></head>
<body><header><h1>{esc(title)}</h1><p>{subtitle}</p></header><main>{body}</main>
<footer>{foot} · ISO weeks, Monday 00:00 UTC · No Azure or Octopus Deploy: data from GitHub only (cmis + GitHub Actions)</footer></body></html>
"""


def system_report(slug, weeks, latest, stamp, run_url):
    recent = list(reversed(weeks[-12:]))
    cols = ([dict(latest['currentWeek'], provisional=True)] if latest and latest.get('currentWeek') else []) + recent
    r12 = (latest or {}).get('rolling12') or {}
    envs = []
    for w in cols:
        for e in w['metrics'].get('deployments', {}):
            if e not in envs:
                envs.append(e)
    envs.sort(key=lambda e: (e != 'prod', e))

    def head(w):
        cls = ' class="sofar"' if w.get('provisional') else ''
        start = dt.date.fromisoformat(w['start'][:10])
        tag = '<span class="tag">so far</span>' if w.get('provisional') else ''
        return f'<th{cls}>{esc(w["week"])}{tag}<br><span class="muted">{start:%b %d}</span></th>'

    def row(label, f, r12v='', hint=''):
        sofar = ' class="sofar"'
        cells = ''.join('<td' + (sofar if w.get('provisional') else '') + '>' + f(w['metrics']) + '</td>' for w in cols)
        note = ' <span class="muted">' + esc(hint) + '</span>' if hint else ''
        return f'<tr><td>{esc(label)}{note}</td>{cells}<td class="r12">{r12v}</td></tr>'

    def group(label):
        return f'<tr class="group"><td colspan="{len(cols) + 2}">{esc(label)}</td></tr>'

    m = lambda k, d=0: (lambda x: num(x.get(k), d))
    rows = [group('Flow'),
            row('Items started', m('itemsStarted'), num(r12.get('itemsStarted'))),
            row('Items delivered', m('itemsDelivered'), num(r12.get('itemsDelivered'))),
            row('Work in process', m('wip'), num(r12.get('wip')), 'end of week'),
            row('Mean time to delivery', lambda x: num(x.get('mttdDays'), 3), num(r12.get('mttdDays'), 3), 'days'),
            row('Forward moves', m('progress'), num(sum(w['metrics'].get('progress', 0) for w in weeks[-12:]))),
            row('Rework', m('rework'), num(sum(w['metrics'].get('rework', 0) for w in weeks[-12:]))),
            row('Net throughput', m('netThroughput'), num(sum(w['metrics'].get('netThroughput', 0) for w in weeks[-12:])))]
    for e in envs:
        total = sum(w['metrics'].get('deployments', {}).get(e, {}).get('count', 0) for w in weeks[-12:])
        failed = sum(w['metrics'].get('deployments', {}).get(e, {}).get('failed', 0) for w in weeks[-12:])
        d = lambda x, k: x.get('deployments', {}).get(e, {}).get(k)
        rows += [group(f'Deployments: {e}'),
                 row('Deployments', lambda x: num(d(x, 'count') or 0), num(total)),
                 row('Failed', lambda x: (f'<span class="bad">{d(x, "failed")}</span>' if d(x, 'failed') else num(0)), num(failed)),
                 row('Failed share', lambda x: pct(d(x, 'failedShare')), pct(failed / total if total else None))]
    rows += [group('Waste'),
             row('Items stopped', m('itemsStopped'), num(sum(w['metrics'].get('itemsStopped', 0) for w in weeks[-12:])), 'taken off the plate without delivery')]
    links = ''.join(f'<li>{esc(w["week"])}: <a href="{esc(w.get("meta", {}).get("runUrl"))}">run</a></li>' for w in recent if w.get('meta', {}).get('runUrl'))
    last = (latest or {}).get('lastWeek')
    cards = [('Last finished week', last['week'] if last else '–'), ('Delivered (Rolling 12)', r12.get('itemsDelivered', 0)),
             ('MTTD days (Rolling 12)', '–' if r12.get('mttdDays') is None else f'{r12["mttdDays"]:.3f}'),
             ('Prod deploys (Rolling 12)', r12.get('prodDeployments', 0)),
             ('Prod failed share', '–' if r12.get('prodFailedShare') is None else f'{r12["prodFailedShare"]*100:.0f}%')]
    body = '<div class="cards">' + ''.join(f'<div class="card"><div class="k">{esc(k)}</div><div class="v">{esc(v)}</div></div>' for k, v in cards) + '</div>'
    body += ('<div class="tablewrap"><table><thead><tr><th>Metric</th>' + ''.join(head(w) for w in cols)
             + f'<th class="r12">Rolling 12<br><span class="muted">{r12.get("weeks", 0)} finished wk</span></th></tr></thead><tbody>'
             + ''.join(rows) + '</tbody></table></div>')
    body += ('<p class="muted">Newest week first. "So far" is the current week, provisional until it closes. Rolling 12 covers finished weeks only: '
             'sums for counts, the last week for work in process, the mean of weekly means for MTTD.</p>')
    if links:
        body += f'<h3>Source runs</h3><ul>{links}</ul>'
    repo = (latest or {}).get('repository', '')
    sub = f'<a style="color:#c9d3e3" href="https://github.com/{esc(repo)}">{esc(repo)}</a> · delivery scorecard'
    return page(f'Scorecard: {(latest or {}).get("name", slug)}', sub, body, stamp, run_url)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--data', required=True)
    ap.add_argument('--out', default='')
    ap.add_argument('--summary', default='')
    ap.add_argument('--artifact-url', default='')
    a = ap.parse_args()
    root = Path(a.data)
    run_url = os.environ.get('RUN_URL', '')
    stamp = dt.datetime.now(ET).strftime('%Y-%m-%d %H:%M')
    weeks, latest = load(root)
    slug = (latest or {}).get('system', 'site')
    changed = []
    for target, s, u in [(root / 'index.html', None, '')] + ([(Path(a.out) / 'index.html', stamp, run_url)] if a.out else []):
        text = system_report(slug, weeks, latest, s, u)
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists() or target.read_text() != text:
            target.write_text(text)
            changed.append(str(target))
    if a.summary:
        cw = (latest or {}).get('currentWeek') or {}
        mm = cw.get('metrics') or {}
        dep = mm.get('deployments', {})
        r12 = (latest or {}).get('rolling12') or {}
        lw = (latest or {}).get('lastWeek')
        lm = (lw or {}).get('metrics') or {}
        lines = [f'## Delivery scorecard: {(latest or {}).get("name", slug)}', '',
                 '| | Week | Started | Delivered | WIP | MTTD days | Prod deploys (failed) | Preview deploys (failed) |', '|---|---|---|---|---|---|---|---|']
        def line(label, wk, m):
            d = m.get('deployments', {})
            return (f'| {label} | {wk} | {m.get("itemsStarted", "–")} | {m.get("itemsDelivered", "–")} | {m.get("wip", "–")} | {"–" if m.get("mttdDays") is None else m["mttdDays"]} | '
                    f'{d.get("prod", {}).get("count", 0)} ({d.get("prod", {}).get("failed", 0)}) | {d.get("preview", {}).get("count", 0)} ({d.get("preview", {}).get("failed", 0)}) |')
        lines.append(line('So far', cw.get('week', '–'), mm))
        lines.append(line('Last finished', lw['week'], lm) if lw else '| Last finished | – | | | | | | |')
        lines.append(f'| Rolling 12 | {r12.get("weeks", 0)} wk | {r12.get("itemsStarted", 0)} | {r12.get("itemsDelivered", 0)} | {r12.get("wip", 0)} | {"–" if r12.get("mttdDays") is None else r12["mttdDays"]} | '
                     f'{r12.get("prodDeployments", 0)} ({r12.get("prodFailed", 0)}) | |')
        lines += ['', 'HTML report: artifact **scorecard-report**' + (f' ([download]({a.artifact_url}))' if a.artifact_url else '')
                  + ', and `index.html` on the `scorecard-data` branch.', '']
        with open(a.summary, 'a') as f:
            f.write('\n'.join(lines))
    print('report changed:', ', '.join(changed) or 'nothing')


if __name__ == '__main__':
    main()
