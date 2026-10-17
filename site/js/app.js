import { parseBlocks, findPerson, homeState, parisDate, changedBlocks, formatTime } from './model.js';
import { getSlug, setSlug, clearSlug, getSeen, setSeen } from './store.js';
import { renderPicker, renderHome, el } from './render.js';
import { createPlanningSource } from './data.js';

const root = document.getElementById('app');

// ?now=<ISO> simule l'heure (outil de test) ; l'horloge continue ensuite d'avancer.
const nowParam = new URLSearchParams(location.search).get('now');
const clockOffset = nowParam && !Number.isNaN(Date.parse(nowParam)) ? Date.parse(nowParam) - Date.now() : 0;
const nowFn = () => new Date(Date.now() + clockOffset);

let planning = null;
let selectedDay = null;
let online = true;

function defaultDay(now) {
  const today = parisDate(now);
  return planning.days.some((d) => d.date === today) ? today : planning.days[0].date;
}

// Compare le planning vu en dernier par ce bénévole au planning courant.
function pendingChanges(person) {
  const seen = getSeen();
  if (!seen || seen.slug !== person.slug) {
    setSeen({ slug: person.slug, version: planning.version, blocks: person.blocks });
    return new Set();
  }
  if (seen.version === planning.version) return new Set();
  const changed = changedBlocks(seen.blocks, person.blocks);
  if (changed.size === 0) setSeen({ slug: person.slug, version: planning.version, blocks: person.blocks });
  return changed;
}

function statusLine() {
  const parts = [`Planning mis à jour à ${formatTime(new Date(planning.generatedAt))}`];
  if (!online) parts.push('hors-ligne');
  return el('p', online ? 'status' : 'status offline', parts.join(' · '));
}

function updateBanner(person, changed) {
  const btn = el('button', 'link-btn', 'OK');
  btn.type = 'button';
  btn.addEventListener('click', () => {
    setSeen({ slug: person.slug, version: planning.version, blocks: person.blocks });
    render();
  });
  return el('div', 'banner', el('span', null, `Planning mis à jour : ${changed.size} créneau(x) modifié(s)`), btn);
}

function render() {
  if (!planning) return;
  const person = getSlug() ? findPerson(planning, getSlug()) : null;
  if (!person) {
    if (getSlug()) clearSlug();
    renderPicker(root, planning.people, (slug) => { setSlug(slug); selectedDay = null; render(); });
    return;
  }
  const now = nowFn();
  const blocks = parseBlocks(person);
  const changed = pendingChanges(person);
  selectedDay ??= defaultDay(now);
  renderHome(root, {
    person, planning, blocks, now, selectedDay, changed,
    state: homeState(blocks, planning.days, now),
    extra: [changed.size ? updateBanner(person, changed) : null, statusLine()],
    onSelectDay: (d) => { selectedDay = d; render(); },
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
