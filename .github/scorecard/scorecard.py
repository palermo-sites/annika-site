#!/usr/bin/env python3
"""Weekly delivery scorecard of this website system (the site is the system level of the platform; website-platform-kit
docs/scorecard-pilot.md, decision 0004).

Harvest this repository with cmis (GitHub only; GitHub Actions runs are the deployments: deploy.yml on main is prod,
staging.yml on pull requests is preview), score every finished ISO week (Monday 00:00 UTC to Monday 00:00 UTC) that has
no file yet, and write into --data (a worktree of the scorecard-data branch): weeks/<YYYY>-W<ww>.json, latest.json and
README.md. A week file is written once; --force rewrites it and keeps the previous numbers in its history. latest.json
and README.md hold no timestamp. Run again with the same inputs: nothing changes.
"""
import argparse, datetime as dt, hashlib, json, os, subprocess, sys, urllib.request, urllib.error
from pathlib import Path

SCHEMA_VERSION = 1
DEFAULT_WORKFLOWS = 'staging.yml!pull_request:preview,deploy.yml@main:prod'
DEFAULT_ENVIRONMENTS = 'preview:Preview,prod:Delivered'
UTC = dt.timezone.utc


def gh(path, token):
    req = urllib.request.Request(f'https://api.github.com/{path}', headers={
        'Authorization': f'Bearer {token}', 'Accept': 'application/vnd.github+json', 'X-GitHub-Api-Version': '2022-11-28',
        'User-Agent': 'site-scorecard'})
    try:
        with urllib.request.urlopen(req) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        if e.code in (403, 404):
            return None
        raise


def monday(d):
    return d - dt.timedelta(days=d.weekday())


def iso(d):
    y, w, _ = d.isocalendar()
    return f'{y}-W{w:02d}'


def parse_week(text):
    y, w = text.split('-W')
    return dt.date.fromisocalendar(int(y), int(w), 1)


def cmis(args, env):
    cmd = os.environ.get('CMIS', 'cmis').split() + ['--workspace', str(WORK / 'ws'), '--store', str(WORK / 'store'), '--json'] + args
    out = subprocess.run(cmd, capture_output=True, text=True, env=env)
    try:
        doc = json.loads(out.stdout)
    except json.JSONDecodeError:
        sys.exit(f'cmis {args[0:2]} failed: {out.stdout[-2000:]} {out.stderr[-2000:]}')
    if not doc.get('ok'):
        sys.exit(f'cmis {args[0:2]} failed: {json.dumps(doc.get("error"))}')
    return doc['data']


def runs(repo, workflow, token, since, until):
    """Completed runs of one workflow entry (file[@branch][!event]) created in [since, until)."""
    file, branch, event = workflow, None, None
    if '!' in file:
        file, event = file.split('!', 1)
    if '@' in file:
        file, branch = file.split('@', 1)
    out, page = [], 1
    while True:
        q = f'repos/{repo}/actions/workflows/{file}/runs?status=completed&per_page=100&page={page}&created={since:%Y-%m-%d}..{(until - dt.timedelta(days=1)):%Y-%m-%d}'
        q += f'&branch={branch}' if branch else ''
        q += f'&event={event}' if event else ''
        doc = gh(q, token)
        items = (doc or {}).get('workflow_runs', [])
        out += [r for r in items if r['conclusion'] not in ('skipped', 'cancelled', 'neutral', 'stale', None)]
        if len(items) < 100:
            return out
        page += 1


def week_doc(slug, system, repo, start, score, deployments, items_delivered):
    end = start + dt.timedelta(days=7)
    p = score['periods'][0] if score['periods'] else {}
    mttd_weeks = p.get('meanTimeToDelivery')
    return {
        'schemaVersion': SCHEMA_VERSION,
        'system': slug,
        'week': iso(start),
        'start': f'{start:%Y-%m-%d}T00:00:00Z',
        'end': f'{end:%Y-%m-%d}T00:00:00Z',
        'metrics': {
            'itemsStarted': p.get('itemsStarted', 0),
            'itemsDelivered': p.get('itemsDelivered', 0),
            'wip': p.get('workInProcess', 0),
            'mttdDays': None if mttd_weeks is None else round(mttd_weeks * 7, 3),
            'progress': p.get('throughput', 0),
            'rework': p.get('rework', 0),
            'netThroughput': p.get('netThroughput', 0),
            'itemsStopped': p.get('itemsStopped', 0),
            'deployments': deployments,
        },
        'coverage': {'issuesAndPullRequests': 'ok', 'deployments': 'ok' if (dt.date.today() - start).days < 85 else 'partial'},
        'source': {'repositories': [repo], 'cmisVersion': CMIS_VERSION, 'configHash': CONFIG_HASH},
        'history': [],
    }


