"""Libellés et couleurs des postes, partagés par l'Excel et le site."""

ROLE_LABELS = {
    'Backup': 'Standiers',
    'Run': 'Run',
    'Stand': 'Stand IC',
    'Awards': 'Awards',
    'Media': 'Média',
    'Briefing': 'Briefing',
    'Off': 'Off',
    '': '—',
}
ROLE_COLORS = {
    'Backup': '2E7D32',
    'Run':    '1565C0',
    'Stand':  'E65100',
    'Awards': 'B71C1C',
    'Media':  '00838F',
    'Briefing': '827717',
    'Off':    '212121',
    '':       '3A3A3A',
}

# Ordre d'affichage et explications des postes (page « Rôles » du site)
ROLE_ORDER = ['Backup', 'Run', 'Stand', 'Awards', 'Briefing', 'Media', 'Off']
ROLE_DESCRIPTIONS = {
    'Backup': "Accueil et animation au stand Indie. Aux heures de repas, le Run bascule en Standiers (pas de Run) ; pendant les Awards, 2 personnes tiennent l'accueil.",
    'Run': "IC volant : tu te déplaces entre les différents points du pôle selon les besoins. Inclut le vote du public et le check des stands 1 jour.",
    'Stand': "Tenue du Stand IC / Stunjam.",
    'Awards': "Mobilisation sur les Indie Awards, le samedi de 18h30 à 20h.",
    'Briefing': "Briefing d'équipe du vendredi, de 10h00 à 10h30.",
    'Media': "Captation média du pôle (Chris).",
    'Off': "Temps libre ou repas : 30 minutes le midi et 30 minutes le soir, en groupe.",
}
