import urllib.request
import urllib.error
import urllib.robotparser as robotparser
from urllib.parse import urlparse, urljoin
import json
import time
from bs4 import BeautifulSoup


# ==================== HTTP REQUEST FUNCTIONS ====================

def fetch_url(url, user_agent="WebCrawler/1.0", timeout=10):
    """
    Fetches HTML content from a URL with a custom User-Agent header.
    
    Args:
        url (str): The URL to fetch
        user_agent (str): Custom User-Agent identifier
        timeout (int): Request timeout in seconds
        
    Returns:
        bytes: HTML content if successful, None otherwise
    """
    headers = {"User-Agent": user_agent}
    request = urllib.request.Request(url, headers=headers)
    
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            content_type = response.headers.get("Content-Type", "")
            if "text/html" not in content_type:
                return None
            return response.read()
    except urllib.error.HTTPError as e:
        print(f"HTTP error {e.code} for {url}")
        return None
    except urllib.error.URLError as e:
        print(f"URL error for {url}: {e.reason}")
        return None


# ==================== ROBOTS.TXT HANDLING ====================

def initialize_robot_parser(base_url, user_agent="WebCrawler/1.0"):
    """
    Initializes a robot parser to read and respect robots.txt rules.
    
    Args:
        base_url (str): The base URL of the website
        user_agent (str): Custom User-Agent identifier
        
    Returns:
        RobotFileParser: Parser object for robots.txt rules
    """
    parsed_url = urlparse(base_url)
    robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
    
    robot_parser = robotparser.RobotFileParser()
    robot_parser.set_url(robots_url)
    robot_parser.read()
    
    return robot_parser


def is_crawlable(robot_parser, url, user_agent="WebCrawler/1.0"):
    """
    Checks if the URL can be crawled according to robots.txt rules.
    
    Args:
        robot_parser (RobotFileParser): Robot parser object
        url (str): URL to check
        user_agent (str): Custom User-Agent identifier
        
    Returns:
        bool: True if crawlable, False otherwise
    """
    return robot_parser.can_fetch(user_agent, url)


# ==================== HTML PARSING ====================

def extract_title(soup):
    """
    Extracts the page title from HTML.
    
    Args:
        soup (BeautifulSoup): Parsed HTML object
        
    Returns:
        str: Page title
    """
    if soup.title and soup.title.string:
        return soup.title.string.strip()
    return ""


def extract_description(soup):
    """
    Extracts the product description from HTML.
    
    Args:
        soup (BeautifulSoup): Parsed HTML object
        
    Returns:
        str: Product description text
    """
    p_tag = soup.find("p")
    if p_tag:
        return p_tag.get_text(strip=True)
    return ""


def extract_product_features(soup):
    """
    Extracts product features from the features list in HTML.
    
    Args:
        soup (BeautifulSoup): Parsed HTML object
        
    Returns:
        dict: Dictionary with feature names as keys and values as values
    """
    features = {}
    features_ul = soup.find("ul", class_="product-features")
    
    if features_ul:
        for list_item in features_ul.find_all("li"):
            strong_tag = list_item.find("strong")
            if strong_tag:
                feature_name = strong_tag.get_text(strip=True).replace(":", "").lower()
                feature_value = list_item.get_text(strip=True).replace(strong_tag.get_text(), "").strip()
                features[feature_name] = feature_value
    
    return features


def extract_product_reviews(soup, page_url):
    """
    Extracts product reviews from the reviews section in HTML.
    
    Args:
        soup (BeautifulSoup): Parsed HTML object
        page_url (str): The URL of the product page
        
    Returns:
        list: List of review dictionaries with id, rating, text, and date
    """
    reviews = []
    reviews_div = soup.find("div", class_="reviews")
    
    if reviews_div:
        for review_count, review in enumerate(reviews_div.find_all("div", class_="review"), 1):
            rating_tag = review.find("span", class_="rating")
            text_tag = review.find("p")
            date_tag = review.find("span", class_="date")
            
            review_data = {
                "id": f"{page_url.split('/')[-1]}-{review_count}",
                "rating": int(rating_tag.get_text()) if rating_tag else None,
                "text": text_tag.get_text(strip=True) if text_tag else "",
                "date": date_tag.get_text(strip=True) if date_tag else ""
            }
            reviews.append(review_data)
    
    return reviews


