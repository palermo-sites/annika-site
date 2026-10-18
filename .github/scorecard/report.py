#!/usr/bin/env python3
"""Scorecard report of this website system from its daily facts (--data: worktree of scorecard-data).

Views: today so far, rolling 7/30/90 days, Rolling 12 weeks and months; grouped by week, month and quarter (current
period so far first, newest first); the last 14 days. The same tables go to index.html (styled; committed without a
timestamp), to the artifact copy (--out, stamped in America/New_York with the run link) and to the run's Summary page
(--summary: GitHub renders table, details and b; CSS is stripped there).
"""
import argparse, datetime as dt, html, json, os, sys
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent))
import views  # noqa: E402

ET = ZoneInfo('America/New_York')
CSS = """
body{margin:0;font:14px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;color:#1f2933;background:#f7f9fb}
header{background:#14213d;color:#fff;padding:24px 32px}header h1{margin:0;font-size:22px;font-weight:600}header p{margin:4px 0 0;color:#c9d3e3}header a{color:#c9d3e3}
main{padding:8px 32px 24px;max-width:1500px}h2{font-size:17px;margin:28px 0 10px}a{color:#2457a6}
table{border-collapse:collapse;background:#fff;border:1px solid #e3e8ee;font-variant-numeric:tabular-nums}
th,td{padding:7px 12px;border-bottom:1px solid #e3e8ee;text-align:right;white-space:nowrap}th:first-child,td:first-child{text-align:left}
thead th{background:#f1f4f8;font-size:12px}tbody th{background:#eef3fb;text-align:left;color:#14213d}
thead th:nth-child(2),tbody td:nth-child(2){background:#fffcf2}details{margin:12px 0}p.note{color:#6b7785}
footer{padding:16px 32px 32px;color:#6b7785;font-size:12px}
"""


def esc(v):
    return html.escape(str(v))


def n(v, d=0):
    return '–' if v is None else (f'{v:.{d}f}' if d else str(v))


def pct(v):
    return '–' if v is None else (f'<b>{v * 100:.0f}%</b>' if v > 0 else '0%')


def table(cols, envs):
    """cols: [(header html, aggregate)]. One row per metric, grouped."""
    c = lambda f: ''.join(f'<td align="right">{f(a)}</td>' for _, a in cols)
    g = lambda label: f'<tr><th colspan="{len(cols) + 1}" align="left">{esc(label)}</th></tr>'
    r = lambda label, f: f'<tr><td>{esc(label)}</td>{c(f)}</tr>'
    k = lambda name: (lambda a: n(a['counts'].get(name)))
    rows = [g('Flow'), r('Items started', k('itemsStarted')), r('Items delivered', k('itemsDelivered')),
            r('Work in process (end of period)', k('wipEndOfDay')),
            r('Mean time to delivery (days)', lambda a: n(a['delivery']['mttdDays'], 3)),
            r('Forward moves', k('forwardMoves')), r('Rework', k('rework')), r('Net throughput', k('netThroughput'))]
    for e in envs:
        d = lambda a, f, e=e: a['deployments'].get(e, {}).get(f)
        rows += [g(f'Deployments: {e.upper() if e == "uat" else e}'), r('Deployments', lambda a, d=d: n(d(a, 'count') or 0)),
                 r('Failed', lambda a, d=d: f'<b>{d(a, "failed")}</b>' if d(a, 'failed') else '0'),
                 r('Failed share', lambda a, d=d: pct(d(a, 'failedShare')))]
    rows += [g('Waste'), r('Items stopped (off the plate without delivery)', k('itemsStopped'))]
    head = ''.join(f'<th>{h}</th>' for h, _ in cols)
    return f'<table><thead><tr><th>Metric</th>{head}</tr></thead><tbody>{"".join(rows)}</tbody></table>'


