import json
import string
import math
import nltk
import random
from collections import defaultdict
from nltk.corpus import stopwords

nltk.download("stopwords")
STOPWORDS = stopwords.words("english")


def load_json_file(file_path):
    """
    Loads a JSON file from the specified path.

    Parameters
    ----------
    file_path : str
        The path to the JSON file to load.

    Returns
    -------
    dict
        The parsed data from the JSON file.
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)


def tokenize_text(text):
    """
    Tokenizes text by removing punctuation and stopwords.

    Parameters
    ----------
    text : str
        The text to tokenize.

    Returns
    -------
    list
        A list of tokens after processing the text.
    """
    if not text:
        return []
    
    text = text.lower()
    text = text.translate(str.maketrans('', '', string.punctuation))
    tokens = text.split()
    return [token for token in tokens if token not in STOPWORDS]


def expand_query_with_synonyms(query_tokens, synonyms_dict):
    """
    Expands the query by adding synonyms for each token in the query.

    Parameters
    ----------
    query_tokens : list
        A list of tokens representing the query.
    synonyms_dict : dict
        A dictionary containing tokens and their corresponding synonyms.

    Returns
    -------
    list
        A list of expanded tokens that includes synonyms for the query tokens.
    """
    expanded_query = []
    for token in query_tokens:
        expanded_query.append(token)
        expanded_query.extend(synonyms_dict.get(token, []))
    return expanded_query


def filter_documents(tokens, index_data, match_all=True):
    """
    Filters documents based on the presence of tokens in the index data.

    Parameters
    ----------
    tokens : list
        A list of query tokens to match against the documents.
    index_data : dict
        A dictionary where the keys are tokens and the values are lists of document URLs that contain those tokens.
    match_all : bool, optional
        If True, all tokens must be present in the document. If False, at least one token must be present (default is True).

    Returns
    -------
    list
        A list of document URLs that match the tokens based on the match_all criteria.
    """
    matched_urls = []
    for key, docs in index_data.items():
        key_lower = key.lower()
        if match_all:
            if all(token in key_lower for token in tokens):
                matched_urls.extend(docs)
        else:
            if any(token in key_lower for token in tokens):
                matched_urls.extend(docs)
    return matched_urls


def compute_bm25(query_tokens, index_data, k1=1.5, b=0.75):
    """
    Computes BM25 ranking for documents based on the query tokens.

    Parameters
    ----------
    query_tokens : list
        A list of tokens representing the search query.
    index_data : dict
        A dictionary where the keys are tokens and the values are lists of documents containing those tokens.
    k1 : float, optional
        The BM25 parameter for term frequency scaling (default is 1.5).
    b : float, optional
        The BM25 parameter for document length normalization (default is 0.75).

    Returns
    -------
    dict
        A dictionary where the keys are document URLs and the values are their BM25 scores.
    """
    N = len(index_data)  # Total number of documents
    avgdl = sum(len(docs) for docs in index_data.values()) / N  # Average document length
    scores = defaultdict(float)

    for token in query_tokens:
        if token in index_data:
            df = len(index_data[token])  # Document frequency
            idf = math.log((N - df + 0.5) / (df + 0.5) + 1)

            for doc, doc_data in index_data[token].items():
                tf = doc_data.get(token, 0)  # How many times the token appears in the document
                doc_len = len(doc_data)  # Document length (total number of terms in the document)
                
                score = idf * ((tf * (k1 + 1)) / (tf + k1 * (1 - b + b * (doc_len / avgdl))))
                scores[doc] += score

    return scores


def rank_documents(query_tokens, index_data, title_index, review_index):
    """
    Ranks documents based on BM25 scores, exact match, title presence, review scores, and other relevant signals.
    Includes humorous adjustments based on a 'discussion' between Elon Musk and Donald Trump.
    USA-related terms are boosted, Greenland-related terms are penalized.
    This choice is purely humoristic

    Parameters
    ----------
    query_tokens : list
        A list of tokens representing the search query.
    index_data : dict
        A dictionary where the keys are tokens and the values are lists of documents containing those tokens.
    title_index : dict
        A dictionary where the keys are tokens found in document titles and the values are lists of document URLs.
    review_index : dict
        A dictionary where the keys are document URLs and the values are review data for each document.

    Returns
    -------
    list
        A sorted list of tuples, where each tuple contains a document URL and its corresponding score.
    """
    bm25_scores = compute_bm25(query_tokens, index_data)

    # Add score for presence in title
    for token in query_tokens:
        if token in title_index:
            for doc in title_index[token]:
                bm25_scores[doc] += 2  # Strong weight for titles

    # Add score for customer reviews
    for doc, reviews in review_index.items():
        if "mean_mark" in reviews:
            # Normalize to a 5-star rating
            bm25_scores[doc] += reviews["mean_mark"] / 5  
            
            # Add additional bonuses based on the review score
            if reviews["mean_mark"] == 5:
                bm25_scores[doc] += 5  # Bonus for perfect scores
            elif reviews["mean_mark"] > 4.5:
                bm25_scores[doc] += 3  # Bonus for scores greater than 4.5
            elif reviews["mean_mark"] > 4:
                bm25_scores[doc] += 2  # Bonus for scores greater than 4
            elif reviews["mean_mark"] > 3:
                bm25_scores[doc] += 1  # Bonus for scores greater than 3

    # Humor: Boost score for USA-related terms 
    usa_keywords = ['usa', 'hamburgers', 'pizzas', 'new-york', 'america', 'freedom', 'bacon', 'rockets', 'tesla', 'trump']
    for doc in bm25_scores:
        for token in usa_keywords:
            if token in index_data and doc in index_data[token]:
                bm25_scores[doc] += bm25_scores[doc]*1.47 + 0.08  # Boost for America-related terms

    # Humor: Bad score for Greenland-related terms 
    greenland_keywords = ['greenland', 'ice', 'cold', 'arctic', 'glaciers', 'snow', 'frozen', 'polar']
    for doc in bm25_scores:
        for token in greenland_keywords:
            # If the document contains a Greenland-related keyword, apply a penalty
            if token in index_data and doc in index_data[token]:
                bm25_scores[doc] = max(0, bm25_scores[doc]*0.96 - 0.08) 

    # Use position information to improve ranking
    for doc in bm25_scores:
        doc_tokens = index_data.get(doc, [])
        for i, token in enumerate(doc_tokens):
            if token in query_tokens:
                # The earlier the word, the more points it gives
                position_score = 1 / (i + 1)  # Earlier tokens get more weight
                bm25_scores[doc] += position_score  # Add this score to the overall document score
                print(f"Position-based boost for {doc}: +{position_score:.2f} (Token '{token}' is at position {i+1})")  # Position-based boost

    # Sort results by score
    return sorted(bm25_scores.items(), key=lambda x: x[1], reverse=True)


def ensure_unique_scores(ranked_results):
    """
    Ensures that all documents in the ranked results have unique scores.

    Parameters
    ----------
    ranked_results : list
        A list of tuples, each containing a document URL and its score.

    Returns
    -------
    list
        A sorted list of tuples with unique scores, where ties are broken with small random adjustments.
    """
    scores = defaultdict(list)
    
    # Group documents by their scores
    for doc, score in ranked_results:
        scores[score].append(doc)
    
    # For scores with more than one document, add a small random adjustment to break the tie
    adjusted_results = []
    for score, docs in scores.items():
        if len(docs) > 1:
            while len(docs) > 1:
                doc = random.choice(docs)
                adjusted_results.append((doc, score + random.uniform(0.01, 0.1)))  # Add small random increment
                docs.remove(doc)
        if docs:
            adjusted_results.append((docs[0], score))  # Add remaining document with the same score

    # Sort the adjusted results by score
    adjusted_results.sort(key=lambda x: x[1], reverse=True)
    return adjusted_results


def process_query(query, index_data, synonyms_dict, title_index, review_index, match_all=True):
    """
    Processes a search query, expands it with synonyms, filters relevant documents, and ranks the results.

    Parameters
    ----------
    query : str
        The search query to process.
    index_data : dict
        A dictionary where the keys are tokens and the values are lists of documents containing those tokens.
    synonyms_dict : dict
        A dictionary containing tokens and their corresponding synonyms.
    title_index : dict
        A dictionary where the keys are tokens found in document titles and the values are lists of document URLs.
    review_index : dict
        A dictionary where the keys are document URLs and the values are review data for each document.
    match_all : bool, optional
        If True, all query tokens must be present in the documents. If False, at least one token must be present (default is True).

    Returns
    -------
    list
        A sorted list of tuples, where each tuple contains a document URL and its corresponding score.
    """
    tokens = tokenize_text(query)
    expanded_tokens = expand_query_with_synonyms(tokens, synonyms_dict)
    matched_docs = filter_documents(expanded_tokens, index_data, match_all)
    
    ranked_results = rank_documents(expanded_tokens, index_data, title_index, review_index)
    
    # Ensure unique scores
    ranked_results = ensure_unique_scores(ranked_results)

    return ranked_results


def main():
    # Paths to the JSON files
    paths = {
        "brand": 'index_provided/brand_index.json',
        "description": 'index_provided/description_index.json',
        "domain": 'index_provided/domain_index.json',
        "origin": 'index_provided/origin_index.json',
        "synonyms": 'index_provided/origin_synonyms.json',
        "reviews": 'index_provided/reviews_index.json',
        "title": 'index_provided/title_index.json'
    }

    # Load the index data
    origin_index = load_json_file(paths["origin"])
    origin_synonyms = load_json_file(paths["synonyms"])
    review_index = load_json_file(paths["reviews"])
    title_index = load_json_file(paths["title"])

    # Test with three queries
    test_query = "Unleash the power within with our 'Dark Red Potion', an energy drink."
    ranked_results = process_query(
        test_query,
        origin_index,
        origin_synonyms,
        title_index,
        review_index,
        match_all=True
    )

    # Format output as JSON
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

    # Save the output to a JSON file
    with open('ranked_tests.json', 'w') as outfile:
        json.dump(output, outfile, indent=2)



    test_query = "Step out in style with our Women's High Heel Sandals. These sandals feature a strappy design that adds"
    ranked_results = process_query(
        test_query,
        origin_index,
        origin_synonyms,
        title_index,
        review_index,
        match_all=True
    )

    # Format output as JSON
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

    # Save the output to a JSON file
    with open('ranked_tests_2.json', 'w') as outfile:
        json.dump(output, outfile, indent=2)



    test_query = "Blue"
    ranked_results = process_query(
        test_query,
        origin_index,
        origin_synonyms,
        title_index,
        review_index,
        match_all=True
    )

    # Format output as JSON
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

    # Save the output to a JSON file
    with open('ranked_tests_3.json', 'w') as outfile:
        json.dump(output, outfile, indent=2)

if __name__ == '__main__':
    main()