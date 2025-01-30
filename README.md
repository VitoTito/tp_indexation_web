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




## Index Structure

The create_index.py script generates several indexes as JSON files. These indexes allow for efficient searching through the product data and are structured as follows:

- `index_title_with_positions.json`: An inverted index for product titles. This file contains tokens extracted from the title, along with their positions within each document.
- `index_description_with_positions.json`: An inverted index for product descriptions, similar to the title index but applied to the description.
- `reviews_index.json`: An index for product reviews. It contains the total number of reviews, average rating, and the last rating for each product. This index is not inverted and is used to retrieve products with the best ratings.
- `features_index.json`: An inverted index for product features (e.g., brand, origin, etc.). Each feature is treated as a text field, and tokens are extracted and indexed for each product.