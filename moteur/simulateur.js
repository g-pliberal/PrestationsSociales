// Le calculateur d'illustration de la page « Calculer ».
//
// CE N'EST PAS UN SIMULATEUR DE DROITS, et le calcul est court pour cette
// raison : socle fixe, revenu du travail entier, contribution proportionnelle.
// C'est exactement la mécanique que la note décrit, et rien de plus. Deux des
// trois paramètres dont il a besoin — le taux de la contribution et le forfait
// enfant — ne sont pas fixés par la note, qui les renvoie au calibrage : ils
// sont donc réglables dans la page, et le résultat dit à chaque fois sous
// quelles hypothèses il a été obtenu.
//
// IL COMPARE DÉSORMAIS AU SYSTÈME ACTUEL, et c'est le seul ajout de fond. Un
// calculateur qui ne montre que le régime proposé ne répond pas à la question
// que le lecteur se pose — est-ce que j'y gagne ? —, et cette question finit
// par être tranchée par le calculateur de quelqu'un d'autre. La colonne
// « aujourd'hui » applique les barèmes 2026 ; elle est une ESTIMATION, la page
// le dit, et son détail est affiché poste par poste pour être vérifiable.
//
// Les barèmes ne sont pas écrits ici : ils sont injectés dans la page par
// `construire_site.py`, depuis `chiffrage.py`, et lus ci-dessous. Deux jeux de
// barèmes finiraient par ne plus dire la même chose.
//
// Tout se calcule ici, dans le navigateur. Rien n'est envoyé, il n'y a pas de
// serveur, et la page ne charge aucune bibliothèque.

"use strict";

/** Les paliers du barème de convergence : droit au socle, et haut de la
 *  fourchette de contribution. La note donne la contribution en fourchette
 *  (« 25 % à 50 % ») ; le calcul retient le HAUT, et la page le dit — un
 *  résultat optimiste sur le net serait le seul qu'on ne puisse pas vérifier. */
const CONVERGENCE = {
  complet: { socle: 1, contribution: 1, libelle: "régime commun" },
  75: { socle: 0.75, contribution: 1, libelle: "9 à 10 ans de résidence" },
  50: { socle: 0.5, contribution: 0.75, libelle: "6 à 8 ans de résidence" },
  25: { socle: 0.25, contribution: 0.5, libelle: "3 à 5 ans de résidence" },
  0: { socle: 0, contribution: 0.25, libelle: "moins de 3 ans de résidence" },
};

/** Les revenus du travail pour lesquels la page dresse le tableau de lecture.
 *  Le dernier sert d'échelle aux barres. */
const PALIERS = [0, 500, 1000, 1500, 2000, 3000, 4000];

/** Les barèmes 2026, écrits dans la page par le générateur. */
const BAREMES = JSON.parse(document.getElementById("baremes").textContent);

/** Le montant forfaitaire du RSA d'un foyer, forfait logement déduit.
 *  Le barème va de 100 % pour une personne à 210 % pour quatre, puis ajoute
 *  40 % par personne supplémentaire ; le forfait logement suit le même
 *  escalier. C'est la seule partie du système actuel qui se calcule exactement. */
function rsaFoyer(personnes) {
  const bareme = BAREMES.rsa;
  const coefficient = personnes <= 4
    ? bareme.coefficients[String(personnes)]
    : bareme.coefficients["4"] + bareme.supplementaire * (personnes - 4);
  const part = bareme.partsLogement[String(personnes)]
    ?? bareme.partLogementGrande;
  const reference = bareme.base * bareme.coefficients[String(Math.min(personnes, 3))];
  return bareme.base * coefficient - reference * part;
}

/** Ce que la même situation perçoit AUJOURD'HUI, poste par poste.
 *
 *  C'est une estimation, et elle est construite pour ne jamais flatter la
 *  réforme : le RSA et les allocations familiales sont exacts, l'aide au
 *  logement et la prime d'activité sont approchées par leur forme générale —
 *  l'une décroît jusqu'à s'éteindre vers deux SMIC, l'autre culmine au SMIC.
 *  Là où l'approximation a un sens, elle est prise du côté GÉNÉREUX pour le
 *  système actuel : surestimer ce qu'on remplace est la seule erreur qui ne
 *  puisse pas se retourner contre nous.
 *
 *  Rend `null` quand la comparaison n'a pas de sens : sous le régime
 *  transitoire des nouveaux résidents, le système actuel a ses propres règles
 *  de durée de séjour, et les superposer donnerait un chiffre faux. */
