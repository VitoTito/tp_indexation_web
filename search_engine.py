import json
from engine import process_query, load_json_file

# Charger les données d'index depuis les fichiers JSON
paths = {
    "brand": 'index_provided/brand_index.json',
    "description": 'index_provided/description_index.json',
    "domain": 'index_provided/domain_index.json',
    "origin": 'index_provided/origin_index.json',
    "synonyms": 'index_provided/origin_synonyms.json',
    "reviews": 'index_provided/reviews_index.json',
    "title": 'index_provided/title_index.json'
}

# Charger les index
origin_index = load_json_file(paths["origin"])
origin_synonyms = load_json_file(paths["synonyms"])
title_index = load_json_file(paths["title"])
review_index = load_json_file(paths["reviews"])

# Requête de test
test_query = "Dragon Energy Potion"

# Appeler la fonction de recherche
ranked_results = process_query(
    test_query,
    origin_index,
    origin_synonyms,
    title_index,
    review_index,
    match_all=True
)

# Formatage des résultats pour l'affichage ou pour enregistrer dans un fichier
output = {
    "total_documents": len(origin_index),
    "filtered_documents": len(ranked_results),
    "results": [
        {
            "title": doc,
            "url": doc,
            "score": score
        } for doc, score in ranked_results
    ]
}

# Sauvegarder les résultats dans un fichier JSON
with open('ranked_results.json', 'w') as outfile:
    json.dump(output, outfile, indent=2)

# Afficher un message pour confirmer que les résultats ont été sauvegardés
print("Les résultats ont été sauvegardés dans 'ranked_results.json'.")
