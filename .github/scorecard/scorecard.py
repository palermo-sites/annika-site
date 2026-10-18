#!/usr/bin/env python3
"""Daily delivery facts of this website system (website-platform-kit decision 0006: the site is the system and
carries its scorecard; daily granularity; America/New_York calendar days).

Harvest this repository with cmis (GitHub only), read every timestamped event behind the scorecard's cells
(`cmis connections score-drill`: items started, items delivered, forward moves, rework) plus this repository's
GitHub Actions runs (deployments: deploy.yml on main = prod, staging.yml on pull requests = UAT), and bucket them
by calendar day in America/New_York. Writes into --data (a worktree of the scorecard-data branch):

  days/YYYY-MM-DD.json  one per finished day: additive raw counts, delivery-duration list and sum, item and move
                        events with timestamps, deployments per environment with outcome. Written once (--force
                        rewrites and keeps the previous counts in history).
  daily.json            compact index of every finished day (counts, and `hours`: per America/New_York hour with
                        activity or a change of work in process; quiet hours are omitted) plus today so far.
  latest.json           today so far (provisional), the last finished day, and the named views.

Any grouping is computed from the additive facts: sums of counts, MTTD = sum of durations / number delivered,
work in process = the last day's end-of-day value, failed share = failed / deployments. No timestamps in committed
files except the immutable meta block of a day file; a rerun with the same inputs changes nothing.
"""
import argparse, datetime as dt, hashlib, json, os, subprocess, sys, urllib.request, urllib.error
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent))
import views  # noqa: E402

SCHEMA_VERSION = 2
TZ_NAME = 'America/New_York'
TZ = ZoneInfo(TZ_NAME)
UTC = dt.timezone.utc
DEFAULT_WORKFLOWS = 'staging.yml!pull_request:uat,deploy.yml@main:prod'
DEFAULT_ENVIRONMENTS = 'uat:UAT,prod:Delivered'
METRICS = {'itemsstarted': 'started', 'itemsdelivered': 'delivered', 'progress': 'forward', 'rework': 'rework'}
STOP_STATUSES = {'Backlog', 'Created', 'New', 'To Do'}


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


def cmis(args, env, base):
    out = subprocess.run(base + args, capture_output=True, text=True, env=env)
    try:
        doc = json.loads(out.stdout)
    except json.JSONDecodeError:
        sys.exit(f'cmis {args[0:2]} failed: {out.stdout[-2000:]} {out.stderr[-2000:]}')
    if not doc.get('ok'):
        sys.exit(f'cmis {args[0:2]} failed: {json.dumps(doc.get("error"))}')
    return doc['data']


def parse_ts(s):
    return dt.datetime.fromisoformat(s.replace('Z', '+00:00')).astimezone(UTC)


def zulu(t):
    return t.astimezone(UTC).strftime('%Y-%m-%dT%H:%M:%SZ')


def day_of(t):
    return t.astimezone(TZ).date()


def day_bounds(d):
    start = dt.datetime.combine(d, dt.time(), TZ)
    end = dt.datetime.combine(d + dt.timedelta(days=1), dt.time(), TZ)
    return start, end


def months(lo, hi):
    m = dt.date(lo.year, lo.month, 1)
    while m <= hi:
        nxt = dt.date(m.year + (m.month == 12), m.month % 12 + 1, 1)
        yield m, nxt - dt.timedelta(days=1)
        m = nxt


