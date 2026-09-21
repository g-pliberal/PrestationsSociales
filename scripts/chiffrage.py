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

#: La pension nette médiane, tous régimes : la moitié des retraités perçoit
#: moins. C'est le cas type que la décision sur le troisième étage crée, et il
#: doit figurer à côté de celui du minimum vieillesse, qui perd encore.
PENSION_MEDIANE = 1560.0

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


def boucler(socle_mensuel: float = SOCLE_CIBLE) -> Bouclage:
    """LE BOUCLAGE PUBLIÉ : les deux étages, adulte et senior.

    C'est le défaut, et c'est délibéré. Ce module a d'abord porté un bouclage
    à un seul étage ; quand le second est arrivé, six appels sur sept ont
    continué de renvoyer l'ancien chiffre sans que rien ne le signale. Le
    défaut d'une fonction est ce qu'on obtient quand on ne réfléchit pas — il
    doit donc être la réponse juste. `boucler_etage()` reste disponible pour
    le tableau qui décompose les deux étages, et il faut l'appeler exprès.
    """
    return boucler_etage(
        socle_mensuel,
        personnes=POPULATION_18_64 + POPULATION_65_PLUS,
        # L'ASPA est absorbée, mais le complément vieillesse en sert une part :
        # il se retranche donc de l'économie, et non du coût brut.
        absorbe_milliards=(sum(poste.milliards for poste in ABSORBEES)
                           + ASPA_COUT
                           - cout_complement_vieillesse(socle_mensuel)))


