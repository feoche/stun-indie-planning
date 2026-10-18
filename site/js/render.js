// Rendu DOM. Tout texte passe par textContent (jamais innerHTML).
import { blocksOfDay, formatTime, parisDate, platformOf, roleLabel } from './model.js';

export function el(tag, className, ...children) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  for (const child of children) {
    if (child === null || child === undefined) continue;
    node.append(child);
  }
  return node;
}

export function renderPicker(root, people, onPick) {
  const list = el('div', 'picker-list');
  for (const p of people) {
    const btn = el('button', 'picker-btn', p.name);
    btn.type = 'button';
    btn.addEventListener('click', () => onPick(p.slug));
    list.append(btn);
  }
  root.replaceChildren(
    el('header', 'top', el('h1', null, 'Stunfest Indie')),
    el('main', 'content', el('p', 'lead', 'Qui es-tu ?'), list),
  );
}

function roleInfo(planning, role) {
  return planning.roles[role] ?? { label: role, color: '#424242' };
}

function roleChip(planning, role, slug) {
  const info = roleInfo(planning, role);
  const chip = el('span', 'chip', roleLabel(info, slug));
  chip.style.background = info.color;
  return chip;
}

function dayLabel(planning, date) {
  return planning.days.find((d) => d.date === date)?.label ?? '';
}

function minutesLeft(end, now) {
  const min = Math.max(1, Math.ceil((end - now) / 60000));
  if (min < 60) return `encore ${min} min`;
  const h = Math.floor(min / 60);
  const m = min % 60;
  return `encore ${h} h${m ? String(m).padStart(2, '0') : ''}`;
}

function currentCard(planning, block, now, slug) {
  const info = roleInfo(planning, block.role);
  const card = el('section', 'card now',
    el('h2', null, 'En ce moment'),
    el('p', 'role', roleLabel(info, slug)),
    el('p', 'meta', `jusqu'à ${formatTime(block.end)} · ${minutesLeft(block.end, now)}`));
  card.style.background = info.color;
  return card;
}

function nextCard(planning, block, withDay, slug) {
  const info = roleInfo(planning, block.role);
  const when = withDay ? dayLabel(planning, parisDate(block.start)) : '';
  const card = el('section', 'card next',
    el('h2', null, 'Ensuite'),
    el('p', 'role', roleLabel(info, slug)),
    el('p', 'meta', `à ${formatTime(block.start)}${when ? ' · ' + when : ''}`));
  card.style.borderLeftColor = info.color;
  return card;
}

const MESSAGES = {
  before: 'Le festival commence vendredi 23 octobre.',
  after: 'Le festival est terminé. Merci !',
  'off-day': 'Pas de service ce jour-là.',
  'not-started': 'Ta journée n\'a pas encore commencé.',
  'done-today': 'Ta journée est terminée. Merci !',
};

function timeline(planning, blocks, selectedDay, state, changed, slug) {
  const list = el('ol', 'timeline');
  const day = blocksOfDay(blocks, selectedDay);
  if (day.length === 0) {
    list.append(el('li', 'empty', 'Pas de service ce jour-là.'));
    return list;
  }
  for (const b of day) {
    const info = roleInfo(planning, b.role);
    const item = el('li', 'slot',
      el('span', 'slot-time', `${formatTime(b.start)}–${formatTime(b.end)}`),
      roleChip(planning, b.role, slug));
    item.style.borderLeftColor = info.color;
    if (state.current === b) item.classList.add('current');
    if (changed.has(b.start.toISOString())) item.classList.add('changed');
    if (b.role === 'Off') item.classList.add('quiet');
    list.append(item);
  }
  return list;
}

