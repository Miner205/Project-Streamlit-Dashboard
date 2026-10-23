# EFREI Project Streamlit Dashboard
Data Storytelling Dashboard
Arthur Donnat

Navigation : accueil et consignes, histoire, EDA, analyse interactive, qualité et méthodes.


Dans la barre latérale, charger le TXT départemental complet. Le calcul est local au processus Streamlit ; sur un hébergement distant, l’upload transfère le fichier au serveur. `st.cache_data` conserve les tables traitées en cache du processus : ne pas y envoyer de fichiers confidentiels.



## Limites actuelles

- Le fichier intégral de l’utilisateur n’était pas disponible lors de la génération. Aucune conclusion nationale n’a été calculée.
- Pas de série temporelle : un seul tour de 2022.
- Carte non implémentée. Les codes départementaux sont géographiques : une carte reste nécessaire pour la conformité finale. Il faudra un fond compatible avec les codes et la couverture réelle, documenter sa source/licence et auditer les codes non joints.
- Pas encore de storyboard final, de rapport, de vidéo ni de déploiement. Les trois graphiques constituent une première exploration, pas une histoire finalisée.
- La fiche data.gouv consultée affiche « License Not Specified ». Clarifier la licence de la ressource avant redistribution. La licence générale du site ne suffit pas.
- `detect_browser_language()` est intégré avec choix manuel prioritaire et repli FR. L’installation et le rendu de ce composant tiers doivent être testés dans un vrai navigateur. Sa version n’a pas été vérifiée, elle n’est donc pas inventée ni figée.



## requirements :
Python 3.13 (Conda used)

## To run the web app :
- In pycharm terminal, run the command "streamlit run app/Accueil_-_Home.py" in the project folder.
- open a web page with url "http://localhost:8501/"
- to close/stop the app do ctrl+c in the terminal

OR you can also create a new pycharm run configuration to run it using :
- a (new) python run configuration
- with your python interpreter
- with, instead of 'script' by default, 'module' with the value 'streamlit'
- and with parameters 'run app/Accueil_-_Home.py'


## Format particulier du fichier

17 colonnes départementales, suivies de N blocs candidat à 6 champs : sexe, nom, prénom, voix, % voix/inscrits, % voix/exprimés. L’en-tête peut ne nommer que le premier bloc. Le parseur n’utilise donc pas directement `pd.read_csv` avec cet en-tête.

- Codes texte, notamment 01, 2A et 2B.
- UTF-8 avec/sans BOM, sinon Windows-1252.
- Séparateur `;`, virgules décimales.
- Rejet des lignes mal formées, effectifs négatifs, pourcentages invalides et codes départementaux dupliqués.
- Table territoires séparée de la table résultats candidat : aucun total d’inscrits/votants n’est multiplié par le nombre de candidats.
- Ratios agrégés calculés comme somme des numérateurs / somme des dénominateurs, jamais comme moyenne simple des pourcentages départementaux.
- Le filtre candidat ne modifie ni la participation ni le dénominateur exprimés.
- Contrôles des identités comptables, sommes des voix, cohérence des candidats et pourcentages publiés (tolérance 0,02 point).

Les anomalies comptables sont signalées sans bloquer les vues ; les erreurs structurelles bloquent l’import. Le périmètre national n’est pas présumé. Les colonnes techniques des tableaux et les diagnostics du parseur ne sont pas entièrement traduits.




## Langues

L’application importe `from language_detection import detect_browser_language` et appelle le composant sans argument à chaque exécution. Un retour initial vide utilise temporairement l'anglais. Les locales fr-* et en-* sont normalisées. Le sélecteur manuel est prioritaire.

Le composant tiers nécessite une validation dans un vrai navigateur : accès au navigateur, rendu de son iframe et retour asynchrone. Une exception de détection produit un avertissement et laisse le sélecteur utilisable. Une dépendance absente fait échouer le démarrage : installer requirements.txt au préalable.

## Tests

```bash
python -m unittest discover -s tests -v
```

Tests unitaires : normalisation des locales, parité des clés FR/EN, total du barème et taille des checklists. Ils ne remplacent pas un test de l’application et du composant dans un navigateur.

Validation manuelle : navigateur français puis anglais, autre langue, changement manuel de langue, changement de langue après sélection des cases, largeur mobile, lisibilité, liens. Les compteurs d’accueil sont des objectifs pédagogiques, pas des KPI analytiques.

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

## Data
- source of the used dataset : https://www.data.gouv.fr/datasets/election-presidentielle-des-10-et-24-avril-2022-resultats-definitifs-du-1er-tour
- cf dataset info on the streamlit app.