function aujourdhui(reglage, revenu) {
  if (reglage.palier.socle < 1) return null;
  const smic = BAREMES.smicNet;
  const postes = [];

  if (reglage.senior) {
    const complement = Math.max(0, BAREMES.aspa - revenu);
    if (complement > 0) postes.push(["ASPA", complement]);
  } else {
    const personnes = 1 + reglage.enfants;
    const rsa = Math.max(0, rsaFoyer(personnes) - revenu);
    if (rsa > 0) postes.push(["RSA", rsa]);

    if (revenu > 0) {
      const forme = revenu <= smic
        ? revenu / smic
        : Math.max(0, (BAREMES.primeExtinction * smic - revenu)
          / ((BAREMES.primeExtinction - 1) * smic));
      const coefficient = personnes <= 4
        ? BAREMES.rsa.coefficients[String(personnes)]
        : BAREMES.rsa.coefficients["4"]
          + BAREMES.rsa.supplementaire * (personnes - 4);
      const prime = BAREMES.primeAuSmic * forme * coefficient;
      if (prime > 1) postes.push(["prime d'activité", prime]);
    }

    const base = personnes === 1 ? BAREMES.aplSansRessources : BAREMES.aplFamille;
    const apl = base * Math.max(0, 1 - revenu / (BAREMES.aplExtinction * smic));
    if (apl > 1) postes.push(["aide au logement", apl]);

    if (reglage.enfants >= 2) {
      postes.push(["allocations familiales",
        BAREMES.allocationsFamiliales
        + BAREMES.allocationsParEnfantSup * (reglage.enfants - 2)]);
    }
  }

  const prestations = postes.reduce((somme, [, montant]) => somme + montant, 0);
  return { postes, prestations, total: revenu + prestations };
}

const euros = new Intl.NumberFormat("fr-FR", {
  style: "currency", currency: "EUR", maximumFractionDigits: 0,
});

function nombre(champ, defaut) {
  const valeur = Number.parseFloat(champ.value.replace(",", "."));
  return Number.isFinite(valeur) && valeur >= 0 ? valeur : defaut;
}

function echapper(texte) {
  return String(texte).replace(/[&<>"']/g, (caractere) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#x27;",
  }[caractere]));
}

/** Ce que le calcul retient de la page, à un instant donné. */
function reglages() {
  const formulaire = document.getElementById("calcul");
  const parametres = document.getElementById("reglages");
  const palier = CONVERGENCE[formulaire.residence.value] || CONVERGENCE.complet;
  return {
    revenu: nombre(formulaire.revenu, 0),
    enfants: Math.round(nombre(formulaire.enfants, 0)),
    senior: formulaire.statut.value === "senior",
    palier,
    socle: nombre(parametres.socle, 550),
    taux: nombre(parametres.taux, 30) / 100,
    forfait: nombre(parametres.forfait, 200),
  };
}

/** Les trois opérations de la réforme, pour un revenu du travail donné. */
function compte(reglage, revenu) {
  const socle = reglage.socle * reglage.palier.socle;
  const enfants = reglage.forfait * reglage.enfants;
  const contribution = revenu * reglage.taux * reglage.palier.contribution;
  return {
    socle, enfants, contribution,
    disponible: revenu + socle + enfants - contribution,
  };
}

function fiche(etiquette, valeur, precision) {
  return `<div class="fiche"><div class="valeur">${valeur}</div>`
    + `<div class="etiquette">${echapper(etiquette)}</div>`
    + `<div class="precision">${precision}</div></div>`;
}

/** Le tableau de lecture : le même calcul à sept niveaux de revenu, avec une
 *  barre pour voir d'un coup que la pente ne s'inverse jamais. La barre ne dit
 *  rien à elle seule — le montant est écrit à côté, dans la même cellule.
 *
 *  La colonne « aujourd'hui » est la raison d'être du tableau : sans elle, sept
 *  lignes de revenu disponible ne se comparent à rien. Avec elle, on lit d'un
 *  coup d'œil à partir de quel revenu la réforme devient gagnante — et en
 *  dessous de quel revenu elle ne l'est pas. */
