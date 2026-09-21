#!/usr/bin/env python3
"""Le chiffrage du programme : bouclage budgétaire et cas-types.

CE MODULE N'EST PAS LA NOTE DE DOCTRINE, et c'est sa raison d'être.

La note (§18) pose une règle — « le revenu universel doit être présenté en coût
net, jamais seulement en coût brut » — puis ne donne pas le coût net. Elle
identifie le risque budgétaire (§20.1) et demande des cas-types pour les
familles monoparentales (§20.2) sans les produire. Ce module produit les deux.

Il s'ensuit que le site porte désormais DEUX espèces de phrases, qui ne doivent
jamais être mélangées dans un même paragraphe :

  - la DOCTRINE, tirée de la note, qui se cite « Note de doctrine, §n » ;
  - le CHIFFRAGE, tiré des barèmes publics et de statistiques publiées, qui se
    cite par sa source et par ses hypothèses.

Le chiffrage n'engage pas le parti : il montre ce à quoi la note s'engagerait si
on la calibrait de telle ou telle façon. C'est pourquoi tout ici est CALCULÉ à
partir des constantes ci-dessous, et rien n'est recopié : changer une hypothèse
change toutes les pages d'un coup, et aucun nombre du site ne peut dériver d'un
autre.

Toutes les constantes portent leur source. Les barèmes sont ceux de 2026.
"""

from __future__ import annotations

from dataclasses import dataclass

MILLIARD = 1_000_000_000

# -- 1. les barèmes en vigueur, pour la colonne « aujourd'hui » --------------
#
# Ce sont des montants publiés, vérifiables, et c'est ce qui rend les cas-types
# difficiles à contester : un adversaire qui veut les attaquer doit attaquer le
# barème, pas nous.

RSA_PERSONNE_SEULE = 651.69      # € / mois, montant forfaitaire 2026
RSA_FORFAIT_LOGEMENT = 78.20     # € / mois, déduit si le foyer est logé (12 %)
#: Le barème du RSA selon le nombre de personnes du foyer : 100 %, 150 %, 180 %,
#: 210 %, puis +40 % par personne supplémentaire.
RSA_COEFFICIENTS = {1: 1.0, 2: 1.5, 3: 1.8, 4: 2.1}
RSA_COEFFICIENT_SUPPLEMENTAIRE = 0.4
#: Le forfait logement suit le même barème : 12 % du montant d'une personne,
#: 16 % de celui de deux, 16,5 % de celui de trois et au-delà.
RSA_FORFAIT_LOGEMENT_PARTS = {1: 0.12, 2: 0.16}
RSA_FORFAIT_LOGEMENT_PART_GRANDE = 0.165

AAH = 1041.59                    # € / mois au 1er avril 2026
ASPA_PERSONNE_SEULE = 1043.59    # € / mois au 1er janvier 2026
ALLOCATIONS_FAMILIALES_2 = 153.01  # € / mois, deux enfants, sous plafond

#: Le SMIC net mensuel est donné en fourchette parce qu'il en existe plusieurs
#: lectures selon les cotisations retenues. Les cas-types prennent le bas : un
#: résultat flatteur obtenu par le haut serait le seul qu'on ne puisse pas
#: vérifier. C'est la règle déjà suivie par le calculateur pour la convergence.
SMIC_NET = 1443.0                # € / mois, temps plein
PRIME_ACTIVITE_AU_SMIC = 230.0   # € / mois, personne seule, ordre de grandeur

#: L'aide au logement varie tellement selon la zone et le loyer qu'un montant
#: unique serait faux partout. Le site publie donc la moyenne ET l'amplitude,
#: et les cas-types disent laquelle ils emploient.
APL_MOYENNE = 220.0              # € / mois, tous bénéficiaires
APL_SANS_RESSOURCES = 290.0      # € / mois, foyer au RSA (cas-type DREES)
APL_FAMILLE = 400.0              # € / mois, famille avec deux enfants
APL_ETUDIANT = 180.0             # € / mois, étudiant décohabitant

SEUIL_PAUVRETE = 1337.0          # € / mois, personne seule (INSEE, 2024)

#: Allocations familiales : le montant de base couvre deux enfants, chaque
#: enfant suivant ajoute environ ce montant-ci.
ALLOCATIONS_FAMILIALES_PAR_ENFANT_SUP = 196.0