def boucler_etage(socle_mensuel: float = SOCLE_CIBLE,
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

    Le site publie un taux rond ; s'en servir ailleurs à la décimale ferait
    répondre le calculateur et les cas-types à quelques euros près sur les
    mêmes situations. Un écart pareil ne se remarque que quand quelqu'un le
    cherche, et quelqu'un le cherchera.
    """
    return round(boucler(socle_mensuel).taux, 2)


def calibrations() -> list[Bouclage]:
    """Les calibrations que le site met côte à côte, réforme complète.

    De la première marche de la note au socle qui ne fait aucun perdant, en
    passant par le plafond que la Constitution impose : c'est l'échelle
    complète de l'arbitrage, et elle montre ce qu'il coûte.
    """
    niveaux = [SOCLE_MARCHE, SOCLE_CIBLE, SOCLE_PLAFOND, SOCLE_NEUTRALITE]
    return [boucler(niveau) for niveau in sorted(set(niveaux))]


# -- 4. le troisième étage : servi à tous ------------------------------------
#
# SECONDE DÉCISION DU PARTI. La note pose trois étages (§3) et n'en chiffre
# qu'un. Le socle senior pouvait se lire de deux façons : différentiel, au
# niveau de l'ASPA — auquel cas l'architecture n'a plus que deux étages —, ou
# servi à tous, comme le socle adulte.
#
# IL EST SERVI À TOUS. C'est la lecture cohérente avec le §3, et c'est la seule
# tenable une fois admis que la contribution s'ajoute à l'impôt : l'assiette
# comprend les pensions, et un retraité qui paie sans rien recevoir n'est pas
# une conséquence acceptable d'une réforme qui promet un socle à chacun.
#
# Elle coûte quatre-vingt-treize milliards, et elle fait passer la contribution
# de treize à dix-neuf points. C'est le prix de la cohérence, et il est écrit.

ASPA_COUT = 4.3   # Md€ / an, dépense actuelle du minimum vieillesse

SENIOR_SERVI_A_TOUS = True

#: Les bénéficiaires actuels du minimum vieillesse. Le socle leur est versé
#: comme aux autres, mais il est inférieur à ce qu'ils touchent : il leur faut
#: un complément, exactement comme l'AAH devient un complément handicap (§10).
BENEFICIAIRES_ASPA = 700_000


def cout_senior(socle_mensuel: float = SOCLE_CIBLE) -> float:
    """Le coût net du troisième étage, en Md€ : le brut moins l'ASPA absorbée."""
    return (cout_brut(socle_mensuel, POPULATION_65_PLUS) / MILLIARD
            - ASPA_COUT)


#: Le complément vieillesse porte les ressources au niveau de l'ASPA. Il est
#: DIFFÉRENTIEL, comme elle, et c'est ce qui le rend abordable : le socle étant
#: servi à tous, il ne reste à payer que ce qui dépasse.
COMPLEMENT_VIEILLESSE_PLAFOND = ASPA_PERSONNE_SEULE


def complement_vieillesse(pension: float, socle_mensuel: float = SOCLE_CIBLE) -> float:
    """Ce que touche, en plus du socle, un retraité dont la pension est faible."""
    return max(0.0, COMPLEMENT_VIEILLESSE_PLAFOND - socle_mensuel - pension)


def cout_complement_vieillesse(socle_mensuel: float = SOCLE_CIBLE) -> float:
    """Le coût annuel du complément vieillesse, en Md€.

    ATTENTION À LA MÉCANIQUE, parce qu'elle est contre-intuitive et qu'une
    première version de ce calcul s'y est trompée d'un facteur quatre.

    L'ASPA est DIFFÉRENTIELLE : elle complète les ressources jusqu'à un
    plafond. Un bénéficiaire qui touche 512 € d'ASPA a donc déjà 532 € de
    pension par ailleurs. Servir le socle à tous lui apporte 550 € de plus, ce
    qui le fait passer AU-DESSUS du plafond : il n'a plus besoin de rien.

    Le complément ne paie donc, par bénéficiaire, que la part de l'ASPA
    d'aujourd'hui qui EXCÈDE le socle — et non l'écart entre le socle et le
    plafond, qui supposerait une pension nulle pour tous.

    Faute de connaître la distribution des montants d'ASPA servis, on la prend
    uniforme entre zéro et le plafond. L'hypothèse n'est pas gratuite : une
    telle distribution a pour moyenne la moitié du plafond, soit 521,80 €, et
    la moyenne observée est de 512 € — deux pour cent d'écart. C'est une
    coïncidence utile, et elle est dite plutôt que cachée.
    """
    plafond = COMPLEMENT_VIEILLESSE_PLAFOND
    if socle_mensuel >= plafond:
        return 0.0
    moyenne_versee = (plafond - socle_mensuel) ** 2 / (2 * plafond)
    return moyenne_versee * 12 * BENEFICIAIRES_ASPA / MILLIARD


def aspa_moyenne_observee() -> float:
    """L'allocation moyenne effectivement servie, qui valide l'hypothèse."""
    return ASPA_COUT * MILLIARD / BENEFICIAIRES_ASPA / 12


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
# égales par ailleurs. L'impôt sur le revenu n'y apparaît pas parce qu'il NE
# BOUGE PAS : le parti a tranché, la contribution s'y ajoute (voir §7). Ces
# cas-types, écrits avant l'arbitrage, en étaient déjà le calcul direct.

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
    #: Vide pour la métropole. Un cas type d'outre-mer se lit contre un barème
    #: local, et il doit le dire : sans quoi on compare deux choses qui ne sont
    #: pas comparables.
    territoire: str = ""

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
            "Retraité au minimum vieillesse, sans pension",
            "À l'ASPA, et sans aucune autre ressource. Le cas le plus "
            "défavorable de la population du minimum vieillesse.",
            [("ASPA", ASPA_PERSONNE_SEULE)],
            [("Socle senior", socle),
             ("Complément vieillesse", complement_vieillesse(0, socle))],
            "Neutre, et c'est le complément vieillesse qui le rend tel. Le "
            "socle seul l'aurait fait perdre "
            f"{ASPA_PERSONNE_SEULE - socle:.0f} € par mois : c'est le décalque "
            "exact du complément handicap que la note prévoit au §10, appliqué "
            "à la vieillesse.",
            "La neutralité suppose un complément différentiel calibré sur le "
            f"plafond de l'ASPA, soit {ASPA_PERSONNE_SEULE:.2f} € de ressources "
            "garanties."),
        CasType(
            "Retraité à la pension médiane",
            "La moitié des retraités perçoit moins que cette pension.",
            [("Pension nette", PENSION_MEDIANE)],
            [("Pension nette", PENSION_MEDIANE),
             ("Socle senior", socle),
             ("Contribution de solidarité", -round(PENSION_MEDIANE * taux))],
            "C'est ce que produit la décision de servir le socle senior à "
            "tous. L'assiette de la contribution comprend les pensions : sans "
            "troisième étage, ce retraité paierait sans rien recevoir. Avec "
            "lui, il gagne — et c'est le cas de la très grande majorité des "
            "retraités, puisque la bascule ne se fait qu'au-dessus de "
            f"{boucler(socle).bascule_mensuelle:.0f} € de pension.",
            "Aucune pension n'augmente du fait de la réforme (§15) : c'est le "
            "socle qui s'ajoute, pas la pension qui change."),
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
            "À Mayotte, célibataire sans emploi",
            "Au RSA mahorais, dont le barème est réduit de moitié.",
            [("RSA de Mayotte", RSA_MAYOTTE)],
            [("Socle adulte", socle)],
            "Le gain le plus spectaculaire du programme, et il tient à une "
            "seule chose : le socle est <strong>le même pour tous</strong>. "
            "Un barème réduit de moitié ne survit pas à un droit universel — "
            "c'est une conséquence de la doctrine, pas une faveur.",
            "L'aide au logement n'est pas comptée : elle n'a pas à Mayotte la "
            "forme qu'elle a ailleurs. Le coût de l'alignement est chiffré à "
            "part.",
            territoire="Mayotte"),
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


