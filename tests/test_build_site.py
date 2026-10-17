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


def test_jeff_friday_single_block():
    fri = [b for b in person('Jeff')['blocks'] if b['start'].startswith('2026-10-23')]
    assert fri == [{'start': '2026-10-23T11:00:00+02:00', 'end': '2026-10-23T22:00:00+02:00', 'role': 'Run'}]


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
    assert {'Pause', 'Briefing'} <= set(PLANNING['roles'])
    assert PLANNING['roles']['Run'] == {'label': 'Run', 'color': '#1565C0'}
    slugs = [p['slug'] for p in PLANNING['people']]
    assert slugs == sorted(slugs) and len(slugs) == 11