#: Les deux prestations qui décroissent avec le revenu sont approchées par leur
#: FORME plutôt que par leur barème : l'aide au logement s'éteint vers deux
#: SMIC, la prime d'activité culmine au SMIC et s'éteint vers 1,8 SMIC. Le
#: barème exact dépend du loyer, de la zone et du trimestre de référence — le
#: donner pour exact serait la seule chose qu'on ne puisse pas défendre.
APL_EXTINCTION_SMIC = 2.0
PRIME_EXTINCTION_SMIC = 1.8

#: Bourse sur critères sociaux, échelon 5, versée dix mois sur douze.
BOURSE_ECHELON_5_ANNUELLE = 4587.0
BOURSE_MOIS = 10


def prime_activite(revenu: float, personnes: int = 1) -> float:
    """La prime d'activité, approchée par sa forme : elle culmine au SMIC.

    Approchée, et non calculée : le barème réel dépend du trimestre de
    référence, des bonifications individuelles et de la composition du foyer.
    La forme, elle, ne fait aucun doute — nulle sans activité, maximale autour
    du SMIC, éteinte vers 1,8 SMIC — et c'est tout ce dont un ordre de grandeur
    a besoin.
    """
    if revenu <= 0:
        return 0.0
    if revenu <= SMIC_NET:
        forme = revenu / SMIC_NET
    else:
        forme = max(0.0, (PRIME_EXTINCTION_SMIC * SMIC_NET - revenu)
                    / ((PRIME_EXTINCTION_SMIC - 1) * SMIC_NET))
    return PRIME_ACTIVITE_AU_SMIC * forme * _coefficient_rsa(personnes)


def aide_au_logement(revenu: float, personnes: int = 1) -> float:
    """L'aide au logement, approchée par sa décroissance jusqu'à deux SMIC.

    C'est la prestation la plus variable du système — du simple au double selon
    la zone et le loyer —, donc celle qu'il ne faut surtout pas donner pour
    exacte. Le site publie la moyenne, l'amplitude, et cette forme.
    """
    base = APL_SANS_RESSOURCES if personnes == 1 else APL_FAMILLE
    return base * max(0.0, 1 - revenu / (APL_EXTINCTION_SMIC * SMIC_NET))


def allocations_familiales(enfants: int) -> float:
    """Les allocations familiales : rien avant deux enfants."""
    if enfants < 2:
        return 0.0
    return (ALLOCATIONS_FAMILIALES_2
            + ALLOCATIONS_FAMILIALES_PAR_ENFANT_SUP * (enfants - 2))


def _coefficient_rsa(personnes: int) -> float:
    """Le coefficient du barème selon la taille du foyer."""
    if personnes <= 4:
        return RSA_COEFFICIENTS[personnes]
    return RSA_COEFFICIENTS[4] + RSA_COEFFICIENT_SUPPLEMENTAIRE * (personnes - 4)


def rsa_foyer(personnes: int) -> float:
    """Le montant forfaitaire du RSA pour un foyer, forfait logement déduit."""
    montant = RSA_PERSONNE_SEULE * _coefficient_rsa(personnes)
    part = RSA_FORFAIT_LOGEMENT_PARTS.get(
        personnes, RSA_FORFAIT_LOGEMENT_PART_GRANDE)
    reference = RSA_PERSONNE_SEULE * RSA_COEFFICIENTS[min(personnes, 3)]
    return montant - reference * part


# -- 2. le périmètre et le coût brut -----------------------------------------

POPULATION_18_64 = 40_000_000    # l'hypothèse de la note elle-même (§4)
POPULATION_65_PLUS = 14_700_000  # pour le troisième étage, que la note ne chiffre pas
ENFANTS = 13_800_000             # enfants à charge, ordre de grandeur

SOCLE_CIBLE = 550                # € / mois, cible de régime stabilisé (note, §4)
SOCLE_MARCHE = 500               # € / mois, première marche (note, §20.1)


def cout_brut(socle_mensuel: float, personnes: int) -> float:
    """Le coût brut annuel d'un socle, en euros."""
    return socle_mensuel * 12 * personnes


