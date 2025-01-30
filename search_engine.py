import json
from engine import process_query, load_json_file

# Load index data from JSON files
paths = {
    "brand": 'index_provided/brand_index.json',
    "description": 'index_provided/description_index.json',
    "domain": 'index_provided/domain_index.json',
    "origin": 'index_provided/origin_index.json',
    "synonyms": 'index_provided/origin_synonyms.json',
    "reviews": 'index_provided/reviews_index.json',
    "title": 'index_provided/title_index.json'
}

# Load the indexes
origin_index = load_json_file(paths["origin"])
origin_synonyms = load_json_file(paths["synonyms"])
title_index = load_json_file(paths["title"])
review_index = load_json_file(paths["reviews"])

# Request
test_query = "Dragon Energy Potion"

# Call the search function
ranked_results = process_query(
    test_query,
    origin_index,
    origin_synonyms,
    title_index,
    review_index,
    match_all=True
)

# Format the results for display or to save them in a file
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

# Save the results to a JSON file
with open('ranked_results.json', 'w') as outfile:
    json.dump(output, outfile, indent=2)

# Print a message to confirm that the results have been saved
print("The results have been saved to 'ranked_results.json'.")
