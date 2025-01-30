import json
import re
import string
import os
from urllib.parse import urlparse, parse_qs
from collections import defaultdict

# Input and output files
INPUT_FILE = "products.jsonl"
PROCESSED_FILE = "processed_products.jsonl"

# Common English stopwords
STOPWORDS = set(["the", "a", "an", "and", "or", "of", "to", "in", "on", "with", "for", "by", "at", "from", 
                 "is", "it", "this", "that", "as", "are", "was", "were", "be", "been", "has", "have", "had"])

# Extraction des informations des URLs
def extract_product_info(url):
    """Extracts product ID and variant (if any) from a given URL."""
    try:
        match = re.search(r"/product/(\d+)", url)
        product_id = match.group(1) if match else None

        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        
        variant_id = query_params["variant"][0] if "variant" in query_params else None

        return {"product_id": product_id, "variant": variant_id}
    except Exception as e:
        print(f"Error parsing URL: {url}. Error: {e}")
        return {"product_id": None, "variant": None}

def load_and_process_data(filename):
    """Loads JSONL data, extracts product IDs and variants from URLs."""
    processed_data = []
    
    if not os.path.exists(filename):
        print(f"Error: The file {filename} does not exist.")
        return []

    try:
        with open(filename, "r", encoding="utf-8") as file:
            for line in file:
                try:
                    doc = json.loads(line.strip())
                    doc.update(extract_product_info(doc.get("url", "")))
                    processed_data.append(doc)
                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON line: {line}. Error: {e}")
                    continue
    except Exception as e:
        print(f"Error reading file {filename}: {e}")
        return []
    
    return processed_data

def save_processed_data(data, output_file=PROCESSED_FILE):
    """Saves processed data back to JSONL format."""
    try:
        with open(output_file, "w", encoding="utf-8") as file:
            for doc in data:
                file.write(json.dumps(doc, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"Error saving processed data to {output_file}: {e}")

# Création des index inversés
def tokenize(text):
    """Tokenizes text by removing punctuation and stopwords."""
    if not text:
        return []
    
    text = text.lower()
    text = text.translate(str.maketrans('', '', string.punctuation))
    tokens = text.split()
    return [token for token in tokens if token not in STOPWORDS]

def build_inverted_index_with_positions(field, data):
    """Builds an inverted index from a given field, including positions of words in the documents."""
    inverted_index = defaultdict(lambda: defaultdict(list))  # Token -> document_id -> positions
    
    for doc_id, doc in enumerate(data):
        field_value = doc.get(field, "")
        tokens = tokenize(field_value)
        for position, token in enumerate(tokens):
            inverted_index[token][doc_id].append(position)
    
    # Convert the dictionary structure into a format compatible for JSON output
    return {token: {doc_id: positions for doc_id, positions in doc_ids.items()} for token, doc_ids in inverted_index.items()}

def save_index(index, filename):
    """Saves an index to a JSON file."""
    try:
        with open(filename, "w", encoding="utf-8") as file:
            json.dump(index, file, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving index to {filename}: {e}")

# Création de l'index des reviews
def build_reviews_index(data):
    """Builds an index for reviews with total count, average rating, and last rating."""
    reviews_index = {}
    
    for doc_id, doc in enumerate(data):
        reviews = doc.get("product_reviews", [])
        
        if reviews:
            try:
                # Calcul du nombre total de reviews
                total_reviews = len(reviews)
                
                # Calcul de la note moyenne
                average_rating = sum(review.get("rating", 0) for review in reviews) / total_reviews
                
                # Dernière note (note de la dernière review)
                last_rating = reviews[-1].get("rating") if reviews else None
                
                # Création de l'index des reviews
                reviews_index[doc_id] = {
                    "total_reviews": total_reviews,
                    "average_rating": average_rating,
                    "last_rating": last_rating
                }
            except Exception as e:
                print(f"Error processing reviews for product ID {doc_id}. Error: {e}")
        else:
            print(f"No reviews for product ID {doc_id}")
    
    return reviews_index

def save_reviews_index(reviews_index, filename="reviews_index.json"):
    """Sauvegarde l'index des reviews dans un fichier JSON."""
    try:
        with open(filename, "w", encoding="utf-8") as file:
            json.dump(reviews_index, file, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving reviews index to {filename}: {e}")

# Création de l'index des features
def build_features_index(data):
    """Builds an inverted index for product features such as brand, origin, etc."""
    features_index = defaultdict(set)

    for doc_id, doc in enumerate(data):
        features = doc.get("product_features", {})
        
        for feature_name, feature_value in features.items():
            if feature_value:
                # Tokenisation des valeurs de features
                tokens = tokenize(str(feature_value))
                for token in tokens:
                    features_index[token].add(doc_id)

    # Convertir les sets en listes pour un format compatible JSON
    return {token: list(doc_ids) for token, doc_ids in features_index.items()}

def save_features_index(features_index, filename="features_index.json"):
    """Sauvegarde l'index des features dans un fichier JSON."""
    try:
        with open(filename, "w", encoding="utf-8") as file:
            json.dump(features_index, file, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving features index to {filename}: {e}")

# Pipeline principale
def main():
    # Étape 1 : Extraction des informations des URLs
    data = load_and_process_data(INPUT_FILE)
    if not data:
        print("No data processed, exiting.")
        return
    
    save_processed_data(data)
    print("Processing completed! Data saved to processed_products.jsonl")

    # Étape 2 : Construction des index inversés pour title et description avec positions
    indexed_data = load_and_process_data(PROCESSED_FILE)
    title_index = build_inverted_index_with_positions("title", indexed_data)
    description_index = build_inverted_index_with_positions("description", indexed_data)

    save_index(title_index, "index_title_with_positions.json")
    save_index(description_index, "index_description_with_positions.json")

    # Étape 3 : Construction de l'index des reviews
    reviews_index = build_reviews_index(indexed_data)
    if not reviews_index:
        print("Reviews index is empty!")
    else:
        save_reviews_index(reviews_index, "reviews_index.json")
        print("Reviews index creation completed!")

    # Étape 4 : Construction de l'index des features
    features_index = build_features_index(indexed_data)
    save_features_index(features_index, "features_index.json")
    print("Features index creation completed!")

    print("All indexing completed!")

if __name__ == "__main__":
    main()
