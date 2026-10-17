import { parseBlocks, findPerson, homeState, parisDate } from './model.js';
import { getSlug, setSlug, clearSlug } from './store.js';
import { renderPicker, renderHome } from './render.js';

const root = document.getElementById('app');

// ?now=<ISO> simule l'heure (outil de test) ; l'horloge continue ensuite d'avancer.
const nowParam = new URLSearchParams(location.search).get('now');
const clockOffset = nowParam && !Number.isNaN(Date.parse(nowParam)) ? Date.parse(nowParam) - Date.now() : 0;
const nowFn = () => new Date(Date.now() + clockOffset);

let planning = null;
let selectedDay = null;

function defaultDay(now) {
  const today = parisDate(now);
  return planning.days.some((d) => d.date === today) ? today : planning.days[0].date;
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
  selectedDay ??= defaultDay(now);
  renderHome(root, {
    person, planning, blocks, now, selectedDay,
    state: homeState(blocks, planning.days, now),
    onSelectDay: (d) => { selectedDay = d; render(); },
    onChangePerson: () => { clearSlug(); render(); },
  });
}

async function load() {
  const res = await fetch('./data/planning.json', { cache: 'no-store' });
  planning = await res.json();
  render();
}

load().catch(() => { root.textContent = 'Impossible de charger le planning.'; });
setInterval(render, 30000);