# -- 3. ce que le socle remplace vraiment ------------------------------------
#
# LE POINT DÉLICAT EST ICI, et c'est celui sur lequel un contradicteur nous
# attendra. Une prestation SUPPRIMÉE est une économie. Une prestation REMPLACÉE
# par un dispositif nouveau n'en est pas une : elle finance ce dispositif.
#
# Les prestations familiales et le quotient familial sont dans le second cas —
# la note les remplace par le crédit familial (§8) — et les compter comme
# recettes ferait apparaître 51 Md€ d'économies qui n'existent pas. Le bouclage
# ci-dessous les traite donc à part, dans son propre bloc.

@dataclass(frozen=True)
class Poste:
    """Une ligne du bouclage : un montant annuel, et d'où il vient."""
    libelle: str
    milliards: float
    source: str
    detail: str = ""


ABSORBEES = [
    Poste("RSA", 12.0, "CNAF",
          "Le socle le remplace intégralement (note, §6)."),
    Poste("Prime d'activité", 10.7, "PLF 2024",
          "Remplacée par le cumul du socle et du revenu du travail (note, §6)."),
    Poste("Aides au logement absorbées", 12.0, "CNAF",
          "Sur environ 17 Md€ au total : le reste couvre les ménages pour "
          "lesquels la note maintient un ciblage (note, §12)."),
    Poste("Aides jeunes et bourses recentrées", 2.0, "MESR",
          "Les bourses de vie courante, les aides jeunes locales et nationales "
          "que le socle rend redondantes (note, §13)."),
]

#: Ce que le crédit familial remplace — et qui n'est donc pas une économie, mais
#: la contrepartie d'une dépense nouvelle que la note ne chiffre pas (§8).
CONTREPARTIE_FAMILIALE = [
    Poste("Prestations familiales générales", 34.3, "CNAF 2024",
          "Allocations familiales, complément familial, allocation de rentrée "
          "scolaire, prestation d'accueil du jeune enfant."),
    Poste("Quotient familial", 16.5, "Dépenses fiscales",
          "L'avantage en impôt lié aux parts d'enfants."),
]

#: Ce que la note range dans son financement mais qui n'a rien à y faire, et
#: pourquoi. Le bouclage du site les exclut EXPRESSÉMENT : un bouclage qui tient
#: sans eux est infiniment plus solide qu'un bouclage qui en dépend.
EXCLUS_DU_BOUCLAGE = [
    ("Les effets de retour sur l'emploi",
     "Tout programme en annonce, aucun n'est vérifiable avant d'avoir gouverné. "
     "Les compter ici reviendrait à financer une dépense certaine par une "
     "recette hypothétique, et à affaiblir les quatre lignes qui, elles, "
     "tiennent."),
    ("Les économies administratives",
     "Elles sont réelles, mais d'un ordre de grandeur sans rapport avec le "
     "coût du socle : quelques milliards contre plus de deux cents."),
    ("La fin du non-recours",
     "Elle COÛTE de l'argent, elle n'en rapporte pas. Un tiers des foyers "
     "éligibles au RSA ne le demandent pas ; les servir tous est précisément "
     "ce que l'automaticité promet, et c'est une dépense assumée, pas une "
     "recette. La note la range parmi ses sources de financement : c'est une "
     "erreur de raisonnement, et elle est corrigée ici."),
]

#: L'assiette de la contribution. La CSG rapporte 157 Md€ à un taux moyen
#: d'environ 9,2 % : son assiette est donc de l'ordre de 1 700 Md€. C'est la
#: seule assiette large déjà en place, et donc la seule référence honnête pour
#: convertir un coût net en points de prélèvement.
CSG_RENDEMENT = 157.0
CSG_TAUX_MOYEN = 0.092
ASSIETTE_LARGE = CSG_RENDEMENT / CSG_TAUX_MOYEN   # ≈ 1 707 Md€


@dataclass(frozen=True)
class Bouclage:
    """Le bouclage d'une calibration : du coût brut au taux de contribution."""
    socle: float
    brut: float
    absorbe: float
    net: float
    taux: float
    bascule_annuelle: float
    bascule_mensuelle: float
    socle_annuel: float


