# Planning bénévolat Stunfest 2026 — pôle Indie

Projet exporté depuis une conversation Claude.ai. Objectif : planning visuel (Excel coloré) des bénévoles du pôle Indie pour les 3 jours du Stunfest (23, 24, 25 octobre 2026), plus un document d'accompagnement.

## Fichiers
- `build_schedule6.py` : génère `schedule.json` (créneaux de 30 min, rôles par personne). Source de vérité des règles métier.
- `make_xlsx2.py` : lit `schedule.json` et produit `Planning_Stunfest2026_Indie.xlsx` (un onglet par jour, colonnes = personnes, lignes = créneaux, couleurs par poste, légende et notes).
- `schedule.json`, `Planning_Stunfest2026_Indie.xlsx` : sorties actuelles.
- `Document_Temps_forts_Roles_Evenements.md` : version Markdown du document (la version en ligne a été éditée dans Claude Docs : https://claude.ai/code/artifact/bfbee688-4a61-448c-b12a-b69b46b4897b).

Usage : `python build_schedule6.py && python make_xlsx2.py && python build_site.py` (dépendance : openpyxl). Les chemins sont relatifs au dossier des scripts.

## Règles métier (toutes implémentées)
- Créneaux de 30 min, début à 9h00. Tout le monde finit à 20h tous les jours (décidé le 2026-10-18). La zone Indé ferme à 19h30 : de 19h30 à 20h, rangement, tout le monde en Run (Chris en Média) ; le samedi, les Awards occupent ce dernier créneau.
- Ouverture au public : vendredi 14h, samedi et dimanche 10h. Bénévoles présents dès 9h pour la préparation (tout le monde en Run : vendredi 9h-14h, samedi/dimanche 9h-10h). Fermeture de la zone Indé à 19h30 tous les soirs.
- Postes (libellé Excel) : Backup = « Standiers » (ex-Back-up standiers Indie), Run (IC volant : espaces indés + renfort freeplay), Stand = « Stand IC » (Stand IC / Stunjam), Awards, Média (Chris), Off (inclut les pauses repas).
- Préférence pour 1h sur un même poste plutôt que 30 min (2026-10-22, `HALF_STINT_BONUS`), et varier le poste d'un passage à l'autre (`REPEAT_PENALTY`). Les passages de 30 min restants sont imposés par les horaires : bords des fenêtres repas, clôture de 19h30, Awards.
- Max 2h consécutives sur un même poste. Dérogations explicites : préparation du vendredi matin (tout le monde en Run), Standiers fixes pendant les Awards (2h30, sans rotation).
- Repas : 30 min déjeuner (fenêtre 11h30-14h) + 30 min dîner (fenêtre 18h30-20h) par personne, affichés en « Off » (le rôle « Pause » n'existe plus). Voir « Repas » ci-dessous.
- Équipe (11) : François, Chris, Étienne, Florent, Arthur, Mael, Gabriel, Lylou, Robin (samedi et dimanche seulement), Suliac, Jeff (3 jours, de 11h à 20h, dans la rotation comme les autres ; seul en Run après la fermeture).
- Indisponibilités ponctuelles (clé `away` de `DAYS`, 2026-10-22) : Arthur Off samedi 18h-18h30 et dimanche 12h-13h30 (il déjeune pendant son absence).
- Chris : captation Média en continu les 3 jours (hors rotation), pause repas alignée.
- 2 personnes en Run, sauf aux horaires de repas (voir ci-dessous) ; le renfort à 3 le samedi pour le jury des Awards a été abandonné.
- Horaires de repas (2026-10-18) : plus aucun Run. Les places de Run passent en Standiers : jusqu'à 5 Standiers + 1 Stand IC, ceux qui mangent ou qui atteindraient 2h consécutives sont en Off. Hors vendredi midi (préparation, tout le monde en Run) et hors clôture 19h30-20h (tout le monde en Run).
- Indie Awards (samedi 18h30-20h, tronqués à la fin de journée ; la cérémonie prévoyait jusqu'à 20h30, à confirmer) : 2 personnes fixes restent en Standiers sur toute la durée ; le reste de l'équipe (Jeff dès 18h30 inclus) est sur Awards ; Chris reste en Média.

## Points ouverts
- Le rôle « Vote public » a été supprimé (2026-10-18) : le Run vérifie que les postes de vote du public fonctionnent et que les stands 1 jour sont bien installés.
- Le script valide l'absence de dépassement des 2h consécutives hors dérogations (affiche `issues hors dérogations: []`). À conserver à chaque modification.

## Mises à jour décidées (2026-10-17)
- Jeff : présent les 3 jours de 11h à 20h, dans la rotation (Standiers / Run / Stand IC, pauses repas comprises) depuis le 2026-10-18 ; sur Awards dès 18h30 le samedi.
- Briefing vendredi 10h00-10h30 (toute l'équipe, Chris compris, sans Jeff).
- `roles.py` : libellés et couleurs partagés Excel / site. `site/` : PWA publiée sur GitHub Pages (spec : `docs/superpowers/specs/`, plan : `docs/superpowers/plans/`).

## Publier une mise à jour du planning
1. Modifier les règles dans `build_schedule6.py`, puis `python build_schedule6.py && python make_xlsx2.py && python build_site.py`.
2. `git add -A && git commit -m "Planning: ..." && git push` sur `main` : le workflow `.github/workflows/pages.yml` déploie `site/` (visible après environ une minute).
3. Les bénévoles voient la bannière « Planning mis à jour » à la prochaine ouverture ou dans la minute si l'appli est ouverte.

## Modifications depuis le téléphone pendant le festival (Claude Code web / appli mobile)
François pilote les changements depuis son téléphone (session cloud, `CLAUDE_CODE_REMOTE=true`). Pour chaque demande :
1. Dépendances si besoin : `pip install -r requirements.txt`.
2. Appliquer la demande dans `build_schedule6.py` (absences ponctuelles : clé `away` de `DAYS`), puis `python build_schedule6.py && python make_xlsx2.py && python build_site.py`.
3. `python -m pytest -q && npm run test:js` : tout doit passer et le script doit afficher `issues hors dérogations: []`. Sinon, ne rien publier et expliquer le blocage.
4. Commiter (`Planning: ...`) et pousser directement sur `main`, sans branche `claude/` ni PR : c'est ce qui publie le site. Si le push sur `main` est refusé, le dire et donner le lien de la branche poussée.
5. Répondre court (lecture sur téléphone) : qui change de poste, quand, et la confirmation que c'est publié.
- Site : https://feoche.github.io/stun-indie-planning/ (réglage unique : Settings > Pages > Source = GitHub Actions, fait).
- Tests : `python -m pytest` et `npm run test:js` ; test local : `python -m http.server 8000 -d site`, puis `?now=2026-10-24T14:10:00%2B02:00` pour simuler l'heure.
- Si un fichier de `site/js` ou `site/*.css` change de façon incompatible, incrémenter `SHELL_CACHE` dans `site/sw.js`.
- Repas (2026-10-18) : fenêtres 11h30-14h et 18h30-20h (pas de repas pendant le rangement de 19h30), 30 min par personne, étalés sur toute la fenêtre par groupes d'au moins 3 personnes en Off ensemble (déjeuner : 11h30, 12h30, 13h30 ; dîner vendredi/dimanche : 18h30 et 19h00 ; dîner samedi : 18h30, 19h00 et 19h30). Vendredi : le déjeuner a lieu pendant la préparation. Samedi : le dîner a lieu pendant les Awards (hypothèse, à confirmer) ; les 2 Standiers fixes mangent ensemble à 19h30, remplacés sur l'accueil par 2 personnes des Awards. Tout le monde mange midi et soir (testé). Chris (Média, libre de ses horaires) mange lui aussi dans un groupe d'au moins 3 personnes en Off et reste en Média le reste du temps. Garde-fous : `tests/test_schedule.py`.
- Appli : bouton « Voir le planning complet » (route `#equipe`, `site/js/team.js`) : qui est où maintenant + grille du jour par personne.
- Page « Rôles » (`#roles`) : définitions dans `roles.py` (ROLE_DESCRIPTIONS, ROLE_ORDER), publiées dans planning.json ; liens depuis l'accueil et le planning complet.
- Easter egg : dans la vue personnelle de Florent (accueil, chronologie, alertes) tous les postes ont le suffixe « Chapeau » (UI seulement, `roleLabel` dans model.js ; ni .ics, ni planning complet, ni page Rôles).
- Vendredi avant 14h, le Run s'appelle « Installation » (rôle dédié, `roles.py`).
