# Planning Stunfest 2026 — Application web bénévoles (PWA)

Date : 2026-10-17. Festival : vendredi 23 au dimanche 25 octobre 2026 (dans 6 jours à la date de rédaction).

## Intention

Les 11 bénévoles du pôle Indie doivent pouvoir, depuis leur téléphone et sans demander à personne, voir leur planning et savoir où ils doivent être maintenant et ensuite. Aujourd'hui le planning est un Excel avec une colonne par personne : illisible sur mobile, et personne n'est prévenu d'un changement de poste.

L'organisateur (l'utilisateur) génère le planning avec des scripts Python existants, et peut le modifier pendant le festival. Les bénévoles doivent voir les changements rapidement.

## Objectifs

- Un bénévole choisit son prénom dans une liste et voit : son poste en cours, son poste suivant avec l'heure, puis sa journée complète.
- Interface pensée d'abord pour le téléphone (lecture à une main, gros texte, utilisable debout sur un site de festival).
- Un rappel 10 minutes avant chaque nouvelle affectation, sans serveur (voir « Rappels »).
- Mise à jour du planning environ une minute après publication, visible dans l'appli.
- Fonctionne hors-ligne avec la dernière version connue (4G saturée sur site).
- Hébergé sur GitHub Pages, gratuit, sans compte ni service tiers.

## Non-objectifs

