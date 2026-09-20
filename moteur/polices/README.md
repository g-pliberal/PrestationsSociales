# Les polices du site

Deux familles, et rien d'autre.

- **[Public Sans](https://public-sans.digital.gov/)**, la sans-serif de l'affiche
  — titres en capitales, texte courant, chiffres. C'est un fichier **variable** :
  un seul pour toutes les graisses de 100 à 900, ce qui évite d'en charger
  quatre pour les 400, 500, 700 et 900 que la feuille demande.
- **[Instrument Serif](https://github.com/Instrument/instrument-serif)**, pour
  les chapeaux, les promesses des engagements et les titres d'encadré. Une seule
  graisse, romain seul : l'italique n'est utilisée nulle part, et ne se charge
  donc pas.

Les deux sont sous **SIL Open Font License 1.1** — `LICENSE-public-sans.md` et
`LICENSE-instrument-serif.txt`, à côté, recopiées sans retouche. Elle autorise
l'usage, la modification et la redistribution, y compris incorporées à un site ;
la seule obligation est de ne pas les vendre seules et de conserver la licence,
ce que fait ce dossier.

## Pourquoi elles sont ici, et pas chez Google

Parce que la page promet que **rien n'est envoyé**. Une balise
`<link href="fonts.googleapis.com">` aurait fait mentir cette phrase : une
requête de police emporte l'adresse IP du lecteur, la page d'où elle part et
son navigateur, chez un tiers, à chaque visite. Le site ne demande aucune
ressource externe — ni police, ni script, ni feuille, ni pictogramme —, et ces
fichiers sont ce qui permet de continuer à l'écrire.

C'est aussi ce qui fait que le site fonctionne hors ligne une fois chargé, et
qu'il ne s'abîme pas le jour où une URL de `fonts.gstatic.com` change.

## Les fichiers

| Fichier | Famille | Sous-ensemble |
|---|---|---|
| `public-sans-latin.woff2` | Public Sans (variable, 100–900) | latin |
| `public-sans-latin-ext.woff2` | Public Sans (variable, 100–900) | latin-ext |
| `instrument-serif-latin.woff2` | Instrument Serif 400 | latin |
| `instrument-serif-latin-ext.woff2` | Instrument Serif 400 | latin-ext |

Deux sous-ensembles et non un : `latin` porte l'essentiel du français, mais pas
les `œ`, les `ÿ`, ni les guillemets et tirets que la typographie française
traîne. Le navigateur ne va chercher `latin-ext` que s'il rencontre un de ces
caractères, grâce aux `unicode-range` de la feuille — soit, en pratique, dès le
premier « œ » d'une page, et jamais sur les autres. Les quatre fichiers pèsent
78 ko au total.

## Les remplacer ou en ajouter une

Les `@font-face` sont en tête de `FEUILLE_DE_STYLE`, dans
`src/retraite_notionnelle/web/gabarit.py` — le seul endroit où la feuille
existe ; `moteur/style.css` en est extrait par
`python scripts/construire_donnees.py` et ne se modifie jamais à la main.

Pour récupérer un fichier depuis Google Fonts sans laisser le site en dépendre :

```bash
curl -A "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120" \
  "https://fonts.googleapis.com/css2?family=Public+Sans:wght@400;500;700;900" \
  | grep -A3 'latin'                       # y lire les URL de fonts.gstatic.com
curl -o moteur/polices/nom.woff2 "https://fonts.gstatic.com/s/..."
```

puis recopier dans la feuille les `unicode-range` que ce CSS donne pour chaque
sous-ensemble : les inventer ferait charger les deux fichiers à toutes les
pages, ou n'en ferait charger aucun.
