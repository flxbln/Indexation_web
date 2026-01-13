#===============Fonctions de base pour les requêtes HTTP=====================================

import urllib.request
import urllib.error
from urllib.parse import urlparse
import time
from bs4 import BeautifulSoup
import urllib.robotparser as robotparser


#==========================================================================================
##### Fonction de requête HTTP

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

### Initialisation du parser robots
def init_robot_parser(base_url, user_agent="MyCrawler/1.0"):
    parsed_url = urlparse(base_url)
    robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"

    rp = robotparser.RobotFileParser()
    rp.set_url(robots_url)
    rp.read()

    return rp


###Vérifier si une URL est autorisée
def can_fetch(rp, url, user_agent="MyCrawler/1.0"):
    return rp.can_fetch(user_agent, url)




#=================Parsing HTML (titre, premier paragraphe, liens)=================================

def parse_html(html_content, base_url):
    soup = BeautifulSoup(html_content, "html.parser")

    # Titre
    title = soup.title.string.strip() if soup.title else ""

    # Premier paragraphe
    first_p = ""
    p_tag = soup.find("p")
    if p_tag:
        first_p = p_tag.get_text(strip=True)

    # Liens internes
    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.startswith("/"):
            links.append(base_url + href)

    return {
        "title": title,
        "first_paragraph": first_p,
        "links": links
    }