def boucler(socle_mensuel: float = SOCLE_CIBLE,
            personnes: int = POPULATION_18_64,
            absorbe_milliards: float | None = None) -> Bouclage:
    """Le bouclage complet, du coût brut au point de bascule.

    Le POINT DE BASCULE est le revenu à partir duquel la contribution dépasse le
    socle reçu — la frontière entre bénéficiaire net et contributeur net. C'est
    le chiffre le plus favorable au programme, et celui que le site n'écrivait
    nulle part.
    """
    if absorbe_milliards is None:
        absorbe_milliards = sum(poste.milliards for poste in ABSORBEES)
    brut = cout_brut(socle_mensuel, personnes) / MILLIARD
    net = brut - absorbe_milliards
    taux = net / ASSIETTE_LARGE
    socle_annuel = socle_mensuel * 12
    bascule = socle_annuel / taux if taux > 0 else float("inf")
    return Bouclage(socle=socle_mensuel, brut=brut, absorbe=absorbe_milliards,
                    net=net, taux=taux, bascule_annuelle=bascule,
                    bascule_mensuelle=bascule / 12, socle_annuel=socle_annuel)


#: Le socle qui rendrait neutre le perdant principal — le célibataire sans
#: emploi, aujourd'hui au RSA et à l'aide au logement. Il n'est pas choisi : il
#: est CALCULÉ, et c'est ce qui rend l'arbitrage lisible.
SOCLE_NEUTRALITE = round(rsa_foyer(1) + APL_SANS_RESSOURCES)


def taux_publie(socle_mensuel: float = SOCLE_CIBLE) -> float:
    """Le taux tel que le site l'ÉCRIT : arrondi au point de pourcentage.

    Le site publie « 13 % » ; s'en servir ailleurs à 13,31 % ferait répondre le
    calculateur et les cas-types à quelques euros près sur les mêmes
    situations. Un écart pareil ne se remarque que quand quelqu'un le cherche,
    et quelqu'un le cherchera.
    """
    return round(boucler(socle_mensuel).taux, 2)


def calibrations() -> list[Bouclage]:
    """Les quatre calibrations que le site met côte à côte.

    De la première marche de la note au socle qui ne fait aucun perdant : c'est
    l'échelle complète de l'arbitrage, et elle montre ce qu'il coûte.
    """
    niveaux = [SOCLE_MARCHE, SOCLE_CIBLE, 600, SOCLE_NEUTRALITE]
    return [boucler(niveau) for niveau in sorted(set(niveaux))]


# -- 4. le troisième étage, que la note ne chiffre pas -----------------------

ASPA_COUT = 4.3   # Md€ / an, dépense actuelle du minimum vieillesse


@dataclass(frozen=True)
class EtageSenior:
    libelle: str
    cout_net: float
    montant: str
    consequence: str


def etages_seniors(socle_mensuel: float = SOCLE_CIBLE) -> list[EtageSenior]:
    """Les deux lectures possibles du « socle senior », et leur prix.

    La note pose trois étages (§3) et n'en chiffre qu'un. Entre les deux
    lectures, l'écart est de quatre-vingt-treize milliards et de cinq cents
    euros par mois pour sept cent mille personnes : ce n'est pas un détail de
    calibrage, c'est un choix politique qui doit être écrit.
    """
    universel = cout_brut(socle_mensuel, POPULATION_65_PLUS) / MILLIARD - ASPA_COUT
    return [
        EtageSenior(
            "Socle senior différentiel, au niveau de l'ASPA",
            ASPA_COUT,
            f"{ASPA_PERSONNE_SEULE:,.2f} € par mois".replace(",", " "),
            "Aucun bénéficiaire actuel du minimum vieillesse ne perd un euro. "
            "Mais le troisième étage n'est plus universel, et l'architecture "
            "de la note n'en compte plus que deux."),
        EtageSenior(
            "Socle senior universel, au niveau du socle adulte",
            universel,
            f"{socle_mensuel} € par mois",
            "L'architecture à trois étages est respectée. Mais le minimum "
            "vieillesse passe de "
            f"{ASPA_PERSONNE_SEULE:,.2f} € à {socle_mensuel} € "
            "pour environ 700 000 personnes, et le coût net de la réforme "
            f"augmente de {universel:,.0f} Md€.".replace(",", " "),
        ),
    ]




# -- 5. le forfait enfant ----------------------------------------------------
#
# La note prévoit un crédit familial en deux parties — un forfait monétaire et
# une réduction proportionnelle d'impôt (§8) — et n'en chiffre aucune. Or c'est
# le forfait qui décide du sort des familles monoparentales, que la note
# désigne elle-même comme son risque social principal (§20.2).