def runs(repo, workflow, token, since, until):
    """Completed runs of one workflow entry (file[@branch][!event]) created on UTC dates since..until."""
    file, branch, event = workflow, None, None
    if '!' in file:
        file, event = file.split('!', 1)
    if '@' in file:
        file, branch = file.split('@', 1)
    out, page = [], 1
    while True:
        q = f'repos/{repo}/actions/workflows/{file}/runs?status=completed&per_page=100&page={page}&created={since:%Y-%m-%d}..{until:%Y-%m-%d}'
        q += f'&branch={branch}' if branch else ''
        q += f'&event={event}' if event else ''
        items = (gh(q, token) or {}).get('workflow_runs', [])
        out += [r for r in items if r['conclusion'] not in ('skipped', 'cancelled', 'neutral', 'stale', None)]
        if len(items) < 100:
            return out
        page += 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--data', required=True, help='worktree of the scorecard-data branch')
    ap.add_argument('--config', default=str(Path(__file__).resolve().parent / 'config.json'))
    ap.add_argument('--days', default='', help='YYYY-MM-DD or YYYY-MM-DD..YYYY-MM-DD; default: every missing finished day')
    ap.add_argument('--force', action='store_true')
    ap.add_argument('--now', default='', help='for tests: the instant taken as now (ISO 8601)')
    a = ap.parse_args()
    token = os.environ['GH_TOKEN']
    repo = os.environ['GITHUB_REPOSITORY']
    owner, name = repo.split('/')
    work = Path(os.environ.get('CMIS_WORK', '/tmp/cmis-work'))
    base = os.environ.get('CMIS', 'cmis').split() + ['--workspace', str(work / 'ws'), '--store', str(work / 'store'), '--json']
    now = parse_ts(a.now) if a.now else dt.datetime.now(UTC)
    today = day_of(now)
    cfg = json.loads(Path(a.config).read_text())
    slug = cfg['slug']
    meta = gh(f'repos/{repo}', token)
    first = dt.date.fromisoformat(cfg['since']) if cfg.get('since') else day_of(parse_ts(meta['created_at']))
    workflows = cfg.get('actionsWorkflows', DEFAULT_WORKFLOWS)
    environments = cfg.get('environments', DEFAULT_ENVIRONMENTS)
    cmis_version = os.environ.get('CMIS_VERSION', 'unknown')
    config_hash = 'sha256:' + hashlib.sha256(f'{repo}|{workflows}|{environments}|{TZ_NAME}'.encode()).hexdigest()[:16]
    root = Path(a.data)
    folder = root / 'days'
    folder.mkdir(parents=True, exist_ok=True)

    env = dict(os.environ, **{f'CMIS_{slug.upper().replace("-", "_")}_TOKEN': token})
    conn = slug
    subprocess.run(base[:-1] + ['connections', 'add', '--id', conn, '--tracker', 'GitHubDelivery', '--coordinate', f'owner={owner}',
                                '--coordinate', f'repo={name}', '--coordinate', f'actionsWorkflows={workflows}',
                                '--coordinate', f'environments={environments}', '--replace', '--yes'], capture_output=True, text=True, env=env)
    lo_utc, hi_utc = first - dt.timedelta(days=1), today + dt.timedelta(days=1)
    h = cmis(['connections', 'harvest', '--connection', conn, '--since', f'{lo_utc:%Y-%m-%d}', '--until', f'{hi_utc:%Y-%m-%d}',
              '--on-failure', 'strict'], env, base)
    print(f'{repo}: harvested {h["totalRawRevisions"]} revisions with {h["apiRequestCount"]} requests')

    # Every timestamped event behind the scorecard's cells, month by month (UTC windows; bucketed by ET day below).
    events, seen = [], set()
    for m_lo, m_hi in months(lo_utc, hi_utc):
        for metric, kind in METRICS.items():
            d = cmis(['connections', 'score-drill', '--connection', conn, '--period', 'month', '--since', f'{m_lo:%Y-%m-%d}',
                      '--until', f'{m_hi:%Y-%m-%d}', '--period-label', f'{m_lo:%Y-%m}', '--metric', metric], env, base)
            for it in d.get('items', []):
                key = (kind, it['url'], it.get('oldStatus'), it.get('newStatus'), it['revisionDate'])
                if key in seen:
                    continue
                seen.add(key)
                events.append({'kind': kind, 'id': it['url'].rsplit('/', 1)[-1], 'url': it['url'], 'title': it.get('title', ''),
                               'type': it.get('sourceWorkItemType', ''), 'from': it.get('oldStatus') or None,
                               'to': it.get('newStatus') or None, 'at': parse_ts(it['revisionDate'])})
    started_at, delivered_at = {}, {}
    for e in sorted(events, key=lambda e: e['at']):
        if e['kind'] == 'started':
            started_at.setdefault(e['url'], e['at'])
        if e['kind'] == 'delivered':
            delivered_at.setdefault(e['url'], e['at'])

    wf_env = {w.split(':')[0].strip(): w.split(':')[1].strip() for w in workflows.split(',')}
    deploys = []
    for wf, envname in wf_env.items():
        for r in runs(repo, wf, token, lo_utc, hi_utc):
            at = parse_ts(r.get('run_started_at') or r['created_at'])
            deploys.append({'env': envname, 'id': r['id'], 'url': r['html_url'], 'at': at, 'conclusion': r['conclusion'],
                            'sha': r['head_sha'][:7]})

    def facts(d):
        start, end = day_bounds(d)
        inday = lambda t: start <= t < end
        ev = [e for e in events if inday(e['at'])]
        started = sorted((e for e in ev if e['kind'] == 'started'), key=lambda e: (e['at'], e['id']))
        delivered = sorted((e for e in ev if e['kind'] == 'delivered' and delivered_at.get(e['url']) == e['at']), key=lambda e: (e['at'], e['id']))
        moves = sorted((e for e in ev if e['kind'] in ('forward', 'rework')), key=lambda e: (e['at'], e['id'], e['kind']))
        durations = []
        delivered_items = []
        for e in delivered:
            s = started_at.get(e['url'])
            days = None if s is None else round((e['at'] - s).total_seconds() / 86400, 6)
            if days is not None:
                durations.append(days)
            delivered_items.append({'id': e['id'], 'url': e['url'], 'title': e['title'], 'type': e['type'], 'at': zulu(e['at']),
                                    'startedAt': zulu(s) if s else None, 'durationDays': days})
        wip = sum(1 for u, s in started_at.items() if s < end and not (u in delivered_at and delivered_at[u] < end))
        dep = {}
        for envname in sorted(set(wf_env.values())):
            rs = sorted((r for r in deploys if r['env'] == envname and inday(r['at'])), key=lambda r: (r['at'], r['id']))
            dep[envname] = {'count': len(rs), 'failed': sum(1 for r in rs if r['conclusion'] != 'success'),
                            'runs': [{'id': r['id'], 'url': r['url'], 'at': zulu(r['at']), 'conclusion': r['conclusion'], 'sha': r['sha']} for r in rs]}
        hours = []
        t = start
        while t < end:  # UTC steps, so DST days have 23 or 25 hours
            t2 = t + dt.timedelta(hours=1)
            inh = lambda x: t <= x < t2
            hd = [e for e in delivered if inh(e['at'])]
            hdur = [x['durationDays'] for x in delivered_items if x['durationDays'] is not None and inh(parse_ts(x['at']))]
            hmv = [m for m in moves if inh(m['at'])]
            hc = {'itemsStarted': sum(1 for e in started if inh(e['at'])), 'itemsDelivered': len(hd),
                  'forwardMoves': sum(1 for m in hmv if m['kind'] == 'forward'), 'rework': sum(1 for m in hmv if m['kind'] == 'rework'),
                  'itemsStopped': sum(1 for m in hmv if m['kind'] == 'rework' and m['to'] in STOP_STATUSES)}
            hc['netThroughput'] = hc['forwardMoves'] - hc['rework']
            hc['wipEndOfHour'] = sum(1 for u, s0 in started_at.items() if s0 < t2 and not (u in delivered_at and delivered_at[u] < t2))
            hdep = {}
            for envname in sorted(set(wf_env.values())):
                rs = [r for r in deploys if r['env'] == envname and inh(r['at'])]
                if rs:
                    hdep[envname] = {'count': len(rs), 'failed': sum(1 for r in rs if r['conclusion'] != 'success')}
            busy = any(v for k, v in hc.items() if k != 'wipEndOfHour') or hdep
            if busy or not hours or hours[-1]['counts']['wipEndOfHour'] != hc['wipEndOfHour']:
                lt = t.astimezone(TZ)
                hours.append({'hour': lt.isoformat(timespec='minutes'), 'hourOfDay': lt.hour,
                              'label': lt.strftime('%Y-%m-%d %H:00 ') + ('EDT' if lt.dst() else 'EST'),
                              'counts': hc, 'delivery': {'count': len(hdur), 'durationSumDays': round(sum(hdur), 6)}, 'deployments': hdep})
            t = t2
        forward = sum(1 for m in moves if m['kind'] == 'forward')
        rework = sum(1 for m in moves if m['kind'] == 'rework')
        y, w, _ = d.isocalendar()
        return {
            'schemaVersion': SCHEMA_VERSION, 'system': slug, 'date': f'{d:%Y-%m-%d}', 'timeZone': TZ_NAME,
            'start': start.isoformat(), 'end': end.isoformat(), 'isoWeek': f'{y}-W{w:02d}',
            'counts': {'itemsStarted': len(started), 'itemsDelivered': len(delivered), 'forwardMoves': forward, 'rework': rework,
                       'netThroughput': forward - rework,
                       'itemsStopped': sum(1 for m in moves if m['kind'] == 'rework' and m['to'] in STOP_STATUSES),
                       'wipEndOfDay': wip},
            'delivery': {'count': len(durations), 'durationSumDays': round(sum(durations), 6), 'durationsDays': durations},
            'deployments': dep,
            'hours': hours,
            'items': {'started': [{'id': e['id'], 'url': e['url'], 'title': e['title'], 'type': e['type'], 'at': zulu(e['at'])} for e in started],
                      'delivered': delivered_items},
            'moves': [{'id': m['id'], 'kind': m['kind'], 'from': m['from'], 'to': m['to'], 'at': zulu(m['at'])} for m in moves],
            'source': {'repository': repo, 'cmisVersion': cmis_version, 'configHash': config_hash},
            'history': [],
        }

    if a.days:
        lo, _, hi = a.days.partition('..')
        lo_d, hi_d = dt.date.fromisoformat(lo), dt.date.fromisoformat(hi or lo)
        targets = [lo_d + dt.timedelta(days=i) for i in range((hi_d - lo_d).days + 1)]
    else:
        targets = [first + dt.timedelta(days=i) for i in range(max(0, (today - first).days))]
    targets = [d for d in targets if first <= d < today]
    changed = []
    stamp = lambda: zulu(dt.datetime.now(UTC))
    body = lambda doc: json.dumps({k: v for k, v in doc.items() if k not in ('meta', 'history')}, sort_keys=True)
    for d in targets:
        path = folder / f'{d:%Y-%m-%d}.json'
        if path.exists() and not a.force:
            continue
        doc = facts(d)
        if path.exists():
            old = json.loads(path.read_text())
            if body(old) == body(doc):
                continue
            doc['history'] = old.get('history', []) + [{'replacedAt': stamp(), 'reason': 'force', 'counts': old['counts'], 'source': old['source']}]
        doc['meta'] = {'generatedAt': stamp(), 'runUrl': os.environ.get('RUN_URL', '')}
        path.write_text(json.dumps(doc, indent=2, sort_keys=True) + '\n')
        changed.append(f'days/{path.name}')

    days = [json.loads(p.read_text()) for p in sorted(folder.glob('20*-*-*.json'))]
    today_doc = facts(today)
    compact = lambda doc: {k: doc[k] for k in ('date', 'isoWeek', 'counts')} | {
        'delivery': {'count': doc['delivery']['count'], 'durationSumDays': doc['delivery']['durationSumDays']},
        'deployments': {e: {'count': v['count'], 'failed': v['failed']} for e, v in doc['deployments'].items()},
        'hours': doc.get('hours', [])}
    daily = {'schemaVersion': SCHEMA_VERSION, 'system': slug, 'name': cfg['name'], 'repository': repo, 'timeZone': TZ_NAME,
             'days': [compact(x) for x in days], 'today': compact(today_doc)}
    latest = {'schemaVersion': SCHEMA_VERSION, 'system': slug, 'name': cfg['name'], 'repository': repo, 'timeZone': TZ_NAME,
              'today': {k: today_doc[k] for k in ('date', 'isoWeek', 'start', 'end', 'counts', 'delivery', 'deployments')} | {'provisional': True},
              'lastDay': compact(days[-1]) if days else None,
              'views': views.named_views(daily['days'], today), 'report': 'index.html', 'daily': 'daily.json'}
    for fname, obj in (('daily.json', daily), ('latest.json', latest)):
        p = root / fname
        text = json.dumps(obj, indent=2, sort_keys=True) + '\n'
        if not p.exists() or p.read_text() != text:
            p.write_text(text)
            changed.append(fname)
    print('changed:', ', '.join(changed) or 'nothing')


if __name__ == '__main__':
    main()
