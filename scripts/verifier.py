#!/usr/bin/env python3
"""Vérifie le site : pages à jour, liens internes valides, ancres existantes.

    python3 scripts/verifier.py

Deux choses peuvent dériver dans un dépôt où les pages sont à la fois écrites
par un script ET committées : le HTML peut ne plus correspondre au script — une
retouche faite à la main dans un fichier produit —, et un lien peut pointer vers
une page ou une ancre qui n'existe plus. Ce script refuse les deux, et il sort
en erreur pour qu'une intégration continue puisse s'en servir.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import construire_site as site  # noqa: E402

RACINE = Path(__file__).resolve().parent.parent


def pages_a_jour() -> list[str]:
    """Les pages dont le contenu committé diffère de ce que le script écrit."""
    ecarts = []
    for construire in site.PAGES:
        fichier, attendu = construire()
        chemin = RACINE / fichier
        if not chemin.exists():
            ecarts.append(f"{fichier} : absent du dépôt")
        elif chemin.read_text(encoding="utf-8") != attendu:
            ecarts.append(f"{fichier} : ne correspond plus au générateur")
    return ecarts


def liens_valides() -> list[str]:
    """Les liens et sources internes qui ne mènent nulle part."""
    pages = {chemin.name for chemin in RACINE.glob("*.html")}
    casses = []
    for chemin in sorted(RACINE.glob("*.html")):
        html = chemin.read_text(encoding="utf-8")
        for adresse in re.findall(r'(?:href|src)="([^"]+)"', html):
            if adresse.startswith(("http://", "https://", "mailto:")):
                continue
            cible, _, ancre = adresse.partition("#")
            if cible and cible not in pages and not (RACINE / cible).exists():
                casses.append(f"{chemin.name} → {adresse} : cible introuvable")
                continue
            if ancre:
                porteur = html if not cible else (RACINE / cible).read_text(encoding="utf-8")
                if f'id="{ancre}"' not in porteur:
                    casses.append(f"{chemin.name} → {adresse} : ancre introuvable")
    return casses


def entites_echappees() -> list[str]:
    """Les entités HTML qui se sont affichées en toutes lettres.

    Les intitulés sont échappés (voir `gabarit._propre`) : une entité qui y
    survivrait se lirait « 6600&amp;nbsp;€ » dans la page. Le cas s'est produit
    une fois, il est vérifié depuis.
    """
    fautes = []
    for chemin in sorted(RACINE.glob("*.html")):
        html = chemin.read_text(encoding="utf-8")
        for entite in re.findall(r"&amp;[a-z]+;", html):
            fautes.append(f"{chemin.name} : entité échappée {entite}")
    return fautes


def baremes_servis() -> list[str]:
    """Les barèmes servis au calculateur disent-ils encore ce que dit le module.

    Le calculateur affiche une colonne « aujourd'hui », et il lui faut pour cela
    les barèmes en vigueur. Ils ne sont pas écrits dans le JavaScript : ils sont
    injectés dans la page depuis `chiffrage.py`, précisément pour qu'il n'en
    existe qu'un seul jeu. Cette vérification garde la porte fermée — un barème
    changé d'un côté et pas de l'autre ferait dire à la page et aux cas-types
    deux chiffres différents de la même situation.
    """
    import json

    import chiffrage as ch

    html = (RACINE / "simulateur.html").read_text(encoding="utf-8")
    trouve = re.search(
        r'<script id="baremes" type="application/json">(.*?)</script>', html, re.S)
    if not trouve:
        return ["simulateur.html : les barèmes du calculateur sont absents"]
    try:
        servis = json.loads(trouve.group(1))
    except json.JSONDecodeError as erreur:
        return [f"simulateur.html : barèmes illisibles ({erreur})"]
    if servis != json.loads(json.dumps(ch.baremes_du_calculateur())):
        return ["simulateur.html : les barèmes servis ne sont plus ceux de "
                "chiffrage.py"]
    return []


def chiffrage_signale() -> list[str]:
    """Les pages qui dépassent la note le signalent-elles comme tel.

    Le site porte trois espèces de phrases — la doctrine, tirée de la note ; le
    chiffrage, calculé à partir de barèmes publics ; le droit applicable, tiré
    des textes et de la jurisprudence — et le lecteur doit pouvoir les
    distinguer. Une page qui chiffre ou qui dit le droit sans le signaler ferait
    passer un travail du site pour une position du parti.
    """
    attendus = {
        "financement.html": ["Chiffrage —"],
        "cas-types.html": ["Chiffrage —"],
        "nouveaux-residents.html": ["Droit applicable —"],
    }
    manquants = []
    for fichier, marqueurs in attendus.items():
        html = (RACINE / fichier).read_text(encoding="utf-8")
        for marqueur in marqueurs:
            if marqueur not in html:
                manquants.append(
                    f"{fichier} : porte du « {marqueur.strip(' —')} » sans le signaler")
    return manquants


def main() -> int:
    problemes = (pages_a_jour() + liens_valides() + entites_echappees()
                 + baremes_servis() + chiffrage_signale())
    if problemes:
        for probleme in problemes:
            print(f"✗ {probleme}")
        print(f"\n{len(problemes)} problème(s). "
              "Relancez `python3 scripts/construire_site.py` si les pages ont dérivé.")
        return 1
    print(f"✓ {len(site.PAGES)} pages à jour, liens internes et ancres valides, "
          "barèmes du calculateur conformes, chiffrage signalé.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
