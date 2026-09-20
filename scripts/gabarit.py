"""Le gabarit du site : l'enveloppe des pages et les fragments qu'elles partagent.

Le site est un jeu de pages statiques écrites par `construire_site.py`. Rien n'y
est calculé à la lecture — hors le simulateur d'illustration —, et rien n'y est
chargé d'un tiers : les deux polices, la feuille de style et l'icône sont dans
`moteur/`.

L'APPARENCE EST CELLE DU SITE « RETRAITE À COMPTES NOTIONNELS ». La feuille
`moteur/style.css` en est une copie, et les classes employées ici sont les
siennes : `.affiche`, `.engagements`, `.points`, `ol.gestes`, `.fiches.reperes`,
`.note`, `.carte`, `.creme`, `.encadre`, `section.cle`. Un bloc écrit avec une
classe qui n'existe pas dans cette feuille ne sera pas mis en page : le
vocabulaire est fermé, et c'est ce qui fait que les deux sites se reconnaissent.
"""

from __future__ import annotations

from html import escape

# -- identité ----------------------------------------------------------------

NOM_SITE = "Revenu universel"
TITRE_SITE = "Revenu universel — refonte des prestations sociales"
SITE_PARENT = "https://partiliberalfrancais.fr/"
DEPOT = "https://github.com/g-pliberal/PrestationsSociales"
NOTE = "documents/note-revenu-universel.pdf"

#: Les libellés sont COURTS — « Socle », « Résidents » —, et c'est la barre
#: repliée d'un téléphone qui les raccourcit : à dix onglets, « Le socle » et
#: « Nouveaux résidents » faisaient une quatrième rangée, et un bandeau collé
#: qui mange un quart de l'écran ne colle plus rien d'utile. Le titre de la page
#: dit le reste.
#: La navigation, par FONCTION et non par ordre de rédaction : la promesse, ce
#: qu'elle change pour chacun, les règles, puis les objections. C'est la
#: structure du site parent, et elle vaut ici pour la même raison — un lecteur
#: qui arrive ne cherche pas un chapitre, il cherche sa situation.
GROUPES_NAVIGATION = [
    ("La promesse", [("index.html", "Programme")]),
    ("Ce que ça change", [
        ("revenu-universel.html", "Socle"),
        ("simulateur.html", "Calculer"),
        ("jeunes.html", "Jeunes"),
        ("familles.html", "Familles"),
        ("protections.html", "Protections"),
    ]),
    ("Les règles", [
        ("nouveaux-residents.html", "Résidents"),
        ("financement.html", "Financement"),
        ("calendrier.html", "Calendrier"),
    ]),
    ("Comprendre", [("questions.html", "Questions")]),
]

# -- pictogrammes ------------------------------------------------------------

#: Lucide 1.46.0, sous licence ISC — la même bibliothèque, la même grille de
#: 24 et le même trait de 2 que le site parent, pour que les deux ne dessinent
#: pas le même objet de deux façons.
ICONES = {
    "chevron-down": '<path d="m6 9 6 6 6-6" />',
    "triangle-alert":
        '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 '
        '0 0 0 1.73-3" /><path d="M12 9v4" /><path d="M12 17h.01" />',
    "users": '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />'
             '<circle cx="9" cy="7" r="4" />'
             '<path d="M22 21v-2a4 4 0 0 0-3-3.87" />'
             '<path d="M16 3.13a4 4 0 0 1 0 7.75" />',
}

_ENVELOPPE = ('viewBox="0 0 24 24" fill="none" stroke="currentColor" '
              'stroke-width="2" stroke-linecap="round" stroke-linejoin="round"')


def icone(nom: str, titre: str = "") -> str:
    """Un pictogramme de la bibliothèque, écrit dans la page.

    Sans `titre` il est décoratif : le texte à côté dit déjà ce qu'il dit, et une
    synthèse vocale n'a pas à l'entendre deux fois.
    """
    if nom not in ICONES:
        raise KeyError(f"pictogramme inconnu : {nom}")
    if titre:
        return (f'<svg class="icone" {_ENVELOPPE} role="img">'
                f"<title>{escape(titre)}</title>{ICONES[nom]}</svg>")
    return (f'<svg class="icone" {_ENVELOPPE} aria-hidden="true" '
            f'focusable="false">{ICONES[nom]}</svg>')


