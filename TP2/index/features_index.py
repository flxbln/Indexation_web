import string

STOPWORDS = {"the", "of", "and", "in", "to", "for", "with", "a", "an"}

def tokenize(text):
    text = text.lower()
    text = text.translate(str.maketrans("", "", string.punctuation))
    return [t for t in text.split() if t not in STOPWORDS]


def build_features_index(documents):
    features_index = {}

    for doc in documents:
        doc_id = doc["product_id"]
        features = doc.get("product_features", {})

        for feature_name, feature_value in features.items():
            feature_name = feature_name.lower()
            tokens = tokenize(feature_value)

            features_index.setdefault(feature_name, {})

            for token in tokens:
                features_index[feature_name].setdefault(token, [])

                if doc_id not in features_index[feature_name][token]:
                    features_index[feature_name][token].append(doc_id)

    return features_index

