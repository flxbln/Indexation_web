import re
import string

import nltk
from nltk.corpus import stopwords

nltk.download("stopwords")
STOPWORDS = set(stopwords.words("french"))

def tokenize(text):
    text = text.lower()
    text = text.translate(str.maketrans("", "", string.punctuation))
    tokens = text.split()
    return [t for t in tokens if t not in STOPWORDS]

import string
#Tokenization + normalisation de la requête
def tokenize_and_normalize(text):
    """
    Met en minuscules, supprime la ponctuation, tokenize par espace
    """
    text = text.lower()
    text = text.translate(str.maketrans("", "", string.punctuation))
    return text.split()

def remove_stopwords(tokens):
    return [t for t in tokens if t not in STOPWORDS]

#Augmentation de la requête par synonymes
def expand_with_synonyms(tokens, synonyms):
    """
    Ajoute les synonymes aux tokens de la requête
    """
    expanded = set(tokens)

    for token in tokens:
        if token in synonyms:
            expanded.update(synonyms[token])

    return list(expanded)


# Pipeline complet de traitement de requête
def process_query(query, synonyms):
    tokens = tokenize_and_normalize(query)
    tokens_no_stop = remove_stopwords(tokens)
    expanded_tokens = expand_with_synonyms(tokens_no_stop, synonyms)
    return expanded_tokens


def filter_documents_any_token(tokens, index):
    """
    Retourne les documents contenant au moins un token
    """
    docs = set()

    for token in tokens:
        if token in index:
            docs.update(index[token])

    return docs


def filter_documents_all_tokens(tokens, index):
    """
    Retourne les documents contenant tous les tokens
    """
    doc_sets = []

    for token in tokens:
        if token in index:
            doc_sets.append(set(index[token]))
        else:
            return set()  # si un token est absent → aucun doc possible

    return set.intersection(*doc_sets)
