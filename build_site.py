"""Génère le dossier site/ : data/planning.json (et cal/*.ics) à partir de schedule.json."""
import hashlib
import json
import os
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

from roles import ROLE_COLORS, SITE_LABELS

HERE = os.path.dirname(os.path.abspath(__file__))
TZ = ZoneInfo('Europe/Paris')
DAY_DATES = {
    'Vendredi 23 octobre': (2026, 10, 23),
    'Samedi 24 octobre': (2026, 10, 24),
    'Dimanche 25 octobre': (2026, 10, 25),
}


@dataclass(frozen=True)
class Block:
    start: datetime
    end: datetime
    role: str


def slugify(name):
    return unicodedata.normalize('NFD', name).encode('ascii', 'ignore').decode().lower()


def slot_start(day, idx):
    """Début (aware, Europe/Paris) du créneau idx ; idx 0 = 9h00. Heure locale puis offset du jour."""
    y, m, d = DAY_DATES[day]
    return datetime(y, m, d, 9 + idx // 2, 30 * (idx % 2), tzinfo=TZ)


def _people(schedule):
    names = set()
    for rows in schedule.values():
        for row in rows.values():
            names.update(row)
    return sorted(names, key=slugify)


def person_blocks(schedule, person):
    blocks = []
    for day in DAY_DATES:
        rows = schedule[day]
        cur = None  # (start_idx, role)
        for idx in sorted(int(i) for i in rows):
            role = rows[str(idx)].get(person, '')
            if cur and cur[1] == role:
                continue
            if cur and cur[1]:
                blocks.append(Block(slot_start(day, cur[0]), slot_start(day, idx), cur[1]))
            cur = (idx, role)
        if cur and cur[1]:
            last = max(int(i) for i in rows) + 1
            blocks.append(Block(slot_start(day, cur[0]), slot_start(day, last), cur[1]))
    return sorted(blocks, key=lambda b: b.start)


def build_planning(schedule, generated_at):
    people = []
    for name in _people(schedule):
        people.append({
            'name': name,
            'slug': slugify(name),
            'blocks': [{'start': b.start.isoformat(), 'end': b.end.isoformat(), 'role': b.role}
                       for b in person_blocks(schedule, name)],
        })
    used = {b['role'] for p in people for b in p['blocks']}
    roles = {r: {'label': SITE_LABELS[r], 'color': '#' + ROLE_COLORS[r]} for r in sorted(used)}
    days = [{'date': '%04d-%02d-%02d' % DAY_DATES[d], 'label': d} for d in DAY_DATES]
    content = {'timezone': 'Europe/Paris', 'days': days, 'roles': roles, 'people': people}
    version = hashlib.sha1(json.dumps(content, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:12]
    return {'version': version, 'generatedAt': generated_at.isoformat(), **content}


def write_site(schedule_path, out_dir, generated_at):
    with open(schedule_path, encoding='utf-8') as f:
        schedule = json.load(f)
    planning = build_planning(schedule, generated_at)
    os.makedirs(os.path.join(out_dir, 'data'), exist_ok=True)
    with open(os.path.join(out_dir, 'data', 'planning.json'), 'w', encoding='utf-8') as f:
        json.dump(planning, f, ensure_ascii=False, indent=1)
