import json


def load_titles(filename):
    """Charge les titres depuis un fichier JSON"""
    with open(filename, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [entry["title"] for entry in data]


def load_products(filename):
    """Charge les produits depuis un fichier JSON"""
    with open(filename, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [entry["url"] for entry in data] 


# On charge les titres et produits des deux fichiers
output_titles = load_titles("output.json")
results_titles = load_titles("results.json")

output_products = load_products("output.json")
results_products = load_products("results.json")

# On compare les titres
correct_count_titles = sum(1 for o, r in zip(output_titles, results_titles) if o == r)
total_titles = len(results_titles)
print(f"Titres corrects en position : {correct_count_titles}/{total_titles}")

# On affiche les titres de output et results
print("\nTitres dans output.json :")
for title in output_titles:
    print(title)

print("\nTitres dans results.json :")
for title in results_titles:
    print(title)

# On compare les produits (peu importe l'ordre)
correct_count_products = len(set(output_products) & set(results_products))
total_products = len(results_products)
print(f"\nProduits identiques : {correct_count_products}/{total_products}")
