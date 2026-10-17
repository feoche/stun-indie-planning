# Planning bénévolat Stunfest 2026 — pôle Indie

Projet exporté depuis une conversation Claude.ai. Objectif : planning visuel (Excel coloré) des bénévoles du pôle Indie pour les 3 jours du Stunfest (23, 24, 25 octobre 2026), plus un document d'accompagnement.

## Fichiers
- `build_schedule6.py` : génère `schedule.json` (créneaux de 30 min, rôles par personne). Source de vérité des règles métier.
- `make_xlsx2.py` : lit `schedule.json` et produit `Planning_Stunfest2026_Indie.xlsx` (un onglet par jour, colonnes = personnes, lignes = créneaux, couleurs par poste, légende et notes).
- `schedule.json`, `Planning_Stunfest2026_Indie.xlsx` : sorties actuelles.
- `Document_Temps_forts_Roles_Evenements.md` : version Markdown du document (la version en ligne a été éditée dans Claude Docs : https://claude.ai/code/artifact/bfbee688-4a61-448c-b12a-b69b46b4897b).

Usage : `python build_schedule6.py && python make_xlsx2.py && python build_site.py` (dépendance : openpyxl). Les chemins sont relatifs au dossier des scripts.

## Règles métier (toutes implémentées)
- Créneaux de 30 min, début à 9h00. Fin à 19h30 chaque soir ; le samedi va jusqu'à 21h pour afficher les Indie Awards en entier.
- Ouverture au public : vendredi 14h, samedi et dimanche 10h. Bénévoles présents dès 9h pour la préparation (tout le monde en Run : vendredi 9h-14h, samedi/dimanche 9h-10h). Fermeture de la zone Indé à 19h30 tous les soirs.
- Postes (libellé Excel) : Backup = « Standiers » (ex-Back-up standiers Indie), Run (IC volant), Stand = « Stand IC » (Stand IC / Stunjam), Vote public (~30 min/jour), Awards, Média (Chris), Off (inclut les pauses repas).
- Max 2h consécutives sur un même poste. Dérogations explicites : préparation du vendredi matin (tout le monde en Run), Jeff en Run continu, Standiers fixes pendant les Awards (2h30, sans rotation).
- Pauses : 30 min déjeuner (12h00 ou 13h30) + 30 min dîner (19h00 ou 20h30) par personne, affichées en « Off ».
- Équipe (11) : François, Chris, Étienne, Florent, Arthur, Mael, Gabriel, Lylou, Robin (samedi et dimanche seulement), Suliac, Jeff (à partir de 20h seulement, toujours en Run, sans pause ni rotation).
- Chris : captation Média en continu les 3 jours (hors rotation), pause repas alignée.
- 2 personnes en Run en continu tout le week-end (3 pendant un temps le samedi pour le jury des Awards, abandonné).
- Standiers : 3 personnes simultanées sur les créneaux repas, ramené à 1 pendant l'instant précis des pauses.
- Indie Awards (samedi 18h30-20h30) : 2 personnes fixes restent en Standiers sur toute la durée ; le reste de l'équipe (Jeff dès 20h inclus) est sur Awards ; Chris reste en Média.

## Points ouverts
- Le créneau « Vote public » n'a pas d'horaire fixe dans le document (question posée en commentaire dans le doc en ligne) ; dans le planning il est placé vers 15h sur une personne libre.
- Le script valide l'absence de dépassement des 2h consécutives hors dérogations (affiche `issues hors dérogations: []`). À conserver à chaque modification.

## Mises à jour décidées (2026-10-17)
- Jeff : présent les 3 jours de 11h à 22h, Run continu, sur Awards dès 18h30 le samedi.
- Briefing vendredi 10h00-10h30 (toute l'équipe, Chris compris, sans Jeff).
- `roles.py` : libellés et couleurs partagés Excel / site. `site/` : PWA publiée sur GitHub Pages (spec : `docs/superpowers/specs/`, plan : `docs/superpowers/plans/`).
