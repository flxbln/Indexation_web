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

def score_document(
    doc_id,
    query_tokens,
    title_index,
    description_index,
    brand_index,
    origin_index,
    reviews_index
):
    score = 0.0
    signals = {}

    # --- Token frequency ---
    title_hits = sum(
        1 for t in query_tokens
        if t in title_index and doc_id in title_index[t]
    )

    description_hits = sum(
        1 for t in query_tokens
        if t in description_index and doc_id in description_index[t]
    )

    # Weighted importance
    score += 3 * title_hits
    score += 1 * description_hits

    signals["title_hits"] = title_hits
    signals["description_hits"] = description_hits

    # --- Brand match ---
    brand_hits = sum(
        1 for t in query_tokens
        if t in brand_index and doc_id in brand_index[t]
    )

    score += 4 * brand_hits
    signals["brand_match"] = brand_hits

    # --- Origin match (important for TP3) ---
    origin_hits = sum(
        1 for t in query_tokens
        if t in origin_index and doc_id in origin_index[t]
    )

    score += 5 * origin_hits
    signals["origin_match"] = origin_hits

    # --- Reviews signal ---
    if doc_id in reviews_index:
        avg_rating = reviews_index[doc_id]["avg_rating"]
        review_count = reviews_index[doc_id]["count"]

        score += avg_rating
        score += 0.1 * review_count

        signals["avg_rating"] = avg_rating
        signals["review_count"] = review_count
    else:
        signals["avg_rating"] = 0
        signals["review_count"] = 0

    return score, signals


# Ranking final
def rank_documents(candidates, **kwargs):
    """
    Rank candidate documents using a linear scoring function.
    """
    scores = {}

    for doc_id in candidates:
        scores[doc_id] = score_document(doc_id=doc_id, **kwargs)

    return sorted(scores.items(), key=lambda x: x[1], reverse=True)

def rank_documents(
    candidates,
    query_tokens,
    documents,
    title_index,
    description_index,
    brand_index,
    origin_index,
    reviews_index
):
    ranked = []

    for doc_id in candidates:
        score, signals = score_document(
            doc_id,
            query_tokens,
            title_index,
            description_index,
            brand_index,
            origin_index,
            reviews_index
        )

        ranked.append({
            "title": documents[doc_id]["title"],
            "url": documents[doc_id]["url"],
            "description": documents[doc_id]["description"],
            "score": round(score, 3),
            "signals": signals
        })

    ranked.sort(key=lambda x: x["score"], reverse=True)
    return ranked


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
