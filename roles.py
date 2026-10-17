"""Libellés et couleurs des postes, partagés par l'Excel et le site."""

ROLE_LABELS = {
    'Backup': 'Standiers',
    'Run': 'Run',
    'Stand': 'Stand IC',
    'Vote': 'Vote public',
    'Awards': 'Awards',
    'Media': 'Média',
    'Briefing': 'Briefing',
    'Off': 'Off',
    'Pause': 'Off',
    '': '—',
}
ROLE_COLORS = {
    'Backup': '2E7D32',
    'Run':    '1565C0',
    'Stand':  'E65100',
    'Vote':   '6A1B9A',
    'Awards': 'B71C1C',
    'Media':  '00838F',
    'Briefing': '827717',
    'Off':    '212121',
    'Pause':  '212121',
    '':       '3A3A3A',
}
# L'appli distingue la pause repas du simple temps libre
SITE_LABELS = {**ROLE_LABELS, 'Pause': 'Pause'}
