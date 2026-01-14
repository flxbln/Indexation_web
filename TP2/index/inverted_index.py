from collections import defaultdict
import string

#Liste de stopwords
STOPWORDS = {
    "the", "a", "an", "and", "or", "of", "to", "in", "on",
    "for", "with", "is", "are", "this", "that", "it"
}

#Nettoyage + tokenisation
def tokenize(text):
    tokens = []

    # minuscules
    text = text.lower()

    # suppression ponctuation
    for p in string.punctuation:
        text = text.replace(p, "")

    # tokenisation par espace
    for token in text.split():
        if token and token not in STOPWORDS:
            tokens.append(token)

    return tokens


# Création de l’index
def build_title_index(documents):
    index = defaultdict(set)

    for doc in documents:
        url = doc["url"]
        title = doc.get("title", "")

        tokens = tokenize(title)
        for token in tokens:
            index[token].add(url)

    # conversion set → list (pour JSON)
    return {k: list(v) for k, v in index.items()}


#Index inversé pour la description
def build_description_index(documents):
    index = defaultdict(set)

    for doc in documents:
        url = doc["url"]
        description = doc.get("description", "")

        tokens = tokenize(description)
        for token in tokens:
            index[token].add(url)

    return {k: list(v) for k, v in index.items()}



"""
#Tests rapides assert "chocolate" in title_index
title_index = build_title_index(documents)
assert "chocolate" in title_index
assert isinstance(title_index["chocolate"], list)
assert all(url.startswith("https://") for url in title_index["chocolate"])
"""