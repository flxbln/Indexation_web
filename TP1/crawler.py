import json
import time
from utils import fetch_url, parse_html, init_robot_parser, can_parse_page, is_product_url


###Parcourt les pages du site en respectant les règles de politesse, extrait les informations utiles, 
### suit les liens internes et s’arrête après avoir visité un nombre maximal de pages.

START_URL = "https://web-scraping.dev/products"
MAX_PAGES = 10
DELAY = 1  # politesse : 1 seconde entre chaque requête


def crawl(start_url, max_pages=10, delay=1):
    """"
    Le crawler utilise une file d’attente d’URLs à visiter et applique une stratégie de priorité simple 
    permettant d’explorer en premier les pages produits, identifiées par la présence du token product dans l’URL, 
    tout en respectant une limite maximale de pages visitées.
    
    Paramètres
    ----------
    start_url : Conll
        url de départ
    max_page : int
        nombre 
    delay : float
        politesse : temps entre chaque requête

    
    Returns
    -------
    resultats : list[Tensor]
        List of target token embeddings (one per sentence).
    
    """

    #File d'attente
    visited = set() # URLs déjà visitées (str)
    to_visit = [START_URL]  # URLs à visiter (str)
    resultats = [] # Données extraites (dict complets)

    rp = init_robot_parser(START_URL)



    while to_visit and len(visited) < MAX_PAGES:
        url = to_visit.pop(0)

        if url in visited:
            continue

        if not can_parse_page(rp, url):
            print(f"Blocked by robots.txt: {url}")
            continue

        print(f"Crawling: {url}")
        html = fetch_url(url)

        if html is None:
            continue

        data = parse_html(html, START_URL)
        data["url"] = url

        resultats.append(data)
        visited.add(url)

        # --- Ajout des liens avec priorité ---
        for link_url in data["links"]:

            if link_url in visited or link_url in to_visit:
                continue

            if is_product_url(link_url):
                to_visit.insert(0, link_url)   # priorité haute
            else:
                to_visit.append(link_url)      # priorité normale


        time.sleep(DELAY)
    
    return resultats



##### Sauvegarde en JSON

if __name__ == "__main__":
    resultats = crawl(START_URL)
    
    with open("TP1/data/output.json", "w", encoding="utf-8") as f:
        json.dump(resultats, f, ensure_ascii=False, indent=2)