function tableau(reglage) {
  const maximum = Math.max(
    ...PALIERS.map((revenu) => compte(reglage, revenu).disponible), 1,
  );
  const comparable = aujourdhui(reglage, 0) !== null;
  const lignes = PALIERS.map((revenu) => {
    const resultat = compte(reglage, revenu);
    const part = Math.max(0, Math.min(100, (resultat.disponible / maximum) * 100));
    const bascule = resultat.disponible >= revenu
      ? '<span class="badge proposition">bénéficiaire net</span>'
      : '<span class="badge">contributeur net</span>';
    let colonnes = "";
    if (comparable) {
      const actuel = aujourdhui(reglage, revenu);
      const ecart = resultat.disponible - actuel.total;
      const signe = ecart >= 0 ? "+" : "−";
      colonnes = `<td class="nombre">${euros.format(actuel.total)}</td>`;
      colonnes += `<td class="nombre">${signe} ${euros.format(Math.abs(ecart))}</td>`;
    }
    return `<tr><th class="texte" scope="row">${euros.format(revenu)}</th>`
      + colonnes
      + `<td class="nombre">${euros.format(resultat.disponible)}`
      + `<div class="barre liberal"><span style="width:${part.toFixed(1)}%"></span>`
      + "</div></td>"
      + `<td class="texte">${bascule}</td></tr>`;
  }).join("");
  const titre = comparable
    ? "Le même calcul à sept niveaux de revenu du travail, comparé au système actuel"
    : "Le même calcul à sept niveaux de revenu du travail, par mois";
  const entetes = '<th class="texte" scope="col">Revenu du travail</th>'
    + (comparable
      ? '<th class="nombre" scope="col">Aujourd\u2019hui</th>'
        + '<th class="nombre" scope="col">Écart</th>'
      : "")
    + '<th class="nombre" scope="col">Avec le socle</th>'
    + '<th class="texte" scope="col">Position</th>';
  return '<div class="defilant" tabindex="0" role="region" '
    + `aria-label="${titre}"><table><caption><span>${titre}</span></caption>`
    + `<thead><tr>${entetes}</tr></thead>`
    + `<tbody>${lignes}</tbody></table></div>`;
}

