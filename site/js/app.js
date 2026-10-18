import {
  parseBlocks, findPerson, homeState, parisDate, changedBlocks, removedBlocks, formatTime, clockOffset,
  defaultDay, isAlertActive,
} from './model.js';
import { getSlug, setSlug, clearSlug, getSeen, setSeen } from './store.js';
import { renderPicker, renderHome, renderReminders, el } from './render.js';
import { renderTeam } from './team.js';
import { startReminders } from './reminders.js';
import { createPlanningSource } from './data.js';

const root = document.getElementById('app');

// ?now=<ISO> simule l'heure, en local uniquement ; l'horloge continue ensuite d'avancer.
const offset = clockOffset(location.search, location.hostname, Date.now());
const nowFn = () => new Date(Date.now() + offset);

let planning = null;
let selectedDay = null;
let userPickedDay = false;
let lastToday = null;
let online = true;
let alertBlock = null;

const dayFmt = new Intl.DateTimeFormat('fr-FR', { timeZone: 'Europe/Paris', day: 'numeric', month: 'short' });

// Compare le planning vu en dernier par ce bénévole au planning courant.
function pendingChanges(person) {
  const remember = () => setSeen(person.slug, { version: planning.version, blocks: person.blocks });
  const seen = getSeen(person.slug);
  if (!seen) {
    remember();
    return { changed: new Set(), removed: new Set() };
  }
  if (seen.version === planning.version) return { changed: new Set(), removed: new Set() };
  const changed = changedBlocks(seen.blocks, person.blocks);
  const removed = removedBlocks(seen.blocks, person.blocks);
  if (changed.size === 0 && removed.size === 0) remember();
  return { changed, removed };
}

function statusLine(now) {
  const generated = new Date(planning.generatedAt);
  const day = parisDate(generated) === parisDate(now) ? '' : ` le ${dayFmt.format(generated)}`;
  const parts = [`Planning mis à jour${day} à ${formatTime(generated)}`];
  if (!online) parts.push('hors-ligne');
  return el('p', online ? 'status' : 'status offline', parts.join(' · '));
}

function updateBanner(person, count) {
  const btn = el('button', 'link-btn', 'OK');
  btn.type = 'button';
  btn.addEventListener('click', () => {
    setSeen(person.slug, { version: planning.version, blocks: person.blocks });
    render();
  });
  return el('div', 'banner', el('span', null, `Planning mis à jour : ${count} créneau(x) modifié(s) ou supprimé(s)`), btn);
}

function alertBanner() {
  const mins = Math.max(1, Math.ceil((alertBlock.start - nowFn()) / 60000));
  const label = planning.roles[alertBlock.role]?.label ?? alertBlock.role;
  const ok = el('button', 'link-btn', 'OK');
  ok.type = 'button';
  ok.addEventListener('click', () => { alertBlock = null; render(); });
  return el('div', 'alert', el('span', null, `Dans ${mins} min : ${label} à ${formatTime(alertBlock.start)}`), ok);
}

// Alerte dans l'appli + vibration + notification système si la permission est accordée.
function notify(block) {
  alertBlock = block;
  const label = planning.roles[block.role]?.label ?? block.role;
  const title = `Dans 10 min : ${label}`;
  const body = `à ${formatTime(block.start)}`;
  navigator.vibrate?.([200, 100, 200]);
  if ('Notification' in window && Notification.permission === 'granted') {
    navigator.serviceWorker?.getRegistration().then(
      (reg) => (reg ? reg.showNotification(title, { body }) : new Notification(title, { body })),
    ).catch(() => {});
  }
  render();
}

function render() {
  if (!planning) {
    root.replaceChildren(el('p', 'message', online ? 'Chargement…' : "Hors-ligne : le planning n'a pas encore été téléchargé. Reconnecte-toi une fois."));
    return;
  }
  const person = getSlug() ? findPerson(planning, getSlug()) : null;
  if (!person) {
    if (getSlug()) clearSlug();
    renderPicker(root, planning.people, (slug) => { setSlug(slug); selectedDay = null; userPickedDay = false; render(); });
    return;
  }
  if (location.hash === '#rappels') {
    renderReminders(root, {
      slug: person.slug, baseUrl: new URL('.', location.href).href,
      onBack: () => { location.hash = ''; },
    });
    return;
  }
  if (location.hash === '#equipe') {
    const now = nowFn();
    if (selectedDay === null) selectedDay = defaultDay(planning.days, now);
    renderTeam(root, {
      planning, now, selectedDay, mySlug: person.slug,
      onSelectDay: (d) => { selectedDay = d; userPickedDay = true; render(); },
      onBack: () => { location.hash = ''; },
    });
    return;
  }
  const now = nowFn();
  const blocks = parseBlocks(person);
  const { changed, removed } = pendingChanges(person);
  if (alertBlock && !isAlertActive(alertBlock, now)) alertBlock = null;
  const today = parisDate(now);
  if (today !== lastToday) {
    lastToday = today;
    if (!userPickedDay) selectedDay = null;
  }
  selectedDay ??= defaultDay(planning.days, now);
  renderHome(root, {
    person, planning, blocks, now, selectedDay, changed,
    state: homeState(blocks, planning.days, now),
    extra: [offset ? el('div', 'alert', 'Heure simulée (test)') : null, alertBlock ? alertBanner() : null, changed.size + removed.size ? updateBanner(person, changed.size + removed.size) : null, statusLine(now)],
    onSelectDay: (d) => { selectedDay = d; userPickedDay = true; render(); },
    onChangePerson: () => { clearSlug(); render(); },
  });
}

const source = createPlanningSource({
  url: './data/planning.json',
  onUpdate: (p) => { planning = p; render(); },
  onStatus: (s) => { const was = online; online = s === 'online'; if (was !== online) render(); },
});
source.start();
document.addEventListener('visibilitychange', () => { if (!document.hidden) source.pollNow(); });
setInterval(render, 30000);
window.addEventListener('hashchange', render);
startReminders({
  getBlocks: () => {
    const person = planning && getSlug() ? findPerson(planning, getSlug()) : null;
    return person ? parseBlocks(person) : [];
  },
  getSlug, nowFn, notify,
});

if ('serviceWorker' in navigator) navigator.serviceWorker.register('./sw.js').catch(() => {});