def sections(daily):
    days, today = daily['days'], daily.get('today')
    allx = days + ([today] if today else [])
    envs = views.env_order({e for x in allx for e in x.get('deployments', {})})
    tdate = dt.date.fromisoformat(today['date']) if today else dt.date.today()
    v = views.named_views(days, tdate)
    span = lambda a: f'<br>{esc(a["from"])} – {esc(a["to"])}' if a['from'] else '<br>no finished day'
    out = []
    t = views.aggregate([today], 'Today') if today else views.aggregate([], 'Today')
    out.append(('Rolling views', table([(f'Today so far<br>{esc(tdate)}', t)] +
                                       [(esc(v[k]['label']) + span(v[k]), v[k]) for k in ('rolling7', 'rolling30', 'rolling90')] +
                                       [(f'{esc(v[k]["label"])}<br>{v[k]["periods"]} finished', v[k]) for k in ('rolling12Weeks', 'rolling12Months')], envs)))
    for by, title, keep in (('week', 'By ISO week', 13), ('month', 'By month', 13), ('quarter', 'By quarter', 8)):
        gs = list(reversed(views.group(allx, by)))[:keep]
        cur = views.key(today, by) if today else None
        out.append((title, table([(esc(gv['label']) + (' (so far)' if gv['label'] == cur else '') + f'<br>{gv["days"]} d', gv) for gv in gs], envs)))
    hrs = views.hours(allx, last=48)
    out.append(('By hour (48 hours up to the latest recorded hour, newest first)', table([(esc(h['label'][5:]), views.aggregate([h], h['label'])) for h in reversed(hrs)], envs)))
    prof = views.hour_profile(views.hours(allx))
    out.append(('Hour-of-day profile (all days, America/New_York)', table([(esc(a['label']), a) for a in prof if a['days']], envs)))
    gs = list(reversed(views.group(allx, 'day')))[:14]
    out.append(('By day (last 14)', table([(esc(gv['label']) + (' (so far)' if today and gv['label'] == today['date'] else ''), gv) for gv in gs], envs)))
    return out


NOTE = ('Days are calendar days in America/New_York; weeks are ISO weeks of those days. "So far" is provisional until the day closes; '
        'rolling views end with yesterday. Counts are sums; work in process is the last day\'s end-of-day value; mean time to '
        'delivery is total delivery time / items delivered; failed share is failed / deployments. Deployments are GitHub Actions '
        'runs (deploy.yml on main = prod, staging.yml on pull requests = UAT); no Azure or Octopus Deploy.')


def page(daily, stamp, run_url):
    body = ''.join(f'<h2>{esc(t)}</h2>{h}' for t, h in sections(daily)) + f'<p class="note">{esc(NOTE)}</p>'
    foot = 'Generated ' + (f'{stamp} ET' if stamp else 'by the scorecard workflow') + (f' · <a href="{esc(run_url)}">workflow run</a>' if run_url else '')
    repo = daily.get('repository', '')
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Scorecard: {esc(daily.get('name', ''))}</title><style>{CSS}</style></head>
<body><header><h1>Scorecard: {esc(daily.get('name', ''))}</h1><p><a href="https://github.com/{esc(repo)}">{esc(repo)}</a> · daily delivery facts · data: <code>daily.json</code>, <code>days/</code></p></header>
<main>{body}</main><footer>{foot}</footer></body></html>
"""


def summary(daily, artifact_url):
    secs = sections(daily)
    out = [f'<h2>Delivery scorecard: {esc(daily.get("name", ""))}</h2>', '']
    for i, (t, h) in enumerate(secs):
        if i < 2:
            out += [f'<h3>{esc(t)}</h3>', '', h, '']
        else:
            out += [f'<details><summary><b>{esc(t)}</b></summary>', '', h, '', '</details>', '']
    out += [f'<p>{esc(NOTE)}</p>', '', '<p>Styled HTML: artifact <b>scorecard-report</b>' + (f' (<a href="{esc(artifact_url)}">download</a>)' if artifact_url else '')
            + ', and <code>index.html</code> on the <code>scorecard-data</code> branch.</p>', '']
    return '\n'.join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--data', required=True)
    ap.add_argument('--out', default='')
    ap.add_argument('--summary', default='')
    ap.add_argument('--artifact-url', default='')
    a = ap.parse_args()
    root = Path(a.data)
    daily = json.loads((root / 'daily.json').read_text())
    run_url = os.environ.get('RUN_URL', '')
    stamp = dt.datetime.now(ET).strftime('%Y-%m-%d %H:%M')
    changed = []
    for target, s, u in [(root / 'index.html', None, '')] + ([(Path(a.out) / 'index.html', stamp, run_url)] if a.out else []):
        text = page(daily, s, u)
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists() or target.read_text() != text:
            target.write_text(text)
            changed.append(str(target))
    if a.summary:
        with open(a.summary, 'a') as f:
            f.write(summary(daily, a.artifact_url))
    print('report changed:', ', '.join(changed) or 'nothing')


if __name__ == '__main__':
    main()
