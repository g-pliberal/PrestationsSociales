#!/usr/bin/env python3
"""Écrit les pages du site à partir du gabarit et du texte du programme.

    python3 scripts/construire_site.py

Les pages produites sont committées : le site se sert tel quel, sans étape de
construction chez l'hébergeur. Le texte, lui, n'existe qu'ICI — une phrase du
programme ne doit se trouver qu'à un seul endroit, sans quoi deux pages finissent
par dire deux choses différentes du même dispositif.

La SOURCE est `documents/note-revenu-universel.pdf`, la note de doctrine du Parti
libéral français sur le revenu universel (22 sections). Chaque section du site
dit de quelle section de la note elle est tirée : le lecteur doit pouvoir
vérifier, et le rédacteur suivant doit savoir ce qu'il a le droit de changer.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import chiffrage as ch
import gabarit as g

RACINE = Path(__file__).resolve().parent.parent

#: L'espace fine insécable, séparateur des milliers et espace d'avant-symbole.
#: Les intitulés étant échappés (voir `gabarit._propre`), les nombres sont
#: écrits avec le caractère lui-même et jamais avec une entité HTML.
FINE = "\u202f"


def md(milliards: float) -> str:
    """Un montant en milliards d'euros, à la française.

    La décimale tombe quand elle est nulle : « 264 Md€ » et non « 264,0 Md€ ».
    Un zéro décimal sur un chiffre de cadrage promet une précision qu'aucune de
    ces sources n'a.
    """
    texte = f"{milliards:,.1f}".replace(",", FINE).replace(".", ",")
    if texte.endswith(",0"):
        texte = texte[:-2]
    return texte + f"{FINE}Md€"


def eur(montant: float) -> str:
    """Un montant en euros, arrondi à l'euro."""
    return f"{montant:,.0f}".replace(",", FINE) + f"{FINE}€"


def pourcent(part: float) -> str:
    """Une part, en points de pourcentage entiers."""
    return f"{part * 100:.0f}{FINE}%"


def ancre(texte: str) -> str:
    """Une ancre stable, déduite d'un intitulé.

    Stable est le mot : `hash()` change d'une exécution à l'autre, et une ancre
    qui change à chaque construction ferait échouer `verifier.py` un jour sur
    deux sans que rien n'ait bougé dans le texte.
    """
    sans_accent = (texte.lower()
                   .replace("é", "e").replace("è", "e").replace("ê", "e")
                   .replace("à", "a").replace("â", "a").replace("ô", "o")
                   .replace("î", "i").replace("ï", "i").replace("û", "u")
                   .replace("ç", "c").replace("'", " ").replace("’", " "))
    mots = [mot for mot in re.split(r"[^a-z0-9]+", sans_accent) if mot]
    return "-".join(mots[:5])


def ecart_monoparental(forfait: float) -> str:
    """Ce qu'un niveau de forfait enfant fait au cas type monoparental."""
    cas = ch.cas_types(forfait=forfait)[1]
    if cas.ecart >= 0:
        return f"Neutre, ou gagnante de {eur(cas.ecart)} par mois."
    return (f"Perd {eur(-cas.ecart)} par mois, soit "
            f"{abs(cas.part) * 100:.0f}{FINE}% de son revenu disponible.")

# Les paramètres que la note laisse ouverts. Ils sont ici, ensemble, parce que le
# site les répète et qu'une valeur répétée à quinze endroits finit par ne plus
# être la même partout. Ce sont des ORDRES DE GRANDEUR DE CADRAGE, et le site le
# dit chaque fois qu'il les emploie.
SOCLE_CIBLE = 550          # euros par mois, cible de régime stabilisé
SOCLE_MARCHE = 500         # euros par mois, première marche de la transition
SOCLE_ANNUEL = 6600        # euros par an, l'exemple chiffré de la note (§18)
#: Le même, écrit à la française : espace fine insécable des milliers, et
#: espace fine avant le symbole. Les intitulés sont échappés, donc écrits
#: avec les caractères eux-mêmes et non avec des entités.
SOCLE_ANNUEL_TEXTE = "6\u202f600\u202f€"


def page(fichier: str, onglet: str, description: str, surtitre: str, titre: str,
         chapeau: str, sections: list[tuple[str, str, str]], tete: str = "",
         scripts: str = "") -> tuple[str, str]:
    """Une page complète, de `<!doctype>` à `</html>`.

    `sections` est une liste de trois éléments — l'ancre, le titre de niveau 2 et
    le corps —, et c'est d'elle que le sommaire est déduit : une page ne peut
    donc pas annoncer une section qu'elle n'a pas.
    """
    corps = "".join(f'<section id="{identifiant}"><h2>{titre_2}</h2>{html}</section>'
                    for identifiant, titre_2, html in sections)
    sommaire = g.plan([(identifiant, titre_2) for identifiant, titre_2, _ in sections])
    html = f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<!-- Le vert profond de l'affiche : sur un téléphone, la barre du navigateur le
     reprend, et la page commence où elle commence. -->
<meta name="theme-color" content="#0b3d3a">
<title>{onglet}</title>
<meta name="description" content="{description}">
<link rel="icon" href="moteur/icone.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="moteur/icone.svg">
<!-- La feuille de style est celle du simulateur de retraite du parti, copiée
     telle quelle : les deux sites sont une seule affiche. -->
