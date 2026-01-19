
import json

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


title_index = load_json("TP3/data/indexes/title_index.json")
description_index = load_json("TP3/data/indexes/description_index.json")
brand_index = load_json("TP3/data/indexes/brand_index.json")
reviews_index = load_json("TP3/data/indexes/reviews_index.json")
origin_index = load_json("TP3/data/indexes/origin_index.json")

def load_synonyms(path):
    return load_json(path)


from .preprocessing import filter_documents_all_tokens, filter_documents_any_token, process_query

synonyms = load_synonyms("TP3/data/synonyms.json")

query = "smartphone origine france"

tokens = process_query(query, synonyms)

docs_or = filter_documents_any_token(tokens, description_index)
docs_and = filter_documents_all_tokens(tokens, description_index)

print("OR:", docs_or)
print("AND:", docs_and)

