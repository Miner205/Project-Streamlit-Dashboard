# EFREI Project Streamlit Dashboard
Data Storytelling Dashboard
Arthur Donnat

cf App for more infos


# Github link :
https://github.com/Miner205/Project-Streamlit-Dashboard

# Deployed App link :
https://project-app-dashboard-arthur.streamlit.app/

# Link to used datasets :
Election présidentielle des 10 et 24 avril 2022 - Résultats définitifs du 1er tour
https://www.data.gouv.fr/datasets/election-presidentielle-des-10-et-24-avril-2022-resultats-definitifs-du-1er-tour
Contours des départements français issus d'OpenStreetMap
https://www.data.gouv.fr/datasets/contours-des-departements-francais-issus-d-openstreetmap

# datasets to maybe lookup in the future :
Election présidentielle 2012 - Résultats (par communes)
https://www.data.gouv.fr/datasets/election-presidentielle-2012-resultats-572126
Election présidentielle 2012 - Résultats (par régions, départements, circonscriptions législatives, cantons)
https://www.data.gouv.fr/datasets/election-presidentielle-2012-resultats-572124


## Déploiement et remise finale :
Sur Streamlit Community Cloud : https://project-app-dashboard-arthur.streamlit.app/.

Livrables finaux :
app / URL app déployée,
ZIP dataset/lien + README + Python,
vidéo 2–4 min,
dépôt avec code/rapport et storyboard.
Exemple zip DAI : StApp26_20000_NOM_DAI.zip.

report : no real report provided, since there is already a lot of info in the README, App, Dashboard Story, Video, etc.


## random infos:
Navigation :
- accueil et consignes,
- dahsboard :
  - histoire,
  - qualité et méthodes,
  - EDA,
  - analyse interactive.

Dans la barre latérale, charger le TXT départemental complet. Le calcul est local au processus Streamlit ; sur un hébergement distant, l’upload transfère le fichier au serveur. `st.cache_data` conserve les tables traitées en cache du processus : ne pas y envoyer de fichiers confidentiels.


## Limites actuelles & TODO :
- Pas de série temporelle : un seul tour de 2022.
- La fiche data.gouv consultée affiche « License Not Specified » (pour le dataset élection présidentielle).
- try to use libraries : altair, pydeck(optional map layer), pyarrow(memory-efficient opti) etc.
- in sidebar try to put filters above optional upload file.
- droite/gauche (quels départements vote plus à droite ou à gauche etc)
- do blank vote analysis !!!
- bug to fix: department filter ne recup/select par toujours auto les departments quand territoire est changer (entre metropole et outre mer par examples).
- do something par rapport au department 69 // 69D, 69M ??
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


## Format particulier du dataset élection présidentielle :

17 colonnes départementales, suivies de N blocs candidat à 6 champs : sexe, nom, prénom, voix, % voix/inscrits, % voix/exprimés. L’en-tête peut ne nommer que le premier bloc. Le parseur n’utilise donc pas directement `pd.read_csv` avec cet en-tête.

- Codes texte, notamment 01, 2A et 2B.
- UTF-8 avec/sans BOM, sinon Windows-1252.
- Séparateur `;`, virgules décimales.
- Rejet des lignes mal formées, effectifs négatifs, pourcentages invalides et codes départementaux dupliqués.
- Table territoires séparée de la table résultats candidat : aucun total d’inscrits/votants n’est multiplié par le nombre de candidats.
- Ratios agrégés calculés comme somme des numérateurs / somme des dénominateurs, jamais comme moyenne simple des pourcentages départementaux.
- Le filtre candidat ne modifie ni la participation ni le dénominateur exprimés.
- Contrôles des identités comptables, sommes des voix, cohérence des candidats et pourcentages publiés (tolérance 0,02 point).


## Langues :