CONTREPARTIE_FAMILIALE_TOTALE = sum(
    poste.milliards for poste in CONTREPARTIE_FAMILIALE)

#: Le forfait qui coûte exactement ce que le crédit familial remplace : en
#: dessous, la réforme fait des économies sur les familles ; au-dessus, elle
#: dépense davantage. Calculé, pas choisi.
FORFAIT_NEUTRE_BUDGET = round(
    CONTREPARTIE_FAMILIALE_TOTALE * MILLIARD / ENFANTS / 12)

#: Le forfait retenu par défaut sur tout le site. CE N'EST PAS UN CHIFFRE ROND
#: CHOISI À LA MAIN, et c'est délibéré : la valeur par défaut d'un calculateur
#: public devient « le chiffre du parti » qu'on le veuille ou non, et un 200 €
#: rond n'aurait eu aucune justification à opposer. Celui-ci en a une, en une
#: phrase : c'est le forfait qui coûte exactement ce que le crédit familial
#: remplace.
FORFAIT_ILLUSTRATION = FORFAIT_NEUTRE_BUDGET

#: Les trois niveaux que le site met en regard : un forfait bas, le forfait
#: d'équilibre, et celui qui protège les familles monoparentales.
FORFAITS_COMPARES = (200, FORFAIT_NEUTRE_BUDGET, 500)



def cout_forfait(forfait_mensuel: float) -> float:
    """Le coût annuel d'un forfait enfant, en Md€."""
    return forfait_mensuel * 12 * ENFANTS / MILLIARD


# -- 6. les cas-types --------------------------------------------------------
#
# La note demande des cas-types (§20.2) et n'en produit aucun. Ils sont ici.
#
# LA RÈGLE DE CONSTRUCTION EST D'AFFICHER LES PERDANTS. Un jeu de cas-types qui
# ne montre que des gagnants ne convainc personne et se retourne au premier
# contre-exemple ; un jeu qui montre ses perdants nommément est le seul dont on
# garde le contrôle. Trois des sept ci-dessous perdent.
#
# Convention de calcul, la même pour tous : la contribution de solidarité est
# prise sur le revenu du travail tel qu'il est versé aujourd'hui, toutes choses
# égales par ailleurs. Elle ne modélise pas le sort de l'impôt sur le revenu,
# que la note ne tranche pas — et c'est précisément le point que la page du
# financement met en avant.

@dataclass(frozen=True)
class CasType:
    """Une situation, avant et après, et ce que l'écart veut dire."""
    nom: str
    detail: str
    aujourd_hui: list[tuple[str, float]]
    demain: list[tuple[str, float]]
    lecture: str
    reserve: str = ""
    personnes: int = 1

    @property
    def avant(self) -> float:
        return sum(montant for _, montant in self.aujourd_hui)

    @property
    def apres(self) -> float:
        return sum(montant for _, montant in self.demain)

    @property
    def ecart(self) -> float:
        return self.apres - self.avant

    @property
    def part(self) -> float:
        return self.ecart / self.avant if self.avant else 0.0

    @property
    def perdant(self) -> bool:
        """Au-delà de 2 % d'écart : en deçà, le bruit des hypothèses domine."""
        return self.part < -0.02

    @property
    def gagnant(self) -> bool:
        return self.part > 0.02