def body(doc):
    return json.dumps({k: v for k, v in doc.items() if k not in ('meta', 'history')}, sort_keys=True)


def rolling(weeks):
    last = weeks[-12:]
    m = [w['metrics'] for w in last]
    mttds = [x['mttdDays'] for x in m if x['mttdDays'] is not None]
    prod = [x['deployments'].get('prod', {}) for x in m]
    count = sum(p.get('count', 0) for p in prod)
    failed = sum(p.get('failed', 0) for p in prod)
    return {
        'weeks': len(last), 'from': last[0]['week'] if last else None, 'to': last[-1]['week'] if last else None,
        'itemsStarted': sum(x['itemsStarted'] for x in m), 'itemsDelivered': sum(x['itemsDelivered'] for x in m),
        'wip': m[-1]['wip'] if m else 0,
        'mttdDays': round(sum(mttds) / len(mttds), 3) if mttds else None,
        'prodDeployments': count, 'prodFailed': failed, 'prodFailedShare': round(failed / count, 3) if count else None,
    }


def fmt(v, unit=''):
    return '–' if v is None else (f'{v:.3f}{unit}' if isinstance(v, float) else f'{v}{unit}')


def report(slug, system, weeks, provisional):
    cols = weeks[-12:]
    lines = [f'# Scorecard: {system["name"]} (`{slug}`)', '',
             'Weekly delivery numbers (ISO weeks, Monday 00:00 UTC). Written by `.github/scorecard/scorecard.py` on the default branch; do not edit. HTML: `index.html`.', '']
    def row(label, f):
        cells = [f(w) for w in cols] + ([f(provisional)] if provisional else [])
        return f'| {label} | ' + ' | '.join(cells) + ' |'
    head = [w['week'] for w in cols] + ([provisional['week'] + ' (so far)'] if provisional else [])
    if not head:
        lines.append('No finished week yet.')
    else:
        lines += ['| Metric | ' + ' | '.join(head) + ' |', '|---|' + '---|' * len(head),
                  row('Items started', lambda w: fmt(w['metrics']['itemsStarted'])),
                  row('Items delivered', lambda w: fmt(w['metrics']['itemsDelivered'])),
                  row('Work in process', lambda w: fmt(w['metrics']['wip'])),
                  row('Mean time to delivery (days)', lambda w: fmt(w['metrics']['mttdDays'])),
                  row('Progress / rework', lambda w: f"{w['metrics']['progress']} / {w['metrics']['rework']}"),
                  row('Prod deployments (failed)', lambda w: f"{w['metrics']['deployments'].get('prod', {}).get('count', 0)} ({w['metrics']['deployments'].get('prod', {}).get('failed', 0)})"),
                  row('Preview deployments (failed)', lambda w: f"{w['metrics']['deployments'].get('preview', {}).get('count', 0)} ({w['metrics']['deployments'].get('preview', {}).get('failed', 0)})")]
    r = rolling(weeks)
    lines += ['', f'## Rolling 12 ({r["weeks"]} finished week(s){", " + r["from"] + " to " + r["to"] if r["from"] else ""})', '',
              f'- Items started: {r["itemsStarted"]}, delivered: {r["itemsDelivered"]}, work in process: {r["wip"]}',
              f'- Mean time to delivery: {fmt(r["mttdDays"], " days")} (mean of weekly means)',
              f'- Prod deployments: {r["prodDeployments"]}, failed: {r["prodFailed"]}, failed share: {fmt(r["prodFailedShare"])}', '']
    return '\n'.join(lines)


