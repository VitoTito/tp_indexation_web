# Web Crawler Indexation 

This project is a crawler that explores a website to collect information about products, creates inverted indexes from the extracted data, and stores them in JSON files. The crawler uses the `BeautifulSoup` library to scrape product data, respects the `robots.txt` rules of the crawled websites, and generates several index files used for efficient searching within the data.

## Prerequisites

Before running the project, install the necessary dependencies with the following command in the terminal:

```bash
pip install -r requirements.txt
```


## Project Files

The project consists of several main files:
- `crawler.py`: This script is responsible for crawling and extracting product information from the website. It collects basic information such as product ID, variant (if present), title, description, reviews, and product features.
- `create_index.py`: This script takes the extracted data and indexes it by creating inverted indexes for titles, descriptions, reviews, and features of products. It also handles word positions in titles and descriptions, in addition to creating a review index (with total reviews, average rating, and last rating).
- `test.py`: This file is used to compare the crawled results with a reference file, focusing on comparing product titles and product data.
- `requirements.txt`: This file contains a list of Python dependencies required to run the project.
- `engine.py`: This script contains functions for processing search queries, tokenizing text, computing BM25 ranking scores, expanding queries with synonyms, and ranking documents based on various signals (such as title presence, review scores, and humoristic adjustments)
- `search_engine.py`: This script is responsible for loading pre-built indexes (such as title, description, reviews, etc.), processing a search query using the functions from engine.py, and saving the ranked search results to a JSON file.



## Index Structure

The create_index.py script generates several indexes as JSON files. These indexes are in the folder `index/` allow for efficient searching through the product data and are structured as follows:

- `index_title_with_positions.json`: An inverted index for product titles. This file contains tokens extracted from the title, along with their positions within each document.
- `index_description_with_positions.json`: An inverted index for product descriptions, similar to the title index but applied to the description.
- `reviews_index.json`: An index for product reviews. It contains the total number of reviews, average rating, and the last rating for each product. This index is not inverted and is used to retrieve products with the best ratings.
- `features_index.json`: An inverted index for product features (e.g., brand, origin, etc.). Each feature is treated as a text field, and tokens are extracted and indexed for each product.


## Implementation Details
### Title and Description Indexes
- The script tokenizes product titles and descriptions by removing punctuation and stopwords.
- It builds an inverted index that associates tokens with the documents they appear in, along with their positions in those documents.
- The resulting index allows for efficient querying of product titles and descriptions based on specific keywords.

### Review Index
- The reviews index is built using the total number of reviews, the average rating, and the last review's rating for each product.
- This index is not inverted and is designed to help rank products by their review data (e.g., highest-rated products).

### Feature Index
- The feature index is built by tokenizing product features (such as brand, origin, etc.).
- It creates an inverted index of these tokens, which allows for searching based on features like the product's brand or origin.


## Example of Usage

You can create the indexes using the following command:

```bash
python create_index.py
```

This will generate the following index files in the `index/` folder:
- `index_title_with_positions.json`
- `index_description_with_positions.json`
- `reviews_index.json`
- `features_index.json`

## engine.py


`engine.py` is responsible for the core functionality of processing search queries. It contains several helper functions to handle text tokenization, BM25 ranking, query expansion, and document filtering.
Key Functions:

- `load_json_file`: Loads a JSON file and returns its parsed data.

`tokenize_text`: Tokenizes the input text by removing punctuation and stopwords, and returns a list of processed tokens.

`expand_query_with_synonyms`: Expands the query by adding synonyms for each token in the query, allowing for broader search results.

- `filter_documents`: Filters documents based on the presence of tokens in the index data. The match_all parameter determines whether all tokens must be present in a document or just any one of them.

- `compute_bm25`: Computes BM25 ranking scores for documents based on the query tokens. BM25 is a ranking function used in information retrieval systems.

- `rank_documents`: Ranks documents based on BM25 scores, exact matches, title presence, review scores, and humoristic adjustments (related to USA and Greenland keywords). It also uses position-based scoring to give higher scores to earlier matching tokens.

- `ensure_unique_scores`: Ensures that all documents in the ranked results have unique scores. It adds small random adjustments to break ties in document scores.

- `process_query`: Processes a search query by tokenizing the query, expanding it with synonyms, filtering relevant documents, and ranking the results using the above functions.

### Humorous Adjustments:

- USA-related terms: Terms related to the USA (e.g., "america", "freedom", "rockets") boost document scores.
- Greenland-related terms: Terms related to Greenland (e.g., "ice", "snow") apply a penalty to document scores.

## search_engine.py

`search_engine.py` is the script that runs the actual search process using pre-built indexes. It loads the necessary indexes, processes a search query using the functions from engine.py, and saves the ranked results to a JSON file : 

- Loading Indexes: The script loads various pre-built indexes from JSON files, including the title index, description index, reviews index, and synonyms dictionary.
- Processing the Query: The search query is passed to the process_query() function in engine.py, where it is tokenized, expanded with synonyms, and ranked using BM25.
- Saving Results: The ranked results are saved to a JSON file (ranked_results.json), which contains the total number of documents, the number of filtered documents, and the sorted results with their corresponding scores.

To launch search_engine.py, just change line 21/22 : 

``` bash
# Request
test_query = "Dragon Energy Potion"
```