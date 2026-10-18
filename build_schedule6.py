"""Génère schedule.json : planning bénévoles pôle Indie, Stunfest 2026 (23-25 octobre).
Créneaux de 30 min à partir de 9h00 (idx 0 = 9h00, idx 1 = 9h30, ...).
Rôles internes : Backup (affiché Standiers), Run, Stand, Awards, Media, Briefing, Pause/Off.
"""
import json, os, itertools as it

HERE = os.path.dirname(os.path.abspath(__file__))

def slot_index(hour, half):
    return (hour - 9) * 2 + half

# Fenêtres repas : 11h30-14h et 18h30-21h. Au moins 3 personnes en pause en même temps (jamais 1 ou 2).
lunch6, lunch9 = slot_index(12, 0), slot_index(13, 1)      # pauses déjeuner : 12h00 puis 13h30
dinner20 = slot_index(19, 0)                               # pause dîner de Chris (Média) : 19h00
LUNCH_WINDOW = set(range(slot_index(11, 1), slot_index(14, 0)))
DINNER_WINDOW = set(range(slot_index(18, 1), slot_index(21, 0)))
meal_window = LUNCH_WINDOW | DINNER_WINDOW  # Standiers renforcés à 3 hors instants de pause
awards_start, awards_end = slot_index(18, 1), slot_index(20, 1)  # 18h30 -> 20h30 (inclus, 5 créneaux)

MEDIA_PERSON = 'Chris'