// ctx : { person, planning, blocks, state, selectedDay, now, onSelectDay, onChangePerson, extra }
export function renderHome(root, ctx) {
  const { person, planning, blocks, state, selectedDay, now } = ctx;
  const changed = ctx.changed ?? new Set();
  const top = el('header', 'top', el('h1', null, person.name));
  const change = el('button', 'link-btn', 'Changer');
  change.type = 'button';
  change.addEventListener('click', ctx.onChangePerson);
  const reminders = el('a', 'link-btn', 'Rappels');
  reminders.href = '#rappels';
  top.append(el('div', 'top-actions', reminders, change));

  const content = el('main', 'content');
  content.append(...(ctx.extra ?? []).filter(Boolean));
  if (state.current) content.append(currentCard(planning, state.current, now, person.slug));
  else content.append(el('p', 'message', MESSAGES[state.kind] ?? ''));
  if (state.next) content.append(nextCard(planning, state.next, state.kind === 'before' || state.kind === 'off-day' || state.kind === 'done-today', person.slug));

  const team = el('a', 'action secondary', 'Voir le planning complet');
  team.href = '#equipe';
  const roles = el('a', 'link-text', 'À quoi correspondent les rôles ?');
  roles.href = '#roles';
  content.append(team, roles);

  const tabs = el('nav', 'tabs');
  for (const d of planning.days) {
    const btn = el('button', 'tab', d.label.split(' ')[0]);
    btn.type = 'button';
    if (d.date === selectedDay) btn.classList.add('active');
    btn.addEventListener('click', () => ctx.onSelectDay(d.date));
    tabs.append(btn);
  }
  content.append(tabs, timeline(planning, blocks, selectedDay, state, changed, person.slug));
  root.replaceChildren(top, content);
}

function section(title, ...children) {
  return el('section', 'help', el('h2', null, title), ...children);
}

// Écran « Rappels » : calendrier du téléphone (abonnement / fichier) et alertes dans l'appli.
export function renderReminders(root, { slug, baseUrl, onBack }) {
  const calUrl = `${baseUrl}cal/${slug}.ics`;
  const back = el('button', 'link-btn', 'Retour');
  back.type = 'button';
  back.addEventListener('click', onBack);

  const platform = platformOf(navigator.userAgent);
  const subscribe = el('a', 'action', "S'abonner au calendrier");
  subscribe.href = calUrl.replace(/^https?:/, 'webcal:');
  // iOS : ouvrir le fichier propose « Ajouter au calendrier » ; l'attribut download l'enverrait dans Fichiers.
  const download = el('a', 'action secondary', platform === 'ios' ? 'Ouvrir le fichier (.ics)' : 'Télécharger le fichier (.ics)');
  download.href = calUrl;
  if (platform !== 'ios') download.download = `stunfest-${slug}.ics`;
  // Android (Chrome) ne gère pas webcal: : seul l'import du fichier fonctionne.
  const actions = platform === 'android' ? [download] : [subscribe, download];

  const alerts = [];
  if ('Notification' in window) {
    const labels = { granted: 'Alertes activées', denied: 'Alertes refusées' };
    const enable = el('button', 'action secondary', labels[Notification.permission] ?? 'Activer les alertes dans l\'appli');
    enable.type = 'button';
    enable.addEventListener('click', async () => {
      const result = await Notification.requestPermission();
      enable.textContent = result === 'granted' ? 'Alertes activées' : 'Alertes refusées';
    });
    alerts.push(enable);
  }

  root.replaceChildren(
    el('header', 'top', el('h1', null, 'Rappels'), back),
    el('main', 'content',
      section('Dans le calendrier du téléphone',
        el('p', null, 'Chaque affectation arrive dans ton calendrier avec un rappel 10 minutes avant, même écran verrouillé.'),
        ...actions,
        el('p', 'note', 'Abonnement : le calendrier se met à jour tout seul, mais le téléphone le rafraîchit avec un délai variable (de quelques dizaines de minutes à plusieurs heures).'),
        el('p', 'note', 'Android / Google Agenda : les calendriers auxquels on s\'abonne n\'envoient pas de rappel. Télécharge le fichier et importe-le. Après un changement de planning, supprime d\'abord le calendrier « Stunfest Indie » puis réimporte le fichier, sinon les anciens créneaux restent.')),
      section('Dans l\'appli',
        el('p', null, 'L\'appli t\'alerte 10 minutes avant ton prochain poste, mais seulement tant qu\'elle est ouverte.'),
        ...alerts,
        el('p', 'note', 'iPhone : ajoute d\'abord l\'appli à l\'écran d\'accueil (Partager > Sur l\'écran d\'accueil) pour pouvoir recevoir des notifications.'))),
  );
}

// Page annexe « Rôles » : à quoi correspond chaque poste.
export function renderRoles(root, { planning, onBack }) {
  const back = el('button', 'link-btn', 'Retour');
  back.type = 'button';
  back.addEventListener('click', onBack);
  const list = Object.values(planning.roles).map((info) => {
    const chip = el('span', 'chip', info.label);
    chip.style.background = info.color;
    return el('section', 'help', chip, el('p', null, info.description));
  });
  root.replaceChildren(
    el('header', 'top', el('h1', null, 'Les rôles'), back),
    el('main', 'content', ...list),
  );
}
