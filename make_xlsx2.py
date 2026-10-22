import json, os
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from roles import ROLE_LABELS, ROLE_COLORS

HERE = os.path.dirname(os.path.abspath(__file__))
sched = json.load(open(os.path.join(HERE, 'schedule.json'), encoding='utf-8'))

DAY_PERSONS = {
    'Vendredi 23 octobre': ['François','Chris','Étienne','Florent','Arthur','Mael','Gabriel','Lylou','Suliac','Jeff'],
    'Samedi 24 octobre':   ['François','Chris','Étienne','Florent','Arthur','Mael','Gabriel','Lylou','Suliac','Robin','Jeff'],
    'Dimanche 25 octobre': ['François','Chris','Étienne','Florent','Arthur','Mael','Gabriel','Lylou','Suliac','Robin','Jeff'],
}

TEXT_WHITE = 'FFFFFF'

def slot_label(idx):
    h = 9 + idx//2
    m = '00' if idx % 2 == 0 else '30'
    return f"{h}h{m}"

wb = Workbook()
wb.remove(wb.active)

thin = Side(style='thin', color='444444')
border = Border(left=thin, right=thin, top=thin, bottom=thin)

for day, persons in DAY_PERSONS.items():
    ws = wb.create_sheet(title=day.replace('octobre', 'oct'))
    ws.sheet_view.showGridLines = False

    ncols = len(persons) + 1
    last_col_letter = get_column_letter(ncols)
    ws.merge_cells(f'A1:{last_col_letter}1')
    ws['A1'] = f"STUNFEST 2026 — Planning bénévolat Indé — {day}"
    ws['A1'].font = Font(name='Arial', size=14, bold=True, color=TEXT_WHITE)
    ws['A1'].fill = PatternFill('solid', fgColor='000000')
    ws['A1'].alignment = Alignment(horizontal='center', vertical='center')
    ws.row_dimensions[1].height = 26

    ws.cell(row=2, column=1, value='Horaire').font = Font(name='Arial', bold=True, color=TEXT_WHITE)
    ws.cell(row=2, column=1).fill = PatternFill('solid', fgColor='000000')
    ws.cell(row=2, column=1).alignment = Alignment(horizontal='center', vertical='center')
    ws.cell(row=2, column=1).border = border
    for ci, p in enumerate(persons, start=2):
        c = ws.cell(row=2, column=ci, value=p)
        c.font = Font(name='Arial', bold=True, color=TEXT_WHITE)
        c.fill = PatternFill('solid', fgColor='000000')
        c.alignment = Alignment(horizontal='center', vertical='center')
        c.border = border
    ws.row_dimensions[2].height = 20

    day_sched = sched[day]
    n_slots = len(day_sched)
    for idx in range(n_slots):
        r = 3 + idx
        tc = ws.cell(row=r, column=1, value=slot_label(idx))
        tc.font = Font(name='Arial', bold=True, color=TEXT_WHITE, size=9)
        tc.fill = PatternFill('solid', fgColor='000000')
        tc.alignment = Alignment(horizontal='center', vertical='center')
        tc.border = border

        row_vals = day_sched[str(idx)]
        for ci, p in enumerate(persons, start=2):
            role = row_vals.get(p, '')
            label_r = ROLE_LABELS.get(role, role)
            c = ws.cell(row=r, column=ci, value=label_r)
            color = ROLE_COLORS.get(role, '424242')
            c.fill = PatternFill('solid', fgColor=color)
            c.font = Font(name='Arial', size=9, bold=(role not in ('Off','')), color=TEXT_WHITE)
            c.alignment = Alignment(horizontal='center', vertical='center', wrap_text=False)
            c.border = border
        ws.row_dimensions[r].height = 14

    last_row = 3 + n_slots - 1

    ws.column_dimensions['A'].width = 9
    for ci in range(2, ncols+1):
        ws.column_dimensions[get_column_letter(ci)].width = 11

    legend_roles = ['Backup', 'Run', 'Installation', 'Stand', 'Awards', 'Media', 'Briefing', 'Off', '']
    legend_row = last_row + 3
    ws.cell(row=legend_row, column=1, value='Légende').font = Font(name='Arial', bold=True, size=12)
    full_names = {
        'Backup': 'Standiers = Back-up standiers Indie',
        'Run': 'Run = IC volant / Run (espaces indés + renfort freeplay ; vérifie les postes de vote du public et l\'installation des stands 1 jour)',
        'Stand': 'Stand IC = Stand IC / Stunjam',
        'Awards': 'Awards = Indie Awards (18h30-20h, samedi) ; 2 personnes fixes restent en Standiers',
        'Media': 'Média = Captation média (Chris, en continu les 3 jours)',
        'Installation': "Installation = montage du pôle avant l'ouverture du vendredi (9h-14h)",
        'Briefing': "Briefing = Briefing d'équipe (vendredi 10h00-10h30)",
        'Off': 'Off (inclut les repas : 30 min le midi, 30 min le soir, répartis sur les fenêtres 11h30-14h et 18h30-20h)',
        '': '— = pas encore arrivé / absent ce jour-là',
    }
    for i, role in enumerate(legend_roles):
        rr = legend_row + 1 + i
        c1 = ws.cell(row=rr, column=1, value='')
        c1.fill = PatternFill('solid', fgColor=ROLE_COLORS[role])
        c2 = ws.cell(row=rr, column=2, value=full_names[role])
        c2.font = Font(name='Arial', size=10)

    note_row = legend_row + len(legend_roles) + 2
    notes = []
    notes.append("FERMETURE DE LA ZONE INDÉ À 19h30 TOUS LES SOIRS (hors Awards du samedi). TOUT LE MONDE FINIT À 20h : rangement de 19h30 à 20h, tout le monde en Run.")
    if 'Vendredi' in day:
        notes.append("Ouverture au public à 14h. Bénévoles présents dès 9h pour la préparation : tout le monde en Run de 9h à 14h.")
        notes.append("Briefing d'équipe 10h00-10h30 (Jeff arrive à 11h).")
    else:
        notes.append("Ouverture au public à 10h. Bénévoles présents dès 9h pour la préparation : tout le monde en Run de 9h à 10h.")
    notes.append("Robin : présent uniquement samedi et dimanche. Jeff : présent les 3 jours de 11h à 20h, dans la rotation. Chris : captation Média en continu.")
    if 'Samedi' in day:
        notes.append("Indie Awards 18h30-20h : 2 personnes restent fixes sur l'accueil Standiers (sans rotation), le reste de l'équipe (y compris Jeff dès 18h30) est sur Awards ; Chris reste en Média. Tout le monde finit à 20h.")
    notes.append("Règles : max 2h consécutives sur un même poste (hors Run de préparation du vendredi matin et Standiers fixes pendant les Awards, demandés explicitement) · un repas de 30 min le midi (fenêtre 11h30-14h) et le soir (fenêtre 18h30-20h) pour chacun·e, y compris Chris (Média le reste du temps) et Jeff, jamais seul : au moins 3 personnes en Off en même temps. Le samedi, les 2 Standiers fixes des Awards mangent ensemble à 19h30, remplacés par 2 personnes des Awards.")
    for i, txt in enumerate(notes):
        ws.cell(row=note_row+i, column=1, value=txt).font = Font(name='Arial', italic=True, size=9)

    ws.freeze_panes = 'B3'

wb.save(os.path.join(HERE, 'Planning_Stunfest2026_Indie.xlsx'))
print("done")