def main():
    global WORK, CMIS_VERSION, CONFIG_HASH
    ap = argparse.ArgumentParser()
    ap.add_argument('--data', required=True, help='worktree of the scorecard-data branch')
    ap.add_argument('--config', default=str(Path(__file__).resolve().parent / 'config.json'))
    ap.add_argument('--weeks', default='', help='YYYY-Www or YYYY-Www..YYYY-Www; default: every missing finished week')
    ap.add_argument('--force', action='store_true')
    ap.add_argument('--today', default='', help='for tests: the date taken as today (UTC)')
    a = ap.parse_args()
    token = os.environ['GH_TOKEN']
    repo = os.environ['GITHUB_REPOSITORY']
    owner, name = repo.split('/')
    WORK = Path(os.environ.get('CMIS_WORK', '/tmp/cmis-work'))
    today = dt.date.fromisoformat(a.today) if a.today else dt.datetime.now(UTC).date()
    current = monday(today)
    CMIS_VERSION = os.environ.get('CMIS_VERSION', 'unknown')
    s = json.loads(Path(a.config).read_text())
    slug = s['slug']
    root = Path(a.data)
    changed = []
    meta = gh(f'repos/{repo}', token)
    created = dt.datetime.fromisoformat(meta['created_at'].replace('Z', '+00:00')).date() if meta else today
    first = monday(dt.date.fromisoformat(s['since'])) if s.get('since') else monday(created)
    workflows = s.get('actionsWorkflows', DEFAULT_WORKFLOWS)
    environments = s.get('environments', DEFAULT_ENVIRONMENTS)
    CONFIG_HASH = 'sha256:' + hashlib.sha256(f'{repo}|{workflows}|{environments}'.encode()).hexdigest()[:16]
    folder = root / 'weeks'
    folder.mkdir(parents=True, exist_ok=True)
    if a.weeks:
        lo, _, hi = a.weeks.partition('..')
        lo_d, hi_d = parse_week(lo), parse_week(hi or lo)
        targets = [lo_d + dt.timedelta(weeks=i) for i in range((hi_d - lo_d).days // 7 + 1)]
    else:
        targets = [first + dt.timedelta(weeks=i) for i in range(max(0, (current - first).days // 7))]
    targets = [w for w in targets if first <= w < current]
    todo = [w for w in targets if a.force or not (folder / f'{iso(w)}.json').exists()]
    env = dict(os.environ, **{f'CMIS_{slug.upper().replace("-", "_")}_TOKEN': token})
    conn = slug
    # (re)declare the connection every run: the configuration is code, not state
    subprocess.run(os.environ.get('CMIS', 'cmis').split() + ['--workspace', str(WORK / 'ws'), '--store', str(WORK / 'store'), 'connections', 'add',
                    '--id', conn, '--tracker', 'GitHubDelivery', '--coordinate', f'owner={owner}', '--coordinate', f'repo={name}',
                    '--coordinate', f'actionsWorkflows={workflows}', '--coordinate', f'environments={environments}', '--replace', '--yes'],
                   capture_output=True, text=True, env=env)
    h = cmis(['connections', 'harvest', '--connection', conn, '--since', f'{min(todo + [first]):%Y-%m-%d}',
              '--until', f'{(current + dt.timedelta(days=6)):%Y-%m-%d}', '--on-failure', 'strict'], env)
    print(f'{repo}: harvested {h["totalRawRevisions"]} revisions with {h["apiRequestCount"]} requests')
    wf_env = {e.split(':')[0].strip(): e.split(':')[1].strip() for e in workflows.split(',')}

    def week(start):
        end = start + dt.timedelta(days=7)
        score = cmis(['connections', 'score', '--connection', conn, '--period', 'week', '--since', f'{start:%Y-%m-%d}',
                      '--until', f'{(end - dt.timedelta(days=1)):%Y-%m-%d}'], env)
        deployments = {}
        for wf, e in wf_env.items():
            rs = runs(repo, wf, token, start, end)
            d = deployments.setdefault(e, {'count': 0, 'failed': 0})
            d['count'] += len(rs)
            d['failed'] += sum(1 for r in rs if r['conclusion'] != 'success')
        for d in deployments.values():
            d['failedShare'] = round(d['failed'] / d['count'], 3) if d['count'] else None
        return week_doc(slug, s, repo, start, score, deployments, None)

    now = lambda: dt.datetime.now(UTC).strftime('%Y-%m-%dT%H:%M:%SZ')
    for w in todo:
        doc = week(w)
        path = folder / f'{iso(w)}.json'
        if path.exists():
            old = json.loads(path.read_text())
            if body(old) == body(doc):
                continue
            doc['history'] = old.get('history', []) + [{'replacedAt': now(), 'reason': 'force', 'metrics': old['metrics'], 'source': old['source']}]
        doc['meta'] = {'generatedAt': now(), 'runUrl': os.environ.get('RUN_URL', '')}
        path.write_text(json.dumps(doc, indent=2, sort_keys=True) + '\n')
        changed.append(f'weeks/{path.name}')
    weeks = [json.loads(p.read_text()) for p in sorted(folder.glob('20*-W*.json'))]
    provisional = week(current)
    provisional['provisional'] = True
    latest = {'schemaVersion': SCHEMA_VERSION, 'system': slug, 'name': s['name'], 'repository': repo,
              'lastWeek': weeks[-1] if weeks else None, 'rolling12': rolling(weeks),
              'currentWeek': {k: provisional[k] for k in ('week', 'start', 'end', 'metrics')},
              'report': 'index.html'}
    for fname, text in (('latest.json', json.dumps(latest, indent=2, sort_keys=True) + '\n'),
                        ('README.md', report(slug, s, weeks, provisional) + '\n')):
        p = root / fname
        if not p.exists() or p.read_text() != text:
            p.write_text(text)
            changed.append(fname)
    print('changed:', ', '.join(changed) or 'nothing')


if __name__ == '__main__':
    main()
