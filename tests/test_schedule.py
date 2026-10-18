import pytest
from build_schedule6 import DAYS, build_day, build_day_with_meals, find_issues

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
    assert all(role(day, i, 'Jeff') != '' for i in range(4, 26))


def test_jeff_awards_only_during_saturday_awards():
    for day in (FRI, SUN):
        assert all(role(day, i, 'Jeff') != 'Awards' for i in range(26))
    assert all(role(SAT, i, 'Jeff') in ('Awards', 'Backup', 'Off') for i in range(19, 24))
    assert all(role(SAT, i, 'Jeff') == 'Run' for i in (24, 25))


@pytest.mark.parametrize('day', [FRI, SAT, SUN])
def test_jeff_is_in_the_rotation(day):
    work = {role(day, i, 'Jeff') for i in range(10, 19)} & {'Backup', 'Run', 'Stand'}
    assert len(work) >= 2, (day, work)


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
            assert role(day, i, 'Jeff') == 'Run'  # seul après la fermeture : reste en Run
    assert role(SAT, 23, 'Robin') in ('Awards', 'Backup')


def test_no_rotation_violation():
    assert find_issues(sched) == []


def test_two_in_run_with_jeff_counted():
    row = sched[FRI][10]
    assert sum(1 for p, r in row.items() if p != 'Chris' and r == 'Run') == 2


# --- fenêtres repas : 11h30-14h (idx 5-9) et 18h30-21h (idx 19-23) ---
LUNCH = range(5, 10)
DINNER = range(19, 24)
TEAM = {
    FRI: TEAM_FRI + ['Jeff'],
    SAT: TEAM_FRI + ['Robin', 'Jeff'],
    SUN: TEAM_FRI + ['Robin', 'Jeff'],
}
MEALS = {d: build_day_with_meals(d, c)[1] for d, c in DAYS.items()}  # {idx: [personnes en repas]}


def test_pause_role_is_gone():
    assert all('Pause' not in sched[d][i].values() for d in sched for i in sched[d])


@pytest.mark.parametrize('day', [FRI, SAT, SUN])
def test_at_least_3_off_together_to_eat(day):
    assert MEALS[day]
    for idx, people in MEALS[day].items():
        assert len(people) >= 3, (day, idx, people)
        assert all(role(day, idx, p) == 'Off' for p in people), (day, idx)


@pytest.mark.parametrize('day', [FRI, SAT, SUN])
def test_meals_only_inside_windows(day):
    assert all(idx in LUNCH or idx in DINNER for idx in MEALS[day])


@pytest.mark.parametrize('day', [FRI, SAT, SUN])
def test_everyone_eats_once_per_window(day):
    for p in TEAM[day]:
        lunch = sum(p in MEALS[day].get(i, []) for i in LUNCH)
        dinner = sum(p in MEALS[day].get(i, []) for i in DINNER)
        fixed = day == SAT and all(role(day, i, p) == 'Backup' for i in range(19, 24))
        assert lunch == 1, (day, p, lunch)
        assert dinner == (0 if fixed else 1), (day, p, dinner)


@pytest.mark.parametrize('day', [FRI, SAT, SUN])
def test_meals_are_spread_over_the_windows(day):
    lunch_slots = [i for i in MEALS[day] if i in LUNCH]
    dinner_slots = [i for i in MEALS[day] if i in DINNER]
    assert len(lunch_slots) >= 3, (day, lunch_slots)
    assert len(dinner_slots) >= 2, (day, dinner_slots)
    assert max(len(MEALS[day][i]) for i in MEALS[day]) <= 5


@pytest.mark.parametrize('day', [SAT, SUN])
def test_two_in_run_during_lunch_window(day):
    for idx in (5, 7, 8, 9):
        assert sum(1 for p, r in sched[day][idx].items() if p != 'Chris' and r == 'Run') == 2, (day, idx)


def test_awards_keep_at_least_3_people_while_others_eat():
    for idx in range(19, 24):
        assert sum(1 for p in TEAM[SAT] if role(SAT, idx, p) == 'Awards') >= 3


def test_no_vote_role_anymore():
    assert all('Vote' not in sched[d][i].values() for d in sched for i in sched[d])
