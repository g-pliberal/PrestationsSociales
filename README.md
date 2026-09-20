# Revenu universel — le programme du Parti libéral français

Un site qui présente aux nouveaux électeurs la refonte des prestations sociales
proposée par le Parti libéral français : remplacer l'empilement des aides
monétaires non contributives par un **revenu universel** simple, automatique et
individualisé, en gardant à part ce qui relève des vulnérabilités spécifiques et
des droits contributifs.

Le site est fait de pages statiques. Il n'y a rien à installer pour le lire, et
rien à construire pour le servir : `index.html` à la racine suffit.

## La source

Tout le contenu est tiré de l'unique document du dépôt,
[`documents/note-revenu-universel.pdf`](documents/note-revenu-universel.pdf) —
la note de doctrine « Revenu universel et refonte des prestations sociales »,
22 sections. Le fichier est celui qui a été versé au dépôt, inchangé ; seul son
nom a été rendu lisible pour que le site puisse y renvoyer.

**Chaque section du site dit de quelle section de la note elle vient**
(« Note de doctrine, §7 »). C'est la règle de rédaction du dépôt : une phrase
qui ne se rattache à aucune section de la note n'a rien à faire sur le site.

Les montants de la note sont des **ordres de grandeur de cadrage**, pas des
engagements chiffrés. Trois paramètres en particulier n'y sont pas fixés : le
niveau exact du socle, le taux de la contribution de solidarité et le montant du
forfait enfant. Le site le signale partout où il les emploie, et le calculateur
les rend réglables plutôt que de les inventer.

## Les pages

| Page | Ce qu'elle porte | Sections de la note |
| --- | --- | --- |
| `index.html` | Le diagnostic, la règle, les trois étages, les dix principes | §1, §2, §3, §22 |
| `revenu-universel.html` | Le socle adulte : montant, individualisation, travail gagnant, prestations absorbées | §4, §5, §6, §12, §17 |
| `simulateur.html` | Le calculateur d'illustration | §5, §18 |
| `jeunes.html` | Le socle dès 18 ans, les APL étudiantes, les bourses | §6, §13, §20.3 |
| `familles.html` | Le crédit familial, le bouclier monoparental, le couple | §7, §8, §9, §11 |
| `protections.html` | Handicap, logement, chômage, retraites : ce qui reste à part | §10, §12, §14, §15 |
| `nouveaux-residents.html` | La convergence sur dix ans, la résidence effective, le contrôle | §16, §17, §20.5 |
| `financement.html` | Coût brut, coût net, contribution de solidarité, progressivité | §18, §20.1 |
| `calendrier.html` | Les cinq années de bascule et les six points de vigilance | §19, §20 |
| `questions.html` | Dix objections, le message politique, le glossaire | §21, §22 |

## L'apparence

Elle est celle du site **Retraite à comptes notionnels** du parti
([g-pliberal/retraitecomptenotionelle](https://github.com/g-pliberal/retraitecomptenotionelle))
— affiche politique : fond vert profond, titres massifs en capitales, or pour ce
qui compte, crème pour ce qu'on doit lire de près.

`moteur/style.css` en est une **copie littérale**, précédée d'un en-tête de
seize lignes qui le dit. Elle n'est pas modifiée ici : c'est ce qui fait que les
deux sites se reconnaissent, et ce qui permet de reporter une correction faite
là-bas par une simple recopie.

```sh
# resynchroniser la feuille depuis le dépôt de la retraite
sed -n '1,16p' moteur/style.css > /tmp/entete.css
cat /tmp/entete.css ../retraitecomptenotionelle/moteur/style.css > moteur/style.css
```

Les deux polices (Public Sans et Instrument Serif, sous licence OFL) viennent du
même dépôt et sont servies depuis `moteur/polices/`. **Le site ne charge aucune
ressource tierce** : ni police, ni script, ni feuille de style extérieure. Une
requête de police chez un tiers emporterait l'adresse IP du lecteur, et le
calculateur promet précisément le contraire.

## Construire

Les pages sont écrites par un script, puis committées.

```sh
python3 scripts/construire_site.py   # réécrit les dix pages
python3 scripts/verifier.py          # pages à jour, liens et ancres valides
```

- `scripts/gabarit.py` — l'enveloppe et les fragments : bandeau, affiche, pied,
  encarts, tableaux, dépliants, mots du glossaire. Le vocabulaire de classes est
  **fermé** : une classe absente de `moteur/style.css` ne sera pas mise en page.
- `scripts/construire_site.py` — le texte du programme, page par page. C'est le
  seul endroit où une phrase du site existe.
- `scripts/verifier.py` — refuse une page qui a dérivé de son générateur, un
  lien interne cassé, une ancre absente.

Le HTML produit est committé pour que l'hébergement n'ait rien à exécuter :
GitHub Pages sur la branche, ou n'importe quel serveur de fichiers.

```sh
python3 -m http.server 8000   # pour relire le site en local
```

## Le calculateur

`moteur/simulateur.js` fait trois opérations, et rien d'autre : ajouter le
socle, ajouter le revenu du travail en entier, retirer la contribution
proportionnelle. Tout se calcule dans le navigateur, rien n'est envoyé.

**Ce n'est pas un simulateur de droits.** Il illustre une mécanique, sous des
hypothèses que la page affiche et que le lecteur peut changer. Il ne chiffre ni
le complément handicap, ni le crédit d'impôt par enfant, ni le bouclier
transitoire, ni les droits contributifs — et il le dit.

## Licence

Code sous licence Apache 2.0 (voir `LICENSE`). Les polices de `moteur/polices/`
portent leurs propres licences OFL, recopiées à côté d'elles. Les pictogrammes
viennent de Lucide 1.46.0, sous licence ISC.