def extract_internal_links(soup, page_url):
    """
    Extracts all internal links from the HTML body.
    
    Args:
        soup (BeautifulSoup): Parsed HTML object
        page_url (str): The URL of the current page
        
    Returns:
        list: List of resolved URLs
    """
    links = []
    for anchor in soup.find_all("a", href=True):
        resolved_url = urljoin(page_url, anchor["href"])
        links.append(resolved_url)
    return links


def parse_html(html_content, page_url):
    """
    Parses HTML content and extracts relevant information including
    product details if the page is a product page.
    
    Args:
        html_content (bytes): Raw HTML content
        page_url (str): The URL of the page
        
    Returns:
        dict: Dictionary containing title, description, product features,
              product reviews, links, and URL
    """
    soup = BeautifulSoup(html_content, "html.parser")
    
    page_data = {
        "url": page_url,
        "title": extract_title(soup),
        "links": extract_internal_links(soup, page_url)
    }
    
    # Extract product-specific information if this is a product page
    if is_product_url(page_url):
        page_data["description"] = extract_description(soup)
        page_data["product_features"] = extract_product_features(soup)
        page_data["product_reviews"] = extract_product_reviews(soup, page_url)
    
    return page_data


# ==================== URL PRIORITIZATION ====================

def is_product_url(url):
    """
    Checks if a URL is a product page.
    
    Args:
        url (str): URL to check
        
    Returns:
        bool: True if URL contains 'product', False otherwise
    """
    return "product" in url.lower()


# ==================== WEB CRAWLER ====================

def crawl(start_url, max_pages=50, request_delay=1, user_agent="WebCrawler/1.0"):
    """
    Crawls a website starting from a given URL, prioritizing product pages.
    
    The crawler:
    - Respects robots.txt rules
    - Prioritizes URLs containing 'product'
    - Stops after visiting max_pages
    - Maintains a delay between requests for politeness
    
    Args:
        start_url (str): Starting URL for the crawler
        max_pages (int): Maximum number of pages to visit
        request_delay (float): Delay between requests in seconds
        user_agent (str): Custom User-Agent identifier
        
    Returns:
        list: List of dictionaries containing extracted page data
    """
    visited_urls = set()
    urls_to_visit = [start_url]
    crawled_data = []
    
    robot_parser = initialize_robot_parser(start_url, user_agent)
    
    while urls_to_visit and len(visited_urls) < max_pages:
        current_url = urls_to_visit.pop(0)
        
        # Skip if already visited
        if current_url in visited_urls:
            continue
        
        # Check robots.txt permission
        if not is_crawlable(robot_parser, current_url, user_agent):
            print(f"Blocked by robots.txt: {current_url}")
            continue
        
        # Fetch page
        print(f"Crawling: {current_url}")
        html_content = fetch_url(current_url, user_agent)
        
        if html_content is None:
            continue
        
        # Extract data
        page_data = parse_html(html_content, current_url)
        crawled_data.append(page_data)
        visited_urls.add(current_url)
        
        # Add new links with priority system
        for link_url in page_data["links"]:
            # Skip if already visited or queued
            if link_url in visited_urls or link_url in urls_to_visit:
                continue
            
            # Add product URLs with high priority (at the beginning)
            if is_product_url(link_url):
                urls_to_visit.insert(0, link_url)
            else:
                urls_to_visit.append(link_url)
        
        # Respect politeness delay
        time.sleep(request_delay)
    
    return crawled_data


# ==================== SAVE RESULTS ====================

def save_to_json(data, output_path):
    """
    Saves crawled data to a JSON file.
    
    Args:
        data (list): List of crawled page data
        output_path (str): Path to the output JSON file
    """
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Results saved to {output_path}")


# ==================== MAIN EXECUTION ====================

if __name__ == "__main__":
    START_URL = "https://web-scraping.dev/products"
    MAX_PAGES = 50
    OUTPUT_FILE = "TP1/results_crawler.json"
    
    # Run crawler
    results = crawl(START_URL, max_pages=MAX_PAGES)
    
    # Save results
    save_to_json(results, OUTPUT_FILE)
    
    print(f"Crawling complete. Total pages visited: {len(results)}")