L’application importe `from language_detection import detect_browser_language` et appelle le composant sans argument à chaque exécution.
Un retour initial vide utilise temporairement l'anglais.
Les locales fr-* et en-* sont normalisées. Le sélecteur manuel est prioritaire.


## Structure : 
Project Streamlit Dashboard/
├── app/
│   ├── .streamlit/
│   │   └── config.toml
│   ├── pages/
│   │   ├── 1_📖_Dashboard_-_Story.py
│   │   ├── 2_📊_Dashboard_-_Quality_and_Method…
│   │   ├── 3_📑_Dashboard_-_Exploration_EDA.py
│   │   └── 4_📑_Dashboard_-_Interactive_Analysis…
│   ├── utils/
│   │   ├── content.json
│   │   ├── geo.py
│   │   ├── i18n.py
│   │   └── parser.py
│   └── 🏠_Accueil_-_Home.py
├── assets/
│   ├── LOGO-EFREI.png
│   └── Photo Arthur Donnat.jpg
├── data/
│   ├── departements-20180101-shp/
│   │   ├── departements - LICENCE.txt
│   │   ├── departements-20180101.cpg
│   │   ├── departements-20180101.dbf
│   │   ├── departements-20180101.prj
│   │   ├── departements-20180101.shp
│   │   ├── departements-20180101.shx
│   │   └── departements-descriptif.txt
│   └── resultats-par-niveau-dpt-t1-france-entiere…
├── .gitignore
├── IndividualStudentPRJ_ Data StorytellingDashbo…
├── README.md
└── requirements.txt
+ Video


## Références :

- Consignes : Individual Student Project : Streamlit Dashboard, Project proposed by Mano Joseph Mathew, EFREI, PDF des consignes.
- https://docs.streamlit.io/
- https://github.com/louisoutin/streamlit-browser-language
- Portails autorisés : https://www.data.gouv.fr/datasets ; https://gd4h.ecologie.gouv.fr/en/catalogue ; https://data.europa.eu/data/combined?locale=en

## Data (main) - élection présidentielle 2022 1er tour :
- source of the used dataset : https://www.data.gouv.fr/datasets/election-presidentielle-des-10-et-24-avril-2022-resultats-definitifs-du-1er-tour
- cf dataset info on the streamlit app.


## Données géographiques :
Le dashboard utilise les **contours des départements français issus d’OpenStreetMap**, 
publiés sur data.gouv.fr :
https://www.data.gouv.fr/datasets/contours-des-departements-francais-issus-d-openstreetmap

### Licence et attribution :
Les contours proviennent d’OpenStreetMap et sont diffusés sous licence 
**Open Data Commons Open Database License (ODbL)**.  
L’attribution suivante doit être conservée :
> © les contributeurs d’OpenStreetMap sous licence ODbL
Source :  
https://www.data.gouv.fr/datasets/contours-des-departements-francais-issus-d-openstreetmap

### Fichiers utilisés :
```text
data/departements-20180101-shp/
├── departements-20180101.shp
├── departements-20180101.shx
├── departements-20180101.dbf
├── departements-20180101.prj
├── departements-20180101.cpg
└── departements-descriptif.txt
```

### Description :
- **Date de référence :** 04/01/2018.
- **Niveau géographique :** département.
- **Système de coordonnées :** WGS84.
- **Couverture :** France métropolitaine, Guadeloupe, Martinique, Guyane, La Réunion et Mayotte.
- **Attributs utilisés :** `code_insee`, `nom`, `nuts3`, `wikidata` et `surf_km2`.
- **Jointure :** `code_insee` du shapefile avec le code département du fichier des résultats de la présidentielle 2022.

### Compatibilité avec les élections de 2022 :
Les contours datent de 2018, tandis que les résultats électoraux datent de 2022.  
Cette différence n’est pas problématique ici, car l’analyse est réalisée au niveau 
départemental et les codes départementaux utilisés pour la jointure restent compatibles.

### Filtre territorial :
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

### Cartes proposées :
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
