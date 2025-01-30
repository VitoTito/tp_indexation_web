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
    Vérifie si le site autorise le crawl en lisant le fichier robots.txt.

    Attributs
    ----------
    url : str
        URL de la page que l'on souhaite crawler.
    user_agent : str, optionnel
        User-Agent utilisé pour la requête HTTP. Par défaut, "CrawlerIndexationWeb/1.0".

    Returns
    --------
    bool
        Retourne True si le crawl est autorisé, sinon False.

    Détails de l'implémentation
    ----------------------------
    La fonction utilise la classe `RobotFileParser` pour lire le fichier `robots.txt`
    du site et vérifier si le crawl est autorisé pour l'URL spécifiée.
    """
    parsed_url = urlparse(url)
    robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"

    rp = RobotFileParser()
    try:
        rp.set_url(robots_url)
        rp.read()
        return rp.can_fetch(user_agent, url)
    except Exception as e:
        print(f"Impossible de lire robots.txt : {e}")
        return False


def fetch_url(url):
    """
    Effectue des requêtes HTTP et récupère le HTML d'une page.

    Attributs
    ----------
    url : str
        URL de la page à récupérer.

    Returns
    --------
    str | None
        Retourne le contenu HTML de la page sous forme de chaîne de caractères,
        ou None en cas d'échec de la requête.

    Détails de l'implémentation
    ----------------------------
    La fonction effectue une requête HTTP à l'URL spécifiée en utilisant la
    bibliothèque `urllib`. Elle gère les erreurs HTTP et de connexion et 
    retourne le contenu HTML de la page.
    """
    try:
        headers = {"User-Agent": "CrawlerIndexationWeb/1.0"}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
            return response.read().decode('utf-8')
    except HTTPError as e:
        print(f"Erreur HTTP {e.code} lors de la requête vers {url}")
    except URLError as e:
        print(f"Erreur de connexion : {e.reason} lors de la requête vers {url}")
    return None


def extract_data(html, base_url):
    """
    Extrait le titre, le premier paragraphe et les liens internes d'une page.

    Attributs
    ----------
    html : str
        Contenu HTML de la page à analyser.
    base_url : str
        URL de la page de base (utilisée pour résoudre les liens relatifs).

    Retourne
    --------
    dict
        Un dictionnaire contenant :
        - "title" : titre de la page (str),
        - "url" : URL de la page (str),
        - "first_paragraph" : premier paragraphe de la page (str),
        - "links" : liste des liens internes (list).

    Détails de l'implémentation
    ----------------------------
    La fonction utilise BeautifulSoup pour analyser le contenu HTML et en extraire
    les informations suivantes :
    - Le titre de la page : priorité donnée à la balise `<title>`, puis à la balise `<h1>`, 
      et enfin à un attribut `<meta name="og:title">`.
    - Le premier paragraphe de la page : extrait de la première balise `<p>`.
    - La liste des liens internes : tous les liens (`<a href="...">`) dont l'URL correspond au même domaine.
    """
    soup = BeautifulSoup(html, "html.parser")

    # On recherche le titre dans la balise <title> (par défaut)
    title = soup.title.string.strip() if soup.title else None

    # On recherche le titre dans une balise <h1> si <title> est vide ou invalide
    if not title:
        h1_tag = soup.find("h1")
        if h1_tag:
            title = h1_tag.get_text().strip()

    # Si le titre n'est toujours pas trouvé, on utilise une autre méthode comme <meta name="og:title">
    if not title:
        meta_title = soup.find("meta", attrs={"property": "og:title"})
        if meta_title and meta_title.get("content"):
            title = meta_title["content"].strip()

    # Si aucun titre valide n'est trouvé, on met un titre par défaut
    if not title:
        title = "Sans titre"

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
    Définit la priorité des URLs pour assurer un ordre cohérent.

    Attributs
    ----------
    url : str
        URL de la page à analyser.

    Retourne
    --------
    int
        Priorité sous forme de nombre entier (0, 1, 2, 3).

    Détails de l'implémentation
    ----------------------------
    La fonction attribue une priorité à chaque URL en fonction de son type :
    - Priorité 0 : Pages produits principales.
    - Priorité 1 : Pages catégories produits.
    - Priorité 2 : Pages variantes des produits.
    - Priorité 3 : Autres pages du site.
    """
    if "product/" in url:
        return 0  # Pages produits principales en priorité
    else:
        return 1  # Autres pages du site


def crawl(seed_url, max_pages=50):
    """
    Crawler qui explore les pages en priorisant les liens produits.

    Attributs
    ----------
    seed_url : str
        URL de départ à partir de laquelle commencer le crawl. 
    max_pages : int, optionnel
        Nombre maximal de pages à explorer. Par défaut, 50 pages.

    Retourne
    --------
    None
        Cette fonction ne retourne aucune valeur, mais elle génère un fichier `output.json`
        contenant les informations collectées.

    Détails de l'implémentation
    ----------------------------
    La fonction commence par la page de départ spécifiée, puis explore les pages liées
    en suivant une logique de priorité basée sur la nature des pages. Elle récupère
    le titre, le premier paragraphe et les liens internes de chaque page visitée, et
    enregistre ces informations dans un fichier JSON. Elle arrête le crawl après avoir
    visité un maximum de 50 pages ou lorsque toutes les pages pertinentes ont été explorées.
    """
    visited = set()
    to_visit = queue.PriorityQueue()
    to_visit.put((0, seed_url))  # On met la priorité haute pour la première page
    data_collected = []

    while not to_visit.empty() and len(visited) < max_pages:
        _, url = to_visit.get()
        if url in visited or not can_fetch(url):
            continue

        print(f"Crawling : {url}")
        html = fetch_url(url)
        if not html:
            continue

        extracted_data = extract_data(html, url)
        data_collected.append(extracted_data)
        visited.add(url)

        # On ajoute les nouveaux liens avec une priorité adaptée
        for link in extracted_data["links"]:
            if link not in visited:
                to_visit.put((get_priority(link), link))

        time.sleep(1)  # La politesse pour éviter d'être bloqué

    # On sauvegarde des résultats dans un fichier JSON
    with open("output.json", "w", encoding="utf-8") as f:
        json.dump(data_collected, f, indent=4, ensure_ascii=False)

    print(f"Crawl terminé. {len(visited)} pages explorées.")


# Tests sur quelques différentes pages de départ
crawl("https://web-scraping.dev/review-policy", max_pages=10)
crawl("https://web-scraping.dev/", max_pages=15)
crawl("https://web-scraping.dev/testimonials", max_pages=20)

# Les résultats montrent que l'on priorise bien les pages ayant 'product' dans l'URL.


# Lancement du crawler final
crawl("https://web-scraping.dev/products")