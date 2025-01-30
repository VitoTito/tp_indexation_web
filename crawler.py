import json
import re
import string
import os
from urllib.parse import urlparse, parse_qs
from collections import defaultdict

# Input and output files
INPUT_FILE = "products.jsonl"
PROCESSED_FILE = "processed_products.jsonl"
INDEX_FOLDER = "index"  # Directory for saving index files

# Common English stopwords
STOPWORDS = set(["the", "a", "an", "and", "or", "of", "to", "in", "on", "with", "for", "by", "at", "from", 
                 "is", "it", "this", "that", "as", "are", "was", "were", "be", "been", "has", "have", "had"])

def extract_product_info_from_url(url):
    """
    Extracts the product ID and variant (if any) from a given URL.

    Parameters
    ----------
    url : str
        The URL of the product page to parse.

    Returns
    -------
    dict
        A dictionary containing the 'product_id' and 'variant_id' (if available).
    """
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

def load_data_from_file(filename):
    """
    Loads product data from a JSONL file.

    Parameters
    ----------
    filename : str
        The path to the JSONL file containing the product data.

    Returns
    -------
    list
        A list of raw product data dictionaries from the file.
    """
    if not os.path.exists(filename):
        print(f"Error: The file {filename} does not exist.")
        return []
    
    product_data = []
    try:
        with open(filename, "r", encoding="utf-8") as file:
            for line in file:
                try:
                    doc = json.loads(line.strip())
                    product_data.append(doc)
                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON line: {line}. Error: {e}")
                    continue
    except Exception as e:
        print(f"Error reading file {filename}: {e}")
    
    return product_data

def process_data(data):
    """
    Processes raw product data by extracting product IDs and variants from URLs.

    Parameters
    ----------
    data : list
        A list of raw product data dictionaries.

    Returns
    -------
    list
        A list of processed product data, with added product_id and variant_id fields.
    """
    processed_data = []
    
    for doc in data:
        doc.update(extract_product_info_from_url(doc.get("url", "")))
        processed_data.append(doc)
    
    return processed_data

