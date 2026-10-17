import pytest
from build_schedule6 import DAYS, build_day, find_issues

FRI, SAT, SUN = 'Vendredi 23 octobre', 'Samedi 24 octobre', 'Dimanche 25 octobre'
TEAM_FRI = ['François', 'Étienne', 'Florent', 'Arthur', 'Mael', 'Gabriel', 'Lylou', 'Suliac']

sched = {d: build_day(d, c) for d, c in DAYS.items()}


def role(day, idx, person):
    return sched[day][idx].get(person, '')


@pytest.mark.parametrize('day', [FRI, SAT, SUN])
def test_all_days_have_26_slots(day):
    assert len(sched[day]) == 26


@pytest.mark.parametrize('day', [FRI, SAT, SUN])
def test_jeff_present_11h_to_22h_all_days(day):
    assert all(role(day, i, 'Jeff') == '' for i in range(0, 4))
    assert all(role(day, i, 'Jeff') in ('Run', 'Awards') for i in range(4, 26))


def test_jeff_awards_only_saturday_1830_2030():
    for i in range(4, 26):
        expected = 'Awards' if 19 <= i <= 23 else 'Run'
        assert role(SAT, i, 'Jeff') == expected
    for day in (FRI, SUN):
        assert all(role(day, i, 'Jeff') != 'Awards' for i in range(26))


def test_friday_briefing_10h():
    for p in TEAM_FRI + ['Chris']:
        assert role(FRI, 2, p) == 'Briefing'
    assert role(FRI, 2, 'Jeff') == ''
    for day in (FRI, SAT, SUN):
        for i in range(26):
            if (day, i) != (FRI, 2):
                assert 'Briefing' not in sched[day][i].values()


def test_team_leaves_after_1930():
    for day, first in ((FRI, 21), (SUN, 21), (SAT, 24)):
        for i in range(first, 26):
            others = [p for p, r in sched[day][i].items() if p != 'Jeff' and r != '']
            assert others == []
    assert role(SAT, 23, 'Robin') in ('Awards', 'Backup')


def test_no_rotation_violation():
    assert find_issues(sched) == []


def test_run_rotation_unchanged_by_jeff():
    row = sched[FRI][10]
    assert sum(1 for p, r in row.items() if p not in ('Jeff', 'Chris') and r == 'Run') == 2