function rendre() {
  const reglage = reglages();
  const resultat = compte(reglage, reglage.revenu);
  const gain = 100 * (1 - reglage.taux * reglage.palier.contribution);
  // Le revenu à partir duquel la contribution dépasse ce qui est versé : c'est
  // le point où l'on cesse d'être bénéficiaire net. Il n'existe pas si le taux
  // ou la part de contribution sont nuls.
  const denominateur = reglage.taux * reglage.palier.contribution;
  const bascule = denominateur > 0
    ? (resultat.socle + resultat.enfants) / denominateur
    : null;

  const verse = resultat.socle + resultat.enfants;
  const detailVerse = reglage.enfants > 0
    ? `${euros.format(resultat.socle)} de socle et `
      + `${euros.format(resultat.enfants)} de forfait enfant`
    : (reglage.senior ? "socle senior, en remplacement de l'ASPA"
      : "socle adulte, sans condition de ressources");

  // La comparaison au système actuel : c'est elle que le lecteur cherche, donc
  // elle est mise AVANT le détail de la mécanique, et son signe est écrit en
  // toutes lettres plutôt que laissé à la couleur d'une barre.
  const actuel = aujourdhui(reglage, reglage.revenu);
  const ecart = actuel ? resultat.disponible - actuel.total : null;

  let fiches = '<div class="fiches reperes">';
  if (actuel) {
    const signe = ecart >= 0 ? "+" : "−";
    fiches += fiche("Aujourd\u2019hui", euros.format(actuel.total),
      actuel.postes.length
        ? actuel.postes.map(([nom, montant]) =>
          `${nom} ${euros.format(montant)}`).join(", ")
        : "aucune prestation, au barème 2026");
    fiches += fiche("Avec le socle", euros.format(resultat.disponible),
      `${euros.format(verse)} versés, `
      + `${euros.format(resultat.contribution)} de contribution`);
    fiches += fiche("Écart", `${signe} ${euros.format(Math.abs(ecart))}`,
      ecart >= 0 ? "par mois, en votre faveur" : "par mois, à votre détriment");
  } else {
    fiches += fiche("Ce qui est versé", euros.format(verse), detailVerse);
    fiches += fiche("Revenu disponible", euros.format(resultat.disponible),
      `contre ${euros.format(reglage.revenu)} de revenu du travail seul`);
  }
  fiches += fiche("Contribution de solidarité", euros.format(resultat.contribution),
    `${(reglage.taux * reglage.palier.contribution * 100).toFixed(0)} % du revenu `
    + "du travail")
    + fiche("Gain pour 100 € gagnés en plus", euros.format(gain),
      "il ne dépend d'aucune aide perdue")
    + "</div>";

  const phrases = [];
  if (actuel) {
    phrases.push("<p>La colonne « aujourd\u2019hui » est une <strong>estimation "
      + "au barème 2026</strong>, pas un relevé de droits : elle ne connaît ni "
      + "votre loyer, ni votre zone, ni votre trimestre de référence. Le RSA et "
      + "les allocations familiales y sont exacts ; l\u2019aide au logement et la "
      + "prime d\u2019activité sont approchées, et prises du côté généreux pour le "
      + "système actuel. "
      + '<a href="cas-types.html">Voir sept situations chiffrées une par une</a></p>');
  } else {
    phrases.push("<p>La comparaison avec le système actuel n\u2019est pas affichée "
      + "sous le régime transitoire : l\u2019accès aux prestations d\u2019aujourd\u2019hui "
      + "obéit à ses propres conditions de durée de séjour, et les superposer "
      + "au barème de convergence donnerait un chiffre faux. "
      + '<a href="nouveaux-residents.html">Voir le barème</a></p>');
  }
  if (bascule !== null) {
    phrases.push("<p>Avec ces réglages, vous êtes <strong>bénéficiaire net</strong> "
      + `tant que votre revenu du travail reste sous ${euros.format(bascule)} par `
      + "mois, et <strong>contributeur net</strong> au-delà : c'est là que la "
      + "contribution dépasse ce que le socle verse.</p>");
  }
  if (reglage.palier.socle < 1) {
    phrases.push("<p>Vous relevez du régime transitoire des nouveaux résidents "
      + `(${reglage.palier.libelle}) : le socle est versé à `
      + `${(reglage.palier.socle * 100).toFixed(0)} %, et la contribution est prise `
      + "ici au haut de sa fourchette. La part de contribution qui excède les droits "
      + "ouverts peut être créditée sur un compte individuel de solidarité, "
      + "mobilisable à l'accès complet au régime ou à la naturalisation — ce crédit "
      + "n'est pas chiffré ici. "
      + '<a href="nouveaux-residents.html">Voir le barème</a></p>');
    if (reglage.enfants > 0) {
      phrases.push("<p>Le forfait enfant est compté en entier : la note ne dit pas si "
        + "le crédit familial suit lui aussi la convergence sur dix ans.</p>");
    }
  }
  if (reglage.senior) {
    phrases.push("<p>Le socle senior est <strong>versé à tous</strong>, au même "
      + "montant que le socle adulte, et il remplace l\u2019ASPA. Il "
      + "<strong>n\u2019augmente aucune pension existante</strong> : ce n\u2019est "
      + "pas la pension qui change, c\u2019est le socle qui s\u2019y ajoute. La "
      + "contribution, elle, porte sur la pension. "
      + '<a href="financement.html#retraites">Voir la décision</a></p>');
    phrases.push("<p>Les bénéficiaires du minimum vieillesse relèvent en plus "
      + "d\u2019un complément, calibré pour qu\u2019ils ne perdent rien. Il n\u2019est "
      + "pas simulé ici.</p>");
  }
  if (reglage.enfants > 0) {
    phrases.push("<p>Seul le forfait enfant est compté ici. Le crédit familial "
      + "comporte une seconde partie — une réduction proportionnelle de l'impôt dû "
      + "par les parents — que la note ne chiffre pas, et un bouclier transitoire "
      + "protège les familles modestes et monoparentales pendant les premières "
      + 'années. <a href="familles.html">Voir les familles</a></p>');
  }

  const hypotheses = '<p class="discret">Hypothèses : socle de '
    + `${euros.format(reglage.socle)} par mois, contribution de solidarité de `
    + `${(reglage.taux * 100).toFixed(0)} % du revenu du travail, forfait enfant de `
    + `${euros.format(reglage.forfait)}. Le socle est un ordre de grandeur de la note ; `
    + "le taux et le forfait ne sont pas fixés par elle, et leurs valeurs par "
    + "défaut sont celles qui bouclent le financement. La colonne "
    + "« aujourd\u2019hui » applique les barèmes au 1ᵉʳ avril 2026. "
    + '<a href="financement.html">Voir le bouclage</a></p>';

  document.getElementById("resultat").innerHTML = fiches
    + (phrases.length ? `<div class="note">${phrases.join("")}</div>` : "")
    + tableau(reglage) + hypotheses;
}

// À la frappe, et non à la validation : il n'y a rien à envoyer, donc rien à
// valider. Le formulaire ne soumet jamais — `submit` est bloqué pour le cas où
// la touche Entrée serait pressée dans un champ.
for (const identifiant of ["calcul", "reglages"]) {
  const formulaire = document.getElementById(identifiant);
  formulaire.addEventListener("input", rendre);
  formulaire.addEventListener("submit", (evenement) => evenement.preventDefault());
}

rendre();
