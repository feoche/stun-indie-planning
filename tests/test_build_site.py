import json
from datetime import datetime, timezone

import pytest

from build_site import (Block, build_planning, person_blocks, slot_start,
                        slugify)

SCHEDULE = json.load(open('schedule.json', encoding='utf-8'))
GEN = datetime(2026, 10, 17, 12, 0, tzinfo=timezone.utc)
PLANNING = build_planning(SCHEDULE, GEN)


def person(name, planning=PLANNING):
    return next(p for p in planning['people'] if p['name'] == name)


def test_slugify():
    assert slugify('François') == 'francois'
    assert slugify('Étienne') == 'etienne'


def test_slot_start_paris_offset():
    assert slot_start('Vendredi 23 octobre', 0).isoformat() == '2026-10-23T09:00:00+02:00'
    assert slot_start('Dimanche 25 octobre', 0).isoformat() == '2026-10-25T09:00:00+01:00'


def test_jeff_blocks_span_11h_to_22h_each_day():
    for date, off in (('2026-10-23', '+02:00'), ('2026-10-24', '+02:00'), ('2026-10-25', '+01:00')):
        day = [b for b in person('Jeff')['blocks'] if b['start'].startswith(date)]
        assert day[0]['start'] == f'{date}T11:00:00{off}'
        assert day[-1]['end'] == f'{date}T20:00:00{off}'
        assert len({b['role'] for b in day}) > 1  # plus uniquement du Run


def test_absent_person_has_no_blocks_that_day():
    assert not [b for b in person('Robin')['blocks'] if b['start'].startswith('2026-10-23')]


def test_blocks_sorted_and_not_overlapping():
    for p in PLANNING['people']:
        blocks = person_blocks(SCHEDULE, p['name'])
        assert blocks == sorted(blocks, key=lambda b: b.start)
        for a, b in zip(blocks, blocks[1:]):
            assert a.end <= b.start and a.start < a.end


def test_version_depends_on_content_only():
    other = build_planning(SCHEDULE, datetime(2026, 10, 18, tzinfo=timezone.utc))
    assert other['version'] == PLANNING['version']
    changed = json.loads(json.dumps(SCHEDULE))
    changed['Vendredi 23 octobre']['0']['François'] = 'Stand'
    assert build_planning(changed, GEN)['version'] != PLANNING['version']


def test_planning_shape():
    assert set(PLANNING) == {'version', 'generatedAt', 'timezone', 'days', 'roles', 'people'}
    assert len(PLANNING['days']) == 3
    assert PLANNING['days'][0] == {'date': '2026-10-23', 'label': 'Vendredi 23 octobre'}
    assert 'Briefing' in PLANNING['roles'] and 'Pause' not in PLANNING['roles']
    assert PLANNING['roles']['Run'] == {'label': 'Run', 'color': '#1565C0'}
    slugs = [p['slug'] for p in PLANNING['people']]
    assert slugs == sorted(slugs) and len(slugs) == 11


# --- .ics ---
from build_site import build_ics, fold_line, ics_escape


def _ics(name='François'):
    return build_ics(name, slugify(name), person_blocks(SCHEDULE, name), GEN)


def _unfold(text):
    return text.replace('\r\n ', '')


def test_ics_one_event_and_alarm_per_non_off_block():
    text = _ics()
    blocks = [b for b in person_blocks(SCHEDULE, 'François') if b.role != 'Off']
    assert text.count('BEGIN:VEVENT') == text.count('BEGIN:VALARM') == len(blocks)
    assert 'TRIGGER:-PT10M' in text
    assert 'SUMMARY:Briefing' in _unfold(text)
    assert 'SUMMARY:Off' not in _unfold(text)


def test_ics_times_utc_and_dst():
    text = _ics()
    assert 'DTSTART:20261023T070000Z' in text
    assert 'DTSTART:20261025T080000Z' in text


def test_ics_crlf_and_line_length():
    text = _ics()
    assert text.endswith('\r\n') and '\n' not in text.replace('\r\n', '')
    assert all(len(l.encode()) <= 75 for l in text.split('\r\n'))


def test_fold_line_roundtrip():
    line = 'X:' + 'é' * 100
    folded = fold_line(line)
    assert all(len(l.encode()) <= 75 for l in folded.split('\r\n'))
    assert folded.replace('\r\n ', '') == line


def test_ics_escape():
    bs = chr(92)
    assert ics_escape('a,b;c' + chr(10) + 'd' + bs + 'e') == 'a' + bs + ',b' + bs + ';c' + bs + 'nd' + bs + bs + 'e'


def test_ics_uid_stable():
    other = build_ics('François', 'francois', person_blocks(SCHEDULE, 'François'),
                      datetime(2026, 10, 20, tzinfo=timezone.utc))
    uids = lambda t: [l for l in t.split('\r\n') if l.startswith('UID:')]
    assert uids(_ics()) == uids(other)
    assert 'UID:francois-20261023-0900@stun-indie-planning' in _ics()


def test_ics_calendar_headers():
    text = _ics()
    for h in ('X-WR-CALNAME:Stunfest Indie', 'REFRESH-INTERVAL;VALUE=DURATION:PT15M',
              'X-PUBLISHED-TTL:PT15M'):
        assert h in text
    assert 'METHOD' not in text


def test_ics_sequence_increases_with_build_time():
    later = build_ics('François', 'francois', person_blocks(SCHEDULE, 'François'),
                      datetime(2026, 10, 24, 12, 0, tzinfo=timezone.utc))
    seq = lambda t: [int(l.split(':')[1]) for l in t.split('\r\n') if l.startswith('SEQUENCE:')]
    assert seq(_ics()) and len(set(seq(_ics()))) == 1
    assert seq(later)[0] > seq(_ics())[0]


def test_committed_ics_files_are_crlf():
    import glob
    files = glob.glob('site/cal/*.ics')
    assert len(files) == 11
    for f in files:
        data = open(f, 'rb').read()
        assert b'\r\n' in data and b'\n' not in data.replace(b'\r\n', b'')


def test_committed_site_matches_schedule():
    """Garde-fou : site/data/planning.json doit être régénéré (python build_site.py) après chaque changement de schedule.json."""
    committed = json.load(open('site/data/planning.json', encoding='utf-8'))
    assert committed['version'] == PLANNING['version']


def test_vote_role_removed_from_site():
    assert 'Vote' not in PLANNING['roles']
