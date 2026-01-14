from utils.url_parser import read_jsonl, enrich_documents
from index.inverted_index import build_description_index, build_title_index, tokenize

docs = read_jsonl("TP2/Input/products.jsonl")
results = enrich_documents(docs)

print(results[1])

title_index = build_title_index(results)

assert isinstance(title_index["chocolate"], list)
assert all(url.startswith("https://") for url in title_index["chocolate"])
