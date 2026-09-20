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
 *  rien à elle seule — le montant est écrit à côté, dans la même cellule. */
function tableau(reglage) {
  const maximum = Math.max(
    ...PALIERS.map((revenu) => compte(reglage, revenu).disponible), 1,
  );
  const lignes = PALIERS.map((revenu) => {
    const resultat = compte(reglage, revenu);
    const part = Math.max(0, Math.min(100, (resultat.disponible / maximum) * 100));
    const bascule = resultat.disponible >= revenu
      ? '<span class="badge proposition">bénéficiaire net</span>'
      : '<span class="badge">contributeur net</span>';
    return `<tr><th class="texte" scope="row">${euros.format(revenu)}</th>`
      + `<td class="nombre">${euros.format(resultat.contribution)}</td>`
      + `<td class="nombre">${euros.format(resultat.disponible)}`
      + `<div class="barre liberal"><span style="width:${part.toFixed(1)}%"></span>`
      + "</div></td>"
      + `<td class="texte">${bascule}</td></tr>`;
  }).join("");
  const titre = "Le même calcul à sept niveaux de revenu du travail, par mois";
  return '<div class="defilant" tabindex="0" role="region" '
    + `aria-label="${titre}"><table><caption><span>${titre}</span></caption>`
    + '<thead><tr><th class="texte" scope="col">Revenu du travail</th>'
    + '<th class="nombre" scope="col">Contribution</th>'
    + '<th class="nombre" scope="col">Revenu disponible</th>'
    + '<th class="texte" scope="col">Position</th></tr></thead>'
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

  const fiches = '<div class="fiches reperes">'
    + fiche("Ce qui est versé", euros.format(verse), detailVerse)
    + fiche("Contribution de solidarité", euros.format(resultat.contribution),
      `${(reglage.taux * reglage.palier.contribution * 100).toFixed(0)} % du revenu `
      + "du travail")
    + fiche("Revenu disponible", euros.format(resultat.disponible),
      `contre ${euros.format(reglage.revenu)} de revenu du travail seul`)
    + fiche("Gain pour 100 € gagnés en plus", euros.format(gain),
      "il ne dépend d'aucune aide perdue")
    + "</div>";

  const phrases = [];
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
    phrases.push("<p>Le socle senior remplace l'ASPA et les dispositifs non "
      + "contributifs de minimum vieillesse. Il <strong>n'augmente aucune pension "
      + "existante</strong> : une pension contributive s'ajoute à ce calcul, selon "
      + 'les droits acquis. <a href="protections.html#retraites">Voir les '
      + "retraites</a></p>");
    phrases.push("<p>La note ne chiffre pas le socle senior séparément : le calcul "
      + "retient ici le montant du socle adulte.</p>");
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
    + "le taux et le forfait ne sont pas fixés par elle et se règlent ci-dessus.</p>";

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