def save_data_to_file(data, output_file=PROCESSED_FILE):
    """
    Saves processed product data to a JSONL file.

    Parameters
    ----------
    data : list
        The list of processed product data to save.
    output_file : str, optional
        The path to the output JSONL file (default is 'processed_products.jsonl').
    """
    try:
        with open(output_file, "w", encoding="utf-8") as file:
            for doc in data:
                file.write(json.dumps(doc, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"Error saving processed data to {output_file}: {e}")

def tokenize_text(text):
    """
    Tokenizes a given text by removing punctuation and stopwords.

    Parameters
    ----------
    text : str
        The text to tokenize.

    Returns
    -------
    list
        A list of tokens (words) that are not stopwords.
    """
    if not text:
        return []
    
    text = text.lower()
    text = text.translate(str.maketrans('', '', string.punctuation))
    tokens = text.split()
    return [token for token in tokens if token not in STOPWORDS]

def build_inverted_index_with_positions(field, data):
    """
    Builds an inverted index from a given field, including positions of words in the documents.

    Parameters
    ----------
    field : str
        The field in the product data to index (e.g., 'title', 'description').
    data : list
        A list of dictionaries containing the product data to index.

    Returns
    -------
    dict
        An inverted index where each token maps to a dictionary of document IDs
        and the positions of the token within those documents.
    """
    inverted_index = defaultdict(lambda: defaultdict(list))  # Token -> document_id -> positions
    
    for doc_id, doc in enumerate(data):
        field_value = doc.get(field, "")
        tokens = tokenize_text(field_value)
        for position, token in enumerate(tokens):
            inverted_index[token][doc_id].append(position)
    
    return {token: {doc_id: positions for doc_id, positions in doc_ids.items()} for token, doc_ids in inverted_index.items()}

def save_index_to_file(index, filename):
    """
    Saves an inverted index to a JSON file.

    Parameters
    ----------
    index : dict
        The inverted index to save.
    filename : str
        The path to the output JSON file.
    """
    if not os.path.exists(INDEX_FOLDER):
        os.makedirs(INDEX_FOLDER)  # Ensure that the index folder exists

    try:
        with open(os.path.join(INDEX_FOLDER, filename), "w", encoding="utf-8") as file:
            json.dump(index, file, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving index to {filename}: {e}")

def build_reviews_index(data):
    """
    Builds an index for reviews with total count, average rating, and last rating.

    Parameters
    ----------
    data : list
        A list of product data dictionaries containing review information.

    Returns
    -------
    dict
        An index where each document ID maps to a dictionary containing the total number of reviews,
        the average rating, and the last rating for the product.
    """
    reviews_index = {}
    
    for doc_id, doc in enumerate(data):
        reviews = doc.get("product_reviews", [])
        
        if reviews:
            try:
                total_reviews = len(reviews)
                average_rating = sum(review.get("rating", 0) for review in reviews) / total_reviews
                last_rating = reviews[-1].get("rating") if reviews else None
                
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

def save_reviews_index_to_file(reviews_index, filename="reviews_index.json"):
    """
    Saves the reviews index to a JSON file.

    Parameters
    ----------
    reviews_index : dict
        The reviews index to save.
    filename : str, optional
        The path to the output JSON file (default is 'reviews_index.json').
    """
    try:
        with open(os.path.join(INDEX_FOLDER, filename), "w", encoding="utf-8") as file:
            json.dump(reviews_index, file, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving reviews index to {filename}: {e}")

def build_features_index(data):
    """
    Builds an inverted index for product features such as brand, origin, etc.

    Parameters
    ----------
    data : list
        A list of product data dictionaries containing feature information.

    Returns
    -------
    dict
        An inverted index where each token in the feature values maps to a set of document IDs.
    """
    features_index = defaultdict(set)

    for doc_id, doc in enumerate(data):
        features = doc.get("product_features", {})
        
        for feature_name, feature_value in features.items():
            if feature_value:
                tokens = tokenize_text(str(feature_value))
                for token in tokens:
                    features_index[token].add(doc_id)

    return {token: list(doc_ids) for token, doc_ids in features_index.items()}

def save_features_index_to_file(features_index, filename="features_index.json"):
    """
    Saves the features index to a JSON file.

    Parameters
    ----------
    features_index : dict
        The features index to save.
    filename : str, optional
        The path to the output JSON file (default is 'features_index.json').
    """
    try:
        with open(os.path.join(INDEX_FOLDER, filename), "w", encoding="utf-8") as file:
            json.dump(features_index, file, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving features index to {filename}: {e}")

def run_main_pipeline():
    """
    Main pipeline that processes product data, extracts product information, and builds inverted indices.
    
    This function loads product data from a JSONL file, extracts information like product IDs,
    variants, and reviews, and then builds inverted indices for product titles, descriptions, and features.
    Finally, it saves the processed data and indices to JSON files.
    """
    data = load_data_from_file(INPUT_FILE)
    if not data:
        print("No data processed, exiting.")
        return
    
    processed_data = process_data(data)
    save_data_to_file(processed_data)
    print("Processing completed! Data saved to processed_products.jsonl")

    indexed_data = load_data_from_file(PROCESSED_FILE)
    title_index = build_inverted_index_with_positions("title", indexed_data)
    description_index = build_inverted_index_with_positions("description", indexed_data)

    save_index_to_file(title_index, "index_title_with_positions.json")
    save_index_to_file(description_index, "index_description_with_positions.json")

    reviews_index = build_reviews_index(indexed_data)
    if reviews_index:
        save_reviews_index_to_file(reviews_index)
        print("Reviews index creation completed!")

    features_index = build_features_index(indexed_data)
    save_features_index_to_file(features_index)
    print("Features index creation completed!")

    print("All indexing completed!")

if __name__ == "__main__":
    run_main_pipeline()
