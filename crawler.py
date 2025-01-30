import time
import json
import queue
import urllib
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
from urllib.error import URLError, HTTPError


def can_fetch(url, user_agent="CrawlerIndexationWeb/1.0"):
    """
    Checks if the site allows crawling by reading the robots.txt file.

    Attributes
    ----------
    url : str
        URL of the page to be crawled.
    user_agent : str, optional
        User-Agent used for the HTTP request. Default is "CrawlerIndexationWeb/1.0".

    Returns
    --------
    bool
        Returns True if crawling is allowed, otherwise False.

    Implementation Details
    ----------------------------
    The function uses the `RobotFileParser` class to read the site's `robots.txt`
    file and check if crawling is allowed for the specified URL.
    """
    parsed_url = urlparse(url)
    robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"

    rp = RobotFileParser()
    try:
        rp.set_url(robots_url)
        rp.read()
        return rp.can_fetch(user_agent, url)
    except Exception as e:
        print(f"Unable to read robots.txt: {e}")
        return False


def fetch_url(url):
    """
    Makes HTTP requests and retrieves the HTML of a page.

    Attributes
    ----------
    url : str
        URL of the page to retrieve.

    Returns
    --------
    str | None
        Returns the HTML content of the page as a string,
        or None if the request fails.

    Implementation Details
    ----------------------------
    The function makes an HTTP request to the specified URL using the
    `urllib` library. It handles HTTP and connection errors and
    returns the HTML content of the page.
    """
    try:
        headers = {"User-Agent": "CrawlerIndexationWeb/1.0"}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
            return response.read().decode('utf-8')
    except HTTPError as e:
        print(f"HTTP Error {e.code} while requesting {url}")
    except URLError as e:
        print(f"Connection error: {e.reason} while requesting {url}")
    return None


def extract_data(html, base_url):
    """
    Extracts the title, first paragraph, and internal links from a page.

    Attributes
    ----------
    html : str
        HTML content of the page to analyze.
    base_url : str
        Base URL of the page (used to resolve relative links).

    Returns
    --------
    dict
        A dictionary containing:
        - "title": title of the page (str),
        - "url": URL of the page (str),
        - "first_paragraph": first paragraph of the page (str),
        - "links": list of internal links (list).

    Implementation Details
    ----------------------------
    The function uses BeautifulSoup to parse the HTML content and extract
    the following information:
    - The title of the page: priority given to the `<title>` tag, then to the `<h1>` tag,
      and finally to a `<meta name="og:title">` attribute.
    - The first paragraph of the page: extracted from the first `<p>` tag.
    - The list of internal links: all links (`<a href="...">`) whose URL matches the same domain.
    """
    soup = BeautifulSoup(html, "html.parser")

    # Search for the title in the <title> tag (default)
    title = soup.title.string.strip() if soup.title else None

    # Search for the title in an <h1> tag if <title> is empty or invalid
    if not title:
        h1_tag = soup.find("h1")
        if h1_tag:
            title = h1_tag.get_text().strip()

    # If the title is still not found, use another method like <meta name="og:title">
    if not title:
        meta_title = soup.find("meta", attrs={"property": "og:title"})
        if meta_title and meta_title.get("content"):
            title = meta_title["content"].strip()

    # If no valid title is found, set a default title
    if not title:
        title = "No title"

    first_paragraph = ""
    p_tag = soup.find("p")
    if p_tag:
        first_paragraph = p_tag.get_text().strip()

    links = []
    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]
        full_url = urljoin(base_url, href)

        if urlparse(full_url).netloc == urlparse(base_url).netloc:
            links.append(full_url)

    return {
        "title": title,
        "url": base_url,
        "first_paragraph": first_paragraph,
        "links": links
    }


def get_priority(url):
    """
    Defines the priority of URLs to ensure a coherent order.

    Attributes
    ----------
    url : str
        URL of the page to analyze.

    Returns
    --------
    int
        Priority as an integer (0, 1, 2, 3).

    Implementation Details
    ----------------------------
    The function assigns a priority to each URL based on its type:
    - Priority 0: Main product pages.
    - Priority 1: Product category pages.
    - Priority 2: Product variant pages.
    - Priority 3: Other site pages.
    """
    if "product/" in url:
        return 0  # Main product pages have the highest priority
    else:
        return 1  # Other site pages


def crawl(seed_url, max_pages=50):
    """
    Crawler that explores pages by prioritizing product links.

    Attributes
    ----------
    seed_url : str
        Starting URL from which to begin the crawl.
    max_pages : int, optional
        Maximum number of pages to explore. Default is 50 pages.

    Returns
    --------
    None
        This function does not return any value, but it generates a `output.json`
        file containing the collected information.

    Implementation Details
    ----------------------------
    The function starts with the specified seed URL, then explores linked pages
    following a priority logic based on the nature of the pages. It retrieves
    the title, first paragraph, and internal links of each visited page, and
    saves this information in a JSON file. It stops the crawl after visiting a maximum of 50 pages
    or when all relevant pages have been explored.
    """
    visited = set()
    to_visit = queue.PriorityQueue()
    to_visit.put((0, seed_url))  # High priority for the first page
    data_collected = []

    while not to_visit.empty() and len(visited) < max_pages:
        _, url = to_visit.get()
        if url in visited or not can_fetch(url):
            continue

        print(f"Crawling: {url}")
        html = fetch_url(url)
        if not html:
            continue

        extracted_data = extract_data(html, url)
        data_collected.append(extracted_data)
        visited.add(url)

        # Add new links with appropriate priority
        for link in extracted_data["links"]:
            if link not in visited:
                to_visit.put((get_priority(link), link))

        time.sleep(1)  # Politeness to avoid being blocked

    # Save results to a JSON file
    with open("output.json", "w", encoding="utf-8") as f:
        json.dump(data_collected, f, indent=4, ensure_ascii=False)

    print(f"Crawl completed. {len(visited)} pages explored.")


# Tests on a few different starting pages
crawl("https://web-scraping.dev/review-policy", max_pages=10)
crawl("https://web-scraping.dev/", max_pages=15)
crawl("https://web-scraping.dev/testimonials", max_pages=20)

# The results show that pages with 'product' in the URL are prioritized.


# Final crawler launch
crawl("https://web-scraping.dev/products")
