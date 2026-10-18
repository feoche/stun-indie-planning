// Logique pure (sans DOM). Tout est calculé en Europe/Paris, jamais dans le fuseau de l'appareil.
export const REMINDER_LEAD_MS = 10 * 60 * 1000;
const TZ = 'Europe/Paris';

const dateFmt = new Intl.DateTimeFormat('fr-FR', { timeZone: TZ, year: 'numeric', month: '2-digit', day: '2-digit' });
const timeFmt = new Intl.DateTimeFormat('fr-FR', { timeZone: TZ, hour: 'numeric', minute: '2-digit', hourCycle: 'h23' });

export function parseBlocks(person) {
  return person.blocks
    .map((b) => ({ start: new Date(b.start), end: new Date(b.end), role: b.role }))
    .sort((a, b) => a.start - b.start);
}

export function findPerson(planning, slug) {
  return planning.people.find((p) => p.slug === slug) ?? null;
}

export function parisDate(date) {
  const p = Object.fromEntries(dateFmt.formatToParts(date).map((x) => [x.type, x.value]));
  return `${p.year}-${p.month}-${p.day}`;
}

export function defaultDay(days, now) {
  const today = parisDate(now);
  return days.some((d) => d.date === today) ? today : days[0].date;
}

export function isAlertActive(block, now) {
  return now < block.start;
}

export function platformOf(userAgent) {
  if (/iPhone|iPad|iPod/.test(userAgent)) return 'ios';
  if (/Android/.test(userAgent)) return 'android';
  return 'other';
}

export function formatTime(date) {
  const parts = Object.fromEntries(timeFmt.formatToParts(date).map((p) => [p.type, p.value]));
  return `${Number(parts.hour)}h${parts.minute}`;
}

export function blocksOfDay(blocks, dateStr) {
  return blocks.filter((b) => parisDate(b.start) === dateStr);
}

// kind: before | after | off-day | not-started | active | done-today
export function homeState(blocks, days, now) {
  const today = parisDate(now);
  if (today < days[0].date) return { kind: 'before', current: null, next: blocks[0] ?? null };
  if (today > days[days.length - 1].date) return { kind: 'after', current: null, next: null };
  const todays = blocksOfDay(blocks, today);
  if (todays.length === 0) {
    const next = blocks.find((b) => b.start > now) ?? null;
    return { kind: 'off-day', current: null, next };
  }
  const i = todays.findIndex((b) => b.start <= now && now < b.end);
  if (i >= 0) return { kind: 'active', current: todays[i], next: todays[i + 1] ?? null };
  const next = todays.find((b) => b.start > now) ?? null;
  if (next) return { kind: 'not-started', current: null, next };
  return { kind: 'done-today', current: null, next: blocks.find((b) => b.start > now) ?? null };
}

export function blockKey(slug, block) {
  return `${slug}|${block.start.toISOString()}|${block.role}`;
}

export function dueReminder(blocks, slug, now, fired) {
  for (const block of blocks) {
    if (block.role === 'Off') continue;
    if (block.start - REMINDER_LEAD_MS <= now && now < block.start) {
      const key = blockKey(slug, block);
      if (!fired.has(key)) return { block, key };
    }
  }
  return null;
}

const sig = (b) => `${new Date(b.start).toISOString()}|${new Date(b.end).toISOString()}|${b.role}`;

// Débuts (ISO UTC) des blocs de oldBlocks qui n'existent plus à l'identique dans newBlocks.
export function removedBlocks(oldBlocks, newBlocks) {
  const after = new Set(newBlocks.map(sig));
  return new Set(oldBlocks.filter((b) => !after.has(sig(b))).map((b) => new Date(b.start).toISOString()));
}

// Accepte des blocs bruts (chaînes ISO) ; renvoie les débuts (ISO UTC) des blocs nouveaux ou modifiés.
export function changedBlocks(oldBlocks, newBlocks) {
  const before = new Set(oldBlocks.map(sig));
  return new Set(newBlocks.filter((b) => !before.has(sig(b))).map((b) => new Date(b.start).toISOString()));
}

// ?now=<ISO> simule l'heure, uniquement en local (jamais en production : un lien partagé afficherait un faux poste).
export function clockOffset(search, hostname, realNow) {
  if (hostname !== 'localhost' && hostname !== '127.0.0.1') return 0;
  const raw = new URLSearchParams(search).get('now');
  const t = raw ? Date.parse(raw) : NaN;
  return Number.isNaN(t) ? 0 : t - realNow;
}
