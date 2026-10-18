"""Groupings of daily delivery facts (website-platform-kit decision 0006). The dashboard's JavaScript implements the
same rules; keep them in step.

A day is a compact fact record: {date, isoWeek, counts{...}, delivery{count, durationSumDays}, deployments{env: {count,
failed}}}. Aggregation: counts are summed except wipEndOfDay (the last day's value); MTTD = sum of delivery durations /
number of delivered items with a known start (never an average of averages); failed share = failed / deployments.
"""
import datetime as dt

ADDITIVE = ('itemsStarted', 'itemsDelivered', 'forwardMoves', 'rework', 'netThroughput', 'itemsStopped')


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
            d = out['deployments'].setdefault(e, {'count': 0, 'failed': 0})
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