# -- 7. la contribution s'ajoute à l'impôt sur le revenu ---------------------
#
# LE PARTI A TRANCHÉ, et c'est la décision la plus lourde du programme.
#
# La note créait une contribution de solidarité proportionnelle (§18) sans dire
# si elle REMPLAÇAIT l'impôt sur le revenu ou si elle s'y AJOUTAIT. Les deux
# lectures sortaient du même texte et ne décrivaient pas le même programme :
# l'une faisait du socle le plus gros allègement jamais consenti au dernier
# décile, l'autre préserve la progressivité du barème.
#
# La position retenue est la seconde : LA CONTRIBUTION S'AJOUTE. Le barème de
# l'impôt sur le revenu reste ce qu'il est, et la contribution vient au-dessus.
#
# Ce choix ferme d'un coup l'attaque principale du programme. Il en ouvre deux
# autres, qui sont calculées ici parce qu'elles ne sont pas des détails de
# calibrage : le taux marginal au sommet du barème, et le sort des retraités.

IR_RENDEMENT = 88.0   # Md€, impôt sur le revenu — inchangé par la réforme

#: Les prélèvements qui se cumulent au sommet du barème, sur les revenus
#: d'activité. ORDRES DE GRANDEUR : l'abattement de 10 % est plafonné, la
#: contribution exceptionnelle sur les hauts revenus ne joue qu'au-delà de
#: certains seuils, et le calcul exact dépend du foyer. La méthode est visible
#: ci-dessous pour qu'on puisse la refaire.
IR_TAUX_SOMMET = 0.45
CEHR_TAUX_SOMMET = 0.04
CSG_CRDS_ACTIVITE = 0.097
CSG_DEDUCTIBLE = 0.068
ASSIETTE_CSG_ACTIVITE = 0.9825

#: Le seuil au-delà duquel un prélèvement risque la censure. Le Conseil d'État
#: a synthétisé la jurisprudence du Conseil constitutionnel — décision
#: 2012-662 DC, qui a censuré des taux marginaux de 75 % — par une règle
#: simple : DEUX TIERS, quelle que soit la source du revenu.
SEUIL_CONFISCATOIRE = 2 / 3


def taux_marginal_sommet(contribution: float | None = None,
                         deductible: bool = True) -> float:
    """Le taux marginal au sommet du barème, revenus d'activité.

    `deductible` dit si la contribution de solidarité s'impute sur l'assiette
    de l'impôt sur le revenu, comme le fait déjà la CSG pour sa part
    déductible. Ce n'est pas un détail technique : c'est ce qui fait passer le
    total au-dessus ou au-dessous du seuil des deux tiers.
    """
    if contribution is None:
        contribution = 0.0
    csg = CSG_CRDS_ACTIVITE * ASSIETTE_CSG_ACTIVITE
    assiette_ir = 1 - CSG_DEDUCTIBLE * ASSIETTE_CSG_ACTIVITE
    if deductible:
        assiette_ir -= contribution
    return (csg + contribution + IR_TAUX_SOMMET * assiette_ir
            + CEHR_TAUX_SOMMET)


