"""Génère schedule.json : planning bénévoles pôle Indie, Stunfest 2026 (23-25 octobre).
Créneaux de 30 min à partir de 9h00 (idx 0 = 9h00, idx 1 = 9h30, ...).
Rôles internes : Backup (affiché Standiers), Run, Stand, Awards, Media, Briefing, Off (repas compris).
"""
import json, os, itertools as it

HERE = os.path.dirname(os.path.abspath(__file__))

def slot_index(hour, half):
    return (hour - 9) * 2 + half

# Fenêtres repas : 11h30-14h et 18h30-21h. Chacun mange 30 min (Off) ; les repas sont étalés sur toute la
# fenêtre par groupes d'au moins 3 personnes (jamais 1 ou 2 seules).
LUNCH_WINDOW = set(range(slot_index(11, 1), slot_index(14, 0)))
DINNER_WINDOW = set(range(slot_index(18, 1), slot_index(21, 0)))
meal_window = LUNCH_WINDOW | DINNER_WINDOW  # Standiers renforcés (jusqu'à 3) pendant les fenêtres repas
awards_start, awards_end = slot_index(18, 1), slot_index(20, 1)  # 18h30 -> 20h30 (inclus, 5 créneaux)

MEDIA_PERSON = 'Chris'
PRESENCE = {'Jeff': (11, 22)}  # présent de 11h à 22h (les autres : toute la journée d'équipe)

DAYS = {
    'Vendredi 23 octobre': {
        'full_day': ['François', 'Étienne', 'Florent', 'Arthur', 'Mael', 'Gabriel', 'Lylou', 'Suliac', 'Jeff'],
        'presence': PRESENCE,
        'awards': None,
        'end_hour': 19.5,
        'all_run_until': 14,   # préparation avant ouverture (14h) : tout le monde en Run
        'prep_counts_toward_limit': False,  # dérogation explicite : pas de limite de 2h sur cette période
        'briefing_slot': slot_index(10, 0),  # briefing 10h00-10h30, toute l'équipe sauf Jeff
        'dinner_slots': (slot_index(18, 1), slot_index(19, 0)),  # 18h30 puis 19h00 (fermeture 19h30)
        'run_count': 2,
    },
    'Samedi 24 octobre': {
        'full_day': ['François', 'Étienne', 'Florent', 'Arthur', 'Mael', 'Gabriel', 'Lylou', 'Suliac', 'Robin', 'Jeff'],
        'presence': PRESENCE,
        'awards': {'start_slot': awards_start, 'end_slot': awards_end},
        'end_hour': 19.5,
        'all_run_until': 10,   # préparation 9h-10h avant ouverture : tout le monde en Run
        'prep_counts_toward_limit': True,
        'dinner_slots': (slot_index(19, 0), slot_index(19, 1)),  # pendant les Awards : 19h00 puis 19h30
        'run_count': 2,
    },
    'Dimanche 25 octobre': {
        'full_day': ['François', 'Étienne', 'Florent', 'Arthur', 'Mael', 'Gabriel', 'Lylou', 'Suliac', 'Robin', 'Jeff'],
        'presence': PRESENCE,
        'awards': None,
        'end_hour': 19.5,
        'all_run_until': 10,   # préparation 9h-10h avant ouverture : tout le monde en Run
        'prep_counts_toward_limit': True,
        'dinner_slots': (slot_index(18, 1), slot_index(19, 0)),  # 18h30 puis 19h00 (fermeture 19h30)
        'run_count': 2,
    },
}

def hour_of(idx):
    return 9 + idx // 2


def day_layout(cfg):
    """(fin de l'équipe, nombre de créneaux) : après la fermeture, seuls les présents tardifs restent."""
    base_end = slot_index(int(cfg['end_hour']), 1 if cfg['end_hour'] % 1 else 0)
    awards = cfg['awards']
    team_end = max(base_end, awards['end_slot'] + 1) if awards else base_end
    late_end = max((end for _, end in cfg['presence'].values()), default=0) * 2 - 18
    return team_end, max(team_end, late_end)