def cas_types(socle: float = SOCLE_CIBLE, taux: float | None = None,
              forfait: float = FORFAIT_ILLUSTRATION) -> list[CasType]:
    """Les sept situations, calculées pour une calibration donnée."""
    if taux is None:
        taux = taux_publie(socle)
    smic_contribution = -round(SMIC_NET * taux)

    return [
        CasType(
            "Célibataire sans emploi, logé",
            "Au RSA et à l'aide au logement. Environ 1,2 million de personnes.",
            [("RSA, forfait logement déduit", rsa_foyer(1)),
             ("Aide au logement", aide_au_logement(0))],
            [("Socle adulte", socle)],
            "C'est le perdant principal de la réforme, et la note ne le voit "
            "pas : son bouclier transitoire (§7) ne couvre que les ménages "
            "<em>avec enfants</em>. Ce cas-type n'est protégé par rien.",
            "Aucun dispositif transitoire prévu à ce jour."),
        CasType(
            "Mère seule, deux enfants, sans emploi",
            "RSA majoré, aide au logement, allocations familiales.",
            [("RSA, forfait logement déduit", rsa_foyer(3)),
             ("Aide au logement", aide_au_logement(0, personnes=3)),
             ("Allocations familiales", allocations_familiales(2))],
            [("Socle adulte", socle),
             (f"Forfait enfant ({forfait:.0f} € × 2)", forfait * 2)],
            "Le risque social que la note désigne elle-même comme principal "
            "(§20.2). Le bouclier transitoire l'amortit deux à trois ans, puis "
            "s'éteint : la perte n'est pas évitée, elle est différée.",
            "Le crédit d'impôt proportionnel, seconde partie du crédit "
            "familial, n'est pas chiffré par la note et ne joue pas ici — un "
            "foyer sans revenu n'est pas imposable.",
            personnes=3),
        CasType(
            "Retraité au minimum vieillesse",
            "À l'ASPA. Environ 700 000 personnes.",
            [("ASPA", ASPA_PERSONNE_SEULE)],
            [("Socle senior, au niveau du socle adulte", socle)],
            "Ce cas-type n'existe que parce que la note ne chiffre pas le "
            "socle senior. Écrire que le socle senior est servi au niveau de "
            "l'ASPA le fait disparaître, pour 4,3 Md€ — le coût actuel du "
            "minimum vieillesse.",
            "Disparaît si le socle senior est calibré au niveau de l'ASPA."),
        CasType(
            "Personne handicapée à l'AAH",
            "Allocation aux adultes handicapés, sans autre ressource.",
            [("AAH", AAH)],
            [("Socle adulte", socle),
             ("Complément handicap", AAH - socle)],
            "Neutre — mais seulement parce que le complément est calibré ici "
            "pour qu'il le soit. La note dit que l'AAH devient un complément "
            "versé en plus du socle (§10) sans jamais écrire son montant. "
            "L'écrire ne coûte rien et ferme une attaque.",
            "La neutralité suppose un complément de "
            f"{AAH - SOCLE_CIBLE:.2f} €, que la note ne fixe pas."),
        CasType(
            "Célibataire au SMIC",
            "Temps plein, logé, prime d'activité et aide au logement.",
            [("Salaire net", SMIC_NET),
             ("Prime d'activité", prime_activite(SMIC_NET)),
             ("Aide au logement", aide_au_logement(SMIC_NET))],
            [("Salaire net", SMIC_NET),
             ("Socle adulte", socle),
             ("Contribution de solidarité", smic_contribution)],
            "À peu près neutre en montant — et c'est le mauvais angle. Ce qui "
            "change, c'est qu'il n'y a plus de dossier, plus de déclaration "
            "trimestrielle, plus rien à perdre en cas d'augmentation ou "
            "d'heures supplémentaires.",
            ""),
        CasType(
            "Couple, deux SMIC, deux enfants",
            "Deux temps pleins. Aujourd'hui, presque aucune prestation.",
            [("Salaires nets", SMIC_NET * 2),
             ("Prime d'activité", prime_activite(SMIC_NET * 2, personnes=4)),
             ("Allocations familiales", allocations_familiales(2))],
            [("Salaires nets", SMIC_NET * 2),
             ("Socle adulte × 2", socle * 2),
             (f"Forfait enfant ({forfait:.0f} € × 2)", forfait * 2),
             ("Contribution de solidarité", smic_contribution * 2)],
            "Le grand gagnant, et il est nombreux. L'individualisation du "
            "socle double le versement là où le système actuel ne verse "
            "presque rien, parce qu'il raisonne par foyer.",
            "", personnes=4),
        CasType(
            "Étudiant décohabitant, non boursier",
            "Logé seul, aide au logement pour toute ressource publique.",
            [("Aide au logement", APL_ETUDIANT)],
            [("Socle adulte", socle)],
            "Le cas-type le plus favorable du programme, et le site ne le "
            "chiffrait pas. Le socle est versé douze mois sur douze, là où une "
            "bourse en couvre dix, et sans dossier annuel.",
            "Un boursier d'échelon 5 est à peu près neutre : "
            f"{BOURSE_ECHELON_5_ANNUELLE / 12 + APL_ETUDIANT:.0f} € par mois "
            "lissés aujourd'hui, contre "
            f"{SOCLE_CIBLE} € demain, la bourse recentrée en plus."),
    ]


