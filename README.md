# Crawler Indexation Web

Ce projet est un crawler qui explore un site web pour récupérer des informations sur les produits et les enregistre dans un fichier `output.json`. Le crawler utilise la bibliothèque `BeautifulSoup` pour extraire les données et respecte les règles du fichier `robots.txt` des sites crawlé.

## Prérequis

Avant de lancer le projet, installer les dépendances nécessaires avec la commande suivante dans le terminal :

```bash
pip install -r requirements.txt
```

Une fois les dépendances installées, vous pouvez lancer le crawler en exécutant le fichier `crawler.py`

Le fichier `output.json` contient les informations extraites par le crawler. On compare ces résultats avec un fichier de référence `results.json`, qui devrait théoriquement contenir les mêmes informations.
Finalement, le script `test.py` compare le contenu des deux fichiers, en se concentrant sur la comparaison des titres et des produits.