def taux_maximal_constitutionnel() -> float:
    """Le taux de contribution au-delà duquel le seuil des deux tiers est franchi.

    On résout l'inégalité du taux marginal pour la contribution, à barème de
    l'impôt sur le revenu inchangé et contribution déductible :

        CSG + t + IR × (assiette − t) + CEHR ≤ 2/3

    Ce n'est pas une curiosité arithmétique. C'est la contrainte que les deux
    décisions du parti — la contribution s'ajoute à l'impôt, le socle senior
    est servi à tous — imposent désormais à TOUT le reste du programme.
    """
    csg = CSG_CRDS_ACTIVITE * ASSIETTE_CSG_ACTIVITE
    assiette_ir = 1 - CSG_DEDUCTIBLE * ASSIETTE_CSG_ACTIVITE
    return ((SEUIL_CONFISCATOIRE - csg - IR_TAUX_SOMMET * assiette_ir
             - CEHR_TAUX_SOMMET) / (1 - IR_TAUX_SOMMET))


def socle_pour_taux(taux: float) -> float:
    """Le socle mensuel que finance un taux donné, réforme complète."""
    net = taux * ASSIETTE_LARGE
    absorbe = sum(poste.milliards for poste in ABSORBEES) + ASPA_COUT
    brut = (net + absorbe) * MILLIARD
    return brut / ((POPULATION_18_64 + POPULATION_65_PLUS) * 12)


#: LE PLAFOND. Le socle le plus élevé que les deux décisions laissent possible
#: sans franchir le seuil des deux tiers. Il n'est pas choisi : il tombe du
#: calcul, et il ferme une option que le site présentait encore comme ouverte —
#: celle d'un socle assez haut pour ne faire aucun perdant.
SOCLE_PLAFOND = round(socle_pour_taux(taux_maximal_constitutionnel()))


#: La part de l'assiette large qui est constituée de pensions de retraite.
#: C'est elle qui décide du sort des retraités sous ce choix, et le chiffre est
#: un ordre de grandeur assumé.
PART_PENSIONS = 0.20


def taux_hors_pensions(socle_mensuel: float = SOCLE_CIBLE) -> float:
    """Le taux qu'il faudrait si les pensions étaient exonérées.

    Exonérer les pensions rétrécit l'assiette d'un cinquième ; le même montant
    à financer sur une assiette plus petite se paie par un taux plus élevé, et
    ce sont les actifs qui le paient.
    """
    return boucler(socle_mensuel).net / (ASSIETTE_LARGE * (1 - PART_PENSIONS))



#: La contrainte de fond. Elle a changé de nature avec les deux décisions du
#: parti : ce n'était qu'un arbitrage politique entre un socle bas et une
#: contribution basse ; c'est désormais un PLAFOND, et il se calcule.
def contrainte_structurelle() -> str:
    retenu = boucler(SOCLE_CIBLE)
    plafond = boucler(SOCLE_PLAFOND)
    perte = abs(cas_types()[0].ecart)
    return (
        f"Un socle de {SOCLE_CIBLE} € laisse le célibataire sans emploi perdre "
        f"{perte:.0f} € par mois, et le socle qui ne ferait aucun perdant est "
        f"de {SOCLE_NEUTRALITE} €. Mais cette option est fermée : à "
        f"{SOCLE_NEUTRALITE} €, la contribution dépasse de loin le taux qui "
        "fait franchir au prélèvement marginal le seuil des deux tiers. Le "
        f"plafond réel est de {SOCLE_PLAFOND} € par mois, pour une contribution "
        f"de {plafond.taux * 100:.0f} % — contre {retenu.taux * 100:.0f} % à la "
        f"cible de {SOCLE_CIBLE} €. Entre les deux, la marge est mince, et elle "
        "est tout ce dont le programme dispose.")


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