def _propre(texte: str) -> str:
    """Le texte d'un intitulé, échappé — et son espace insécable rendue telle.

    Les intitulés (légende de tableau, question d'une carte, titre d'un
    dépliant) sont ÉCHAPPÉS : ils se lisent comme du texte, et une balise qu'on
    y glisserait ne serait pas exécutée. Une entité HTML s'y afficherait donc en
    toutes lettres — « 6600&nbsp;€ » —, ce qu'on a vu une fois. L'entité la plus
    courante du site, l'espace fine insécable qui précède un symbole, est donc
    remplacée par le caractère lui-même avant l'échappement.
    """
    return escape(texte.replace("&nbsp;", "\u202f"))


# -- enveloppe ---------------------------------------------------------------

def navigation(page_active: str) -> str:
    """Les onglets, groupés. L'étiquette de groupe est lue, jamais affichée."""
    morceaux = []
    for etiquette, liens in GROUPES_NAVIGATION:
        onglets = "".join(
            f'<a href="{fichier}"'
            + (' aria-current="page"' if fichier == page_active else "")
            + f">{escape(libelle)}</a>"
            for fichier, libelle in liens
        )
        morceaux.append(f'<span class="groupe">'
                        f'<span class="etiquette">{escape(etiquette)}</span>'
                        f'<span class="liens">{onglets}</span></span>')
    return "".join(morceaux)


def entete(page_active: str) -> str:
    """Bandeau de tête, précédé du lien d'évitement.

    Le lien d'évitement est le premier élément parcouru au clavier : sans lui,
    atteindre le contenu impose de traverser les dix onglets à chaque page.
    """
    return f"""<a class="evitement" href="#contenu">Aller au contenu</a>
<header class="bandeau"><div class="interieur">
  <p class="nom"><a href="index.html">{icone("users")}<span>{escape(NOM_SITE)}</span></a></p>
  <nav aria-label="Navigation principale">{navigation(page_active)}</nav>
</div></header>"""


def affiche(surtitre: str, titre: str, chapeau: str) -> str:
    """Le bloc de tête : sur-titre en or, titre massif, chapeau en serif.

    Le titre est mis en capitales par le STYLE, jamais dans le texte : une
    synthèse vocale lit des capitales lettre par lettre.
    """
    return (f'<div class="affiche"><p class="surtitre">{escape(surtitre)}</p>'
            f'<h1>{titre}</h1><p class="chapeau">{chapeau}</p></div>')


def pied() -> str:
    """Pied de page : d'où vient le programme, et ce que ce site n'est pas."""
    return f"""<footer>
  <p><strong>Ce site présente une proposition, pas un droit en vigueur.</strong>
  Aucune des règles décrites ici n'existe aujourd'hui : elles forment le
  programme que le Parti libéral français soumet au débat. Pour vos droits
  actuels, seules les caisses font foi
  (<a href="https://www.service-public.fr/">service-public.fr</a>).</p>
  <p>Tout le contenu est tiré de la note de doctrine du parti,
  <a href="{NOTE}">« Revenu universel et refonte des prestations sociales »</a>
  (22 sections, reproduite intégralement dans ce dépôt). Les montants qu'elle
  donne sont des <strong>ordres de grandeur de cadrage</strong> : le niveau du
  socle, le forfait enfant et le taux de la contribution de solidarité restent à
  calibrer, et ce site le signale partout où il les emploie.</p>
  <p>Code et textes sur <a href="{DEPOT}">GitHub</a>. L'apparence reprend celle du
  simulateur de retraite du parti, dont la feuille de style est copiée telle
  quelle. <span class="retour-site">Un site du
  <a href="{SITE_PARENT}" target="_top">Parti libéral français</a>.</span></p>
</footer>"""


