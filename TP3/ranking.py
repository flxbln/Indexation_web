import math

def bm25_score(tf, doc_len, avg_doc_len, k1=1.5, b=0.75):
    return ((tf * (k1 + 1)) /
            (tf + k1 * (1 - b + b * doc_len / avg_doc_len)))

def exact_match_score(query, title, description):
    query = query.lower()
    if query in title.lower():
        return 2.0
    if query in description.lower():
        return 1.0
    return 0.0

#Scoring linéaire combiné 
def linear_score(
    bm25,
    title_hits,
    review_score,
    exact_match,
    position_bonus
):
    return (
        1.0 * bm25 +
        2.0 * title_hits +
        1.5 * review_score +
        2.5 * exact_match +
        0.5 * position_bonus
    )

#Utilisation de l’index de position
def position_score(positions):
    if not positions:
        return 0
    return 1 / (1 + min(positions))

#Scoring d’un document complet
def score_document(
    doc_id,
    query_tokens,
    brand_index,
    title_index,
    description_index,
    reviews_index,
    origin_index,
    doc_lengths,
    avg_doc_len,
    title,
    description,
    query
):
    bm25_total = 0
    title_hits = 0
    position_bonus = 0

    for token in query_tokens:
        if token in brand_index and doc_id in brand_index[token]:
            positions = brand_index[token][doc_id]
            tf = len(positions)
            bm25_total += bm25_score(tf, doc_lengths[doc_id], avg_doc_len)
            position_bonus += position_score(positions)

        if token in title_index and doc_id in title_index[token]:
            title_hits += 1

    review_score = reviews_index.get(doc_id, {}).get("average_rating", 0)
    exact = exact_match_score(query, title, description)

    return linear_score(
        bm25_total,
        title_hits,
        review_score,
        exact,
        position_bonus
    )

# Ranking final
def rank_documents(candidates, **kwargs):
    """
    Rank candidate documents using a linear scoring function.
    """
    scores = {}

    for doc_id in candidates:
        scores[doc_id] = score_document(doc_id=doc_id, **kwargs)

    return sorted(scores.items(), key=lambda x: x[1], reverse=True)


def format_results(results, total_docs, query):
    """
    Format ranked documents into a JSON-compatible structure.
    """
    return {
        "metadata": {
            "query": query,
            "total_documents": total_docs,
            "filtered_documents": len(results)
        },
        "results": results
    }
