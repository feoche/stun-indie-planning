// Vue « Planning complet » : qui est où, maintenant et sur toute la journée.
import { el } from './render.js';
import { formatTime, parseBlocks, roleAtTime, slotProgress, slotsOfDay, whoIsWhere } from './model.js';

function chip(planning, role) {
  const info = planning.roles[role] ?? { label: role, color: '#424242' };
  const node = el('span', 'chip', info.label);
  node.style.background = info.color;
  return node;
}

function nowSection(planning, now) {
  const groups = whoIsWhere(planning, now);
  const roles = Object.keys(planning.roles).filter((r) => groups[r]);
  if (roles.length === 0) return null;
  const section = el('section', 'help', el('h2', null, `En ce moment · ${formatTime(now)}`));
  for (const role of roles) {
    section.append(el('div', 'who', chip(planning, role), el('span', 'who-names', groups[role].join(', '))));
  }
  return section;
}

function grid(planning, selectedDay, now, mySlug) {
  const slots = slotsOfDay(planning, selectedDay);
  if (slots.length === 0) return el('p', 'empty', 'Aucun planning ce jour-là.');
  const people = planning.people.map((p) => ({ ...p, parsed: parseBlocks(p) }));

  const head = el('tr', null, el('th', 'corner', ''));
  for (const p of people) head.append(el('th', p.slug === mySlug ? 'me' : null, p.name));

  const body = el('tbody');
  let currentRow = null;
  for (const slot of slots) {
    const isNow = slot <= now && now < new Date(slot.getTime() + 30 * 60000);
    const row = el('tr', isNow ? 'now' : null, el('th', 'time', formatTime(slot)));
    if (isNow) currentRow = row;
    for (const p of people) {
      const role = roleAtTime(p.parsed, slot);
      const info = planning.roles[role];
      const cell = el('td', p.slug === mySlug ? 'me' : null, info ? info.label : '');
      if (info) cell.style.background = info.color;
      if (role === 'Off') cell.classList.add('quiet');
      row.append(cell);
    }
    body.append(row);
  }
  const wrap = el('div', 'grid-wrap', el('table', 'grid', el('thead', null, head), body));
  wrap.currentRow = currentRow;
  wrap.currentSlot = currentRow ? slots[[...body.children].indexOf(currentRow)] : null;
  return wrap;
}

// ctx : { planning, selectedDay, now, mySlug, onSelectDay, onBack }
export function renderTeam(root, ctx) {
  const { planning, selectedDay, now, mySlug } = ctx;
  const back = el('button', 'link-btn', 'Retour');
  back.type = 'button';
  back.addEventListener('click', ctx.onBack);
  const roles = el('a', 'link-btn', 'Rôles');
  roles.href = '#roles';

  const tabs = el('nav', 'tabs');
  for (const d of planning.days) {
    const btn = el('button', 'tab', d.label.split(' ')[0]);
    btn.type = 'button';
    if (d.date === selectedDay) btn.classList.add('active');
    btn.addEventListener('click', () => ctx.onSelectDay(d.date));
    tabs.append(btn);
  }

  // on garde la position de défilement d'un rafraîchissement à l'autre (le trait avance toutes les 30 s)
  const previous = root.querySelector('.grid-wrap');
  const scroll = previous ? { top: previous.scrollTop, left: previous.scrollLeft } : null;
  const table = grid(planning, selectedDay, now, mySlug);
  const live = slotsOfDay(planning, selectedDay).length && table.currentRow ? nowSection(planning, now) : null;
  root.replaceChildren(
    el('header', 'top', el('h1', null, 'Planning complet'), el('div', 'top-actions', roles, back)),
    el('main', 'content', live, tabs, table),
  );
  if (scroll) {
    table.scrollTop = scroll.top;
    table.scrollLeft = scroll.left;
  } else {
    table.currentRow?.scrollIntoView({ block: 'center' }); // ouvre la grille sur le créneau en cours
  }
  drawNowLine(table, now);
}

// Trait horizontal à l'heure courante, placé dans la ligne du créneau en cours selon les minutes écoulées.
function drawNowLine(wrap, now) {
  if (!wrap.currentRow || !wrap.currentSlot) return;
  const wrapTop = wrap.getBoundingClientRect().top;
  const rowRect = wrap.currentRow.getBoundingClientRect();
  const line = el('div', 'now-line');
  line.style.top = `${rowRect.top - wrapTop + wrap.scrollTop + rowRect.height * slotProgress(wrap.currentSlot, now)}px`;
  line.style.width = `${wrap.scrollWidth}px`;
  wrap.append(line);
}