# -- fragments ---------------------------------------------------------------

def note(corps: str, classe: str = "") -> str:
    """Un encart : la réserve, le résumé, l'avertissement."""
    classes = f"note {classe}".strip()
    if "avertissement" in classe:
        return (f'<div class="{classes}">{icone("triangle-alert", "Attention")}'
                f"<div>{corps}</div></div>")
    return f'<div class="{classes}">{corps}</div>'


def carte(corps: str, classe: str = "") -> str:
    classes = f"carte {classe}".strip()
    return f'<div class="{classes}">{corps}</div>'


def encadre(corps: str) -> str:
    return f'<div class="encadre">{corps}</div>'


def points(entrees: list[tuple[str, str]]) -> str:
    """Quelques idées de même poids, côte à côte : titre puis phrase.

    Une liste à puces dirait la même chose, mais elle se lit de haut en bas et
    donne au premier point une importance que les autres n'ont pas.
    """
    corps = "".join(f'<div class="point"><h3>{escape(titre)}</h3><p>{texte}</p></div>'
                    for titre, texte in entrees)
    return f'<div class="points">{corps}</div>'


def gestes(entrees: list[str]) -> str:
    """Une liste numérotée dont le rang est énorme : les principes, les étapes."""
    corps = "".join(f'<li><span class="rang" aria-hidden="true">{i:02d}</span>'
                    f"<span>{texte}</span></li>"
                    for i, texte in enumerate(entrees, start=1))
    return f'<ol class="gestes">{corps}</ol>'


def engagements(entrees: list[tuple[str, str, str]]) -> str:
    """Les chiffres du programme, numérotés, deux par ligne et jamais trois."""
    corps = "".join(
        f'<div class="engagement">'
        f'<div class="rang" aria-hidden="true">{i:02d}</div>'
        f'<div class="chiffre">{chiffre}</div>'
        f'<div class="promesse">{promesse}</div>'
        f'<div class="detail">{detail}</div></div>'
        for i, (chiffre, promesse, detail) in enumerate(entrees, start=1)
    )
    return (f'<section class="engagements" aria-label="Les chiffres du programme">'
            f'<div class="grille">{corps}</div></section>')


def fiches(entrees: list[tuple[str, str, str]]) -> str:
    """Les repères d'ouverture d'une page : l'étiquette d'abord, le nombre après."""
    corps = ""
    for etiquette, valeur, precision in entrees:
        suite = f'<div class="precision">{precision}</div>' if precision else ""
        corps += (f'<div class="fiche"><div class="valeur">{valeur}</div>'
                  f'<div class="etiquette">{_propre(etiquette)}</div>{suite}</div>')
    return f'<div class="fiches reperes">{corps}</div>'


def tableau(entetes: list[str], lignes: list[list[str]], classes: list[str] | None = None,
            titre: str = "", entete_de_ligne: bool = True) -> str:
    """Un tableau, dans un cadre qui défile plutôt que de déborder la page."""
    classes = classes or ["texte"] + ["texte"] * (len(entetes) - 1)
    tete = "".join(f'<th class="{classes[i]}" scope="col">{escape(intitule)}</th>'
                   for i, intitule in enumerate(entetes))
    corps = ""
    for ligne in lignes:
        cellules = ""
        for i, valeur in enumerate(ligne):
            if i == 0 and entete_de_ligne:
                cellules += f'<th class="{classes[i]}" scope="row">{valeur}</th>'
            else:
                cellules += f'<td class="{classes[i]}">{valeur}</td>'
        corps += f"<tr>{cellules}</tr>"
    legende = f"<caption><span>{_propre(titre)}</span></caption>" if titre else ""
    nom = f' role="region" aria-label="{_propre(titre)}"' if titre else ""
    return (f'<div class="defilant" tabindex="0"{nom}><table>{legende}'
            f"<thead><tr>{tete}</tr></thead><tbody>{corps}</tbody></table></div>")