DAYS = {
    'Vendredi 23 octobre': {
        'full_day': ['François', 'Étienne', 'Florent', 'Arthur', 'Mael', 'Gabriel', 'Lylou', 'Suliac'],
        'late': [('Jeff', 11, 22)],
        'awards': None,
        'end_hour': 19.5,
        'all_run_until': 14,   # préparation avant ouverture (14h) : tout le monde en Run
        'prep_counts_toward_limit': False,  # dérogation explicite : pas de limite de 2h sur cette période
        'briefing_slot': slot_index(10, 0),  # briefing 10h00-10h30, toute l'équipe sauf Jeff
        'dinner_slots': (slot_index(18, 1), slot_index(19, 0)),  # 18h30 puis 19h00 (fermeture 19h30)
        'run_count': 2,
    },
    'Samedi 24 octobre': {
        'full_day': ['François', 'Étienne', 'Florent', 'Arthur', 'Mael', 'Gabriel', 'Lylou', 'Suliac', 'Robin'],
        'late': [('Jeff', 11, 22)],
        'awards': {'start_slot': awards_start, 'end_slot': awards_end},
        'end_hour': 19.5,
        'all_run_until': 10,   # préparation 9h-10h avant ouverture : tout le monde en Run
        'prep_counts_toward_limit': True,
        'dinner_slots': (slot_index(19, 0), slot_index(19, 1)),  # pendant les Awards : 19h00 puis 19h30
        'run_count': 2,
    },
    'Dimanche 25 octobre': {
        'full_day': ['François', 'Étienne', 'Florent', 'Arthur', 'Mael', 'Gabriel', 'Lylou', 'Suliac', 'Robin'],
        'late': [('Jeff', 11, 22)],
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

def build_day(day_name, cfg):
    full_day = cfg['full_day']
    late = cfg['late']
    awards = cfg['awards']
    end_hour = cfg['end_hour']
    all_run_until = cfg.get('all_run_until')
    run_count_cfg = cfg.get('run_count', 2)

    base_end_slots = slot_index(int(end_hour), 1 if end_hour % 1 else 0)
    team_end_slots = max(base_end_slots, awards['end_slot'] + 1) if awards else base_end_slots
    day_n_slots = max(team_end_slots, max(end for _, _, end in late) * 2 - 18)  # fin tardive des 'late'

    dinner_a, dinner_b = cfg['dinner_slots']
    pause_set = {lunch6, lunch9, dinner_a, dinner_b}
    first_slots = {lunch6, dinner_a}

    cur_role = {p: None for p in full_day}
    run_len = {p: 0 for p in full_day}
    total_work = {p: 0 for p in full_day}
    role_totals = {p: {'Backup': 0, 'Run': 0, 'Stand': 0} for p in full_day}
    paused_meal = {p: {'lunch': False, 'dinner': False} for p in full_day}
    awards_standiers = None  # 2 personnes fixes sur l'accueil Standiers pendant toute la durée des Awards

    schedule = {idx: {} for idx in range(day_n_slots)}

    def meal_of(idx):
        return 'lunch' if idx in (lunch6, lunch9) else 'dinner'

    def choose_pausers(idx, candidates, n_working=None):
        """Pausers à cet instant de repas. 1er instant : tous sauf n_working (ou la moitié) ; 2e : les restants.
        Chaque groupe fait au moins 3 personnes (garanti par les tests)."""
        meal = meal_of(idx)
        if idx in first_slots:
            ordered = sorted(candidates, key=lambda p: -total_work[p])
            size = len(candidates) - n_working if n_working is not None else len(candidates) - len(candidates) // 2
            pausers = set(ordered[:size])
        else:
            pausers = {p for p in candidates if not paused_meal[p][meal]}
        for p in pausers:
            paused_meal[p][meal] = True
        return pausers

    for idx in range(day_n_slots):
        h = hour_of(idx)
        row = {}

        # Chris : Média en continu, pause repas sur le 1er sous-créneau de chaque repas
        if idx in (lunch6, dinner20):
            media_role = 'Pause'
        else:
            media_role = 'Media'

        # Jeff (présence décalée) : toujours en Run entre son arrivée et son départ
        for person, start_h, end_h in late:
            row[person] = 'Run' if start_h <= h < end_h else ''

        # Après le départ de l'équipe, seuls les 'late' restent
        if idx >= team_end_slots:
            schedule[idx] = row
            continue

        # Indie Awards : 2 personnes fixes en Standiers, le reste de l'équipe sur Awards (Chris reste en Média)
        if awards and awards['start_slot'] <= idx <= awards['end_slot']:
            if awards_standiers is None:
                candidates = sorted(full_day, key=lambda p: sum(role_totals[p].values()))
                awards_standiers = candidates[:2]
            eating = choose_pausers(idx, [p for p in full_day if p not in awards_standiers]) if idx in pause_set else set()
            for p in full_day:
                if p in eating:
                    row[p] = 'Pause'
                    cur_role[p] = None
                    run_len[p] = 0
                elif p in awards_standiers:
                    row[p] = 'Backup'
                    run_len[p] = run_len[p] + 1 if cur_role[p] == 'Backup' else 1
                    cur_role[p] = 'Backup'
                    total_work[p] += 1
                    role_totals[p]['Backup'] += 1
                else:
                    row[p] = 'Awards'
                    cur_role[p] = None
                    run_len[p] = 0
            for person, start_h, end_h in late:
                if start_h <= h < end_h:
                    row[person] = 'Awards'
            row[MEDIA_PERSON] = media_role
            schedule[idx] = row
            continue

        # Briefing : toute l'équipe (Chris compris) ; Jeff n'est pas encore arrivé
        if idx == cfg.get('briefing_slot'):
            for p in full_day:
                row[p] = 'Briefing'
                cur_role[p], run_len[p] = None, 0
            row[MEDIA_PERSON] = 'Briefing'
            schedule[idx] = row
            continue

        # Préparation avant ouverture : tout le monde en Run (dérogation au max 2h)
        if all_run_until is not None and h < all_run_until:
            # repas pendant la préparation : 3 personnes restent en Run, les autres mangent (au moins 3 ensemble)
            eating = choose_pausers(idx, full_day, n_working=3) if idx in pause_set else set()
            for p in full_day:
                row[p] = 'Pause' if p in eating else 'Run'
                if p in eating:
                    cur_role[p], run_len[p] = None, 0
                elif cfg.get('prep_counts_toward_limit', True):
                    run_len[p] = run_len[p] + 1 if cur_role[p] == 'Run' else 1
                    cur_role[p] = 'Run'
                    total_work[p] += 1
                    role_totals[p]['Run'] += 1
                else:
                    cur_role[p], run_len[p] = None, 0
            row[MEDIA_PERSON] = media_role
            schedule[idx] = row
            continue

        # Rotation normale
        is_pause_instant = idx in pause_set
        backup_n = 3 if (idx in meal_window and not is_pause_instant) else 1
        run_n = max(run_count_cfg - 1, 1) if is_pause_instant else run_count_cfg
        stand_n = 1
        needed = ['Backup'] * backup_n + ['Stand'] * stand_n + ['Run'] * run_n

        if is_pause_instant:
            pausers = choose_pausers(idx, full_day, n_working=len(needed))
            available = [p for p in full_day if p not in pausers]
        else:
            pausers = set()
            available = list(full_day)

        def valid(p, role):
            return not (cur_role.get(p) == role and run_len.get(p, 0) >= 4)

        avail_sorted = sorted(available, key=lambda p: sum(role_totals[p].values()))
        cand_pool = avail_sorted[:max(len(needed) + 3, len(avail_sorted))]
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
        for p in full_day:
            if p in pausers:
                row[p] = 'Pause'
            elif p in assigned:
                row[p] = assigned[p]
            else:
                row[p] = 'Off'

        for p in full_day:
            r = row[p]
            if r in ('Backup', 'Run', 'Stand'):
                run_len[p] = run_len[p] + 1 if cur_role[p] == r else 1
                cur_role[p] = r
                total_work[p] += 1
                role_totals[p][r] += 1
            else:
                cur_role[p] = None
                run_len[p] = 0

        row[MEDIA_PERSON] = media_role

        schedule[idx] = row

    return schedule

def find_issues(all_sched):
    """Validation : pas plus de 4 créneaux (2h) consécutifs sur un même poste de travail,
    hors dérogations explicites : Run du vendredi avant 14h, Standiers pendant les Awards,
    Jeff (Run continu), Chris (Média continu)."""
    roles_work = {'Backup', 'Run', 'Stand'}
    issues = []
    for day, cfg in DAYS.items():
        n = len(all_sched[day])
        for p in cfg['full_day']:
            run_l, prev = 0, None
            for idx in range(n):
                h = hour_of(idx)
                r = all_sched[day][idx].get(p, '')
                forced_run = (cfg.get('all_run_until') is not None and h < cfg['all_run_until']
                              and not cfg.get('prep_counts_toward_limit', True))
                in_awards = cfg['awards'] and cfg['awards']['start_slot'] <= idx <= cfg['awards']['end_slot']
                if forced_run or in_awards:
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
