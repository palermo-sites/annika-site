"""Groupings of daily delivery facts (website-platform-kit decision 0006). The dashboard's JavaScript implements the
same rules; keep them in step.

A day is a compact fact record: {date, isoWeek, counts{...}, delivery{count, durationSumDays}, deployments{env: {count,
failed}}}. Aggregation: counts are summed except wipEndOfDay (the last day's value); MTTD = sum of delivery durations /
number of delivered items with a known start (never an average of averages); failed share = failed / deployments.
"""
import datetime as dt

ENV_ALIASES = {'preview': 'uat'}  # the UAT environment was called preview before 2026-10-18; read old facts under the new name


def env_name(e):
    return ENV_ALIASES.get(e, e)


def env_order(envs):
    """UAT before prod, then any other environment alphabetically."""
    rank = {'uat': 0, 'prod': 1}
    return sorted({env_name(e) for e in envs}, key=lambda e: (rank.get(e, 2), e))


ADDITIVE = ('itemsStarted', 'itemsDelivered', 'forwardMoves', 'rework', 'netThroughput', 'itemsStopped')


def hours(days, last=None, now=None):
    """Hour records (oldest first) of the given days, with quiet hours filled in: zero counts, work in process carried
    from the previous hour. A record: {label, hour (ISO, local offset), hourOfDay, counts, delivery, deployments}.
    `last`: keep only the last N hours, ending with the hour of `now` (an aware datetime) when given."""
    import zoneinfo
    tz = zoneinfo.ZoneInfo('America/New_York')
    by = {h['hour']: h for x in days for h in x.get('hours', [])}
    if not days:
        return []
    start = dt.datetime.fromisoformat(days[0]['date'] + 'T00:00').replace(tzinfo=tz).astimezone(dt.timezone.utc)
    end_day = dt.date.fromisoformat(days[-1]['date']) + dt.timedelta(days=1)
    end = dt.datetime.combine(end_day, dt.time(), tz).astimezone(dt.timezone.utc)
    if now is not None:
        end = min(end, now.astimezone(dt.timezone.utc).replace(minute=0, second=0, microsecond=0) + dt.timedelta(hours=1))
    out, wip, t = [], 0, start
    while t < end:
        lt = t.astimezone(tz)
        k = lt.isoformat(timespec='minutes')
        h = by.get(k)
        if h:
            wip = h['counts'].get('wipEndOfHour', wip)
            rec = dict(h)
        else:
            rec = {'hour': k, 'hourOfDay': lt.hour, 'label': lt.strftime('%Y-%m-%d %H:00 ') + ('EDT' if lt.dst() else 'EST'),
                   'counts': {a: 0 for a in ADDITIVE}, 'delivery': {'count': 0, 'durationSumDays': 0}, 'deployments': {}}
        rec['counts'] = dict(rec['counts'], wipEndOfDay=wip)  # the hour's end value, under the name aggregate() reads
        rec['date'] = rec['label'][:10]
        rec['quiet'] = h is None
        out.append(rec)
        t += dt.timedelta(hours=1)
    if now is None:  # end with the last recorded hour, so the output depends on the data only
        while out and out[-1]['quiet']:
            out.pop()
    return out[-last:] if last else out


def hour_profile(hour_records):
    """Hour-of-day profile (0-23, America/New_York): additive counts summed across days; WIP is not meaningful here."""
    out = []
    for hod in range(24):
        a = aggregate([h for h in hour_records if h['hourOfDay'] == hod], f'{hod:02d}:00')
        a['counts']['wipEndOfDay'] = None
        out.append(a)
    return out


def key(day, by):
    d = dt.date.fromisoformat(day['date'])
    return {'day': day['date'], 'week': day['isoWeek'], 'month': f'{d:%Y-%m}', 'quarter': f'{d.year}-Q{(d.month - 1) // 3 + 1}'}[by]


def aggregate(days, label=''):
    out = {'label': label, 'days': len(days), 'from': days[0]['date'] if days else None, 'to': days[-1]['date'] if days else None,
           'counts': {k: sum(x['counts'].get(k, 0) for x in days) for k in ADDITIVE}, 'deployments': {}}
    out['counts']['wipEndOfDay'] = days[-1]['counts'].get('wipEndOfDay', 0) if days else 0
    n = sum(x['delivery']['count'] for x in days)
    s = sum(x['delivery']['durationSumDays'] for x in days)
    out['delivery'] = {'count': n, 'durationSumDays': round(s, 6), 'mttdDays': round(s / n, 4) if n else None}
    for x in days:
        for e, v in x.get('deployments', {}).items():
            d = out['deployments'].setdefault(env_name(e), {'count': 0, 'failed': 0})
            d['count'] += v['count']
            d['failed'] += v['failed']
    for d in out['deployments'].values():
        d['failedShare'] = round(d['failed'] / d['count'], 4) if d['count'] else None
    return out


def group(days, by):
    """Aggregates per group key, oldest first."""
    buckets = {}
    for x in sorted(days, key=lambda x: x['date']):
        buckets.setdefault(key(x, by), []).append(x)
    return [aggregate(v, k) for k, v in buckets.items()]


def rolling(days, n, end):
    """The n calendar days ending with `end` (inclusive)."""
    lo = end - dt.timedelta(days=n - 1)
    return aggregate([x for x in days if lo <= dt.date.fromisoformat(x['date']) <= end], f'Last {n} days')


def named_views(days, today):
    """Rolling 7/30/90 days of finished days (ending yesterday) and Rolling 12 weeks/months of finished periods."""
    y = today - dt.timedelta(days=1)
    tw, tm = key({'date': f'{today:%Y-%m-%d}', 'isoWeek': '%d-W%02d' % today.isocalendar()[:2]}, 'week'), f'{today:%Y-%m}'
    weeks = [g for g in group(days, 'week') if g['label'] != tw][-12:]
    months = [g for g in group(days, 'month') if g['label'] != tm][-12:]
    flat = lambda gs, label: aggregate([x for x in days if key(x, 'week' if 'week' in label else 'month') in {g['label'] for g in gs}], label) | {
        'periods': len(gs)}
    return {'rolling7': rolling(days, 7, y), 'rolling30': rolling(days, 30, y), 'rolling90': rolling(days, 90, y),
            'rolling12Weeks': flat(weeks, 'Rolling 12 weeks'), 'rolling12Months': flat(months, 'Rolling 12 months')}
