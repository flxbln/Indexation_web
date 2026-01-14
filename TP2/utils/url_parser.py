import json
from urllib.parse import urlparse, parse_qs

#Parser un fichier JSONL
def read_jsonl(filepath):
    documents = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            documents.append(json.loads(line))
    return documents


#Fonction de parsing d’URL 
def parse_product_url(url):
    parsed = urlparse(url)

    # ID produit
    product_id = None
    path_parts = parsed.path.strip("/").split("/")
    if len(path_parts) >= 2 and path_parts[-2] == "product":
        product_id = path_parts[-1]

    # Variante
    query_params = parse_qs(parsed.query)
    variant = query_params.get("variant", [None])[0]

    return product_id, variant

#AJouter product_id et variant au document
def enrich_documents(documents):
    enriched = []

    for doc in documents:
        product_id, variant = parse_product_url(doc["url"])

        doc["product_id"] = product_id
        doc["variant"] = variant

        enriched.append(doc)

    return enriched


#Tests rapides
assert parse_product_url("https://web-scraping.dev/product/12")[0] == "12"
assert parse_product_url("https://web-scraping.dev/product/12?variant=blue")[1] == "blue"