# -- 9. l'outre-mer ----------------------------------------------------------
#
# LA NOTE N'EN PARLE PAS. Vingt-deux sections, aucune mention des départements
# et régions d'outre-mer ni des collectivités. C'est le silence le plus coûteux
# du document : trois personnes sur dix y sont couvertes par les minima
# sociaux, contre une sur dix en métropole, et un programme social muet sur ces
# territoires sera lu comme un programme écrit contre eux.
#
# Il y a là deux questions distinctes, et les confondre serait une faute :
#   - dans les DROM, le socle s'applique de plein droit, mais il y rencontre un
#     niveau de pauvreté et un niveau de prix qui ne sont pas ceux de la
#     métropole — et, à Mayotte, un barème du RSA réduit de moitié ;
#   - dans plusieurs collectivités, la protection sociale est une compétence
#     LOCALE, et le socle ne peut pas s'y appliquer par décision de Paris.

RSA_MAYOTTE = 325.85   # € / mois, personne seule, 2026 — la moitié du barème


@dataclass(frozen=True)
class Territoire:
    nom: str
    population: int
    pauvrete: float        # part sous le seuil de pauvreté national
    ecart_prix: float      # niveau général des prix, écart avec la métropole
    rsa: float             # montant forfaitaire applicable, personne seule
    note: str = ""

    @property
    def aligne(self) -> bool:
        """Le barème du RSA y est-il celui de la métropole."""
        return abs(self.rsa - RSA_PERSONNE_SEULE) < 1


#: Les cinq départements et régions d'outre-mer. Le socle s'y applique de plein
#: droit : ils sont déjà dans l'hypothèse de population de la note (§4).
DROM = [
    Territoire("La Réunion", 885_174, 0.361, 0.07, RSA_PERSONNE_SEULE),
    Territoire("Guadeloupe", 388_000, 0.345, 0.12, RSA_PERSONNE_SEULE),
    Territoire("Martinique", 347_686, 0.268, 0.12, RSA_PERSONNE_SEULE),
    Territoire("Guyane", 312_055, 0.53, 0.12, RSA_PERSONNE_SEULE),
    Territoire("Mayotte", 320_000, 0.773, 0.07, RSA_MAYOTTE,
               "Recensement en cours ; le barème du RSA y est réduit de moitié."),
]

#: Les collectivités où la protection sociale relève de la collectivité
#: elle-même. Ce n'est pas une nuance administrative : c'est une limite de
#: compétence, et le programme ne peut pas la franchir seul.
COLLECTIVITES_AUTONOMES = [
    ("Nouvelle-Calédonie", 268_000,
     "Loi organique n° 99-209 du 19 mars 1999",
     "La protection sociale est une compétence de la Nouvelle-Calédonie, qui a "
     "son propre système."),
    ("Polynésie française", 280_000,
     "Loi organique n° 2004-192 du 27 février 2004",
     "La Polynésie française est compétente et autonome en matière de "
     "protection sociale."),
]

#: Le panier alimentaire métropolitain coûte de 37 % à 48 % de plus dans les
#: DROM. C'est ce chiffre-là, et non l'écart du niveau général, qui décide de
#: ce qu'un socle de 550 € permet d'acheter.
ECART_PRIX_ALIMENTAIRE = (0.37, 0.48)

#: Part de la population couverte par les minima sociaux, conjoints et enfants
#: compris (DREES).
COUVERTURE_MINIMA_DROM = 0.30
COUVERTURE_MINIMA_METROPOLE = 0.10


def population_drom() -> int:
    return sum(territoire.population for territoire in DROM)


def cout_alignement_mayotte(socle_mensuel: float = SOCLE_CIBLE) -> float:
    """Ce que coûterait le socle plein à Mayotte, en Md€ bruts.

    Ordre de grandeur, et il faut le dire comme tel : Mayotte est un
    département très jeune — près de la moitié de sa population a moins de
    18 ans — et la condition de séjour régulier y réduit l'assiette dans une
    proportion que ce calcul ne connaît pas.
    """
    mayotte = next(t for t in DROM if t.nom == "Mayotte")
    adultes = mayotte.population * 0.45
    return socle_mensuel * 12 * adultes / MILLIARD


