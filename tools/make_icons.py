"""Génère les icônes de la PWA dans site/icons/ (fond noir, texte blanc, marge de sécurité maskable)."""
import os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'site', 'icons')
FONTS = ['C:/Windows/Fonts/arialbd.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf']


def font(size):
    for path in FONTS:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default(size)


def icon(size):
    img = Image.new('RGB', (size, size), '#000000')
    d = ImageDraw.Draw(img)
    bar = int(size * 0.06)
    d.rectangle([int(size * .2), int(size * .64), int(size * .8), int(size * .64) + bar], fill='#1565C0')
    # texte dans la zone centrale de 60 % (zone de sécurité maskable)
    for text, y, fs in (('STUN', .30, .2), ('INDIE', .47, .13)):
        f = font(int(size * fs))
        w = d.textlength(text, font=f)
        d.text(((size - w) / 2, size * y), text, font=f, fill='#FFFFFF', anchor='la')
    return img


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    for name, size in (('icon-192.png', 192), ('icon-512.png', 512), ('apple-touch-icon.png', 180)):
        icon(size).save(os.path.join(OUT, name))
    print('icônes générées')
