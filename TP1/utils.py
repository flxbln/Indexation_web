#===============Fonctions de base pour les requêtes HTTP=====================================

import urllib.request
import urllib.error
from urllib.parse import urlparse, urljoin
import time
from bs4 import BeautifulSoup
import urllib.robotparser as robotparser


#==========================================================================================
##### Fonction de requête HTTP

#Récupère le contenu HTML d’une page web à partir de son URL en respectant un User-Agent et en gérant les erreurs HTTP et réseau.

def fetch_url(url, user_agent="MyCrawler/1.0"):
    """
    Récupère le contenu HTML d'une page.
    """
    headers = {
        "User-Agent": user_agent
    }

    request = urllib.request.Request(url, headers=headers)

    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            content_type = response.headers.get("Content-Type", "")
            if "text/html" not in content_type:
                return None
            return response.read()
    except urllib.error.HTTPError as e:
        print(f"HTTP error {e.code} for {url}")
    except urllib.error.URLError as e:
        print(f"URL error for {url}: {e.reason}")
    return None




#================Lecture et respect du robots.txt (politesse)============================================
"""
Les propriétaires de sites Web utilisent le chier /robots.txt pour donner des
instructions sur leur site aux crawlers 
ex: ce qui est accessible ou non sur la page
"""


#Initialise et charge le fichier robots.txt du site afin de connaître les règles d’exploration autorisées pour le crawler.

### Initialisation du parser robots
def init_robot_parser(base_url, user_agent="MyCrawler/1.0"):
    parsed_url = urlparse(base_url)
    robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"

    rp = robotparser.RobotFileParser()
    rp.set_url(robots_url)
    rp.read()

    return rp




#=================Parsing HTML (titre, premier paragraphe, liens)=================================

#Vérifie si une URL donnée peut être explorée par le crawler selon les règles définies dans le fichier robots.txt.
def can_parse_page(rp, url, user_agent="MyCrawler/1.0"):
    """
    Vérifie si le crawler a le droit de récupérer et parser une page donnée.
    """
    if not rp.can_fetch(user_agent, url):
        return False
    return True


#Analyse le contenu HTML d’une page pour en extraire le titre, le premier paragraphe de texte et la liste des liens internes présents dans le corps de la page.

def parse_html(html_content, page_url):
    """
    Parse le HTML d'une page pour extraire le titre, le premier paragraphe
    et les liens internes, en conservant la page source des liens.
    """
    
    soup = BeautifulSoup(html_content, "html.parser")

    # --- Title ---
    title = soup.title.string.strip() if soup.title and soup.title.string else ""

    # --- Description ---
    description = ""
    if "/product/" in page_url:
        p = soup.find("p")
        if p:
            description = p.get_text(strip=True)


    # --- Liens internes + provenance ---
    links = []
    base_domain = urlparse(page_url).netloc

    for a in soup.find_all("a", href=True):
        href = a["href"]
        absolute_url = urljoin(page_url, href) # combine une base URL
        parsed_href = urlparse(absolute_url)

        # On ne garde que les liens internes
        if parsed_href.netloc == base_domain:
            links.append({
                "url": absolute_url,
                "from_page": page_url
            })

    return {
        "url": page_url,
        "title": title,
        "description": description,
        "product_features": {},
        "links": links,
        "product_reviews": []
    }

#===============Système de priorité=========================

def is_product_url(url):
    return "product" in url.lower()
