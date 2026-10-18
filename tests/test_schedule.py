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


# --- fenêtres repas : 11h30-14h (idx 5-9) et 18h30-21h (idx 19-23) ---
LUNCH = range(5, 10)
DINNER = range(19, 24)
TEAM = {
    FRI: TEAM_FRI,
    SAT: TEAM_FRI + ['Robin'],
    SUN: TEAM_FRI + ['Robin'],
}


def eaters(day, idx):
    return [p for p in TEAM[day] if role(day, idx, p) == 'Pause']


@pytest.mark.parametrize('day', [FRI, SAT, SUN])
def test_at_least_3_off_together_to_eat(day):
    for idx in range(26):
        n = len(eaters(day, idx))
        assert n == 0 or n >= 3, (day, idx, n)


@pytest.mark.parametrize('day', [FRI, SAT, SUN])
def test_meal_breaks_only_inside_windows(day):
    for idx in range(26):
        if eaters(day, idx):
            assert idx in LUNCH or idx in DINNER, (day, idx)


@pytest.mark.parametrize('day', [FRI, SAT, SUN])
def test_everyone_gets_one_lunch_break(day):
    for p in TEAM[day]:
        assert sum(role(day, i, p) == 'Pause' for i in LUNCH) == 1, (day, p)


@pytest.mark.parametrize('day', [FRI, SAT, SUN])
def test_dinner_break_for_everyone_but_fixed_standiers(day):
    for p in TEAM[day]:
        n = sum(role(day, i, p) == 'Pause' for i in DINNER)
        fixed = day == SAT and all(role(day, i, p) == 'Backup' for i in range(19, 24))
        assert n == (0 if fixed else 1), (day, p, n)


def test_awards_keep_at_least_3_people_while_others_eat():
    for idx in range(19, 24):
        assert sum(1 for p in TEAM[SAT] if role(SAT, idx, p) == 'Awards') >= 3
