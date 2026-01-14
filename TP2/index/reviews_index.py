def build_reviews_index(documents):
    reviews_index = {}

    for doc in documents:
        doc_id = doc["product_id"]
        reviews = doc.get("product_reviews", [])

        if not reviews:
            reviews_index[doc_id] = {
                "count": 0,
                "avg_rating": None,
                "last_rating": None
            }
            continue

        ratings = [r["rating"] for r in reviews]

        reviews_index[doc_id] = {
            "count": len(ratings),
            "avg_rating": sum(ratings) / len(ratings),
            "last_rating": ratings[-1]
        }

    return reviews_index

