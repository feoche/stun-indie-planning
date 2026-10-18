import pytest
from build_schedule6 import DAYS, build_day, build_day_with_meals, find_issues

FRI, SAT, SUN = 'Vendredi 23 octobre', 'Samedi 24 octobre', 'Dimanche 25 octobre'
TEAM_FRI = ['François', 'Étienne', 'Florent', 'Arthur', 'Mael', 'Gabriel', 'Lylou', 'Suliac']

sched = {d: build_day(d, c) for d, c in DAYS.items()}


def role(day, idx, person):
    return sched[day][idx].get(person, '')


@pytest.mark.parametrize('day', [FRI, SAT, SUN])
def test_everyone_ends_at_20h(day):
    assert len(sched[day]) == 22  # 9h00 -> 20h00
    assert all(sched[day][21].get(p) for p in TEAM[day])  # encore tous en poste à 19h30


@pytest.mark.parametrize('day', [FRI, SAT, SUN])
def test_jeff_present_11h_to_20h_all_days(day):
    assert all(role(day, i, 'Jeff') == '' for i in range(0, 4))
    assert all(role(day, i, 'Jeff') != '' for i in range(4, 22))


def test_jeff_awards_only_during_saturday_awards():
    for day in (FRI, SUN):
        assert all(role(day, i, 'Jeff') != 'Awards' for i in range(22))
    assert all(role(SAT, i, 'Jeff') in ('Awards', 'Backup', 'Off') for i in range(19, 22))


@pytest.mark.parametrize('day', [FRI, SAT, SUN])
def test_jeff_is_in_the_rotation(day):
    work = {role(day, i, 'Jeff') for i in range(10, 19)} & {'Backup', 'Run', 'Stand'}
    assert len(work) >= 2, (day, work)


def test_friday_briefing_10h():
    for p in TEAM_FRI + ['Chris']:
        assert role(FRI, 2, p) == 'Briefing'
    assert role(FRI, 2, 'Jeff') == ''
    for day in (FRI, SAT, SUN):
        for i in range(22):
            if (day, i) != (FRI, 2):
                assert 'Briefing' not in sched[day][i].values()


@pytest.mark.parametrize('day', [FRI, SUN])
def test_closing_half_hour_everyone_in_run(day):
    """Fermeture de la zone à 19h30 : tout le monde en Run (rangement) jusqu'à 20h, Chris en Média."""
    for p in TEAM[day]:
        assert role(day, 21, p) == ('Media' if p == 'Chris' else 'Run'), (day, p)


def test_no_rotation_violation():
    assert find_issues(sched) == []


def test_two_in_run_with_jeff_counted():
    row = sched[FRI][10]
    assert sum(1 for p, r in row.items() if p != 'Chris' and r == 'Run') == 2


# --- fenêtres repas : 11h30-14h (idx 5-9) et 18h30-20h (idx 19-21, avant la clôture de 19h30 hors samedi) ---
LUNCH = range(5, 10)
DINNER = range(19, 22)
TEAM = {
    FRI: TEAM_FRI + ['Jeff', 'Chris'],
    SAT: TEAM_FRI + ['Robin', 'Jeff', 'Chris'],
    SUN: TEAM_FRI + ['Robin', 'Jeff', 'Chris'],
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
    if day != SAT:
        assert all(idx != 21 for idx in MEALS[day])  # pas de repas pendant la clôture


@pytest.mark.parametrize('day', [FRI, SAT, SUN])
def test_everyone_eats_once_per_window(day):
    for p in TEAM[day]:
        lunch = sum(p in MEALS[day].get(i, []) for i in LUNCH)
        dinner = sum(p in MEALS[day].get(i, []) for i in DINNER)
        assert (lunch, dinner) == (1, 1), (day, p, lunch, dinner)


@pytest.mark.parametrize('day', [FRI, SAT, SUN])
def test_chris_eats_with_others_and_is_media_otherwise(day):
    for window in (LUNCH, DINNER):
        mine = [i for i in window if 'Chris' in MEALS[day].get(i, [])]
        assert len(mine) == 1, (day, mine)
        assert len(MEALS[day][mine[0]]) >= 3  # jamais seul
    for i in range(22):
        r = role(day, i, 'Chris')
        if True:
            expected = 'Briefing' if (day, i) == (FRI, 2) else ('Off' if 'Chris' in MEALS[day].get(i, []) else 'Media')
            assert r == expected, (day, i, r)


def test_saturday_stand_always_covered_by_two_standiers_during_awards():
    for idx in range(19, 22):
        assert sum(1 for p in TEAM[SAT] if role(SAT, idx, p) == 'Backup') == 2, idx


@pytest.mark.parametrize('day', [FRI, SAT, SUN])
def test_meals_are_spread_over_the_windows(day):
    lunch_slots = [i for i in MEALS[day] if i in LUNCH]
    dinner_slots = [i for i in MEALS[day] if i in DINNER]
    assert len(lunch_slots) >= 3, (day, lunch_slots)
    assert len(dinner_slots) >= 2, (day, dinner_slots)
    assert max(len(MEALS[day][i]) for i in MEALS[day]) <= 6


@pytest.mark.parametrize('day', [SAT, SUN])
def test_two_in_run_during_lunch_window(day):
    for idx in (5, 7, 8, 9):
        assert sum(1 for p, r in sched[day][idx].items() if p != 'Chris' and r == 'Run') == 2, (day, idx)


def test_awards_keep_at_least_3_people_while_others_eat():
    for idx in range(19, 22):
        assert sum(1 for p in TEAM[SAT] if role(SAT, idx, p) == 'Awards') >= 3


def test_no_vote_role_anymore():
    assert all('Vote' not in sched[d][i].values() for d in sched for i in sched[d])