<link rel="stylesheet" href="moteur/style.css">
</head>
<body>
{g.entete(fichier)}
<main id="contenu">
{g.affiche(surtitre, titre, chapeau)}
{tete}
{sommaire}
{corps}
</main>
{g.pied()}
<script src="moteur/site.js" defer></script>
{scripts}</body>
</html>
"""
    return fichier, html


# -- 1. le programme ---------------------------------------------------------

def accueil():
    tete = g.note(
        "<p><strong>En trois phrases.</strong> Aujourd'hui, une quinzaine d'aides "
        "différentes se superposent, chacune avec ses conditions, ses seuils et ses "
        "démarches : personne ne sait ce qu'il touche, ni ce qu'il perdra en "
        "travaillant plus. Le Parti libéral français propose de les remplacer par un "
        "<strong>revenu universel</strong> : une somme versée automatiquement à "
        "chaque adulte qui vit en France, la même pour tous, qui ne diminue jamais "
        "quand on gagne de l'argent. Les situations particulières — le handicap, la "
        "dépendance, l'enfance en danger, l'urgence — gardent des dispositifs à "
        "part.</p>", "resume")

    entree = g.carte(
        '<p class="surtitre">Ce que ça donne pour vous</p>'
        "<h2 class=\"serif\">Votre revenu, avec le socle et la contribution</h2>"
        "<p>Le calculateur du site prend votre salaire, votre situation, et montre "
        "ce que le revenu universel y ajoute — et ce que la contribution de "
        "solidarité en reprend. Tout se calcule dans votre navigateur.</p>"
        '<p class="actions"><a class="bouton" href="simulateur.html">Ouvrir le '
        "calculateur</a>"
        '<a href="revenu-universel.html">Comprendre le socle d\'abord</a></p>',
        "creme")

    chiffres = g.engagements([
        (f"{SOCLE_CIBLE}&nbsp;€",
         "Le socle mensuel visé pour chaque adulte, versé sans condition de ressources.",
         f"C'est la cible de régime stabilisé. La réforme démarre par une première "
         f"marche autour de {SOCLE_MARCHE}&nbsp;€ par mois, le temps de vérifier le "
         "bouclage budgétaire. Le socle est individuel : il ne dépend ni du conjoint, "
         "ni du foyer, ni du logement."),
        ("18 ans",
         "L'âge d'ouverture du socle, sans exception et sans délai.",
         "Aujourd'hui le RSA est fermé avant 25 ans, sauf cas particuliers, et les "
         "18-25 ans dépendent d'un empilement d'aides étudiantes, d'APL et de "
         "solidarité familiale. Avec le socle, un majeur a un droit propre."),
        ("5 ans",
         "La durée de la bascule, année par année et annoncée d'avance.",
         "Année 1 la préparation et le simulateur public, année 2 le socle adulte et "
         "l'absorption du RSA, année 3 les aides au logement, année 4 le soutien aux "
         "enfants, année 5 la stabilisation."),
        ("10 ans",
         "La durée de convergence vers le socle complet pour un nouveau résident étranger.",
         "Les droits et les devoirs avancent ensemble : la contribution de solidarité "
         "monte au même rythme que l'accès au socle, et la part versée au-delà des "
         "droits ouverts est créditée sur un compte individuel. La naturalisation "
         "donne accès immédiat au régime commun."),
    ])

    diagnostic = (
        "<p>Le système social français poursuit des objectifs légitimes : réduire la "
        "pauvreté, soutenir les familles, protéger les personnes âgées modestes, aider "
        "les personnes handicapées. Mais il le fait par accumulation. Minima sociaux, "
        "aides au logement, prestations familiales, compléments sous condition de "
        "ressources, dispositifs d'activité, aides locales, exonérations, majorations, "
        "statuts particuliers, exceptions : chaque dispositif a sa logique, et "
        "l'ensemble n'en a plus.</p>"
        + g.points([
            ("Personne ne comprend",
             "Peu de bénéficiaires savent pourquoi ils touchent ce montant-là, à partir "
             "de quel seuil il baisse, ni ce que produira une reprise d'activité, une "
             "mise en couple, une séparation ou un déménagement."),
            ("Des droits non versés",
             "Une aide qui exige une démarche, une compréhension fine des règles et une "
             "actualisation régulière n'atteint pas tous ceux qui y ont droit. Une part "
             "de la pauvreté subsiste non parce que la solidarité n'existe pas, mais "
             "parce qu'elle est trop compliquée pour arriver à destination."),
            ("Travailler peut faire perdre",
             "Reprendre un emploi, augmenter son temps de travail ou accepter un salaire "
             "plus élevé fait perdre une partie des aides. Le gain net est parfois "
             "faible, incertain ou différé : ce sont les "
             + g.mot("trappes à inactivité",
                     "Situation où travailler davantage ne rapporte presque rien, parce "
                     "que le supplément de salaire est absorbé par la perte d'aides.")
             + " et les "
             + g.mot("effets de seuil",
                     "Franchir un euro de revenu au-dessus d'une limite fait perdre d'un "
                     "coup une aide entière.")
             + "."),
            ("On ne sait plus ce qu'on paie",
             "Une partie des prélèvements dits sociaux finance en réalité de la "
             "redistribution, tandis que certaines prestations présentées comme "
             "assurantielles servent des objectifs de solidarité. Le citoyen ne "
             "distingue plus ce qu'il paie pour acquérir des droits et ce qu'il paie "
             "pour financer la solidarité."),
        ])
        + g.note("<p>Le constat de départ n'est donc pas le niveau de la dépense "
                 "sociale, mais sa <strong>structure</strong> : il s'agit de passer d'un "
                 "État social d'empilement à un État social de clarté.</p>")
        + g.source("Note de doctrine, §1 — Diagnostic.")
    )

    regle = (
        "<p>La doctrine repose sur une distinction simple : la solidarité monétaire "
        "générale doit être automatique et lisible ; les vulnérabilités particulières "
        "doivent être traitées par des dispositifs dédiés. D'où la formule :</p>"
        + g.encadre('<p class="chapeau" style="margin:0">Universaliser le socle, '
                    "cibler l'accompagnement.</p>")
        + "<p>Le revenu universel garantit un minimum stable à chaque adulte éligible. "
        "Il remplace les aides générales de revenu, rend le travail toujours gagnant, "
        "supprime une grande partie des effets de seuil, réduit le non-recours et "
        "simplifie l'administration. Mais il ne prétend pas résoudre toutes les "
        "situations sociales par un chèque uniforme : une personne handicapée, "
        "dépendante, sans domicile, victime de violences ou atteinte d'une pathologie "
        "lourde doit continuer à bénéficier d'un accompagnement spécifique.</p>"
        "<p>Le revenu universel n'est donc pas une disparition de l'État social. "
        "C'est une <span class=\"cle-texte\">clarification de son rôle</span>.</p>"
        + g.source("Note de doctrine, §2 — Principe général.")
    )

    etages = (
        "<p>Le dispositif tient en trois blocs, qui ne poursuivent pas le même but.</p>"
        + g.tableau(
            ["Étage", "Ce qu'il fait", "Ce qu'il remplace"],
            [["Revenu universel adulte",
              "Le cœur de la réforme : un socle individuel pour chaque adulte éligible, "
              "cumulable avec le travail.",
              "Les minima sociaux et la plupart des prestations monétaires générales "
              "des personnes d'âge actif."],
             ["Soutien à l'enfant",
              "Une redistribution assumée des adultes sans enfant vers les familles, y "
              "compris aisées : élever un enfant est un coût privé et un bénéfice "
              "collectif.",
              "Les prestations familiales générales et une grande partie du quotient "
              "familial, remplacés par un crédit familial par enfant."],
             ["Revenu universel senior",
              "Le socle de solidarité vieillesse. Il n'augmente aucune pension "
              "existante.",
              "L'ASPA et les mécanismes non contributifs de minimum vieillesse."]],
            ["texte", "long", "long"],
            "Les trois étages du dispositif")
        + g.source("Note de doctrine, §3 — Architecture du dispositif.")
    )

    principes = (
        "<p>La note résume sa doctrine en dix principes. Ils sont la grille de lecture "
        "de tout le reste du site.</p>"
        + g.gestes([
            "<strong>Individualisation maximale</strong> — le socle est attaché à la "
            "personne, pas au foyer.",
            "<strong>Résidence effective</strong> — il est réservé à ceux qui vivent "
            "réellement en France.",
            "<strong>Travail toujours gagnant</strong> — chaque euro gagné par "
            "l'activité augmente le revenu disponible.",
            "<strong>Absorption des aides générales</strong> — RSA, prime d'activité, "
            "aides au logement pour la majorité et autres aides monétaires générales "
            "sont remplacés par le socle.",
            "<strong>Soutien familial explicite</strong> — chaque enfant ouvre droit à "
            "un crédit familial, forfait plus avantage fiscal.",
            "<strong>Protection des familles monoparentales</strong> — un bouclier "
            "temporaire et ciblé pendant la transition.",
            "<strong>Handicap en complément</strong> — l'AAH devient un complément au "
            "socle, elle n'est pas absorbée.",
            "<strong>Assurance à part</strong> — chômage et retraites contributives "
            "relèvent de droits acquis, distincts de la solidarité.",
            "<strong>Socle senior limité</strong> — il remplace l'ASPA et n'augmente "
            "pas les pensions.",
            "<strong>Droits et devoirs progressifs pour les étrangers</strong> — "
            "convergence sur dix ans, la naturalisation ouvrant le régime commun.",
        ])
        + g.source("Note de doctrine, §22 — Synthèse doctrinale.")
    )

    suite = (
        "<p>Le reste du site prend les situations une par une.</p>"
        + g.points([
            ("Le socle",
             'Ce qu\'est le revenu universel adulte, son montant, et pourquoi le '
             'travail y est toujours gagnant. <a href="revenu-universel.html">Lire</a>'),
            ("Jeunes et étudiants",
             'Le socle dès 18 ans, l\'absorption des APL étudiantes, ce que deviennent '
             'les bourses. <a href="jeunes.html">Lire</a>'),
            ("Familles",
             'Le crédit familial par enfant, le couple, et le bouclier pour les familles '
             'monoparentales. <a href="familles.html">Lire</a>'),
            ("Ce qui reste à part",
             'Handicap, dépendance, logement, chômage, retraites : les dispositifs que '
             'le socle ne remplace pas. <a href="protections.html">Lire</a>'),
            ("Nouveaux résidents",
             'La convergence sur dix ans, le compte individuel de solidarité, la '
             'résidence effective. <a href="nouveaux-residents.html">Lire</a>'),
            ("Financement",
             'Coût brut, coût net, contribution de solidarité et fiche de paie à trois '
             'niveaux. <a href="financement.html">Lire</a>'),
            ("Calendrier",
             'Les cinq années de la bascule, et les six risques que la note identifie '
             'elle-même. <a href="calendrier.html">Lire</a>'),
            ("Objections",
             "Les questions qu'on pose en premier, avec les réponses de la note. "
             '<a href="questions.html">Lire</a>'),
        ])
    )

    return page(
        "index.html",
        f"{g.TITRE_SITE} — Parti libéral français",
        "Le programme du Parti libéral français pour les prestations sociales : un "
        "revenu universel de 550 € par mois dès 18 ans, qui remplace le RSA, la prime "
        "d'activité et les aides au logement, sans jamais baisser quand on travaille.",
        "Programme — prestations sociales",
        "Un socle pour chacun,<br>le travail toujours gagnant",
        "Remplacer le maquis des aides sociales par un revenu universel simple, "
        "automatique et individuel — et garder un accompagnement dédié pour ceux qui "
        "en ont vraiment besoin.",
        [("probleme", "Le problème : un système devenu illisible", diagnostic),
         ("regle", "La règle : universaliser le socle, cibler l'accompagnement", regle),
         ("etages", "Les trois étages du dispositif", etages),
         ("principes", "Les dix principes", principes),
         ("suite", "Votre situation", suite)],
        tete=tete + chiffres + entree)


# -- 2. le socle -------------------------------------------------------------

def socle():
    reperes = g.fiches([
        ("Socle mensuel visé", f"{SOCLE_CIBLE}&nbsp;€",
         f"Première marche autour de {SOCLE_MARCHE}&nbsp;€ pendant la transition."),
        ("Âge d'ouverture", "18 ans", "Sans condition de ressources ni de parcours."),
        ("Condition", "Résider",
         "Résidence effective en France, et séjour régulier. La nationalité seule ne "
         "suffit pas."),
        ("Ce qui le fait baisser", "Rien",
         "Ni un salaire, ni une mise en couple, ni un déménagement."),
    ])

    individuel = (
        "<p>Le revenu universel adulte serait versé à <strong>chaque adulte "
        "éligible résidant effectivement en France</strong>. Son principe est "
        "individuel : il ne dépend ni du statut conjugal, ni de la composition du "
        "foyer, ni du revenu du conjoint, ni du parcours administratif antérieur.</p>"
        "<p>Cette individualisation n'est pas un détail technique. Aujourd'hui, la vie "
        "privée modifie fortement l'accès aux prestations : le RSA, les "
        + g.mot("APL", "Aides personnelles au logement, versées selon le loyer, les "
                       "ressources et la composition du foyer.")
        + " et certaines aides familiales dépendent du foyer. D'où des effets absurdes "
        "— perte de droits lors d'une mise en couple, instabilité après une "
        "séparation, intérêt à retarder une déclaration, dépendance économique au "
        "conjoint, complexité pour les jeunes adultes et pour les revenus "
        "irréguliers.</p>"
        "<p>Le socle met fin à cette logique : <span class=\"cle-texte\">il est "
        "attaché à la personne</span>. Deux personnes qui ont le même revenu touchent "
        "le même socle, qu'elles soient mariées, séparées, colocataires ou "
        "hébergées.</p>"
        + g.source("Note de doctrine, §4 — Le revenu universel adulte.")
    )

    montant = (
        f"<p>La cible recommandée est d'environ <strong>{SOCLE_CIBLE}&nbsp;€ par "
        f"mois</strong> pour un adulte, avec une première marche possible autour de "
        f"{SOCLE_MARCHE}&nbsp;€ par mois pendant la transition. En retenant environ "
        "40&nbsp;millions de personnes de 18 à 64 ans, l'ordre de grandeur du coût "
        "brut est le suivant.</p>"
        + g.tableau(
            ["Socle mensuel", "Coût annuel brut approximatif"],
            [["500&nbsp;€", "240&nbsp;Md€"],
             [f"{SOCLE_CIBLE}&nbsp;€ <span class=\"badge proposition\">cible</span>",
              "264&nbsp;Md€"],
             ["600&nbsp;€", "288&nbsp;Md€"]],
            ["texte", "nombre"],
            "Coût brut du socle adulte, selon son montant")
        + g.note(
            "<p><strong>Ces montants sont des coûts bruts.</strong> Ils ne doivent "
            "jamais être confondus avec le coût net de la réforme : le socle remplace "
            "des prestations existantes — RSA, prime d'activité, une grande partie des "
            "aides au logement, certaines aides jeunes, une partie des prestations "
            "familiales ou fiscales — et il est accompagné d'un impôt proportionnel qui "
            "reprend progressivement le transfert auprès des revenus moyens et élevés. "
            "<a href=\"financement.html\">Voir le financement</a>.</p>",
            "avertissement")
        + f"<p>Ce coût net, la note ne le donne pas. Il est calculé sur la page "
        f"du financement : <strong>{md(ch.boucler().net)}</strong> une fois "
        f"déduites les prestations que le socle absorbe, soit une contribution "
        f"de solidarité de <strong>{pourcent(ch.taux_publie())}</strong> et un "
        f"point de bascule à {eur(ch.boucler().bascule_mensuelle)} de revenu "
        "mensuel — en dessous, on reçoit plus qu'on ne verse. "
        '<a href="financement.html#net">Voir le calcul, ligne à ligne</a></p>'
        + g.repere("Coût net calculé à partir des dépenses constatées de "
                   "chaque prestation absorbée ; taux rapporté à une assiette "
                   "de l'ordre de celle de la CSG.")
        + "<p>Le socle n'est pas conçu comme un revenu de confort, et il ne remplace "
        "pas le salaire. Il garantit une sécurité minimale, compatible avec la reprise "
        "d'activité, l'entrepreneuriat, la formation, le temps partiel, les revenus "
        "irréguliers et les transitions professionnelles.</p>"
        + g.source("Note de doctrine, §4 et §18.")
    )

    travail = (
        "<p>C'est l'objectif central de la réforme. Aujourd'hui, une hausse du revenu "
        "d'activité peut entraîner la baisse simultanée de plusieurs aides : le "
        + g.mot("taux marginal effectif",
                "Part d'un euro supplémentaire gagné qui repart en impôts, en "
                "cotisations ou en aides perdues.")
        + " devient très élevé pour certains ménages modestes, et la reprise d'emploi "
        "se traduit par un gain faible, difficile à anticiper, parfois annulé par la "
        "perte d'APL, de prime d'activité ou de complément familial.</p>"
        "<p>Le socle corrige cela à la racine : <strong>il est conservé quand on "
        "travaille</strong>. Le salaire s'ajoute au socle, puis l'impôt proportionnel "
        "s'applique selon une règle unique et prévisible.</p>"
        + g.encadre('<p class="chapeau" style="margin:0">Chaque euro gagné par le '
                    "travail augmente le revenu disponible.</p>")
        + g.points([
            ("Reprise d'emploi sécurisée",
             "Accepter un contrat ne fait plus perdre de droits : il n'y a plus de "
             "droits à perdre, seulement un socle qui reste."),
            ("Temps partiel intéressant",
             "Quelques heures par semaine rapportent exactement ce qu'elles valent, "
             "moins la contribution proportionnelle."),
            ("Revenus irréguliers",
             "Intérim, saisons, missions, auto-entreprise : le socle ne se recalcule "
             "pas à chaque changement, donc il ne se perd pas."),
            ("Fiche de paie lisible",
             "Un taux unique, un socle fixe : le revenu disponible se calcule de tête. "
             '<a href="simulateur.html">Essayer</a>'),
        ])
        + g.source("Note de doctrine, §5 — Le travail toujours gagnant.")
    )

    remplace = (
        "<p>Le socle remplace les prestations monétaires générales dont la fonction est "
        "de garantir un revenu minimal ou de compléter un bas revenu.</p>"
        + g.tableau(
            ["Dispositif actuel", "Traitement proposé"],
            [["RSA", "Remplacement par le socle adulte"],
             ["Prime d'activité", "Remplacement par le cumul socle + revenu du travail"],
             ["APL, pour la majorité des bénéficiaires", "Absorption dans le socle"],
             ["APL étudiantes", "Absorption dans le socle adulte dès 18 ans"],
             ["Certaines aides jeunes", "Remplacement par le socle adulte"],
             ["Certaines aides locales de revenu", "Extinction ou harmonisation"],
             ["Prestations monétaires générales sous condition de ressources",
              "Réexamen et absorption progressive"]],
            ["long", "long"],
            "Ce que le socle adulte absorbe")
        + "<p>La réforme est assumée : les aides au logement ne sont pas sanctuarisées "
        "comme un système parallèle. Pour la majorité des bénéficiaires, étudiants "
        "compris, elles sont absorbées dans le socle. C'est une condition de lisibilité "
        "et de neutralité — deux personnes ayant le même revenu ne doivent pas dépendre "
        "d'un maquis administratif différent selon leur logement, leur statut étudiant, "
        "leur bail ou leur situation familiale.</p>"
        + g.note(
            "<p>Trois familles de dispositifs ne sont <strong>pas</strong> absorbées : "
            "les compensations du handicap et de la dépendance, les dispositifs "
            "d'urgence et de protection, et les droits contributifs — chômage et "
            "retraites — qui relèvent de ce que l'on a cotisé. "
            "<a href=\"protections.html\">Voir ce qui reste à part</a>.</p>")
        + g.source("Note de doctrine, §6 et §12.")
    )

    residence = (
        "<p>Le socle est attaché à la <strong>résidence effective</strong> en France, "
        "et la nationalité seule ne suffit pas : un citoyen français durablement "
        "installé à l'étranger n'y a pas droit. Inversement, un résident étranger en "
        "séjour régulier y accède progressivement, selon le calendrier de convergence "
        "sur dix ans.</p>"
        "<p>Le contrôle change de nature. Il ne s'agit plus de vérifier en permanence "
        "des dizaines de conditions de ressources et de composition familiale, mais de "
        "garantir que chaque bénéficiaire est une personne réelle, unique, résidente et "
        "éligible : identité, unicité, résidence effective, régularité du séjour, "
        "décès, expatriation, doublons administratifs, usurpation d'identité.</p>"
        + g.source("Note de doctrine, §17 — Résidence effective, fraude et contrôle. "
                   "Voir aussi <a href=\"nouveaux-residents.html\">Nouveaux "
                   "résidents</a>.")
    )

    return page(
        "revenu-universel.html",
        f"Le socle — {g.TITRE_SITE}",
        "Le revenu universel adulte : 550 € par mois, individuel, dès 18 ans, "
        "conservé intégralement quand on travaille, en remplacement du RSA, de la prime "
        "d'activité et des aides au logement.",
        "Le socle",
        "Un revenu, une règle,<br>aucune condition de ressources",
        "Le revenu universel adulte est versé à chaque adulte qui vit en France. Il ne "
        "baisse jamais quand on gagne de l'argent : c'est sa propriété la plus "
        "importante.",
        [("individuel", "Un droit attaché à la personne", individuel),
         ("montant", "Combien, et combien ça coûte", montant),
         ("travail", "Pourquoi le travail devient toujours gagnant", travail),
         ("remplace", "Ce que le socle remplace", remplace),
         ("residence", "Qui y a droit", residence)],
        tete=reperes)


# -- 3. le calculateur -------------------------------------------------------

def simulateur():
    """La page du calculateur.

    Ce n'est PAS un simulateur de droits, et la page le dit trois fois : deux des
    trois paramètres dont il a besoin — le taux de la contribution de solidarité
    et le forfait enfant — ne sont pas fixés par la note, qui les renvoie
    explicitement au calibrage. Ils sont donc RÉGLABLES, et affichés comme tels.
    Un calculateur qui les donnerait pour acquis inventerait le programme au lieu
    de l'expliquer.
    """
    formulaire = (
        '<div class="carte creme">'
        '<div class="simulateur-court">'
        '<div class="tete"><h2 class="serif">Votre revenu disponible</h2>'
        '<span class="etiquette">Illustration, pas un droit</span></div>'
        '<form id="calcul" class="grille" novalidate>'
        + g.champ("revenu", "Revenu du travail", "1400",
                  "En euros par mois, avant contribution.",
                  attributs={"min": "0", "max": "50000", "step": "10",
                             "inputmode": "numeric"})
        + g.liste("statut", "Votre situation", [
            ("adulte", "Adulte de 18 à 64 ans"),
            ("senior", "Retraité — socle senior"),
        ], "adulte", "Le socle senior remplace l'ASPA, il n'augmente aucune pension.")
        + g.champ("enfants", "Enfants à charge", "0",
                  "Chaque enfant ouvre un crédit familial.",
                  attributs={"min": "0", "max": "12", "step": "1",
                             "inputmode": "numeric"})
        + g.liste("residence", "Résidence en France", [
            ("complet", "Français, ou résident depuis plus de 10 ans"),
            ("75", "Résident régulier depuis 9 à 10 ans"),
            ("50", "Résident régulier depuis 6 à 8 ans"),
            ("25", "Résident régulier depuis 3 à 5 ans"),
            ("0", "Résident régulier depuis moins de 3 ans"),
        ], "complet", "La convergence se fait sur dix ans.")
        + "</form></div></div>"
        + g.depliant(
            "Les trois paramètres que la note ne fixe pas",
            "<p>Le socle a une cible affichée ; le taux de la contribution et le "
            "forfait enfant, non — la note les renvoie au calibrage budgétaire. Ils "
            "sont donc réglables ici, et les chiffres ci-dessous en dépendent "
            "entièrement.</p>"
            "<p>Leurs valeurs par défaut ne sont pas des nombres ronds choisis "
            "à la main. La valeur par défaut d'un calculateur public finit par "
            "être citée comme « le chiffre du parti », et un chiffre rond n'a "
            "rien à opposer : celles-ci sont <strong>calculées</strong>. Le "
            f"taux de {pourcent(ch.boucler().taux)} est celui qui boucle le "
            f"financement du socle ; le forfait de "
            f"{eur(ch.FORFAIT_ILLUSTRATION)} est celui qui coûte exactement ce "
            "que le crédit familial remplace. "
            '<a href="financement.html">Voir le bouclage</a></p>'
            '<form id="reglages" class="grille" novalidate>'
            + g.liste("socle", "Socle adulte", [
                ("500", "500 € par mois — première marche"),
                ("550", "550 € par mois — cible"),
                ("600", "600 € par mois"),
            ], str(SOCLE_CIBLE), "Ordre de grandeur donné par la note (§4).")
            + g.champ("taux", "Contribution de solidarité",
                      f"{ch.boucler().taux * 100:.0f}",
                      "En % du revenu. Le taux qui boucle le financement.",
                      attributs={"min": "0", "max": "70", "step": "1",
                                 "inputmode": "numeric"})
            + g.champ("forfait", "Forfait enfant", str(ch.FORFAIT_ILLUSTRATION),
                      "En euros par mois. Le forfait qui équilibre le bloc "
                      "familial.",
                      attributs={"min": "0", "max": "1000", "step": "10",
                                 "inputmode": "numeric"})
            + "</form>", "reglages-bloc")
    )

    # Les barèmes 2026 de la colonne « aujourd'hui », écrits DANS la page.
    # Le script ne doit en recopier aucun : deux jeux de barèmes finiraient par
    # ne plus dire la même chose, et c'est la faute que ce dépôt s'interdit déjà
    # pour le texte du programme.
    baremes = ('<script id="baremes" type="application/json">'
               + json.dumps(ch.baremes_du_calculateur(), ensure_ascii=True)
               + "</script>")

    resultat = (
        '<div id="resultat" aria-live="polite">'
        + g.note("<p>Réglez les champs ci-dessus : le calcul se fait à la frappe, "
                 "dans votre navigateur. Si rien ne s'affiche, c'est que JavaScript "
                 "est désactivé — les formules sont alors données en clair plus "
                 "bas.</p>")
        + "</div>"
    )

    lecture = (
        "<p>Le calcul est volontairement réduit à trois lignes, parce que c'est tout "
        "ce que la réforme demande :</p>"
        + g.gestes([
            "<strong>On ajoute le socle</strong> — un montant fixe, connu d'avance, "
            "qui ne dépend d'aucune déclaration.",
            "<strong>On ajoute le revenu du travail, en entier</strong> — aucune aide "
            "ne baisse parce qu'il augmente.",
            "<strong>On retire la contribution de solidarité</strong> — un pourcentage "
            "unique du revenu du travail, le même pour tous.",
        ])
        + "<p>De cette combinaison naît la progressivité, sans barème compliqué : le "
        "socle est fixe, la contribution est proportionnelle. Aux revenus faibles, le "
        "socle dépasse ce que l'on paie, et l'on est <strong>bénéficiaire net</strong> ; "
        "aux revenus moyens, il est en partie repris ; aux revenus élevés, la "
        "contribution le dépasse largement et l'on est <strong>contributeur "
        "net</strong>.</p>"
        + g.tableau(
            ["Revenu annuel", "Effet du socle", "Effet redistributif"],
            [["Faible revenu", "Socle supérieur à l'impôt payé", "Bénéficiaire net"],
             ["Revenu moyen", "Socle partiellement repris par l'impôt",
              "Contribution nette modérée"],
             ["Haut revenu", "Impôt largement supérieur au socle", "Contributeur net"]],
            ["texte", "long", "texte"],
            f"La progressivité, avec un socle de {SOCLE_ANNUEL_TEXTE} par an et une "
            "contribution proportionnelle")
        + g.source("Note de doctrine, §18 — Financement : coût brut, coût net et "
                   "contribution de solidarité.")
    )

    reserves = (
        g.note(
            "<p><strong>Ce calculateur n'ouvre aucun droit et n'estime pas vos aides "
            "actuelles.</strong> Il illustre la mécanique d'une proposition : socle "
            "fixe, revenu entier, contribution proportionnelle. Il ne tient compte ni "
            "de la fiscalité de consommation, ni de la fiscalité foncière, ni du crédit "
            "d'impôt proportionnel par enfant, ni du bouclier transitoire prévu pour "
            "les familles modestes et monoparentales pendant les deux ou trois "
            "premières années.</p>", "avertissement")
        + g.points([
            ("Le taux est une hypothèse",
             "La note ne fixe aucun taux de contribution : elle dit seulement qu'il est "
             "proportionnel, identifié à part des cotisations, et qu'il finance le socle "
             'et les prestations non contributives maintenues. '
             '<a href="financement.html">Voir le financement</a>'),
            ("Le forfait enfant est une hypothèse",
             "La note prévoit un crédit familial en deux parties — un forfait et une "
             "réduction proportionnelle d'impôt — sans en donner le montant. Seul le "
             'forfait est simulé ici. <a href="familles.html">Voir les familles</a>'),
            ("Les compléments ne sont pas simulés",
             "Complément handicap, dépendance, aides d'urgence, assurance chômage "
             "contributive et pensions contributives s'ajoutent au socle et ne sont pas "
             'dans ce calcul. <a href="protections.html">Voir les protections</a>'),
            ("La colonne « aujourd'hui » est une estimation",
             "Elle applique les barèmes 2026 à la situation saisie, et elle ne "
             "connaît ni votre loyer, ni votre zone, ni votre trimestre de "
             "référence. Pour des situations chiffrées une par une, voir les "
             '<a href="cas-types.html">cas types</a> ; pour vos droits réels, '
             "seuls les organismes font foi "
             '(<a href="https://www.service-public.fr/">service-public.fr</a>).'),
        ])
    )

    return page(
        "simulateur.html",
        f"Calculer — {g.TITRE_SITE}",
        "Un calculateur d'illustration : ce que le revenu universel ajoute à votre "
        "revenu du travail, ce que la contribution de solidarité en reprend, et à "
        "partir de quel salaire on devient contributeur net.",
        "Calculer",
        "Socle, salaire,<br>contribution : le compte",
        "Trois opérations, et aucune condition de ressources. Réglez votre situation : "
        "le calcul se fait dans votre navigateur, rien n'est envoyé.",
        [("lecture", "Comment ce chiffre est obtenu", lecture),
         ("reserves", "Ce que ce calcul ne dit pas", reserves)],
        tete=formulaire + resultat,
        scripts=baremes + '<script src="moteur/simulateur.js" defer></script>')


# -- 3 bis. les cas types ----------------------------------------------------
#
# LA NOTE DEMANDE CES CAS-TYPES ET NE LES PRODUIT PAS. Elle désigne les familles
# monoparentales comme son risque social principal et renvoie leur chiffrage à
# plus tard (§20.2). Tant qu'ils manquent, la seule réponse du site à « est-ce
# que j'y gagne ? » est un calculateur qui ne connaît pas le système actuel.
#
# LA RÈGLE DE CETTE PAGE EST D'AFFICHER LES PERDANTS D'ABORD. Un jeu de
# cas-types qui ne montre que des gagnants ne tient pas le premier
# contre-exemple venu ; un jeu qui nomme ses perdants et dit ce qu'il propose
# pour eux est le seul dont on garde la main. Trois des sept perdent.

def _cas_type(cas) -> str:
    """Une situation, en une carte : le détail, les deux régimes, l'écart.

    La carte est encadrée parce qu'elle sera capturée et partagée hors du site —
    c'est ce qu'on fait d'un cas type, et il doit rester lisible seul.
    """
    badge = ('<span class="badge">perdant</span>' if cas.perdant
             else '<span class="badge proposition">gagnant</span>' if cas.gagnant
             else '<span class="badge proposition">à peu près neutre</span>')
    def detail(postes):
        """Les postes d'un régime, en une ligne. Un poste nul n'est pas un
        poste : « prime d'activité 0 € » n'apprend rien et alourdit la carte."""
        return " + ".join(
            f"{libelle} {eur(montant)}" if montant >= 0
            else f"{libelle} − {eur(-montant)}"
            for libelle, montant in postes if round(montant) != 0)
    signe = "+" if cas.ecart >= 0 else "−"
    corps = (
        g.tableau(
            ["Régime", "Composition", "Par mois"],
            [["Aujourd'hui", detail(cas.aujourd_hui),
              f"<strong>{eur(cas.avant)}</strong>"],
             ["Avec le socle", detail(cas.demain),
              f"<strong>{eur(cas.apres)}</strong>"],
             ["<strong>Écart</strong>", badge,
              f"<strong>{signe} {eur(abs(cas.ecart))}</strong> "
              f"({signe} {abs(cas.part) * 100:.0f} %)"]],
            ["texte", "long", "nombre"],
            f"{cas.nom} : aujourd'hui et avec le socle")
        + f"<p>{cas.lecture}</p>"
        + (g.note(f"<p><strong>Réserve.</strong> {cas.reserve}</p>")
           if cas.reserve else "")
    )
    return g.cle(cas.nom, cas.detail, corps,
                 identifiant="cas-" + ancre(cas.nom))


def cas_types():
    b = ch.boucler()
    cas = ch.cas_types()
    perdants = [c for c in cas if c.perdant]
    autres = [c for c in cas if not c.perdant]

    reperes = g.fiches([
        ("Situations chiffrées", str(len(cas)),
         "Des barèmes 2026 d'un côté, le programme de l'autre."),
        ("Dont perdantes", str(len(perdants)),
         "Elles sont détaillées en premier, avec ce qu'il faudrait pour "
         "les fermer."),
        ("Socle qui ne ferait aucun perdant", eur(ch.SOCLE_NEUTRALITE),
         f"Contre {eur(ch.SOCLE_CIBLE)} dans la cible de la note."),
    ])

    lecture = (
        "<p>Un programme qui ne publie que ses gagnants se fait définir par ses "
        "perdants. Cette page fait donc l'inverse : elle chiffre sept "
        "situations aux barèmes en vigueur, elle commence par celles qui "
        "perdent, et elle dit pour chacune ce qu'il faudrait décider pour que "
        "la perte disparaisse.</p>"
        + g.gestes([
            "<strong>La colonne « aujourd'hui » est au barème 2026</strong> — "
            "RSA, aide au logement, allocations familiales, AAH, ASPA, prime "
            "d'activité. Ce sont des montants publiés, vérifiables un par un.",
            "<strong>La colonne « avec le socle » applique la note</strong> — "
            f"socle de {eur(ch.SOCLE_CIBLE)}, forfait enfant de "
            f"{eur(ch.FORFAIT_ILLUSTRATION)}, contribution de "
            f"{pourcent(b.taux)} sur le revenu du travail.",
            "<strong>Rien d'autre ne bouge</strong> — la contribution est "
            "prise sur le revenu tel qu'il est versé aujourd'hui. Le sort de "
            "l'impôt sur le revenu n'est pas modélisé, parce que la note ne le "
            'tranche pas. <a href="financement.html#contribution-et-impot">Voir '
            "pourquoi c'est le point le plus important</a>.",
        ])
        + g.note(
            "<p><strong>Ce ne sont pas des droits, et ce ne sont pas des "
            "moyennes.</strong> Une aide au logement varie du simple au double "
            "selon la zone et le loyer ; une prime d'activité dépend du "
            "trimestre. Chaque cas type dit l'hypothèse qu'il retient, et elle "
            "est prise du côté défavorable au programme quand elle est "
            "incertaine — un résultat flatteur obtenu par une hypothèse "
            "généreuse serait le seul qu'on ne puisse pas défendre.</p>",
            "avertissement")
        + g.repere("Barèmes au 1ᵉʳ avril 2026 pour les prestations revalorisées, "
                   "au 1ᵉʳ janvier 2026 pour l'ASPA. Seuil de pauvreté INSEE : "
                   f"{eur(ch.SEUIL_PAUVRETE)} par mois pour une personne seule.")
    )

    ceux_qui_perdent = (
        "<p>Les trois situations ci-dessous perdent avec la calibration que la "
        "note retient. Deux d'entre elles se ferment par une décision qui ne "
        "coûte presque rien ; la troisième est l'arbitrage central du "
        "programme.</p>"
        + "".join(_cas_type(c) for c in perdants)
        + g.note(
            "<p><strong>Ce que ces trois cas ont en commun : ils n'ont pas de "
            "revenu du travail.</strong> Le socle leur apporte moins que "
            "l'empilement actuel parce que cet empilement était, pour eux, "
            "plus généreux que le socle — c'est la contrepartie arithmétique "
            "de la simplicité. Le programme ne peut pas à la fois supprimer le "
            "millefeuille et garantir que personne n'y perde, sauf à porter le "
            f"socle à {eur(ch.SOCLE_NEUTRALITE)} et la contribution à "
            f"{pourcent(ch.boucler(ch.SOCLE_NEUTRALITE).taux)}. "
            '<a href="financement.html#arbitrage">Voir ce que coûte chaque '
            "niveau de socle</a></p>", "vigilance")
    )

    ceux_qui_gagnent = (
        "<p>Les quatre autres situations gagnent ou sont à peu près neutres. "
        "Les deux dernières sont les meilleurs arguments du programme, et le "
        "site ne les chiffrait nulle part.</p>"
        + "".join(_cas_type(c) for c in autres)
    )

    profil = (
        "<p>Mis bout à bout, les sept cas dessinent un profil, et il vaut mieux "
        "le connaître avant qu'un institut ne le publie.</p>"
        + g.points([
            ("Les grands gagnants sont au milieu",
             "Le couple bi-actif est le plus gros gain de la série, parce que "
             "l'individualisation double un versement là où le système actuel, "
             "qui raisonne par foyer, ne verse presque rien. C'est mérité, "
             "c'est cohérent, et c'est très coûteux."),
            ("Les perdants sont tout en bas",
             "Les trois perdants sont les trois situations sans revenu du "
             "travail. Une réforme qui prend au premier décile pour "
             "redistribuer au cinquième est défendable si on l'assume ; elle "
             "est indéfendable si on la découvre en campagne."),
            ("Les jeunes sont le meilleur terrain",
             "L'étudiant décohabitant multiplie par trois sa ressource "
             "publique, et c'est le seul cas où le programme tient exactement "
             "ce qu'il promet : plus simple, plus généreux, sans dossier."),
            ("Le travail est mieux traité partout",
             "Aucun des sept ne perd en travaillant davantage. C'est vrai, "
             "c'est vérifiable, et c'est le seul argument qui ne dépende "
             "d'aucune hypothèse de calibrage."),
        ])
        + g.note(
            f"<p>{ch.contrainte_structurelle()}</p>", "vigilance")
        + g.repere("Écarts calculés à partir des sept situations ci-dessus, "
                   f"pour un socle de {eur(ch.SOCLE_CIBLE)} et une contribution "
                   f"de {pourcent(b.taux)}.")
    )

    return page(
        "cas-types.html",
        f"Cas types — {g.TITRE_SITE}",
        "Sept situations chiffrées aux barèmes 2026, avant et après la "
        "réforme, perdants compris : célibataire au RSA, famille "
        "monoparentale, minimum vieillesse, AAH, SMIC, couple bi-actif, "
        "étudiant.",
        "Cas types",
        "Sept situations,<br>perdants compris",
        "Ce que chacun touche aujourd'hui, ce qu'il toucherait avec le socle, "
        "et l'écart. Les situations qui perdent sont en premier.",
        [("lecture", "Comment ces chiffres sont faits", lecture),
         ("perdants", "Les situations qui perdent", ceux_qui_perdent),
         ("gagnants", "Les situations qui gagnent", ceux_qui_gagnent),
         ("profil", "Ce que l'ensemble dessine", profil)],
        tete=reperes)


# -- 4. les jeunes -----------------------------------------------------------

def jeunes():
    reperes = g.fiches([
        ("Ouverture du socle", "18 ans", "Contre 25 ans pour le RSA aujourd'hui."),
        ("Socle mensuel", f"{SOCLE_CIBLE}&nbsp;€",
         "Le même que pour tout adulte : il n'y a pas de socle jeune au rabais."),
        ("Conditions de ressources des parents", "Aucune",
         "Le droit est propre, l'administration n'a plus à reconstituer la solidarité "
         "familiale."),
        ("APL étudiantes", "Absorbées",
         "Remplacées par le socle, versé directement et librement utilisable."),
    ])

    ouverture = (
        "<p>Le revenu universel adulte est ouvert <strong>à partir de 18 ans</strong>. "
        "C'est une décision structurante, et elle met fin à une anomalie : aujourd'hui "
        "les 18-25 ans sont largement privés du droit commun de la solidarité — l'accès "
        "au RSA leur est fermé sauf cas particuliers — tout en étant maintenus dans un "
        "système complexe d'aides étudiantes, d'APL, de dépendance familiale, d'aides "
        "locales et de dispositifs ciblés.</p>"
        "<p>Avec le socle, <span class=\"cle-texte\">les jeunes sont largement "
        "gagnants</span> : ils reçoivent, dès leur majorité, le même montant que "
        "n'importe quel adulte, sans avoir à démontrer que leurs parents ne les aident "
        "pas, sans dossier à renouveler, et sans que la somme dépende de leur logement "
        "ou de leur statut.</p>"
        + g.points([
            ("Un droit propre",
             "Le socle est individuel : il ne dépend ni du revenu des parents, ni du "
             "fait d'être rattaché à leur foyer fiscal, ni d'une rupture familiale à "
             "prouver."),
            ("Étudier, travailler, ou les deux",
             "Un emploi étudiant ne fait rien perdre : le salaire s'ajoute au socle, "
             "moins la contribution proportionnelle."),
            ("Se loger sans dossier",
             "Les APL étudiantes disparaissent dans le socle, qui est versé en argent "
             "libre d'usage plutôt qu'en subvention liée au bail."),
            ("Une relation clarifiée avec les parents",
             "L'administration n'a plus à reconstituer en permanence la solidarité "
             "familiale réelle ou supposée."),
        ])
        + g.source("Note de doctrine, §13 — Jeunes adultes et étudiants.")
    )

    bourses = (
        "<p>En contrepartie, les aides spécifiques aux étudiants sont recentrées. Les "
        "bourses ne doivent plus servir à compenser l'absence de socle adulte, puisque "
        "ce socle existera : les <strong>bourses de vie courante</strong> sont donc "
        "réexaminées et limitées aux cas particuliers. Les bourses restent possibles "
        "pour :</p>"
        + '<ul class="serree">'
        + "".join(f"<li>{motif}</li>" for motif in [
            "des frais de formation élevés",
            "une mobilité géographique nécessaire",
            "du matériel ou de l'équipement professionnel",
            "l'excellence ou le mérite",
            "une rupture familiale",
            "un handicap",
            "une situation sociale exceptionnelle",
        ])
        + "</ul>"
        + g.note("<p>Le principe général est que <strong>le socle adulte constitue la "
                 "vie courante des jeunes majeurs</strong> : logement, nourriture, "
                 "transports. Les bourses financent ce qui est propre aux études, pas "
                 "ce qui est commun à tous les adultes.</p>")
        + g.source("Note de doctrine, §6 et §13.")
    )

    reserve = (
        g.note(
            "<p>Un point de vigilance concerne les zones où le logement est très cher : "
            "l'absorption des APL est cohérente, mais elle peut y créer des tensions, et "
            "la réforme du logement doit suivre rapidement pour éviter que le socle ne "
            "soit capté par les loyers. C'est la note elle-même qui l'écrit.</p>",
            "avertissement")
        + '<p class="actions"><a class="bouton" href="simulateur.html">Calculer avec un '
        'emploi étudiant</a><a href="calendrier.html">Voir les risques identifiés</a></p>'
        + g.source("Note de doctrine, §20.3 — Risque logement.")
    )

    return page(
        "jeunes.html",
        f"Jeunes et étudiants — {g.TITRE_SITE}",
        "Le revenu universel ouvert dès 18 ans : un droit propre, sans condition de "
        "ressources des parents, qui remplace les APL étudiantes et recentre les "
        "bourses sur les frais d'études.",
        "Jeunes et étudiants",
        "Majeur à 18 ans,<br>donc éligible à 18 ans",
        "Aujourd'hui, la solidarité commence à 25 ans et passe par un dossier. Demain, "
        "elle commence à la majorité et se verse sans être demandée.",
        [("ouverture", "Le socle dès la majorité", ouverture),
         ("bourses", "Ce que deviennent les bourses", bourses),
         ("reserve", "La réserve que la note fait elle-même", reserve)],
        tete=reperes)


# -- 5. les familles ---------------------------------------------------------

def familles():
    credit = (
        "<p>La réforme concilie deux principes : individualiser au maximum les droits "
        "des adultes, et maintenir une incitation claire à la formation de familles "
        "stables et à la natalité. La situation démographique justifie de conserver une "
        + g.mot("redistribution horizontale",
                "Transfert entre ménages de même niveau de vie mais de charges "
                "différentes — ici, des adultes sans enfant vers les parents.")
        + " des adultes sans enfant vers les parents : élever un enfant représente un "
        "coût privé et un bénéfice collectif.</p>"
        "<p>Un forfait pur serait très lisible, mais il réduirait fortement le soutien "
        "aux familles des classes moyennes supérieures et aisées, alors que la politique "
        "familiale doit rester universelle dans son principe. La proposition est donc de "
        "remplacer les prestations familiales générales et une grande partie du "
        + g.mot("quotient familial",
                "Mécanisme actuel qui réduit l'impôt sur le revenu en fonction du "
                "nombre de parts du foyer, donc du nombre d'enfants.")
        + " par un <strong>crédit familial par enfant</strong>, en deux parties.</p>"
        + g.tableau(
            ["Élément", "Fonction"],
            [["Forfait enfant",
              "Soutien monétaire universel au coût de l'enfant, versé pour chaque "
              "enfant."],
             ["Crédit d'impôt proportionnel",
              "Maintien d'une incitation fiscale pour les familles imposables, y compris "
              "les plus aisées."],
             ["Compléments ciblés transitoires",
              "Protection des familles modestes et monoparentales pendant la "
              "réforme."]],
            ["texte", "long"],
            "L'architecture indicative du soutien à l'enfant")
        + g.encadre(
            '<p class="chapeau" style="margin:0 0 .6rem">Le soutien public à l\'enfant '
            "doit être explicite, lisible et universel.</p>"
            "<p>Il doit reconnaître à la fois le coût immédiat de l'enfant pour le foyer "
            "et la contribution démographique des familles à la soutenabilité du "
            "pays.</p>")
        + g.note(
            "<p>Deux écueils sont nommés par la note : une dépense excessive si le "
            "crédit d'impôt est totalement déplafonné, et une perte de soutien pour les "
            "ménages qui contribuent fortement à l'impôt et à la natalité. La doctrine "
            "recommandée est donc un soutien familial <strong>explicite, horizontal, "
            "universel, mais fiscalement maîtrisé</strong>.</p>")
        + g.source("Note de doctrine, §8 — Soutien aux enfants et redistribution "
                   "horizontale.")
    )

    bouclier = (
        "<p>L'absorption des APL et des prestations familiales dans un système plus "
        "simple peut créer des perdants transitoires, notamment parmi les familles "
        "modestes et monoparentales. La note identifie ce point comme "
        "<strong>le principal risque social de la réforme</strong>, et non comme un "
        "détail d'application.</p>"
        "<p>Les familles monoparentales cumulent souvent plusieurs fragilités : un seul "
        "revenu d'activité, des coûts fixes élevés, un logement contraint, la garde des "
        "enfants, des pensions alimentaires irrégulières, un risque de pauvreté plus "
        "élevé. Elles bénéficient aujourd'hui de prestations multiples, parfois "
        "complexes mais importantes.</p>"
        "<p>La réforme prévoit donc un <strong>bouclier transitoire</strong>, dont les "
        "six caractéristiques sont posées d'avance pour qu'il ne devienne pas une "
        "prestation permanente :</p>"
        + '<ul class="serree">'
        + "".join(f"<li>{trait}</li>" for trait in [
            "temporaire",
            "ciblé",
            "décroissant",
            "non transmissible",
            "non renouvelable",
            "concentré sur les deux ou trois premières années de la réforme",
        ])
        + "</ul>"
        + g.encadre(
            '<p class="chapeau" style="margin:0">Aucun ménage modeste avec enfants, et '
            "en particulier aucune famille monoparentale modeste, ne doit subir une "
            "perte brutale de revenu disponible pendant les premières années de "
            "transition.</p>")
        + g.note("<p>Le bouclier ne doit pas recréer durablement le millefeuille que la "
                 "réforme supprime : son objectif est d'éviter les ruptures de revenu "
                 "pendant la bascule, puis de s'éteindre.</p>", "vigilance")
        + g.source("Note de doctrine, §7 — Transition spécifique pour les familles "
                   "modestes et monoparentales.")
    )

    couple = (
        "<p>Le socle reste individualisé : il ne pénalise pas la mise en couple et ne "
        "crée pas de dépendance économique entre conjoints. Se mettre en ménage ne fait "
        "donc rien perdre, et se séparer ne déclenche aucun recalcul.</p>"
        "<p>Le parti assume par ailleurs une <strong>préférence modérée pour la "
        "stabilité familiale</strong>, notamment par le mariage ou des formes juridiques "
        "équivalentes d'engagement durable. Cette préférence ne passe pas par une "
        "familialisation du socle — ce serait contradictoire avec la simplicité et "
        "l'autonomie individuelle — mais par la fiscalité familiale : le mariage peut "
        "continuer à produire des effets fiscaux limités, transparents et compatibles "
        "avec l'impôt proportionnel.</p>"
        + g.points([
            ("Individualisation du socle",
             "Le droit au revenu ne dépend jamais de la situation conjugale."),
            ("Reconnaissance fiscale limitée",
             "Sans revenir à un quotient conjugal complexe, la loi peut reconnaître "
             "qu'un couple stable est une unité de solidarité privée et d'éducation des "
             "enfants."),
            ("Les obligations privées demeurent",
             "Pensions alimentaires et obligations parentales continuent de relever du "
             "droit privé : elles ne conditionnent pas le socle, mais elles ne "
             "disparaissent pas."),
            ("Moins d'enquêtes sur la vie privée",
             "Le socle réduit l'intrusion administrative dans la vie familiale, sans "
             "supprimer les obligations civiles entre personnes privées."),
        ])
        + g.source("Note de doctrine, §9 — Couple, mariage et stabilité familiale ; "
                   "§11 — Pensions alimentaires et solidarités privées.")
    )

    return page(
        "familles.html",
        f"Familles — {g.TITRE_SITE}",
        "Le crédit familial par enfant — forfait plus crédit d'impôt proportionnel —, "
        "le bouclier transitoire pour les familles monoparentales, et un socle qui ne "
        "dépend jamais de la situation conjugale.",
        "Familles",
        "Un socle par adulte,<br>un crédit par enfant",
        "Les droits des adultes sont individualisés ; le soutien aux enfants, lui, reste "
        "explicite et universel — et les familles monoparentales sont protégées pendant "
        "la bascule.",
        [("credit", "Le crédit familial par enfant", credit),
         ("bouclier", "Le bouclier des familles monoparentales", bouclier),
         ("couple", "Couple, mariage, pensions alimentaires", couple)])


# -- 6. ce qui reste à part --------------------------------------------------

def protections():
    handicap = (
        "<p>Le socle <strong>n'absorbe pas</strong> les dispositifs liés au handicap. "
        "L'"
        + g.mot("AAH", "Allocation aux adultes handicapés : prestation actuelle versée "
                       "aux personnes dont le handicap limite durablement l'accès à "
                       "l'emploi.")
        + " est transformée en <strong>complément handicap</strong>, versé en plus du "
        "revenu universel : le socle est le plancher commun, le complément compense "
        "l'incapacité ou la restriction durable d'activité.</p>"
        + g.tableau(
            ["Politique", "Traitement proposé"],
            [["AAH", "Complément handicap, en plus du socle"],
             ["PCH — compensation du handicap", "Maintien à part"],
             ["APA — autonomie des personnes âgées", "Maintien à part"],
             ["Protection de l'enfance", "Maintien à part"],
             ["Hébergement d'urgence", "Maintien à part"],
             ["Grande exclusion", "Accompagnement spécifique"],
             ["Santé urgente et santé publique", "Maintien à part"]],
            ["texte", "long"],
            "Les dispositifs que le socle ne remplace pas")
        + g.note(
            "<p>Cette distinction répond à l'objection la plus fréquente faite au revenu "
            "universel : l'idée qu'un montant unique remplacerait indistinctement toutes "
            "les formes de solidarité. <strong>Ce n'est pas la position du parti.</strong> "
            "Ces besoins sont spécifiques, souvent individualisés, et ne peuvent pas être "
            "traités par un transfert uniforme.</p>")
        + g.source("Note de doctrine, §10 — Handicap, dépendance et vulnérabilités "
                   "spécifiques.")
    )

    logement = (
        "<p>Les aides personnelles au logement jouent un rôle social réel, mais elles "
        "cumulent plusieurs défauts : complexité, forte dépendance au statut résidentiel, "
        "interaction avec les loyers, traitement différencié des ménages, coût budgétaire "
        "élevé, faible lisibilité. Elles sont donc <strong>absorbées dans le socle pour "
        "la majorité des bénéficiaires</strong> : étudiants, jeunes actifs, personnes "
        "seules, et la plupart des ménages sans vulnérabilité spécifique. Le socle "
        "remplace la subvention personnalisée au logement par un montant libre "
        "d'usage.</p>"
        "<p>Pour les familles modestes, en particulier monoparentales, une transition "
        "spécifique est nécessaire afin d'éviter une perte brutale — c'est l'objet du "
        "<a href=\"familles.html#bouclier\">bouclier transitoire</a>.</p>"
        "<p>Le <strong>logement social</strong> est un sujet distinct : c'est une "
        "redistribution en nature et une allocation administrative du logement, qui pose "
        "ses propres problèmes — files d'attente, faible mobilité, effets de rente, "
        "inégalités entre bénéficiaires et non-bénéficiaires, mauvaise allocation "
        "territoriale. Le parti souhaite à terme réduire drastiquement sa place dans sa "
        "forme actuelle, au profit d'une politique d'offre, de construction, de mobilité "
        "résidentielle et de réforme foncière. Cela relève d'un chapitre séparé du "
        "programme.</p>"
        + g.note("<p>La règle retenue ici est simple : <strong>les APL sont absorbées "
                 "dans le socle pour la majorité des bénéficiaires</strong> ; le logement "
                 "social et la réforme structurelle du logement sont traités "
                 "séparément.</p>")
        + g.source("Note de doctrine, §12 — Logement.")
    )

    chomage = (
        "<p>Le socle remplace les minima sociaux de base, mais <strong>il ne remplace pas "
        "l'assurance chômage</strong>. Celle-ci est reconstruite comme un système "
        "strictement contributif : elle relève de l'assurance, non de la solidarité "
        "nationale générale. Dans cette logique, elle pourrait devenir plus clairement "
        "assurantielle, potentiellement facultative ou modulable, avec des droits "
        "correspondant aux contributions effectivement versées.</p>"
        + g.tableau(
            ["Fonction", "Instrument"],
            [["Socle minimal permanent", "Revenu universel"],
             ["Perte temporaire de revenu d'activité", "Assurance chômage contributive"],
             ["Formation ou reconversion",
              "Dispositifs spécifiques, éventuellement assurantiels"],
             ["Fin de droits", "Retour au seul socle, sans bascule administrative "
                               "complexe"]],
            ["texte", "long"],
            "Qui fait quoi, en cas de perte d'emploi")
        + "<p>La perte d'emploi ne plonge donc plus dans une succession de dispositifs : "
        "<span class=\"cle-texte\">le socle demeure</span>, et les compléments dépendent "
        "des droits assurantiels acquis.</p>"
        + g.source("Note de doctrine, §14 — Chômage.")
    )

    retraites = (
        "<p>Le revenu universel senior est un <strong>socle de solidarité "
        "vieillesse</strong>. Il remplace pour l'essentiel l'"
        + g.mot("ASPA", "Allocation de solidarité aux personnes âgées, l'actuel minimum "
                        "vieillesse, versée sous condition de ressources.")
        + " et les dispositifs non contributifs de minimum vieillesse. La position est "
        "explicite : <strong>aucune pension existante n'a vocation à augmenter du fait de "
        "cette réforme.</strong></p>"
        "<p>La France consacre déjà une part très élevée de sa richesse nationale aux "
        "retraites. Le chapitre retraites du programme assume une trajectoire "
        "d'économies, une clarification entre solidarité et contributivité, et le "
        "développement de la capitalisation. Cinq principes sont retenus ici :</p>"
        + g.gestes([
            "le socle senior garantit une solidarité aux personnes âgées ;",
            "les pensions contributives relèvent des droits acquis et du chapitre "
            "retraites ;",
            "la réforme ne crée aucune hausse générale des pensions ;",
            "les économies sur la dépense vieillesse sont détaillées dans le chapitre "
            "dédié ;",
            "la solidarité vieillesse est financée par l'impôt, les droits contributifs "
            "par cotisations ou capitalisation.",
        ])
        + g.note("<p>Le socle senior ne doit pas devenir une nouvelle couche de dépense "
                 "sur un système déjà coûteux. Le détail du régime de retraite proposé "
                 "— comptes notionnels, taux unique, garantie vieillesse — fait l'objet "
                 "d'un <a href=\"https://github.com/g-pliberal/retraitecomptenotionelle\">"
                 "programme et d'un simulateur séparés</a>.</p>")
        + g.source("Note de doctrine, §15 — Retraites : RU senior et maîtrise de la "
                   "dépense.")
    )

    return page(
        "protections.html",
        f"Ce qui reste à part — {g.TITRE_SITE}",
        "Handicap, dépendance, protection de l'enfance, hébergement d'urgence, chômage "
        "contributif, pensions : les dispositifs que le revenu universel ne remplace "
        "pas, et pourquoi.",
        "Ce qui reste à part",
        "Un socle uniforme<br>ne règle pas tout",
        "Le revenu universel remplace les aides générales de revenu. Il ne touche ni aux "
        "compensations du handicap, ni à l'urgence, ni à ce que l'on a cotisé.",
        [("handicap", "Handicap, dépendance, urgence", handicap),
         ("logement", "Logement : absorption des APL, réforme séparée", logement),
         ("chomage", "Chômage : une assurance, pas une aide", chomage),
         ("retraites", "Retraites : un socle, pas une hausse", retraites)])


# -- 7. les nouveaux résidents -----------------------------------------------

def nouveaux_residents():
    principe = (
        "<p>Le revenu universel est un droit attaché à l'appartenance stable à la "
        "communauté nationale. Il n'est pas conçu comme une prestation immédiatement "
        "ouverte à toute personne présente sur le territoire, mais comme le socle de "
        "solidarité d'une société politique durable. D'où un principe unique :</p>"
        + g.encadre('<p class="chapeau" style="margin:0">Les droits sociaux universels et '
                    "les contributions de solidarité doivent progresser ensemble.</p>")
        + "<p>Pour les <strong>citoyens français</strong> résidant effectivement en "
        "France, le socle est ouvert immédiatement et intégralement. Pour les "
        "<strong>ressortissants étrangers</strong>, l'accès complet est acquis après dix "
        "ans de résidence régulière, sauf exceptions prévues par la loi ou par les "
        "engagements européens et internationaux de la France.</p>"
        "<p>Pendant cette période, le résident étranger relève d'un régime transitoire : "
        "il ne perçoit pas immédiatement le socle complet, mais il ne supporte pas "
        "immédiatement la contribution complète de solidarité ; et la part de "
        "contribution qui excède ses droits immédiats peut être "
        "<strong>créditée sur un compte individuel de solidarité</strong>, mobilisable "
        "lors de l'accès complet au régime, de la naturalisation ou d'une installation "
        "durable reconnue.</p>"
        + g.note("<p>Pas de droit complet sans rattachement durable et effectif, mais pas "
                 "de contribution complète sans droits correspondants.</p>")
        + g.source("Note de doctrine, §16 — Accès des étrangers.")
    )

    bareme = (
        "<p>Le barème indicatif de convergence est le suivant. La colonne des droits et "
        "celle des devoirs montent ensemble, par construction.</p>"
        + g.tableau(
            ["Durée de résidence régulière", "Droit au revenu universel",
             "Contribution de solidarité", "Traitement doctrinal"],
            [["0 à 2 ans", "0 % du socle", "0 % à 25 %", "Phase d'installation"],
             ["3 à 5 ans", "25 % du socle", "25 % à 50 %", "Rattachement initial"],
             ["6 à 8 ans", "50 % du socle", "50 % à 75 %", "Intégration durable"],
             ["9 à 10 ans", "75 % du socle", "75 % à 100 %", "Convergence"],
             ["Après 10 ans", "100 % du socle", "100 %", "Régime commun"]],
            ["texte", "nombre", "nombre", "long"],
            "Barème indicatif de convergence sur dix ans")
        + "<p>La <strong>naturalisation</strong> entraîne l'accès au régime commun : elle "
        "marque l'entrée complète dans la communauté politique nationale. Des mécanismes "
        "d'accès accéléré peuvent être prévus pour les personnes démontrant une "
        "contribution significative et durable : activité professionnelle déclarée, "
        "paiement régulier de l'impôt et des cotisations, carte de résident, diplôme "
        "obtenu en France suivi d'une insertion professionnelle, création d'entreprise ou "
        "emploi de salariés.</p>"
        "<p>Le régime applicable aux citoyens de l'Union européenne doit respecter les "
        "engagements européens de la France. Le principe demeure que l'accès au socle "
        "complet suppose un droit au séjour régulier et un rattachement réel à la société "
        "française : les séjours courts ou dépourvus d'ancrage économique et social "
        "n'ouvrent pas automatiquement le régime complet.</p>"
        + g.source("Note de doctrine, §16.")
    )

    hors = (
        "<p>Les protections fondamentales sont maintenues <strong>hors du revenu "
        "universel</strong>, et ne suivent donc pas ce barème :</p>"
        + '<ul class="serree">'
        + "".join(f"<li>{item}</li>" for item in [
            "la protection de l'enfance",
            "l'hébergement d'urgence",
            "les soins urgents",
            "la santé publique",
            "le droit d'asile",
            "la lutte contre les violences",
            "l'aide humanitaire minimale",
        ])
        + "</ul>"
        + g.note(
            "<p>Ce mécanisme n'est pas le cœur du financement de la réforme : c'est une "
            "clause de soutenabilité, de réciprocité et d'acceptabilité. Il évite à la "
            "fois le guichet ouvert immédiat et la contribution sans droits.</p>")
        + g.note(
            "<p>La note identifie ici un risque juridique : la transition sur dix ans "
            "devra être expertisée au regard du droit constitutionnel et européen. La "
            "doctrine reste fondée sur la résidence effective, la contribution, l'accès "
            "progressif aux droits et la réciprocité — <strong>non sur une exclusion "
            "purement nationalitaire</strong>.</p>", "vigilance")
        + g.source("Note de doctrine, §16 et §20.5 — Risque juridique.")
    )

    controle = (
        "<p>Le socle est attaché à la <strong>résidence effective</strong>, et la "
        "nationalité seule ne suffit pas : un Français durablement installé à l'étranger "
        "n'en bénéficie pas. Cette condition est centrale pour la soutenabilité du "
        "système.</p>"
        "<p>La simplification réduit certaines fraudes — celles qui vivent des seuils, "
        "des déclarations complexes et des changements de situation. En revanche, elle "
        "exige un contrôle plus strict de quelques critères fondamentaux :</p>"
        + '<ul class="serree">'
        + "".join(f"<li>{item}</li>" for item in [
            "l'identité",
            "l'unicité du bénéficiaire",
            "la résidence effective",
            "la régularité du séjour",
            "le décès",
            "l'expatriation",
            "les doublons administratifs",
            "l'usurpation d'identité",
        ])
        + "</ul>"
        + "<p>Le contrôle social change ainsi de nature : il ne s'agit plus de vérifier "
        "en permanence des dizaines de conditions de ressources ou de composition "
        "familiale, mais de garantir que chaque bénéficiaire est une personne "
        "<strong>réelle, unique, résidente et éligible</strong>.</p>"
        + g.source("Note de doctrine, §17 — Résidence effective, fraude et contrôle.")
    )

    return page(
        "nouveaux-residents.html",
        f"Nouveaux résidents — {g.TITRE_SITE}",
        "Droits et devoirs progressifs sur dix ans : le barème de convergence vers le "
        "socle complet, le compte individuel de solidarité, et les protections "
        "maintenues hors du revenu universel.",
        "Nouveaux résidents",
        "Les droits et les devoirs<br>avancent ensemble",
        "Un socle immédiat et entier pour les citoyens français résidant en France ; pour "
        "les résidents étrangers, une convergence sur dix ans où l'accès aux droits et la "
        "contribution montent du même pas.",
        [("principe", "Le principe", principe),
         ("bareme", "Le barème de convergence", bareme),
         ("hors", "Ce qui reste hors du barème", hors),
         ("controle", "Résidence effective et contrôle", controle)])


# -- 8. le financement -------------------------------------------------------
#
# CETTE PAGE PORTE LE CHIFFRAGE, et c'est le seul endroit du site où une phrase
# ne vient pas de la note. La note pose la règle — « présenté en coût net,
# jamais seulement en coût brut » (§18) — et s'arrête là. La page publiait donc
# 264 Md€ en gros, disait qu'il fallait regarder le coût net, et ne le donnait
# pas : elle posait la question et laissait la réponse à l'adversaire.
#
# Tous les nombres ci-dessous sortent de `chiffrage.py`. Aucun n'est recopié.

def financement():
    b = ch.boucler()
    reperes = g.fiches([
        ("Coût brut du socle adulte", md(b.brut),
         f"{ch.SOCLE_CIBLE} € par mois pour environ 40 millions de personnes "
         "de 18 à 64 ans."),
        ("Coût net, une fois les prestations absorbées", md(b.net),
         "C'est ce chiffre-là qu'il faut financer, et lui seul."),
        ("Contribution de solidarité correspondante", pourcent(b.taux),
         "Sur une assiette large, de l'ordre de celle de la CSG."),
    ])

    lignes = [[f"<strong>Coût brut</strong> — {ch.SOCLE_CIBLE} € × 12 × 40 millions",
               f"<strong>{md(b.brut)}</strong>", ""]]
    for poste in ch.ABSORBEES:
        lignes.append([poste.libelle, f"− {md(poste.milliards)}", poste.detail])
    lignes.append(["<strong>Coût net à financer</strong>",
                   f"<strong>{md(b.net)}</strong>",
                   "Le seul chiffre qui commande le reste."])

    net = (
        "<p>La note pose une règle de présentation et n'en tire pas les "
        "conséquences : le revenu universel doit être présenté <strong>en coût "
        "net, jamais seulement en coût brut</strong>. Voici donc le coût net. "
        "Il est calculé à partir des dépenses publiques constatées, et chaque "
        "ligne porte sa source.</p>"
        + g.tableau(
            ["Poste", "Montant annuel", "Ce que c'est"],
            lignes, ["long", "nombre", "long"],
            "Du coût brut au coût net du socle adulte")
        + g.note(
            "<p><strong>Les prestations familiales n'apparaissent pas dans ce "
            "tableau, et c'est volontaire.</strong> La note ne les supprime "
            "pas : elle les remplace par le crédit familial (§8). Une "
            "prestation remplacée n'est pas une économie — elle finance le "
            "dispositif qui la remplace. Les inscrire ici ferait apparaître "
            f"{md(ch.CONTREPARTIE_FAMILIALE_TOTALE)} de recettes qui "
            "n'existent pas, et ce serait la première chose qu'un "
            "contradicteur démonterait.</p>")
        + g.repere("Dépenses constatées : CNAF, comptes 2024 ; prime "
                   "d'activité, PLF 2024. Coût brut calculé sur l'hypothèse de "
                   "population de la note elle-même (§4).")
    )

    taux = (
        f"<p>Financer {md(b.net)} suppose une assiette. La seule assiette large "
        "déjà en place est celle de la CSG : elle rapporte "
        f"{md(ch.CSG_RENDEMENT)} à un taux moyen d'environ "
        f"{pourcent(ch.CSG_TAUX_MOYEN)}, elle est donc de l'ordre de "
        f"{md(ch.ASSIETTE_LARGE)}. Le rapport donne le taux :</p>"
        + g.tableau(
            ["Ce qu'il faut financer", "Assiette", "Contribution de solidarité"],
            [[md(b.net), md(ch.ASSIETTE_LARGE),
              f"<strong>{pourcent(b.taux)}</strong>"]],
            ["nombre", "nombre", "nombre"],
            "Le taux de la contribution, pour un socle de "
            f"{ch.SOCLE_CIBLE} € par mois")
        + "<p>Ce taux est un chiffre lourd, et il vaut mieux l'écrire soi-même "
        "que se le faire écrire. Il a une contrepartie, que le site ne disait "
        "nulle part — <strong>le point de bascule</strong> : le revenu à partir "
        "duquel la contribution dépasse le socle reçu.</p>"
        + g.engagements([
            (pourcent(b.taux), "La contribution de solidarité",
             "Un taux unique, sur une assiette large, pour financer le socle."),
            (eur(b.bascule_mensuelle), "Le point de bascule",
             "En dessous de ce revenu mensuel, on reçoit plus qu'on ne verse. "
             "C'est le cas de l'écrasante majorité des actifs."),
        ])
        + g.repere("Rendement et taux moyen de la CSG, 2025. L'assiette en est "
                   "déduite, et le taux est le rapport du coût net à cette "
                   "assiette.")
    )

    arbitrage = (
        "<p>Le taux ci-dessus dépend entièrement du niveau du socle, et c'est "
        "là qu'est l'arbitrage réel du programme. Le voici en entier, y compris "
        "la calibration que la note n'envisage pas : celle qui ne fait "
        "<em>aucun</em> perdant.</p>"
        + g.tableau(
            ["Socle adulte", "Coût net", "Contribution", "Point de bascule",
             "Ce que ça fait"],
            [[eur(c.socle) + " / mois", md(c.net), pourcent(c.taux),
              eur(c.bascule_mensuelle) + " / mois",
              ("Première marche de la transition (note, §20.1)."
               if c.socle == ch.SOCLE_MARCHE else
               "Cible de régime stabilisé (note, §4)."
               if c.socle == ch.SOCLE_CIBLE else
               "Le socle auquel plus personne ne perd — voir les "
               '<a href="cas-types.html">cas types</a>.'
               if c.socle == ch.SOCLE_NEUTRALITE else
               "Haut de la fourchette citée par la note.")]
             for c in ch.calibrations()],
            ["texte", "nombre", "nombre", "nombre", "long"],
            "Ce que coûte chaque niveau de socle")
        + g.note(
            f"<p>{ch.contrainte_structurelle()}</p>", "vigilance")
        + g.repere("Le socle de neutralité n'est pas choisi : il est calculé "
                   "comme la somme du RSA, forfait logement déduit, et de "
                   "l'aide au logement d'un foyer sans ressources, au barème "
                   "2026.")
    )

    trous = (
        "<p>Trois montants manquent au programme, et l'ordre de grandeur de "
        "chacun est tel qu'aucun chiffrage ne tient tant qu'ils ne sont pas "
        "écrits. Les voici, avec ce que chaque réponse coûte.</p>"
        + g.depliant(
            "Le socle senior — un écart de 93 milliards",
            "<p>La note pose trois étages (§3) et n'en chiffre qu'un. Le coût "
            f"brut de {md(b.brut)} ne couvre que les 18-64 ans. Pour le "
            "troisième étage, deux lectures, et elles ne coûtent pas la même "
            "chose :</p>"
            + g.tableau(
                ["Lecture", "Montant servi", "Coût net", "Conséquence"],
                [[etage.libelle, etage.montant, md(etage.cout_net),
                  etage.consequence]
                 for etage in ch.etages_seniors()],
                ["long", "texte", "nombre", "long"],
                "Les deux lectures possibles du socle senior")
            + "<p>Tant que ce n'est pas tranché, un lecteur qui applique le "
            f"socle adulte lit une baisse de {eur(ch.ASPA_PERSONNE_SEULE)} à "
            f"{eur(ch.SOCLE_CIBLE)} sur le minimum vieillesse. Écrire que le "
            "socle senior est servi au niveau de l'ASPA ferme la question pour "
            f"{md(ch.ASPA_COUT)}.</p>",
            "socle-senior")
        + g.depliant(
            "Le forfait enfant — le montant qui décide du sort des monoparentales",
            "<p>Le crédit familial remplace "
            f"{md(ch.CONTREPARTIE_FAMILIALE_TOTALE)} de prestations familiales "
            "et de quotient familial. Son forfait n'est pas chiffré par la "
            "note. Or c'est lui qui décide si la famille monoparentale perd, "
            "et de combien.</p>"
            + g.tableau(
                ["Forfait enfant", "Ce qu'il coûte", "Écart avec ce qu'il remplace",
                 "Ce qu'il fait au cas type monoparental"],
                [[eur(forfait) + " / mois", md(ch.cout_forfait(forfait)),
                  ("− " if ch.cout_forfait(forfait) < ch.CONTREPARTIE_FAMILIALE_TOTALE
                   else "+ ")
                  + md(abs(ch.cout_forfait(forfait)
                           - ch.CONTREPARTIE_FAMILIALE_TOTALE)),
                  ecart_monoparental(forfait)]
                 for forfait in ch.FORFAITS_COMPARES],
                ["texte", "nombre", "nombre", "long"],
                "Ce que coûte chaque niveau de forfait enfant")
            + "<p>La lecture est sans échappatoire : le forfait qui équilibre "
            f"le bloc familial est de {eur(ch.FORFAIT_NEUTRE_BUDGET)}, celui "
            "qui protège les familles monoparentales est nettement au-dessus, "
            "et l'écart entre les deux est le prix de la promesse faite au "
            "§7.</p>",
            "forfait-enfant")
        + g.depliant(
            "La contribution et l'impôt sur le revenu — la question non tranchée",
            "<p>La note crée une contribution de solidarité proportionnelle "
            "(§18) sans jamais dire si elle <strong>remplace</strong> l'impôt "
            "sur le revenu ou si elle s'y <strong>ajoute</strong>. Les deux "
            "lectures sont ouvertes par le même texte, et elles ne décrivent "
            "pas le même programme.</p>"
            + g.tableau(
                ["Lecture", "Ce qu'elle produit"],
                [[titre, corps]
                 for titre, corps in ch.lectures_de_la_contribution(b)],
                ["texte", "long"],
                "Les deux lectures ouvertes par la note")
            + "<p>C'est le seul point de ce chiffrage qu'un calcul ne peut pas "
            "fermer : il appelle une décision. Tant qu'elle n'est pas écrite, "
            "chacun peut attribuer au programme celle des deux qui l'arrange, "
            "et ce ne sera pas la nôtre.</p>",
            "contribution-et-impot")
        + g.repere("Rendement de l'impôt sur le revenu : "
                   f"{md(ch.IR_RENDEMENT)} en 2024.")
    )

    exclus = (
        "<p>Un bouclage se juge autant à ce qu'il refuse de compter qu'à ce "
        "qu'il compte. Trois postes que la note range parmi ses sources de "
        "financement (§18) sont écartés ici, et il vaut mieux dire pourquoi "
        "que de se le faire demander.</p>"
        + g.points([(titre, corps) for titre, corps in ch.EXCLUS_DU_BOUCLAGE])
        + g.note(
            "<p>Le troisième mérite qu'on s'y arrête, parce que c'est une "
            "erreur de raisonnement et non un désaccord d'hypothèse. La note "
            "inscrit « l'effet inverse du non-recours » parmi ses recettes. "
            "Servir enfin tous ceux qui ont droit est une <strong>dépense "
            "supplémentaire</strong>, et c'est l'une des promesses du "
            "programme : l'automaticité n'a d'intérêt que si elle coûte ce "
            "que le non-recours économisait. Le coût net ci-dessus l'intègre "
            "déjà, puisque le socle est versé à tous par construction.</p>",
            "vigilance")
        + g.source("Note de doctrine, §18 — les postes écartés y figurent ; "
                   "le motif de leur exclusion est propre à ce chiffrage.")
    )

    contribution = (
        "<p>Une <strong>contribution de solidarité</strong> clairement "
        "identifiée est créée, distincte des cotisations contributives. Elle "
        "finance le revenu universel et les prestations non contributives "
        "maintenues. La fiche de paie et le revenu s'organisent alors autour de "
        "trois niveaux, qui répondent à trois questions différentes.</p>"
        + g.tableau(
            ["Niveau", "Signification"],
            [["Brut complet", "Le coût total du travail"],
             ["Net contributif", "Le revenu après les cotisations qui ouvrent des droits"],
             ["Net après solidarité",
              "Le revenu après la contribution qui finance le socle"]],
            ["texte", "long"],
            "Les trois niveaux de la fiche de paie")
        + "<p>Cette architecture sépare enfin ce qui relève de l'assurance, ce "
        "qui relève de la solidarité, et ce qui reste disponible. Au-delà de la "
        "contribution, la note cite d'autres leviers, qu'elle ne chiffre "
        "pas :</p>"
        + '<ul class="serree">'
        + "".join(f"<li>{item}</li>" for item in [
            "la fiscalité de consommation",
            "la fiscalité foncière, notamment une "
            + g.mot("Land Value Tax",
                    "Impôt assis sur la valeur du terrain nu, indépendamment de ce qui "
                    "est bâti dessus : il taxe la rente foncière sans décourager la "
                    "construction."),
            "des économies sur les dépenses sociales redondantes",
        ])
        + "</ul>"
        + g.note(
            "<p>Ces leviers ne sont pas dans le bouclage ci-dessus, et c'est "
            "délibéré : <strong>tant qu'ils ne portent pas de montant et "
            "d'assiette, ils se lisent comme une menace plutôt que comme une "
            "recette.</strong> Une ligne « fiscalité foncière » sans chiffre "
            "devient, dans la bouche d'un adversaire, un impôt sur la maison de "
            "chacun. Le bouclage tient sans eux ; ils doivent être chiffrés "
            "avant d'être cités.</p>", "vigilance")
        + g.source("Note de doctrine, §18.")
    )

    progressivite = (
        "<p>Le socle permet de reconstruire une progressivité effective "
        "<strong>avec un impôt proportionnel</strong>. Elle n'est plus produite "
        "par un barème à tranches, mais par la combinaison d'un montant fixe "
        "versé à tous et d'un prélèvement au même taux pour tous. Le point de "
        f"bascule est à {eur(b.bascule_mensuelle)} par mois :</p>"
        + g.tableau(
            ["Revenu mensuel du travail", "Contribution", "Socle reçu", "Position"],
            [[eur(revenu), eur(revenu * b.taux), eur(ch.SOCLE_CIBLE),
              "Bénéficiaire net" if revenu * b.taux < ch.SOCLE_CIBLE
              else "Contributeur net"]
             for revenu in (0, 1500, 3000, 4500, 8000)],
            ["nombre", "nombre", "nombre", "texte"],
            f"La progressivité, avec un socle de {SOCLE_ANNUEL_TEXTE} par an et "
            f"une contribution de {pourcent(b.taux)}")
        + '<p class="actions"><a class="bouton" href="simulateur.html">Voir sur '
        'votre revenu</a> <a class="bouton" href="cas-types.html">Voir les cas '
        "types</a></p>"
        + g.note(
            "<p><strong>La progressivité du taux moyen n'est pas celle du taux "
            "marginal.</strong> Un prélèvement proportionnel fait payer au "
            "dernier décile la même part que le milieu, là où le barème actuel "
            "lui en fait payer davantage. C'est un choix défendable — il est "
            "lisible, il ne se contourne pas, il ne crée aucun effet de "
            "seuil — mais c'en est un, et il doit être assumé comme tel plutôt "
            "que présenté comme une équivalence technique.</p>", "vigilance")
        + g.source("Note de doctrine, §18 et §20.1 — Risque budgétaire.")
    )

    return page(
        "financement.html",
        f"Financement — {g.TITRE_SITE}",
        f"Le coût net du revenu universel : {md(b.net)} une fois les "
        f"prestations absorbées, soit une contribution de {pourcent(b.taux)} "
        f"et un point de bascule à {eur(b.bascule_mensuelle)} par mois.",
        "Financement",
        "Le coût net, et<br>ce qu'il suppose",
        f"{md(b.brut)} de coût brut, {md(b.net)} de coût net, "
        f"{pourcent(b.taux)} de contribution et un point de bascule à "
        f"{eur(b.bascule_mensuelle)} par mois. Le calcul est ci-dessous, "
        "ligne à ligne.",
        [("net", "Du coût brut au coût net", net),
         ("taux", "Le taux, et le point de bascule", taux),
         ("arbitrage", "Ce que coûte chaque niveau de socle", arbitrage),
         ("trous", "Les trois montants qui manquent", trous),
         ("exclus", "Ce que ce bouclage refuse de compter", exclus),
         ("contribution", "La contribution de solidarité", contribution),
         ("progressivite", "Une progressivité sans barème", progressivite)],
        tete=reperes)


# -- 9. le calendrier --------------------------------------------------------

ANNEES = [
    ("Année 1", "Préparation et transparence", [
        "publication du périmètre des prestations supprimées, absorbées ou maintenues",
        "simulateur public de revenu disponible",
        "audit des aides locales et nationales redondantes",
        "création juridique de la contribution de solidarité",
        "préparation du registre de résidence effective",
        "expérimentation technique du versement automatique",
    ]),
    ("Année 2", "Première bascule adulte", [
        "création du premier niveau de socle adulte",
        "absorption du RSA",
        "absorption progressive de la prime d'activité",
        "mise en place du bouclier temporaire pour les ménages modestes avec enfants",
        "début de la contribution de solidarité",
    ]),
    ("Année 3", "Absorption des aides au logement", [
        "absorption des APL étudiantes",
        "absorption des APL pour les personnes seules et les ménages sans vulnérabilité "
        "spécifique",
        "maintien temporaire ciblé pour les familles modestes et monoparentales",
        "réforme des aides jeunes et des bourses",
    ]),
    ("Année 4", "Soutien familial et fiscalité de l'enfant", [
        "remplacement des prestations familiales générales par le crédit familial par "
        "enfant",
        "réforme du quotient familial",
        "mise en place de l'architecture forfait + avantage fiscal proportionnel",
        "extinction progressive des compléments redondants",
    ]),
    ("Année 5", "Stabilisation", [
        "socle adulte pleinement installé",
        "APL largement absorbées",
        "contribution de solidarité stabilisée",
        "compléments handicap et vulnérabilité clarifiés",
        "régime transitoire des nouveaux résidents intégré",
        "extinction des anciennes prestations redondantes",
    ]),
]

VIGILANCE = [
    ("Risque budgétaire",
     "Le principal risque est de sous-estimer le coût net. Le socle doit être calibré "
     "prudemment : une première marche à 500&nbsp;€ est plus sûre qu'un basculement "
     "immédiat à 550 ou 600&nbsp;€, la cible étant affichée comme objectif de régime "
     "stabilisé, sous condition de bouclage fiscal."),
    ("Risque sur les familles monoparentales",
     "C'est le risque social principal. Ces familles doivent faire l'objet de cas-types "
     "détaillés avant finalisation, et du bouclier transitoire pendant la bascule."),
    ("Risque logement",
     "L'absorption des APL est cohérente, mais elle peut créer des tensions là où le "
     "logement est très cher. La réforme du logement doit suivre rapidement pour éviter "
     "que le socle ne soit capté par les loyers."),
    ("Risque politique sur les retraités",
     "Le socle senior ne doit pas être présenté comme une hausse de pension. Le chapitre "
     "retraites doit assumer clairement les économies recherchées."),
    ("Risque juridique sur les nouveaux résidents",
     "La convergence sur dix ans devra être expertisée au regard du droit constitutionnel "
     "et européen. La doctrine reste fondée sur la résidence effective et la "
     "réciprocité, non sur une exclusion purement nationalitaire."),
    ("Risque de reconstitution du millefeuille",
     "Chaque exception doit être justifiée, sans quoi la réforme recrée les dispositifs "
     "qu'elle supprime. La règle est stricte : toute aide monétaire générale doit être "
     "absorbée ; seules les vulnérabilités spécifiques justifient des dispositifs "
     "séparés."),
]


def calendrier():
    trajectoire = (
        "<p>La réforme est <strong>radicale dans sa cible, progressive dans son "
        "exécution</strong>. Une bascule instantanée créerait des erreurs, des perdants "
        "imprévus, des tensions administratives et des risques politiques considérables ; "
        "à l'inverse, une transition trop longue viderait la réforme de son sens. La mise "
        "en œuvre principale est visée sur cinq ans, avec un bouclier de transition sur "
        "deux à trois ans pour les publics les plus sensibles.</p>"
        + "".join(
            g.depliant(f"{annee} — {intitule}",
                       '<ul class="serree">'
                       + "".join(f"<li>{etape}</li>" for etape in etapes)
                       + "</ul>",
                       f"annee-{i}")
            for i, (annee, intitule, etapes) in enumerate(ANNEES, start=1))
        + g.note("<p>Le bouclier transitoire s'éteint au bout de deux ou trois ans, sauf "
                 "situations exceptionnelles prévues explicitement : il ne doit pas "
                 "devenir une nouvelle prestation permanente.</p>", "vigilance")
        + g.source("Note de doctrine, §19 — Mise en œuvre.")
    )

    risques = (
        "<p>La note consacre une section entière aux objections qu'elle se fait "
        "elle-même. Elles sont reproduites ici sans être adoucies : une réforme qui ne "
        "nomme pas ses risques ne peut pas être discutée.</p>"
        + "".join(g.cle(titre, texte, identifiant=f"risque-{i}")
                  for i, (titre, texte) in enumerate(VIGILANCE, start=1))
        + g.source("Note de doctrine, §20 — Points de vigilance.")
    )

    return page(
        "calendrier.html",
        f"Calendrier et risques — {g.TITRE_SITE}",
        "Les cinq années de la bascule, étape par étape, et les six risques que la note "
        "de doctrine identifie elle-même — budgétaire, monoparental, logement, "
        "retraités, juridique, millefeuille.",
        "Calendrier et risques",
        "Cinq ans pour basculer,<br>six risques nommés",
        "Une cible radicale, une exécution progressive, et un bouclier transitoire qui "
        "doit s'éteindre — annoncés d'avance, avec les risques que la note reconnaît.",
        [("trajectoire", "Les cinq années", trajectoire),
         ("risques", "Les six points de vigilance", risques)])


# -- 10. les questions -------------------------------------------------------

def questions():
    faq = "".join([
        g.cle("Est-ce qu'on peut vivre avec 550 € par mois ?",
              "Non, et ce n'est pas le but. Le socle n'est pas un revenu de confort et il "
              "ne remplace pas un salaire : il garantit une sécurité minimale, compatible "
              "avec la reprise d'activité, l'entrepreneuriat, la formation, le temps "
              "partiel et les revenus irréguliers.",
              g.source("Note de doctrine, §4."), identifiant="q-montant"),
        g.cle("Pourquoi verser de l'argent à des gens qui n'en ont pas besoin ?",
              "Parce que c'est l'impôt qui reprend le transfert, et non un guichet qui le "
              "refuse. Un socle versé à tous puis repris par une contribution "
              "proportionnelle produit la même progressivité qu'un barème compliqué, sans "
              "conditions de ressources à vérifier, sans effet de seuil et sans "
              "non-recours.",
              g.source("Note de doctrine, §18."), identifiant="q-universalite"),
        g.cle("Est-ce que ça n'encourage pas à ne pas travailler ?",
              "C'est l'inverse de la mécanique actuelle. Aujourd'hui, une hausse de "
              "salaire fait perdre des aides, et le gain net peut être presque nul. Avec "
              "le socle, celui-ci est conservé quand on travaille : chaque euro gagné "
              "augmente le revenu disponible.",
              g.source("Note de doctrine, §5."), identifiant="q-travail"),
        g.cle("Les personnes handicapées vont-elles y perdre ?",
              "Non : l'AAH devient un complément handicap versé <em>en plus</em> du "
              "socle, et la PCH, l'APA, la protection de l'enfance, l'hébergement "
              "d'urgence et les soins urgents sont maintenus à part. Le socle ne prétend "
              "pas remplacer une compensation.",
              g.source("Note de doctrine, §10."), identifiant="q-handicap"),
        g.cle("Et si je touche aujourd'hui plus que le socle ?",
              "C'est le risque social que la note identifie comme principal, en "
              "particulier pour les familles modestes et monoparentales. D'où un bouclier "
              "transitoire : temporaire, ciblé, décroissant, non renouvelable, concentré "
              "sur les deux ou trois premières années, avec une règle explicite — aucune "
              "perte brutale de revenu disponible pendant la bascule.",
              "<p>Il faut être clair sur ce que ce bouclier fait et ne fait pas : "
              "il <strong>amortit</strong> la bascule, il ne la supprime pas. "
              "Au terme des deux ou trois ans, la perte est réelle pour qui "
              "touche aujourd'hui plus que le socle. La seule façon de la "
              "supprimer est de porter le socle à "
              f"{eur(ch.SOCLE_NEUTRALITE)}, et la contribution à "
              f"{pourcent(ch.boucler(ch.SOCLE_NEUTRALITE).taux)}. "
              '<a href="cas-types.html">Voir qui perd, et de combien</a></p>',
              g.source("Note de doctrine, §7 ; le chiffrage de la perte est "
                       "propre à ce site."),
              identifiant="q-perdants"),
        g.cle("Est-ce que mes APL disparaissent vraiment ?",
              "Oui, pour la majorité des bénéficiaires, étudiants compris : elles sont "
              "absorbées dans le socle, versé en argent libre d'usage. Les familles "
              "modestes et monoparentales bénéficient d'un maintien temporaire ciblé, et "
              "le logement social relève d'un chapitre séparé du programme.",
              g.source("Note de doctrine, §12."), identifiant="q-apl"),
        g.cle("Le chômage et la retraite sont-ils supprimés ?",
              "Non. Ce sont des droits contributifs : ils correspondent à ce qui a été "
              "cotisé, et ils restent distincts de la solidarité nationale. L'assurance "
              "chômage est reconstruite comme un système strictement contributif, "
              "potentiellement facultatif ou modulable ; les pensions relèvent du "
              "chapitre retraites.",
              g.source("Note de doctrine, §14 et §15."), identifiant="q-assurance"),
        g.cle("Tout le monde y a droit dès son arrivée en France ?",
              "Non. Le socle est attaché à la résidence effective, et l'accès complet "
              "d'un ressortissant étranger est acquis après dix ans de résidence "
              "régulière, la contribution de solidarité montant au même rythme. La "
              "naturalisation ouvre le régime commun. Les protections fondamentales — "
              "asile, soins urgents, protection de l'enfance, hébergement d'urgence — "
              "restent hors de ce barème.",
              g.source("Note de doctrine, §16."), identifiant="q-etrangers"),
        g.cle("Un Français installé à l'étranger le touche-t-il ?",
              "Non : la nationalité seule ne suffit pas. Le socle est attaché à la "
              "résidence effective en France, et c'est l'un des critères que le contrôle "
              "doit vérifier — avec l'identité, l'unicité du bénéficiaire, la régularité "
              "du séjour, le décès et les doublons.",
              g.source("Note de doctrine, §17."), identifiant="q-expatries"),
        g.cle("Ça coûte 264 milliards : comment est-ce finançable ?",
              f"264 milliards est le coût <em>brut</em>. Le coût net est de "
              f"{md(ch.boucler().net)} une fois déduites les prestations que le socle "
              f"absorbe, et il suppose une contribution de solidarité de "
              f"{pourcent(ch.taux_publie())} sur une assiette large. C'est un chiffre "
              "lourd, et il vaut mieux l'écrire soi-même que se le faire écrire.",
              '<p class="actions"><a class="bouton" href="financement.html#net">Voir '
              "le bouclage, ligne à ligne</a></p>",
              g.repere("Calculé à partir des dépenses constatées de chaque prestation "
                       "absorbée. La note, elle, s'arrête au coût brut."),
              identifiant="q-cout"),
        g.cle("Qui y perd ?",
              "Trois situations, et le site les chiffre plutôt que de les laisser "
              "découvrir : le célibataire sans emploi aujourd'hui au RSA et à l'aide "
              "au logement, la famille monoparentale modeste, et le retraité au "
              "minimum vieillesse si le socle senior n'est pas calibré à son niveau. "
              "Les deux dernières se ferment par une décision ; la première est "
              "l'arbitrage central du programme.",
              '<p class="actions"><a class="bouton" href="cas-types.html">Voir les '
              "sept situations</a></p>",
              g.repere("Sept cas types calculés aux barèmes 2026, perdants compris."),
              identifiant="q-perdants-chiffres"),
    ])

    langage = (
        "<p>La réforme se résume ainsi : remplacer le maquis des aides sociales par un "
        "revenu universel simple, automatique et individualisé. Chacun dispose d'un "
        "socle. Chacun garde intérêt à travailler. Les familles sont soutenues "
        "explicitement. Les plus vulnérables conservent un accompagnement spécifique. Les "
        "nouveaux résidents accèdent progressivement aux droits et aux devoirs. L'impôt "
        "devient lisible, la solidarité devient compréhensible, et le travail redevient "
        "toujours gagnant.</p>"
        + g.encadre(
            '<ul class="serree" style="margin:0">'
            + "".join(f"<li>{phrase}</li>" for phrase in [
                "« Un socle pour chacun, des droits clairs pour tous. »",
                "« Le travail doit toujours payer. »",
                "« Moins de guichets, moins de seuils, plus de liberté. »",
                "« Universaliser le socle, cibler les fragilités. »",
                "« Droits sociaux et devoirs fiscaux avancent ensemble. »",
                "« La solidarité doit être automatique pour les citoyens, progressive "
                "pour les nouveaux résidents, renforcée pour les plus vulnérables. »",
                "« Nous remplaçons l'assistanat bureaucratique par une solidarité "
                "lisible. »",
                "« Le revenu universel n'est pas un revenu d'oisiveté : c'est un socle "
                "qui rend le travail plus rentable. »",
            ])
            + "</ul>")
        + "<p>Cette réforme est <strong>radicale</strong> parce qu'elle change la logique "
        "de l'État social ; <strong>libérale</strong> parce qu'elle renforce l'autonomie "
        "individuelle, la lisibilité fiscale, la responsabilité et l'incitation au "
        "travail ; <strong>sociale</strong> parce qu'elle garantit un socle monétaire "
        "simple et automatique ; <strong>soutenable</strong> parce qu'elle assume les "
        "arbitrages budgétaires, la suppression des doublons et la maîtrise de la "
        "dépense.</p>"
        + g.source("Note de doctrine, §21 — Message politique ; §22 — Synthèse "
                   "doctrinale.")
    )

    glossaire = (
        "<p>Les mots que le débat social emploie sans les définir. Aucun n'est "
        "indispensable pour comprendre la proposition, mais tous reviennent dès qu'on en "
        "discute.</p>"
        + g.gloses([
            ("Prestation non contributive",
             "Aide financée par l'impôt et versée sans avoir cotisé pour elle : RSA, "
             "ASPA, AAH, aides au logement. C'est ce que le revenu universel remplace "
             "pour sa partie monétaire générale."),
            ("Prestation contributive",
             "Droit acquis en échange de cotisations : assurance chômage, pension de "
             "retraite. Le revenu universel n'y touche pas."),
            ("Minima sociaux",
             "L'ensemble des prestations garantissant un revenu plancher, dont le RSA est "
             "le principal."),
            ("RSA",
             "Revenu de solidarité active : minimum social versé sous condition de "
             "ressources, au niveau du foyer, largement fermé avant 25 ans."),
            ("Prime d'activité",
             "Complément de revenu versé aux travailleurs modestes, qui décroît quand le "
             "salaire augmente."),
            ("APL",
             "Aides personnelles au logement, calculées selon le loyer, les ressources et "
             "la composition du foyer."),
            ("AAH",
             "Allocation aux adultes handicapés, que la réforme transforme en complément "
             "versé en plus du socle."),
            ("ASPA",
             "Allocation de solidarité aux personnes âgées, l'actuel minimum vieillesse, "
             "que le socle senior remplace."),
            ("PCH et APA",
             "Prestation de compensation du handicap et allocation personnalisée "
             "d'autonomie : deux compensations maintenues à part."),
            ("Non-recours",
             "Fait de ne pas percevoir une aide à laquelle on a droit, faute de l'avoir "
             "demandée ou comprise."),
            ("Effet de seuil",
             "Franchir un euro de revenu au-dessus d'une limite fait perdre d'un coup une "
             "aide entière."),
            ("Taux marginal effectif",
             "Part d'un euro supplémentaire gagné qui repart en prélèvements ou en aides "
             "perdues."),
            ("Redistribution horizontale",
             "Transfert entre ménages de même niveau de vie mais de charges différentes : "
             "ici, des adultes sans enfant vers les parents."),
            ("Quotient familial",
             "Mécanisme fiscal actuel réduisant l'impôt selon le nombre de parts du "
             "foyer, que le crédit familial remplace en grande partie."),
            ("Land Value Tax",
             "Impôt sur la valeur du terrain nu, indépendamment de ce qui est bâti "
             "dessus : il taxe la rente foncière sans décourager la construction."),
        ])
    )

    return page(
        "questions.html",
        f"Questions — {g.TITRE_SITE}",
        "Les dix questions que l'on pose en premier sur le revenu universel, les "
        "réponses de la note de doctrine, et un glossaire des mots du débat social.",
        "Questions",
        "Les objections,<br>et ce que la note répond",
        "Dix questions posées telles qu'elles se posent, avec la réponse du programme et "
        "la section d'où elle vient. Puis les mots du débat, définis.",
        [("faq", "Dix questions", faq),
         ("langage", "Le message en une page", langage),
         ("glossaire", "Le glossaire", glossaire)])


# -- écriture ----------------------------------------------------------------

PAGES = [accueil, socle, simulateur, cas_types, jeunes, familles, protections,
         nouveaux_residents, financement, calendrier, questions]


def main() -> None:
    for construire in PAGES:
        fichier, html = construire()
        (RACINE / fichier).write_text(html, encoding="utf-8")
        print(f"écrit  {fichier}  ({len(html) // 1024} Kio)")


if __name__ == "__main__":
    main()