def build_day_with_meals(day_name, cfg):
    full_day = cfg['full_day']
    presence = cfg['presence']
    awards = cfg['awards']
    end_hour = cfg['end_hour']
    all_run_until = cfg.get('all_run_until')
    run_count_cfg = cfg.get('run_count', 2)

    team_end_slots, day_n_slots = day_layout(cfg)

    cur_role = {p: None for p in full_day}
    run_len = {p: 0 for p in full_day}
    total_work = {p: 0 for p in full_day + [MEDIA_PERSON]}
    role_totals = {p: {'Backup': 0, 'Run': 0, 'Stand': 0} for p in full_day}
    taken = {p: {'lunch': False, 'dinner': False} for p in full_day + [MEDIA_PERSON]}
    awards_standiers = None  # 2 personnes fixes sur l'accueil Standiers pendant toute la durée des Awards

    schedule = {idx: {} for idx in range(day_n_slots)}
    meals = {}   # idx -> personnes en repas à ce créneau (affichées Off)
    plans = {}   # 'lunch' / 'dinner' -> {idx: taille du groupe}

    def spread(window, n):
        """Répartit n personnes en k groupes de >= 3 sur k créneaux régulièrement espacés de la fenêtre."""
        slots = sorted(window)
        k = max(1, min(len(slots), n // 3))
        picks = [slots[int((i + 0.5) * len(slots) / k)] for i in range(k)]
        return {slot: n // k + (1 if i < n % k else 0) for i, slot in enumerate(picks)}

    def eating_now(idx, eligible, pinned=()):
        """Personnes de `eligible` qui mangent au créneau idx (le dernier groupe prend tous ceux qui restent).
        `pinned` mangent ensemble au créneau central du plan (Standiers fixes des Awards)."""
        if idx in LUNCH_WINDOW:
            meal, window = 'lunch', LUNCH_WINDOW
        elif idx in DINNER_WINDOW:
            meal, window = 'dinner', {x for x in DINNER_WINDOW if x < team_end_slots}
        else:
            return set()
        if meal not in plans:
            plans[meal] = spread(window, len(eligible))
        plan = plans[meal]
        if idx not in plan:
            return set()
        todo = [p for p in eligible if not taken[p][meal]]
        slots = sorted(plan)
        pin_slot = slots[len(slots) // 2]
        if pinned:
            mine = [p for p in todo if p in pinned]
            others = [p for p in todo if p not in pinned]
            if idx == pin_slot:
                rest = others if idx == max(plan) else sorted(others, key=lambda p: -total_work[p])[:max(0, plan[idx] - len(mine))]
                group = mine + rest
            else:
                group = others if idx == max(plan) else sorted(others, key=lambda p: -total_work[p])[:plan[idx]]
        else:
            group = todo if idx == max(plan) else sorted(todo, key=lambda p: -total_work[p])[:plan[idx]]
        for p in group:
            taken[p][meal] = True
        meals[idx] = sorted(group)
        return set(group)

    for idx in range(day_n_slots):
        h = hour_of(idx)
        # présents à ce créneau (Jeff : 11h-22h) ; les absents restent vides
        crew = [p for p in full_day if presence.get(p, (0, 99))[0] <= h < presence.get(p, (0, 99))[1]]
        row = {p: '' for p in full_day if p not in crew}

        # Après la fermeture, seuls les présents tardifs restent (Jeff : Run seul)
        if idx >= team_end_slots:
            for p in full_day:
                row[p] = 'Run' if p in crew and p in presence else ''
            schedule[idx] = row
            continue

        # Indie Awards : 2 personnes fixes en Standiers, le reste de l'équipe sur Awards (Chris reste en Média)
        if awards and awards['start_slot'] <= idx <= awards['end_slot']:
            if awards_standiers is None:
                candidates = sorted(crew, key=lambda p: sum(role_totals[p].values()))
                awards_standiers = candidates[:2]
            eating = eating_now(idx, crew + [MEDIA_PERSON], pinned=awards_standiers)
            # les 2 Standiers fixes ; s'ils mangent, 2 personnes des Awards tiennent l'accueil à leur place
            on_stand = [p for p in awards_standiers if p not in eating]
            if len(on_stand) < 2:
                spare = sorted((p for p in crew if p not in eating and p not in awards_standiers),
                               key=lambda p: sum(role_totals[p].values()))
                on_stand += spare[:2 - len(on_stand)]
            for p in crew:
                if p in eating:
                    row[p] = 'Off'
                    cur_role[p] = None
                    run_len[p] = 0
                elif p in on_stand:
                    row[p] = 'Backup'
                    run_len[p] = run_len[p] + 1 if cur_role[p] == 'Backup' else 1
                    cur_role[p] = 'Backup'
                    total_work[p] += 1
                    role_totals[p]['Backup'] += 1
                else:
                    row[p] = 'Awards'
                    cur_role[p] = None
                    run_len[p] = 0
            row[MEDIA_PERSON] = 'Off' if MEDIA_PERSON in eating else 'Media'
            schedule[idx] = row
            continue

        # Briefing : toute l'équipe (Chris compris) ; Jeff n'est pas encore arrivé
        if idx == cfg.get('briefing_slot'):
            for p in crew:
                row[p] = 'Briefing'
                cur_role[p], run_len[p] = None, 0
            row[MEDIA_PERSON] = 'Briefing'
            schedule[idx] = row
            continue

        # Préparation avant ouverture : tout le monde en Run (dérogation au max 2h)
        if all_run_until is not None and h < all_run_until:
            # repas pendant la préparation : les groupes qui mangent sont Off, les autres restent en Run
            eating = eating_now(idx, crew + [MEDIA_PERSON])
            for p in crew:
                row[p] = 'Off' if p in eating else 'Run'
                if p in eating:
                    cur_role[p], run_len[p] = None, 0
                elif cfg.get('prep_counts_toward_limit', True):
                    run_len[p] = run_len[p] + 1 if cur_role[p] == 'Run' else 1
                    cur_role[p] = 'Run'
                    total_work[p] += 1
                    role_totals[p]['Run'] += 1
                else:
                    cur_role[p], run_len[p] = None, 0
            row[MEDIA_PERSON] = 'Off' if MEDIA_PERSON in eating else 'Media'
            schedule[idx] = row
            continue

        # Rotation normale : ceux qui mangent sont Off, les autres couvrent Standiers / Stand IC / Run
        eating = eating_now(idx, crew + [MEDIA_PERSON])
        available = [p for p in crew if p not in eating]
        run_n, stand_n = run_count_cfg, 1
        backup_n = max(1, min(3, len(available) - stand_n - run_n)) if idx in meal_window else 1
        needed = ['Backup'] * backup_n + ['Stand'] * stand_n + ['Run'] * run_n

        def valid(p, role):
            return not (cur_role.get(p) == role and run_len.get(p, 0) >= 4)

        avail_sorted = sorted(available, key=lambda p: sum(role_totals[p].values()))
        cand_pool = avail_sorted[:len(needed) + 2]
        best, best_score = None, None
        for combo in it.permutations(cand_pool, len(needed)):
            if not all(valid(p, role) for p, role in zip(combo, needed)):
                continue
            score = sum(role_totals[p][role] for p, role in zip(combo, needed)) + sum(total_work[p] for p in combo) * 0.01
            if best_score is None or score < best_score:
                best_score, best = score, combo
        if best is None:
            best = available[:len(needed)]

        assigned = {p: role for p, role in zip(best, needed)}
        for p in crew:
            if p in assigned:
                row[p] = assigned[p]
            else:
                row[p] = 'Off'

        for p in crew:
            r = row[p]
            if r in ('Backup', 'Run', 'Stand'):
                run_len[p] = run_len[p] + 1 if cur_role[p] == r else 1
                cur_role[p] = r
                total_work[p] += 1
                role_totals[p][r] += 1
            else:
                cur_role[p] = None
                run_len[p] = 0

        row[MEDIA_PERSON] = 'Off' if MEDIA_PERSON in eating else 'Media'

        schedule[idx] = row

    return schedule, meals


def build_day(day_name, cfg):
    return build_day_with_meals(day_name, cfg)[0]


def find_issues(all_sched):
    """Validation : pas plus de 4 créneaux (2h) consécutifs sur un même poste de travail,
    hors dérogations explicites : Run du vendredi avant 14h, Standiers pendant les Awards,
    Chris (Média continu), et Jeff seul en Run après la fermeture (pas de rotation possible)."""
    roles_work = {'Backup', 'Run', 'Stand'}
    issues = []
    for day, cfg in DAYS.items():
        n = len(all_sched[day])
        team_end, _ = day_layout(cfg)
        for p in cfg['full_day']:
            run_l, prev = 0, None
            for idx in range(n):
                h = hour_of(idx)
                r = all_sched[day][idx].get(p, '')
                forced_run = (cfg.get('all_run_until') is not None and h < cfg['all_run_until']
                              and not cfg.get('prep_counts_toward_limit', True))
                in_awards = cfg['awards'] and cfg['awards']['start_slot'] <= idx <= cfg['awards']['end_slot']
                if forced_run or in_awards or idx >= team_end:
                    prev, run_l = None, 0
                    continue
                if r in roles_work and r == prev:
                    run_l += 1
                elif r in roles_work:
                    run_l = 1
                else:
                    run_l = 0
                if run_l > 4:
                    issues.append((day, p, r, run_l, h))
                prev = r
    return issues

if __name__ == '__main__':
    all_sched = {day: build_day(day, cfg) for day, cfg in DAYS.items()}

    issues = find_issues(all_sched)
    print('issues hors dérogations:', issues)

    out = {day: {str(idx): row for idx, row in sched.items()} for day, sched in all_sched.items()}
    with open(os.path.join(HERE, 'schedule.json'), 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print('saved schedule.json')
