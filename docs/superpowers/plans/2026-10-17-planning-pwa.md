# Planning Stunfest 2026 — PWA bénévoles : plan d'implémentation

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Une PWA statique sur GitHub Pages où chaque bénévole du pôle Indie choisit son prénom et voit son poste en cours, le suivant et sa journée, avec rappels 10 minutes avant via calendrier (`.ics`) et alertes dans l'appli.

**Architecture:** Les scripts Python existants produisent `schedule.json` ; un nouveau `build_site.py` en tire `site/data/planning.json` (blocs d'affectation datés, fuseau Paris) et un `.ics` par personne. Le dossier `site/` est une PWA en JS sans framework (modules ES) qui recharge `planning.json` régulièrement, calcule « en ce moment / ensuite » côté client et se déploie via GitHub Actions. Aucune dépendance serveur.

**Tech Stack:** Python 3 (`openpyxl`, `zoneinfo` + `tzdata`, `pytest`, `Pillow` pour les icônes), JavaScript ES modules, `node --test`, GitHub Pages + GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-10-17-planning-pwa-design.md`

## Global Constraints

- Seulement des fichiers statiques sur GitHub Pages ; aucun serveur, aucun Web Push, aucun service tiers.
- Site servi sous `https://feoche.github.io/stun-indie-planning/` : tous les chemins (manifeste, service worker, données, `.ics`, `webcal://`) sont relatifs.
- Fuseau **Europe/Paris** fixé dans les données, jamais celui de l'appareil. Attention : le changement d'heure a lieu le dimanche 25 octobre 2026 à 3h (+02:00 vendredi et samedi, +01:00 dimanche).
- Uniquement des prénoms (aucun contact). Interface en français uniquement.
- Rappel calendrier : `VALARM` `TRIGGER:-PT10M` ; planning mis à jour environ une minute après publication.
- Mobile d'abord ; couleurs des postes reprises de `ROLE_COLORS` de `make_xlsx2.py`.
- La validation « max 2h consécutives hors dérogations » doit continuer à afficher `issues hors dérogations: []`.
- Flux de l'utilisateur : relancer les scripts Python, puis commit et push sur `git@github.com:feoche/stun-indie-planning.git` (branche `main`). Le push a échoué par SSH (`Permission denied (publickey)`) : ne pas le contourner, demander à l'utilisateur de régler l'accès.

## Review Focus

1. **Changement d'heure du dimanche 25 octobre** : les blocs du dimanche portent `+01:00`, les rappels `.ics` (UTC) et « en ce moment » restent justes.
2. **Appareil dans un autre fuseau** (téléphone réglé sur UTC, Londres…) : poste en cours et heures affichées restent ceux de Paris.
3. **Cache périmé** : `planning.json` n'est jamais servi depuis un cache HTTP/SW périmé quand le réseau marche ; hors-ligne, la dernière version s'affiche avec une mention « hors-ligne » et sans erreur.
4. **Bords de journée et absences** : instant exactement égal à la fin d'un bloc, avant l'arrivée, après la dernière affectation, bénévole absent ce jour-là (Robin le vendredi), avant/après le festival.
5. **Prénom mémorisé disparu du planning** (ou stockage indisponible) : retour à la liste de choix sans plantage ; textes `.ics` avec accents, virgules et lignes longues correctement échappés/repliés.

---

### Task 1: Règles du planning (Jeff 11h–22h, briefing du vendredi)

**Files:**
- Modify: `build_schedule6.py`
- Create: `tests/test_schedule.py`, `pytest.ini` (`[pytest]` / `pythonpath = .`), `requirements.txt` (`openpyxl`, `tzdata`, `pytest`, `Pillow`)

**Interfaces:**
- Produces: `DAYS[day]['late']` devient `list[tuple[str, int, int]]` (nom, heure d'arrivée, heure de fin) ; `DAYS['Vendredi 23 octobre']['briefing_slot'] = 2` ; nouveau rôle `'Briefing'` ; `find_issues(all_sched: dict) -> list` (logique de validation extraite du `__main__`) ; `build_day(day, cfg) -> dict[int, dict[str, str]]`. Les trois jours ont 26 créneaux (idx 0 = 9h00 … 25 = 21h30).

- [ ] **Step 1: Écrire `tests/test_schedule.py`** avec `sched = {d: build_day(d, c) for d, c in DAYS.items()}` et ces tests :
  - `test_all_days_have_26_slots` : `len(sched[day]) == 26`.
  - `test_jeff_present_11h_to_22h_all_days` : `Jeff` vaut `''` (ou absent) aux idx 0–3 et est dans `{'Run','Awards'}` aux idx 4–25, pour les 3 jours.
  - `test_jeff_awards_only_saturday_1830_2030` : samedi idx 19–23 = `'Awards'`, autres idx de Jeff = `'Run'` ; vendredi et dimanche jamais `'Awards'`.
  - `test_friday_briefing_10h` : vendredi idx 2 = `'Briefing'` pour François, Étienne, Florent, Arthur, Mael, Gabriel, Lylou, Suliac et Chris ; Jeff vide ; aucun `'Briefing'` ailleurs (autres idx, autres jours).
  - `test_team_leaves_after_1930` : vendredi et dimanche idx 21–25, samedi idx 24–25 : toute personne autre que Jeff est `''`/absente ; samedi idx 23 : Robin = `'Awards'` ou `'Backup'`.
  - `test_no_rotation_violation` : `find_issues(sched) == []`.
  - `test_run_rotation_unchanged_by_jeff` : vendredi idx 10 (hors Jeff et Chris) compte exactement 2 `'Run'` (Jeff vient en plus des 2 Run de rotation, comme après 20h auparavant ; choix de l'assistant).
- [ ] **Step 2: Lancer** `python -m pytest tests/test_schedule.py -v`. Attendu : FAIL (`find_issues` absent, Jeff à 20h).
- [ ] **Step 3: Implémenter dans `build_schedule6.py`** : Jeff `('Jeff', 11, 22)` les 3 jours ; `day_n_slots = slot_index(22, 0)` (max des fins de `late`) ; pour idx ≥ fin de l'équipe (`max(base_end_slots, awards end+1)`), la ligne ne contient que les personnes de `late` (Run, ou `''` avant leur arrivée) ; au créneau `briefing_slot`, tous les `full_day` et Chris valent `'Briefing'` (la branche préparation existante ne s'applique pas à ce créneau) ; extraire `find_issues`. Mettre à jour la docstring (rôle Briefing).
- [ ] **Step 4: Lancer** les tests (PASS) puis `python build_schedule6.py` : doit afficher `issues hors dérogations: []` et régénérer `schedule.json`.
- [ ] **Step 5: Commit** `git add -A && git commit -m "Planning: Jeff 11h-22h, briefing du vendredi 10h"`.

### Task 2: Excel, rôles partagés et documents à jour

**Files:**
- Create: `roles.py`, `tests/test_xlsx.py`
- Modify: `make_xlsx2.py`, `Document_Temps_forts_Roles_Evenements.md`, `CLAUDE.md`

**Interfaces:**
- Produces: `roles.py` avec `ROLE_LABELS: dict[str,str]` et `ROLE_COLORS: dict[str,str]` (hex sans `#`, valeurs actuelles de `make_xlsx2.py` + `'Briefing': '827717'`, `'Briefing'` → `'Briefing'`) et `SITE_LABELS = {**ROLE_LABELS, 'Pause': 'Pause'}` (l'appli distingue Pause d'Off).

- [ ] **Step 1: Écrire `tests/test_xlsx.py`** : lance `python make_xlsx2.py` (subprocess), ouvre le classeur avec `openpyxl`, vérifie `test_friday_sheet_has_jeff_column` (ligne d'en-tête 2 du vendredi contient `Jeff`) et `test_friday_briefing_cell` (cellule du créneau 10h00 pour François = `'Briefing'`).
- [ ] **Step 2: Lancer** le test : FAIL.
- [ ] **Step 3: Implémenter** : `roles.py` extrait ; `make_xlsx2.py` l'importe ; Jeff ajouté au vendredi dans `DAY_PERSONS` ; légende `Briefing` ; notes mises à jour (« Jeff : présent les 3 jours de 11h à 22h », briefing du vendredi 10h–10h30, samedi jusqu'à 21h pour l'équipe et 22h pour Jeff).
- [ ] **Step 4: Mettre à jour** `Document_Temps_forts_Roles_Evenements.md` (Jeff, briefing, rôle Briefing) et `CLAUDE.md` (règles métier, usage : `python build_schedule6.py && python make_xlsx2.py && python build_site.py`, mention du dossier `site/`).
- [ ] **Step 5: Tests PASS**, régénérer `Planning_Stunfest2026_Indie.xlsx`, commit.

### Task 3: `build_site.py` — `planning.json`

**Files:**
- Create: `build_site.py`, `tests/test_build_site.py`

**Interfaces:**
- Consumes: `schedule.json` (jour → idx → personne → rôle), `roles.SITE_LABELS`, `roles.ROLE_COLORS`.
- Produces :
  - `@dataclass(frozen=True) class Block: start: datetime; end: datetime; role: str`
  - `slugify(name: str) -> str` (sans accents, minuscules : `François` → `francois`)
  - `slot_start(day: str, idx: int) -> datetime` (aware, `ZoneInfo('Europe/Paris')` ; dates 2026-10-23/24/25)
  - `person_blocks(schedule: dict, person: str) -> list[Block]` (créneaux consécutifs de même rôle fusionnés, `''` ignoré, `Off` et `Pause` conservés, triés)
  - `build_planning(schedule: dict, generated_at: datetime) -> dict`, forme exacte :
    `{"version": sha1(contenu sans generatedAt)[:12], "generatedAt": iso, "timezone": "Europe/Paris", "days": [{"date": "2026-10-23", "label": "Vendredi 23 octobre"}, …], "roles": {"Run": {"label": "Run", "color": "#1565C0"}, …}, "people": [{"name": "François", "slug": "francois", "blocks": [{"start": iso+offset, "end": iso+offset, "role": "Run"}]}]}` ; personnes triées par slug.
  - `write_site(schedule_path: str, out_dir: str, generated_at: datetime) -> None` écrit `out_dir/data/planning.json` (UTF-8, `ensure_ascii=False`).

- [ ] **Step 1: Écrire les tests** : `test_slugify` (`François`→`francois`, `Étienne`→`etienne`) ; `test_slot_start_paris_offset` (`slot_start('Vendredi 23 octobre', 0).isoformat() == '2026-10-23T09:00:00+02:00'`, dimanche idx 0 → `'2026-10-25T09:00:00+01:00'`) ; `test_jeff_friday_single_block` (un bloc `11:00→22:00`, `Run`, vendredi) ; `test_absent_person_has_no_blocks_that_day` (Robin : aucun bloc le 23) ; `test_blocks_sorted_and_not_overlapping` pour tout le monde ; `test_version_depends_on_content_only` (même planning avec deux `generated_at` → même `version` ; un rôle modifié → `version` différente) ; `test_planning_shape` (clés `version, generatedAt, timezone, days, roles, people`, 3 jours, `Pause` et `Briefing` présents dans `roles`).
- [ ] **Step 2: Lancer** `python -m pytest tests/test_build_site.py -v` : FAIL.
- [ ] **Step 3: Implémenter** avec `zoneinfo` (ajouter `tzdata` aux prérequis Windows). Fusion : parcourir les idx dans l'ordre, prolonger le bloc tant que le rôle est identique.
- [ ] **Step 4: Tests PASS**, commit.

### Task 4: `build_site.py` — fichiers `.ics`

**Files:**
- Modify: `build_site.py`, `tests/test_build_site.py`

**Interfaces:**
- Produces : `ics_escape(text: str) -> str` (`\\`, `;`, `,`, retours à la ligne) ; `fold_line(line: str) -> str` (repli RFC 5545, ≤ 75 octets par ligne physique, jamais au milieu d'un caractère UTF-8) ; `build_ics(person: str, slug: str, blocks: list[Block], generated_at: datetime) -> str` ; `write_site` écrit aussi `out_dir/cal/<slug>.ics` ; ajout d'un `__main__` : `python build_site.py` lit `schedule.json` et écrit dans `site/`.

- [ ] **Step 1: Écrire les tests** : `test_ics_one_event_and_alarm_per_non_off_block` (nombre de `BEGIN:VEVENT` = nombre de `BEGIN:VALARM` = blocs non-`Off`, `TRIGGER:-PT10M` présent, `Off` exclu, `Pause` et `Briefing` inclus) ; `test_ics_times_utc_and_dst` (vendredi 09h Paris → `DTSTART:20261023T070000Z`, dimanche 09h Paris → `DTSTART:20261025T080000Z`) ; `test_ics_crlf_and_line_length` (séparateur `\r\n`, toute ligne ≤ 75 octets) ; `test_fold_line_roundtrip` (`fold_line('X:' + 'é'*100)` : lignes ≤ 75 octets, dépliage identique) ; `test_ics_escape` (`ics_escape('a,b;c\nd')` == `'a\\,b\\;c\\nd'`) ; `test_ics_uid_stable` (même UID `francois-20261023-0900@stun-indie-planning` sur deux générations avec `generated_at` différents) ; `test_ics_calendar_headers` (`X-WR-CALNAME:Stunfest Indie`, `REFRESH-INTERVAL;VALUE=DURATION:PT15M`, `X-PUBLISHED-TTL:PT15M`, `METHOD` absent).
- [ ] **Step 2: Lancer** : FAIL.
- [ ] **Step 3: Implémenter.** `SUMMARY` = `"<label> — Stunfest Indie"` ; `DESCRIPTION` = plage horaire ; `DTSTAMP` = `generated_at` en UTC.
- [ ] **Step 4: Tests PASS** puis `python build_site.py` : vérifier que `site/data/planning.json` et 11 fichiers `site/cal/*.ics` existent ; commit (données générées incluses).

### Task 5: `model.js` — logique pure côté client

**Files:**
- Create: `package.json` (`{"private": true, "type": "module", "scripts": {"test:js": "node --test tests/js"}}`), `site/js/model.js`, `tests/js/model.test.mjs`

**Interfaces:**
- Produces (toutes pures, sans accès au DOM) :
  - `REMINDER_LEAD_MS = 600000`
  - `parseBlocks(person) -> {start: Date, end: Date, role: string}[]`
  - `findPerson(planning, slug) -> person | null`
  - `parisDate(date: Date) -> 'YYYY-MM-DD'`, `formatTime(date: Date) -> '9h00' | '10h30'` (toujours `Europe/Paris` via `Intl`)
  - `blocksOfDay(blocks, dateStr) -> blocks`
  - `homeState(blocks, days, now) -> {kind: 'before'|'after'|'off-day'|'not-started'|'active'|'done-today', current: Block|null, next: Block|null}` ; `next` = bloc immédiatement suivant (Off/Pause compris) ; instant == fin d'un bloc ⇒ ce bloc n'est plus courant.
  - `blockKey(slug, block) -> '<slug>|<startISO>|<role>'`
  - `dueReminder(blocks, slug, now, fired: Set<string>) -> {block, key} | null` : premier bloc non-`Off` tel que `start - 10 min <= now < start` et clé absente de `fired`.
  - `changedBlocks(oldBlocks, newBlocks) -> Set<string>` des `start` ISO des blocs nouveaux ou modifiés.

- [ ] **Step 1: Vérifier** `node --version` (Node 20+). S'il manque, le dire à l'utilisateur.
- [ ] **Step 2: Écrire `tests/js/model.test.mjs`** (`node:test`, `assert/strict`) : `before` (now = 2026-10-22T12:00Z) ; `not-started` (vendredi 08:59 Paris = `2026-10-23T06:59:00Z`, `next` = premier bloc) ; `active` avec `current`/`next` ; `bloc se termine pile à now` ⇒ `current` = bloc suivant ; `off-day` (Robin le vendredi 12:00) ; `done-today` (dimanche après sa dernière fin) ; `after` (2026-10-26) ; `DST` (bloc `2026-10-25T09:00:00+01:00`, now = `2026-10-25T08:00:00Z` ⇒ courant ; `formatTime(new Date('2026-10-25T08:00:00Z')) === '9h00'` et `formatTime(new Date('2026-10-23T07:00:00Z')) === '9h00'`) ; `dueReminder` : renvoie à 09:50:00 pour un bloc de 10:00, `null` à 09:49:59, `null` à 10:00:00, `null` si clé déjà dans `fired`, ignore `Off` ; `changedBlocks` marque un bloc déplacé et pas un bloc identique ; `findPerson` renvoie `null` pour un slug inconnu.
- [ ] **Step 3: Lancer** `npm run test:js` : FAIL.
- [ ] **Step 4: Implémenter.** Puis relancer les tests dans deux fuseaux (`$env:TZ='UTC'` puis `$env:TZ='Pacific/Auckland'` en PowerShell) : PASS dans les deux.
- [ ] **Step 5: Commit.**

### Task 6: Coquille de l'appli — choix du prénom, accueil, journées

**Files:**
- Create: `site/index.html`, `site/style.css`, `site/js/app.js`, `site/js/render.js`, `site/js/store.js`

**Interfaces:**
- Consumes: `model.js` (`parseBlocks`, `findPerson`, `homeState`, `blocksOfDay`, `formatTime`, `parisDate`).
- Produces :
  - `store.js` : `getSlug() -> string|null`, `setSlug(slug)`, `clearSlug()`, `getFired() -> Set<string>`, `addFired(key)`, `getSeen() -> {version, blocks}|null`, `setSeen(seen)` ; clés `stunindie.person`, `stunindie.fired`, `stunindie.seen` ; tout accès protégé par `try/catch` (stockage indisponible = comportement en mémoire).
  - `render.js` : `renderPicker(root, people, onPick)`, `renderHome(root, {person, planning, state, selectedDay, changed, now, status})`.
  - `app.js` : charge `./data/planning.json`, lit `?now=<ISO>` pour simuler l'heure (outil de test), affiche le sélecteur si pas de prénom ou `findPerson` renvoie `null`.

- [ ] **Step 1: Implémenter** : sélecteur plein écran (prénoms triés, boutons ≥ 48 px) ; en-tête avec prénom et bouton « Changer » ; carte « En ce moment » (poste en couleur, heure de fin, temps restant) ; carte « Ensuite » ; messages des états `before` (« Le festival commence vendredi à 9h »), `after`, `off-day` (« Pas de service ce jour-là »), `not-started`, `done-today` ; onglets Vendredi/Samedi/Dimanche (jour courant par défaut pendant le festival, sinon vendredi) ; chronologie des blocs du jour (dont Off/Pause), le bloc en cours en évidence ; texte inséré via `textContent` uniquement. CSS mobile d'abord (largeur max 480 px, texte ≥ 16 px).
- [ ] **Step 2: Vérifier** avec `python -m http.server 8000 -d site`, dans Chrome (viewport 375×667) : `?now=2026-10-24T14:10:00%2B02:00` pour un prénom donné affiche le bon poste (comparer à `schedule.json`) ; pas de défilement horizontal ; Robin avec `?now=2026-10-23T12:00:00%2B02:00` affiche « Pas de service ce jour-là » ; effacer le prénom stocké ou en stocker un inconnu ramène au sélecteur sans erreur console.
- [ ] **Step 3: Commit.**

### Task 7: Rechargement du planning et bannière de mise à jour

**Files:**
- Create: `site/js/data.js`, `tests/js/data.test.mjs`
- Modify: `site/js/app.js`, `site/js/render.js`

**Interfaces:**
- Produces : `createPlanningSource({url, intervalMs = 60000, fetchFn = fetch, onUpdate, onStatus}) -> {start(), stop(), pollNow() -> Promise<void>}` ; `onUpdate(planning)` appelé seulement quand `version` change (et au premier chargement) ; `onStatus('online'|'offline')`.

- [ ] **Step 1: Écrire `tests/js/data.test.mjs`** avec un faux `fetchFn` : `poll utilise cache: 'no-store'` ; `onUpdate` appelé une fois si la `version` ne change pas entre deux polls, deux fois si elle change ; `échec réseau` ⇒ `onStatus('offline')`, aucune exception, planning précédent conservé ; le poll suivant réussi ⇒ `onStatus('online')`.
- [ ] **Step 2: Lancer** : FAIL.
- [ ] **Step 3: Implémenter** `data.js` ; dans `app.js`, brancher `pollNow()` sur `visibilitychange` (retour au premier plan) et l'intervalle de 60 s. Comparer avec `getSeen()` : si la `version` diffère et que les blocs de la personne ont changé, afficher la bannière « Planning mis à jour » avec `changedBlocks` mis en évidence ; fermer la bannière appelle `setSeen`. Indicateur « Planning mis à jour à HH:MM » et mention « hors-ligne ».
- [ ] **Step 4: Tests PASS** ; vérification manuelle : modifier un rôle dans `site/data/planning.json` pendant que la page tourne ⇒ bannière en moins de 60 s avec le créneau surligné ; couper le serveur ⇒ mention hors-ligne, l'écran reste affiché.
- [ ] **Step 5: Commit.**

### Task 8: Alertes dans l'appli et écran « Rappels »

**Files:**
- Create: `site/js/reminders.js`, `tests/js/reminders.test.mjs`
- Modify: `site/js/app.js`, `site/js/render.js`, `site/style.css`

**Interfaces:**
- Consumes: `dueReminder`, `blockKey`, `store.addFired`.
- Produces : `checkReminders({blocks, slug, now, fired, notify, markFired}) -> void` (pure, injectée) ; `startReminders({getBlocks, getSlug, nowFn, notify, intervalMs = 15000}) -> {stop()}` ; `renderReminders(root, {slug, baseUrl})`, route `#rappels`.

- [ ] **Step 1: Écrire `tests/js/reminders.test.mjs`** : `notify` appelé une fois pour un bloc dû, pas une seconde fois après `markFired` ; non appelé pour un bloc `Off` ; non appelé hors fenêtre de 10 min.
- [ ] **Step 2: Lancer** : FAIL.
- [ ] **Step 3: Implémenter.** `notify` = bannière dans l'appli + `navigator.vibrate` si dispo + `registration.showNotification` si `Notification.permission === 'granted'`. Vérification immédiate au retour au premier plan. Écran Rappels : lien « S'abonner » (`webcal://` + chemin `cal/<slug>.ics` déduit de `location`), bouton « Télécharger » (même fichier), bouton « Activer les alertes dans l'appli » (`Notification.requestPermission()` déclenché par clic uniquement), et explication en français qui doit dire : le téléphone rafraîchit l'abonnement avec un délai variable ; Google Agenda ignore les rappels des calendriers abonnés, donc sur Android importer le fichier et le réimporter après un changement ; les alertes dans l'appli ne sonnent que si elle est ouverte ; sur iPhone, installer l'appli sur l'écran d'accueil pour les notifications.
- [ ] **Step 4: Tests PASS** ; vérification manuelle avec `?now=…T09:49:50…` : bannière d'alerte à 9h50 pour un bloc de 10h00, pas de doublon après rechargement.
- [ ] **Step 5: Commit.**

### Task 9: PWA — manifeste, service worker, icônes

**Files:**
- Create: `site/manifest.webmanifest`, `site/sw.js`, `site/icons/icon-192.png`, `site/icons/icon-512.png`, `site/icons/apple-touch-icon.png` (180 px), `tools/make_icons.py`
- Modify: `site/index.html`, `site/js/app.js`

**Interfaces:**
- Produces : manifeste (`name` « Stunfest Indie », `short_name` « Stun Indie », `start_url` `./`, `scope` `./`, `display` `standalone`, `lang` `fr`, icônes 192/512 dont une `maskable`) ; `sw.js` : coquille (HTML, CSS, JS, icônes, manifeste) en stale-while-revalidate dans un cache versionné, `data/planning.json` et `cal/*` en réseau d'abord avec `cache: 'no-store'` et repli sur le cache, anciens caches supprimés à l'activation, `skipWaiting` + `clients.claim` ; enregistrement par `navigator.serviceWorker.register('./sw.js')`.

- [ ] **Step 1: Générer les icônes** avec `tools/make_icons.py` (Pillow, design libre : fond noir, « S » ou « Indie » en blanc, marge de sécurité pour la version maskable).
- [ ] **Step 2: Implémenter** manifeste, `sw.js`, balises `<link rel="manifest">`, `apple-touch-icon`, `theme-color`, `viewport`.
- [ ] **Step 3: Vérifier** dans Chrome via `http://localhost:8000` : DevTools > Application affiche manifeste valide et SW actif ; cocher « Offline » et recharger : l'accueil s'affiche avec le dernier planning et la mention « hors-ligne » ; modifier `planning.json`, remettre en ligne : la nouvelle version apparaît sans vider le cache à la main.
- [ ] **Step 4: Commit.**

### Task 10: Déploiement GitHub Pages et publication

**Files:**
- Create: `.github/workflows/pages.yml`
- Modify: `CLAUDE.md`

- [ ] **Step 1: Écrire le workflow** : déclenché sur `push` vers `main` (filtre `site/**` et déclenchement manuel), permissions `pages: write` et `id-token: write`, étapes `actions/checkout`, `actions/configure-pages`, `actions/upload-pages-artifact` avec `path: site`, `actions/deploy-pages`.
- [ ] **Step 2: Documenter** dans `CLAUDE.md` le flux de mise à jour (relancer les trois scripts, commit, push ; la mise à jour est visible au bout d'environ une minute) et le réglage unique à faire par l'utilisateur : dépôt > Settings > Pages > Source = « GitHub Actions ».
- [ ] **Step 3: Lancer toute la suite** : `python -m pytest -v` et `npm run test:js` : tout PASS.
- [ ] **Step 4: Commit puis `git push -u origin main`.** Si le push échoue encore par SSH, s'arrêter et demander à l'utilisateur de régler l'accès (clé SSH ajoutée à GitHub, ou URL HTTPS avec `gh auth login`).
- [ ] **Step 5: Vérifier** après déploiement : `https://feoche.github.io/stun-indie-planning/` charge, `data/planning.json` et `cal/francois.ics` répondent 200, les icônes sont servies.

### Task 11: Vérification sur appareils (avant le festival)

**Files:** aucun (liste de contrôle, résultats à rapporter à l'utilisateur).

- [ ] **Step 1: iPhone** : ajouter à l'écran d'accueil, choisir un prénom, s'abonner via `webcal://`, vérifier que les événements portent un rappel 10 minutes ; accorder les alertes et vérifier la bannière avec `?now=`.
- [ ] **Step 2: Android** : installer la PWA, importer le `.ics` dans Google Agenda, vérifier le rappel ; confirmer que l'abonnement ne donne pas de rappel (texte d'aide à ajuster si le constat diffère).
- [ ] **Step 3: Publication réelle** : modifier un créneau, relancer les scripts, pousser ; la bannière « Planning mis à jour » doit apparaître sur les deux téléphones en environ 1 à 2 minutes.
- [ ] **Step 4: Rapporter** ce qui marche et ce qui ne marche pas, sans rien arrondir.
