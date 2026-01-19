
import json

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)



def load_synonyms(path):
    return load_json(path)


import json
from preprocessing import tokenize_query, expand_query_with_synonyms, filter_documents_any
from filtering import filter_documents_any
from ranking import rank_documents
from nltk.corpus import stopwords


def main():
    STOPWORDS = set(stopwords.words("french"))

    # ---- Load indexes ----
    title_index = load_json("TP3/data/indexes/title_index.json")
    description_index = load_json("TP3/data/indexes/description_index.json")
    brand_index = load_json("TP3/data/indexes/brand_index.json")
    reviews_index = load_json("TP3/data/indexes/reviews_index.json")
    origin_index = load_json("TP3/data/indexes/origin_index.json")

    # ---- Load documents ----
    documents = load_json("data/rearranged_products.json")

    # ---- Load synonyms ----
    synonyms = load_json("data/origin_synonyms.json")

    # ---- Test query ----
    query = "chaussures france"

    # 1. Tokenization
    tokens = tokenize_query(query, STOPWORDS)

    # 2. Query expansion
    expanded_tokens = expand_query_with_synonyms(tokens, synonyms)

    # 3. Filtering (OR logic)
    candidate_docs = filter_documents_any(
        expanded_tokens,
        description_index
    )

    print(f"Filtered documents: {len(candidate_docs)}")

    # 4. Ranking
    ranked_docs = rank_documents(
        candidates=candidate_docs,
        query_tokens=expanded_tokens,
        documents=documents,
        title_index=title_index,
        description_index=description_index,
        brand_index=brand_index,
        origin_index=origin_index,
        reviews_index=reviews_index
    )

    # 5. Output (top 10)
    output = {
        "metadata": {
            "query": query,
            "total_documents": len(documents),
            "filtered_documents": len(candidate_docs)
        },
        "results": ranked_docs[:10]
    }

    print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()


""" 
TEST_QUERIES = [
    "chaussures",
    "chaussures france",
    "made in france",
    "sneakers homme",
    "sneakers homme france",
    "t shirt coton",
    "basket running",
    "chaussures avis",
    "chaussures nike",
]
"""