- Pas de notifications Web Push, donc aucun serveur ni service additionnel (refusé par l'utilisateur).
- Pas de comptes, de mots de passe ni de contacts : uniquement des prénoms.
- Pas d'édition du planning dans l'appli. Le planning se modifie en relançant le script Python puis en publiant sur GitHub.
- Pas de vue « toute l'équipe » (qui est où) dans cette version. Le besoin exprimé est « mon planning ».
- Français uniquement.

## Anti-objectifs (un échec même si « ça marche »)

- Afficher un mauvais poste « en cours » (erreur de fuseau, de jour ou de bord de créneau). C'est le pire échec.
- Un rappel qui sonne à la mauvaise heure.
- Un planning obsolète affiché comme s'il était à jour, sans indication.

## Contraintes

- Dépôt : `git@github.com:feoche/stun-indie-planning.git` (l'utilisateur autorise commit et push dessus). Le site sera servi dans un sous-chemin (`https://feoche.github.io/stun-indie-planning/`) : tous les chemins (manifeste, service worker, données, `.ics`, `webcal://`) doivent être relatifs ou tenir compte de ce préfixe.
- Seulement des fichiers statiques sur GitHub Pages. Le dépôt peut être public : seuls des prénoms y figurent (accepté par l'utilisateur).
- Fuseau Europe/Paris, fixé dans les données (ne pas dépendre du fuseau de l'appareil).
- Les données sont produites par les scripts Python existants (`build_schedule6.py`, source de vérité des règles métier). Flux de travail de l'utilisateur : relancer le script, puis publier sur GitHub.

## Changements de règles métier à intégrer dans `build_schedule6.py` (décidés avec l'utilisateur)

1. **Jeff** : présent les 3 jours de 11h00 à 22h00 (au lieu de « à partir de 20h »).
   - Il reste en Run continu, sans pause ni rotation (reconduit de l'ancienne règle).
   - Le samedi, il passe sur Awards à 18h30 avec le reste de l'équipe, au lieu de 20h.
   - Les journées du vendredi et du dimanche vont donc jusqu'à 22h pour lui seul ; les autres partent à 19h30 comme avant.
   - Le samedi, Jeff reste jusqu'à 22h (les autres jusqu'à 21h).
2. **Briefing** vendredi 23 octobre, 10h00–10h30 : nouveau poste « Briefing », toute l'équipe présente à 10h (Chris compris), remplaçant le Run de préparation sur ce créneau. Jeff n'y est pas (il arrive à 11h).
3. **Vote public** : reste à 15h00 sur une personne libre, horaire encore à confirmer (point ouvert, pas bloquant).
4. Pauses de Chris : inchangées (12h00 et 19h00, 30 minutes).

La validation « pas plus de 2h consécutives hors dérogations » doit continuer à passer (`issues hors dérogations: []`). Jeff et Chris restent des dérogations.
Mettre aussi à jour `CLAUDE.md`, `make_xlsx2.py` (Jeff, briefing, légende, notes) et `Document_Temps_forts_Roles_Evenements.md` pour rester cohérents.

## Décisions de conception (par l'utilisateur)

- **PWA** : installable sur l'écran d'accueil (manifeste), planning gardé en cache pour le hors-ligne (service worker).
- **Identification** : le bénévole choisit son prénom dans une liste. Choix mémorisé sur l'appareil, changeable à tout moment.
- **Mise à jour en direct** : l'appli recharge les données à l'ouverture puis régulièrement tant qu'elle est visible. Quand le planning a changé, une bannière « Planning mis à jour » s'affiche avec les créneaux modifiés mis en évidence. Délai attendu : environ une minute après publication (temps de déploiement de GitHub Pages).
- **Rappels** : pas de push. Deux mécanismes :
  1. **Calendrier du téléphone** (fiable écran verrouillé) : chaque bénévole obtient un fichier `.ics` personnel, avec un rappel `-PT10M` par affectation, qu'il peut soit **importer** une fois, soit **s'abonner** (URL `webcal://`) pour que le téléphone le rafraîchisse tout seul.
  2. **Alerte dans l'appli** quand elle est ouverte (ou vivante en arrière-plan) : bannière 10 minutes avant, plus notification système si le bénévole en a accordé la permission. Aucune garantie quand l'appli est fermée.
- **Limites à expliquer clairement dans l'appli** : le rafraîchissement d'un abonnement dépend du téléphone (de quelques dizaines de minutes à plusieurs heures). Google Agenda ignore les rappels des calendriers auxquels on s'abonne : sur Android il faut importer le fichier (et le réimporter après un changement) pour avoir le rappel.
- **Flux de publication** : l'utilisateur relance le script Python puis pousse sur GitHub.

## Contenu et comportement attendus

- Écran d'accueil : prénom choisi, carte « En ce moment » (poste, heure de fin, temps restant), carte « Ensuite » (poste, heure de début). Hors des heures du festival : message clair (« Le festival commence vendredi à 9h » / « Terminé »). Pour un bénévole absent un jour (Robin le vendredi) : afficher « Pas de service ce jour-là ».
- Onglets par jour (vendredi / samedi / dimanche), le jour courant sélectionné par défaut pendant le festival. Vue chronologique de la journée de la personne, créneaux de même poste consécutifs fusionnés en un seul bloc.
- Couleurs par poste reprenant celles de l'Excel (`ROLE_COLORS` dans `make_xlsx2.py`) pour que les bénévoles retrouvent leurs repères. Libellés d'affichage de `ROLE_LABELS` (Backup → « Standiers », Pause → affichée comme une pause).
- Indication de fraîcheur : « Planning mis à jour à HH:MM », et mention « hors-ligne » si les données ne peuvent pas être rechargées.
- Écran « Rappels » : explique les deux mécanismes, boutons « S'abonner » et « Télécharger », mise en garde Android.

## Données

- Le script produit, en plus de `schedule.json`, des données pour le site : liste des prénoms, et pour chaque personne la liste des affectations avec dates/heures absolues (ISO 8601 avec décalage Europe/Paris), postes et étiquettes, et un horodatage de génération.
- Un fichier `.ics` par personne à une URL stable (nom normalisé sans accents). Un `VEVENT` par bloc d'affectation (créneaux consécutifs de même poste fusionnés), `UID` stable, `VALARM` à `-PT10M`. Hint de rafraîchissement (`REFRESH-INTERVAL`, `X-PUBLISHED-TTL`) et nom de calendrier dédié (« Stunfest Indie ») pour pouvoir le supprimer d'un coup.
- Rappels générés pour les postes de travail et les pauses ; pas pour les périodes « Off » (choix de l'assistant).

## Ce qui est laissé au constructeur

- Technologies front (JS sans framework recommandé vu la taille), structure du dépôt, outils de test.
- Organisation du dossier publié et mode de déploiement GitHub Pages (par ex. dossier dédié et workflow GitHub Actions), en gardant le flux « relancer le script puis pousser ».
- Fréquence exacte du rechargement des données, stratégie de cache du service worker (données : réseau d'abord ; coquille de l'appli : cache d'abord).
- Conception visuelle, icônes de l'appli, textes d'aide.
- Gestion des événements calendrier orphelins quand un horaire change entre deux imports (UID basé sur personne + jour + début de bloc ; expliquer le calendrier dédié).

## Choix de l'assistant à vérifier

- Briefing de 30 minutes, Chris inclus, Jeff exclu.
- Jeff en Awards dès 18h30 le samedi.
- Rappels sur les pauses, pas sur le Off.
- JS sans framework, pas de vue « équipe ».

## Risques et vérifications

- Comportement des rappels non vérifiable sans appareils : tester l'abonnement et l'import sur au moins un iPhone et un Android avant le festival.
- Sur iPhone, l'appli installée sur l'écran d'accueil a son propre stockage : le prénom est à rechoisir après installation.
- Calendrier serré : le festival commence le 23 octobre. Si besoin, priorité à (1) planning personnel correct + mise à jour, (2) export `.ics`, (3) alertes dans l'appli ouverte.
