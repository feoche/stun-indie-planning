#!/usr/bin/env python3
"""Bloque sur Instagram les comptes listés sur onbloquelextremedroite.fun.

Deux étapes, à lancer sur TON ordinateur (le site doit être joignable) :
  1. python tools/block_instagram.py extract   -> handles.txt (à relire !)
  2. python tools/block_instagram.py block     -> bloque chaque compte de handles.txt

Dépendance pour l'étape 2 : pip install playwright && playwright install chromium
Le script ouvre un vrai navigateur ; tu te connectes toi-même à Instagram
(aucun mot de passe n'est lu ni stocké). Pauses aléatoires pour éviter les limites.
Les sélecteurs dépendent de l'interface Instagram (FR/EN) et peuvent casser.
"""
import argparse
import random
import re
import sys
import time
import urllib.request
from pathlib import Path

URL = "https://onbloquelextremedroite.fun/"
HANDLES = Path("handles.txt")
DONE = Path("handles_done.txt")
RESERVED = {"p", "reel", "reels", "explore", "accounts", "stories", "direct",
            "tv", "about", "legal", "privacy", "developer", "web", "share"}


def extract(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    html = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")
    found = re.findall(r"instagram\.com/([A-Za-z0-9._]{1,30})", html)
    found += re.findall(r"(?<![\w/])@([A-Za-z0-9._]{2,30})", html)
    seen, out = set(), []
    for h in found:
        h = h.strip(".").lower()
        if h and h not in RESERVED and h not in seen and not h.endswith((".fun", ".com", ".fr")):
            seen.add(h)
            out.append(h)
    return out


def cmd_extract(args):
    handles = extract(args.url)
    HANDLES.write_text("\n".join(handles) + "\n")
    print(f"{len(handles)} comptes écrits dans {HANDLES}. Relis le fichier avant de bloquer.")


def cmd_block(args):
    from playwright.sync_api import sync_playwright

    handles = [h.strip() for h in HANDLES.read_text().split() if h.strip()]
    done = set(DONE.read_text().split()) if DONE.exists() else set()
    todo = [h for h in handles if h not in done]
    print(f"{len(todo)} comptes à bloquer ({len(done)} déjà faits).")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_context().new_page()
        page.goto("https://www.instagram.com/accounts/login/")
        input("Connecte-toi à Instagram dans la fenêtre, puis appuie sur Entrée ici… ")

        for i, h in enumerate(todo, 1):
            try:
                page.goto(f"https://www.instagram.com/{h}/")
                page.wait_for_timeout(2500)
                if page.get_by_text(re.compile(r"Bloqu[ée] |Blocked|Débloquer|Unblock")).count() and \
                        page.get_by_role("button", name=re.compile(r"Débloquer|Unblock")).count():
                    print(f"[{i}/{len(todo)}] {h}: déjà bloqué")
                else:
                    page.get_by_role("button", name=re.compile(r"Options|Plus d.options|More options")).first.click()
                    page.get_by_role("button", name=re.compile(r"^(Bloquer|Block)$")).first.click()
                    page.get_by_role("button", name=re.compile(r"^(Bloquer|Block)$")).last.click()
                    page.wait_for_timeout(1500)
                    print(f"[{i}/{len(todo)}] {h}: bloqué")
                with DONE.open("a") as f:
                    f.write(h + "\n")
            except Exception as e:  # compte inexistant, interface différente, etc.
                print(f"[{i}/{len(todo)}] {h}: ÉCHEC ({type(e).__name__}) -> à faire à la main", file=sys.stderr)
            time.sleep(random.uniform(args.min_delay, args.max_delay))
        browser.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("extract")
    e.add_argument("--url", default=URL)
    e.set_defaults(fn=cmd_extract)
    b = sub.add_parser("block")
    b.add_argument("--min-delay", type=float, default=20)
    b.add_argument("--max-delay", type=float, default=45)
    b.set_defaults(fn=cmd_block)
    a = ap.parse_args()
    a.fn(a)