def depliant(titre: str, corps: str, identifiant: str = "") -> str:
    """Une section repliée : son titre se lit, son détail s'ouvre si on veut."""
    cible = f' id="{escape(identifiant)}"' if identifiant else ""
    return (f'<details class="section"{cible}>'
            f'<summary>{icone("chevron-down")}<span>{_propre(titre)}</span></summary>'
            f'<div class="dedans">{corps}</div></details>')


def cle(question: str, reponse: str, corps: str = "", source: str = "",
        identifiant: str = "") -> str:
    """Une question, sa réponse en une phrase, le détail dessous.

    La carte est encadrée pour se découper : une capture d'écran de ce bloc se
    comprend hors du site, et c'est ce qu'on en fait.
    """
    cible = f' id="{escape(identifiant)}"' if identifiant else ""
    fin = f'<p class="source">{source}</p>' if source else ""
    return (f'<section class="cle"{cible}><h3>{_propre(question)}</h3>'
            f'<p class="reponse">{reponse}</p>{corps}{fin}</section>')


def mot(terme: str, definition: str) -> str:
    """Un mot de jargon, et sa définition dépliable sur place.

    Le site s'adresse à des gens qui n'ont jamais eu à lire un barème. « Minimum
    contributif », « effet de seuil », « prestation non contributive » leur sont
    opaques, et les définir dans le corps du texte l'allonge pour tous les
    autres. Ce n'est pas un attribut `title` : une infobulle de survol ne s'ouvre
    ni au clavier, ni au doigt, ni sous une synthèse vocale.
    """
    return ('<span class="mot"><span class="terme" role="button" tabindex="0" '
            f'aria-expanded="false">{escape(terme)}</span>'
            f'<span class="bulle" role="note" hidden>{escape(definition)}</span></span>')


def gloses(entrees: list[tuple[str, str]]) -> str:
    corps = "".join(f"<dt>{escape(terme)}</dt><dd>{escape(texte)}</dd>"
                    for terme, texte in entrees)
    return f'<dl class="gloses">{corps}</dl>'


def source(texte: str) -> str:
    """D'où vient ce qui précède, dans la note. Toute page en porte au moins une."""
    return f'<p class="discret">{texte}</p>'


def plan(sections: list[tuple[str, str]]) -> str:
    """Le sommaire d'une page, déduit de ses sections : il ne peut pas dériver."""
    if len(sections) < 2:
        return ""
    liens = "".join(f'<li><a href="#{identifiant}">{escape(titre)}</a></li>'
                    for identifiant, titre in sections)
    return ('<nav class="plan" aria-label="Dans cette page">'
            f'<p class="etiquette">Dans cette page</p><ol>{liens}</ol></nav>')


# -- saisie ------------------------------------------------------------------
#
# Les trois rangées d'une cellule de formulaire — libellé, contrôle, rappel —
# sont une sous-grille partagée par toute la rangée (voir `form .grille` dans la
# feuille) : les libellés ont la même hauteur et les champs partent tous de la
# même ligne, même quand l'un porte une ligne d'aide que les autres n'ont pas.

def champ(nom: str, libelle: str, valeur: str, aide: str = "", type_: str = "number",
          attributs: dict[str, str] | None = None) -> str:
    supplement = "".join(f' {cle}="{escape(str(val))}"'
                         for cle, val in (attributs or {}).items())
    aide_html = f'<span class="aide">{escape(aide)}</span>' if aide else ""
    return (f'<div><label for="{nom}">{escape(libelle)}{aide_html}</label>'
            f'<input type="{type_}" id="{nom}" name="{nom}" '
            f'value="{escape(str(valeur))}"{supplement}></div>')


def liste(nom: str, libelle: str, options: list[tuple[str, str]], selection: str,
          aide: str = "") -> str:
    choix = "".join(
        f'<option value="{escape(code)}"' + (" selected" if code == selection else "")
        + f">{escape(texte)}</option>"
        for code, texte in options)
    aide_html = f'<span class="aide">{escape(aide)}</span>' if aide else ""
    return (f'<div><label for="{nom}">{escape(libelle)}{aide_html}</label>'
            f'<select id="{nom}" name="{nom}">{choix}</select></div>')
