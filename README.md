# EFREI Project Streamlit Dashboard
Data Storytelling Dashboard
Arthur Donnat

# Github link :
https://github.com/Miner205/Project-Streamlit-Dashboard

# Deployed App link :
https://project-app-dashboard-arthur.streamlit.app/


## random infos:
Navigation :
- accueil et consignes,
- dahsboard :
  - histoire,
  - qualité et méthodes,
  - EDA,
  - analyse interactive.

Dans la barre latérale, charger le TXT départemental complet. Le calcul est local au processus Streamlit ; sur un hébergement distant, l’upload transfère le fichier au serveur. `st.cache_data` conserve les tables traitées en cache du processus : ne pas y envoyer de fichiers confidentiels.


## Limites actuelles :
- Pas de série temporelle : un seul tour de 2022.
- La fiche data.gouv consultée affiche « License Not Specified » (pour le dataset élection présidentielle).
- some translation in EN missing in dashboard quality.
- etc.


## requirements :
Python 3.13 (Conda used)
requirement.txt


## To run the web app :
- In pycharm terminal, run the command "streamlit run app/🏠_Accueil_-_Home.py" in the project folder.
- open a web page with url "http://localhost:8501/"
- to close/stop the app do ctrl+c in the terminal

OR you can also create a new pycharm run configuration to run it using :
- a (new) python run configuration
- with your python interpreter
- with, instead of 'script' by default, 'module' with the value 'streamlit'
- and with parameters 'run app/🏠_Accueil_-_Home.py'


## Format particulier du dataset élection présidentielle:

17 colonnes départementales, suivies de N blocs candidat à 6 champs : sexe, nom, prénom, voix, % voix/inscrits, % voix/exprimés. L’en-tête peut ne nommer que le premier bloc. Le parseur n’utilise donc pas directement `pd.read_csv` avec cet en-tête.

- Codes texte, notamment 01, 2A et 2B.
- UTF-8 avec/sans BOM, sinon Windows-1252.
- Séparateur `;`, virgules décimales.
- Rejet des lignes mal formées, effectifs négatifs, pourcentages invalides et codes départementaux dupliqués.
- Table territoires séparée de la table résultats candidat : aucun total d’inscrits/votants n’est multiplié par le nombre de candidats.
- Ratios agrégés calculés comme somme des numérateurs / somme des dénominateurs, jamais comme moyenne simple des pourcentages départementaux.
- Le filtre candidat ne modifie ni la participation ni le dénominateur exprimés.
- Contrôles des identités comptables, sommes des voix, cohérence des candidats et pourcentages publiés (tolérance 0,02 point).


## Langues

L’application importe `from language_detection import detect_browser_language` et appelle le composant sans argument à chaque exécution.
Un retour initial vide utilise temporairement l'anglais.
Les locales fr-* et en-* sont normalisées. Le sélecteur manuel est prioritaire.


## Structure

- app.py : composition de l’accueil et choix de langue.
- utils/content.py : contenus FR/EN séparés de l’interface.
- utils/language.py : normalisation testable des locales.
- .streamlit/config.toml : thème natif, sans CSS interne fragile.
- tests/ : tests unitaires indépendants de Streamlit.

## Suite du projet

À réception du dataset : inspecter source, licence, unités, schéma et volume ; définir la question et le public ; concevoir le storyboard ; ajouter des modules de chargement/cache, préparation et visualisation ; créer les pages Histoire, EDA, Analyse, Qualité et Conclusions. La navigation multipage sera ajoutée à ce moment, sans pages factices.

`st.cache_data` n’est pas ajouté artificiellement à cet accueil statique : il sera utilisé pour le chargement et les traitements appropriés. Les exigences des trois visuels, carte ou petits multiples et KPI filtrés concernent le dashboard final, pas cette étape sans données.

## Déploiement et remise finale

Sur Streamlit Community Cloud :.

Livrables finaux : app, ZIP dataset/lien + README + Python, vidéo 2–4 min, URL déployée, dépôt avec code/rapport et storyboard. Exemple DAI : StApp26_20000_NOM_DAI.zip. L’archive de ce socle n’est pas la remise finale.

## Références

- Consignes : Individual Student Project : Streamlit Dashboard, Project proposed by Mano Joseph Mathew, EFREI, PDF des consignes.
- https://docs.streamlit.io/
- https://github.com/louisoutin/streamlit-browser-language
- Portails autorisés : https://www.data.gouv.fr/datasets ; https://gd4h.ecologie.gouv.fr/en/catalogue ; https://data.europa.eu/data/combined?locale=en

## Data (main) - élection présidentielle 2022 1er tour
- source of the used dataset : https://www.data.gouv.fr/datasets/election-presidentielle-des-10-et-24-avril-2022-resultats-definitifs-du-1er-tour
- cf dataset info on the streamlit app.


## Données géographiques
Le dashboard utilise les **contours des départements français issus d’OpenStreetMap**, 
publiés sur data.gouv.fr :
https://www.data.gouv.fr/datasets/contours-des-departements-francais-issus-d-openstreetmap

### Licence et attribution
Les contours proviennent d’OpenStreetMap et sont diffusés sous licence 
**Open Data Commons Open Database License (ODbL)**.  
L’attribution suivante doit être conservée :
> © les contributeurs d’OpenStreetMap sous licence ODbL
Source :  
https://www.data.gouv.fr/datasets/contours-des-departements-francais-issus-d-openstreetmap

### Fichiers utilisés
```text
data/departements-20180101-shp/
├── departements-20180101.shp
├── departements-20180101.shx
├── departements-20180101.dbf
├── departements-20180101.prj
├── departements-20180101.cpg
└── departements-descriptif.txt
```

### Description
- **Date de référence :** 04/01/2018.
- **Niveau géographique :** département.
- **Système de coordonnées :** WGS84.
- **Couverture :** France métropolitaine, Guadeloupe, Martinique, Guyane, La Réunion et Mayotte.
- **Attributs utilisés :** `code_insee`, `nom`, `nuts3`, `wikidata` et `surf_km2`.
- **Jointure :** `code_insee` du shapefile avec le code département du fichier des résultats de la présidentielle 2022.

### Compatibilité avec les élections de 2022
Les contours datent de 2018, tandis que les résultats électoraux datent de 2022.  
Cette différence n’est pas problématique ici, car l’analyse est réalisée au niveau 
départemental et les codes départementaux utilisés pour la jointure restent compatibles.

### Filtre territorial
Une sidebar permet de choisir le territoire affiché :
- Toutes circonscriptions
- France métropolitaine
- Corse
- DOM-TOM
- Guadeloupe
- Martinique
- Guyane
- La Réunion
- Mayotte

### Cartes proposées
- Carte de la participation par département.
- Carte du score départemental d’un candidat sélectionné.
- Contrôle visuel de la couverture géographique et de la jointure des codes INSEE.

###
territoires sans contours départementaux dans le shapefile (ZN, ZP, ZS, ZW, ZX, ZZ):
"ZN": "Nouvelle-Calédonie",
"ZP": "Polynésie française",
"ZS": "Saint-Pierre-et-Miquelon",
"ZW": "Wallis-et-Futuna",
"ZX": "Saint-Martin / Saint-Barthélemy",
"ZZ": "Français établis hors de France".