# -- 10. l'indexation --------------------------------------------------------
#
# LA NOTE NE DIT PAS COMMENT LE SOCLE ÉVOLUE. Elle fixe une cible — 550 € — et
# s'arrête là. Or un montant sans règle d'indexation n'est pas un droit : c'est
# une ligne budgétaire qu'un arbitrage peut raboter chaque automne sans que
# personne n'ait jamais voté sa baisse.
#
# Le précédent est connu : le point d'indice de la fonction publique n'a jamais
# été indexé, et il a perdu près d'un quart de sa valeur en vingt ans, gel après
# gel. Personne n'a voté cette baisse. Elle a simplement eu lieu.

#: La règle actuelle des prestations sociales : revalorisation annuelle sur la
#: moyenne des prix à la consommation hors tabac, avec un plancher qui interdit
#: la baisse en cas de déflation.
INDEXATION_ACTUELLE = "Art. L. 161-25 du code de la sécurité sociale"

#: La croissance du niveau de vie médian, en euros constants : environ 0,8 %
#: par an depuis 2014. C'est le rythme auquel le seuil de pauvreté s'éloigne
#: d'un socle qui ne suivrait que les prix.
CROISSANCE_NIVEAU_DE_VIE = 0.008

HORIZONS = (0, 10, 20)


@dataclass(frozen=True)
class Indexation:
    nom: str
    croissance_reelle: float
    description: str
    defaut: str


REGLES_INDEXATION = [
    Indexation(
        "Sur les prix", 0.0,
        "La règle actuelle des minima sociaux. Le socle garde son pouvoir "
        "d'achat, année après année.",
        "Il décroche du niveau de vie, qui progresse plus vite que les prix. "
        "Personne ne vote cette baisse : elle a lieu toute seule."),
    Indexation(
        "Sur le niveau de vie médian", CROISSANCE_NIVEAU_DE_VIE,
        "Le socle garde sa position relative dans la société, et le seuil de "
        "pauvreté cesse de s'en éloigner.",
        "Le coût reste constant en part de l'assiette, donc la contribution ne "
        "baisse jamais. C'est le prix de la promesse."),
    Indexation(
        "Sur les prix, plus la moitié de la croissance",
        CROISSANCE_NIVEAU_DE_VIE / 2,
        "Le compromis : le socle progresse, moins vite que la société, mais "
        "sans décrocher.",
        "Une règle composite est plus facile à contourner qu'une règle simple. "
        "Elle demande donc une garantie écrite."),
]


@dataclass(frozen=True)
class Projection:
    annee: int
    socle_reel: float       # € d'aujourd'hui
    seuil_reel: float       # € d'aujourd'hui
    part_du_seuil: float
    taux: float


def projeter(regle: Indexation, socle_mensuel: float = SOCLE_CIBLE,
             horizons: tuple[int, ...] = HORIZONS) -> list[Projection]:
    """Ce que devient le socle sous une règle donnée, en euros d'aujourd'hui.

    Tout est exprimé en euros constants : l'inflation disparaît des deux côtés
    et ne laisse voir que ce qui compte, l'écart entre le socle et le niveau de
    vie du pays.

    Le taux de contribution suit le rapport inverse : l'assiette progresse au
    rythme de l'économie, le socle au rythme de sa règle. Un socle indexé sur
    les seuls prix coûte donc un peu moins cher chaque année — ce qui est
    exactement la même chose que dire qu'il donne un peu moins.
    """
    taux_initial = taux_publie(socle_mensuel)
    projections = []
    for annee in horizons:
        croissance = (1 + regle.croissance_reelle) ** annee
        reference = (1 + CROISSANCE_NIVEAU_DE_VIE) ** annee
        socle = socle_mensuel * croissance
        seuil = SEUIL_PAUVRETE * reference
        projections.append(Projection(
            annee=annee,
            socle_reel=socle,
            seuil_reel=seuil,
            part_du_seuil=socle / seuil,
            taux=taux_initial * croissance / reference))
    return projections