# -- 7. la question que la note ne tranche pas -------------------------------
#
# C'est la conclusion du chiffrage, et elle est plus dure que le reste.
#
# La note ne dit nulle part si la contribution de solidarité REMPLACE l'impôt
# sur le revenu ou s'y AJOUTE. Tant que ce n'est pas écrit, le même programme
# se lit de deux façons opposées — et un adversaire choisira la pire.

IR_RENDEMENT = 88.0   # Md€, impôt sur le revenu


def lectures_de_la_contribution(bouclage: Bouclage) -> list[tuple[str, str]]:
    """Les deux lectures possibles, et ce que chacune produit."""
    taux = bouclage.taux * 100
    return [
        ("La contribution remplace l'impôt sur le revenu",
         f"Le prélèvement sur les revenus devient proportionnel, à {taux:.0f} % "
         "environ. Un haut revenu, aujourd'hui imposé à 41 ou 45 % sur sa "
         f"dernière tranche, paie {taux:.0f} %. La réforme devient le plus gros "
         "allègement d'impôt jamais consenti au dernier décile, financé pour "
         "partie par les prestations des premiers. C'est défendable, mais il "
         "faut le savoir avant de l'être."),
        ("La contribution s'ajoute à l'impôt sur le revenu",
         f"Les {taux:.0f} points viennent au-dessus du barème actuel et de la "
         "CSG. La progressivité est préservée, le premier décile est mieux "
         "protégé, et le taux marginal du haut du barème devient "
         "difficilement soutenable. C'est l'autre moitié de l'arbitrage."),
    ]


#: La contrainte de fond, qui ne dépend d'aucune hypothèse : un prélèvement
#: strictement proportionnel ne peut pas concentrer l'effort sur le haut. Le
#: socle qui protège le bas coûte donc un taux qui frappe le milieu, sauf à
#: conserver un élément progressif quelque part.
def contrainte_structurelle() -> str:
    protege = boucler(SOCLE_NEUTRALITE)
    partiel = boucler(SOCLE_CIBLE)
    return (
        f"Un socle de {SOCLE_CIBLE} € laisse le célibataire sans emploi perdre "
        f"{abs(cas_types()[0].ecart):.0f} € par mois. Le socle qui ne fait "
        f"aucun perdant est de {SOCLE_NEUTRALITE} €, et il porte la "
        f"contribution de {partiel.taux * 100:.0f} % à "
        f"{protege.taux * 100:.0f} %. Entre les deux, il n'y a pas de "
        "calibrage habile : il y a un arbitrage politique, et un prélèvement "
        "proportionnel ne permet pas de le contourner.")


# -- 8. les barèmes servis au calculateur ------------------------------------
#
# Le calculateur a besoin des mêmes barèmes que les cas-types pour afficher sa
# colonne « aujourd'hui ». Les recopier en JavaScript les ferait diverger au
# premier ajustement — c'est exactement la faute que le dépôt s'interdit pour
# le texte du programme. Ils sont donc écrits DANS la page par le générateur,
# et le script les lit.


def baremes_du_calculateur() -> dict:
    """Les barèmes 2026 dont la colonne « aujourd'hui » a besoin."""
    return {
        "rsa": {
            "base": RSA_PERSONNE_SEULE,
            "coefficients": {str(k): v for k, v in RSA_COEFFICIENTS.items()},
            "supplementaire": RSA_COEFFICIENT_SUPPLEMENTAIRE,
            "partsLogement": {str(k): v
                              for k, v in RSA_FORFAIT_LOGEMENT_PARTS.items()},
            "partLogementGrande": RSA_FORFAIT_LOGEMENT_PART_GRANDE,
        },
        "aspa": ASPA_PERSONNE_SEULE,
        "aah": AAH,
        "allocationsFamiliales": ALLOCATIONS_FAMILIALES_2,
        "allocationsParEnfantSup": ALLOCATIONS_FAMILIALES_PAR_ENFANT_SUP,
        "smicNet": SMIC_NET,
        "primeAuSmic": PRIME_ACTIVITE_AU_SMIC,
        "primeExtinction": PRIME_EXTINCTION_SMIC,
        "aplSansRessources": APL_SANS_RESSOURCES,
        "aplFamille": APL_FAMILLE,
        "aplExtinction": APL_EXTINCTION_SMIC,
        "seuilPauvrete": SEUIL_PAUVRETE,
    }
