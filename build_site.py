"""Génère le dossier site/ : data/planning.json (et cal/*.ics) à partir de schedule.json."""
import hashlib
import json
import os
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from roles import ROLE_COLORS, ROLE_LABELS

BS, LF, CRLF = chr(92), chr(10), chr(13) + chr(10)
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
    roles = {r: {'label': ROLE_LABELS[r], 'color': '#' + ROLE_COLORS[r]} for r in sorted(used)}
    days = [{'date': '%04d-%02d-%02d' % DAY_DATES[d], 'label': d} for d in DAY_DATES]
    content = {'timezone': 'Europe/Paris', 'days': days, 'roles': roles, 'people': people}
    version = hashlib.sha1(json.dumps(content, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:12]
    return {'version': version, 'generatedAt': generated_at.isoformat(), **content}


def ics_escape(text):
    return (text.replace(BS, BS + BS).replace(';', BS + ';').replace(',', BS + ',')
            .replace(CRLF, LF).replace(LF, BS + 'n'))


def fold_line(line):
    """Repli RFC 5545 : 75 octets max par ligne physique, sans couper un caractère UTF-8."""
    out, cur, size = [], '', 0
    for ch in line:
        n = len(ch.encode())
        if size + n > (75 if not out else 74):
            out.append(cur)
            cur, size = '', 0
        cur += ch
        size += n
    out.append(cur)
    return '\r\n '.join(out)


def _utc(dt):
    return dt.astimezone(timezone.utc).strftime('%Y%m%dT%H%M%SZ')


def build_ics(person, slug, blocks, generated_at):
    lines = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//Stunfest Indie//Planning//FR',
             'CALSCALE:GREGORIAN', 'X-WR-CALNAME:Stunfest Indie', 'X-WR-TIMEZONE:Europe/Paris',
             'REFRESH-INTERVAL;VALUE=DURATION:PT15M', 'X-PUBLISHED-TTL:PT15M']
    for b in blocks:
        if b.role == 'Off':
            continue
        label = ROLE_LABELS[b.role]
        lines += [
            'BEGIN:VEVENT',
            'UID:%s-%s@stun-indie-planning' % (slug, b.start.strftime('%Y%m%d-%H%M')),
            'DTSTAMP:' + _utc(generated_at),
            'SEQUENCE:%d' % (int(generated_at.timestamp()) // 60),
            'DTSTART:' + _utc(b.start),
            'DTEND:' + _utc(b.end),
            'SUMMARY:' + ics_escape(label if b.role == 'Briefing' else label + ' — Stunfest Indie'),
            'DESCRIPTION:' + ics_escape('%s, %s – %s' % (label, b.start.strftime('%Hh%M'), b.end.strftime('%Hh%M'))),
            'BEGIN:VALARM', 'ACTION:DISPLAY', 'DESCRIPTION:' + ics_escape(label), 'TRIGGER:-PT10M', 'END:VALARM',
            'END:VEVENT']
    lines.append('END:VCALENDAR')
    return ''.join(fold_line(l) + CRLF for l in lines)


def write_site(schedule_path, out_dir, generated_at):
    with open(schedule_path, encoding='utf-8') as f:
        schedule = json.load(f)
    planning = build_planning(schedule, generated_at)
    os.makedirs(os.path.join(out_dir, 'data'), exist_ok=True)
    with open(os.path.join(out_dir, 'data', 'planning.json'), 'w', encoding='utf-8') as f:
        json.dump(planning, f, ensure_ascii=False, indent=1)
    os.makedirs(os.path.join(out_dir, 'cal'), exist_ok=True)
    for name in _people(schedule):
        slug = slugify(name)
        with open(os.path.join(out_dir, 'cal', slug + '.ics'), 'w', encoding='utf-8', newline='') as f:
            f.write(build_ics(name, slug, person_blocks(schedule, name), generated_at))


if __name__ == '__main__':
    write_site(os.path.join(HERE, 'schedule.json'), os.path.join(HERE, 'site'), datetime.now(timezone.utc))
    print('site/ généré')
