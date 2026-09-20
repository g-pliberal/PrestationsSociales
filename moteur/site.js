// Le seul script que toutes les pages chargent, et il ne fait qu'une chose :
// ouvrir la définition d'un mot de jargon sous le mot.
//
// Le site s'adresse à des gens qui n'ont jamais eu à lire un barème. « Minimum
// contributif », « non-recours », « taux marginal effectif » leur sont opaques,
// et les définir dans le corps du texte l'allongerait pour tous les autres. La
// définition est donc posée SOUS le mot, et ne s'ouvre que si on la demande.
//
// L'écoute est déléguée sur le document : les mots sont écrits par le
// générateur, ils sont nombreux, et poser un écouteur sur chacun ne servirait
// qu'à en poser cent.

"use strict";

function basculer(terme) {
  const bulle = terme.nextElementSibling;
  if (!bulle || !bulle.classList.contains("bulle")) { return; }
  const ouvert = terme.getAttribute("aria-expanded") === "true";
  terme.setAttribute("aria-expanded", ouvert ? "false" : "true");
  bulle.hidden = ouvert;
}

document.addEventListener("click", (evenement) => {
  const terme = evenement.target.closest(".mot > .terme");
  if (terme) { basculer(terme); }
});

// Le mot est un `<span role="button">` et non un `<button>` — un bouton ne coule
// pas dans une phrase chez Chromium —, si bien que le clavier ne l'active pas de
// lui-même : Entrée et Espace sont donc écoutées ici. Espace ferait défiler la
// page si on la laissait passer.
document.addEventListener("keydown", (evenement) => {
  const terme = evenement.target.closest(".mot > .terme");
  if (!terme) { return; }
  if (evenement.key === "Enter" || evenement.key === " ") {
    evenement.preventDefault();
    basculer(terme);
  }
});
