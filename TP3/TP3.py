import json
import os
import math
import re
import nltk
from nltk.corpus import stopwords

# Download stopwords if not already present
nltk.download("stopwords", quiet=True)

# Global configuration
ENGLISH_STOPWORDS = set(stopwords.words("english"))
DEFAULT_INDEX_DIR = "TP3/indexes"
RESULTS_DIR = "TP3/results"


# Text processing utilities

def clean_texte(text):
    """
    Clean and normalize text by removing special characters and converting to lowercase
    
    Args:
        text (str): Raw text to clean
        
    Returns:
        str: Cleaned text
    """
    if not text:
        return ""
    
    # Convert to lowercase
    text = text.lower()
    
    # Remove special characters, keep only alphanumeric and spaces
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    
    # Remove multiple spaces
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()


def input_text(query):
    """
    Tokenize and process input text into clean tokens
    
    Args:
        query (str): Raw query string
        
    Returns:
        list: List of cleaned tokens
    """
    cleaned = clean_texte(query)
    
    # Split into tokens
    tokens = cleaned.split()
    
    # Remove stopwords
    tokens = [token for token in tokens if token not in ENGLISH_STOPWORDS]
    
    return tokens


def expand_with_synonyms(tokens, synonym_dict):
    """
    Expand token list with synonyms from dictionary
    
    Args:
        tokens (list): Original tokens
        synonym_dict (dict): Dictionary mapping terms to their synonyms
        
    Returns:
        list: Expanded token list including synonyms
    """
    if not synonym_dict:
        return tokens.copy()
    
    augmented_tokens = []
    
    for token in tokens:
        augmented_tokens.append(token)
        
        # Add synonyms if available
        if token in synonym_dict:
            synonyms = synonym_dict[token]
            if isinstance(synonyms, list):
                augmented_tokens.extend(synonyms)
            else:
                augmented_tokens.append(synonyms)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_tokens = []
    for token in augmented_tokens:
        if token not in seen:
            seen.add(token)
            unique_tokens.append(token)
    
    return unique_tokens


class IndexLoader:
    """Handles loading of inverted indexes and product data from disk"""
    
    @staticmethod
    def retrieve_indexes(directory=DEFAULT_INDEX_DIR):
        """
        Load all JSON index files from specified directory
        
        Args:
            directory (str): Path to index directory
            
        Returns:
            dict: Dictionary mapping index names to their content
        """
        if not os.path.isdir(directory):
            raise FileNotFoundError(f"Directory not found: {directory}")
        
        loaded_indexes = {}
        
        for filename in os.listdir(directory):
            if filename.endswith(".json") and filename != "products.jsonl":
                filepath = os.path.join(directory, filename)
                index_name = filename[:-5]
                
                with open(filepath, 'r', encoding='utf-8') as file:
                    loaded_indexes[index_name] = json.load(file)
        
        return loaded_indexes
    
    @staticmethod
    def retrieve_products(path="TP3/data/rearranged_products.jsonl"):
        """
        Load product catalog from JSONL file
        
        Args:
            path (str): Path to products file
            
        Returns:
            dict: URL to product metadata mapping
        """
        catalog = {}
        
        with open(path, 'r', encoding='utf-8') as file:
            for line in file:
                product = json.loads(line.strip())
                catalog[product["url"]] = {
                    "title": product["title"],
                    "description": product["description"]
                }
        
        return catalog


class DocumentFilter:
    """Implements document filtering strategies based on query tokens"""
    
    @staticmethod
    def find_documents_with_any_token(tokens, title_idx, desc_idx):
        """
        Retrieve documents containing at least one query token
        
        Args:
            tokens (list): Query tokens to search for
            title_idx (dict): Title inverted index
            desc_idx (dict): Description inverted index
            
        Returns:
            set: URLs of matching documents
        """
        matched_urls = set()
        
        for token in tokens:
            if token in title_idx:
                matched_urls.update(title_idx[token].keys())
            if token in desc_idx:
                matched_urls.update(desc_idx[token].keys())
        
        return matched_urls
    
    @staticmethod
    def find_documents_with_all_tokens(tokens, field_idx):
        """
        Retrieve documents containing all query tokens in a specific field
        
        Args:
            tokens (list): Query tokens to search for
            field_idx (dict): Inverted index for a specific field
            
        Returns:
            set: URLs of documents containing all tokens
        """
        url_sets = []
        
        for token in tokens:
            if token not in field_idx:
                return set()
            url_sets.append(set(field_idx[token].keys()))
        
        return set.intersection(*url_sets) if url_sets else set()


class BM25Calculator:
    """Implements BM25 ranking algorithm for document scoring"""
    
    def __init__(self, k1=1.2, b=0.75):
        """
        Initialize BM25 parameters
        
        Args:
            k1 (float): Term frequency saturation parameter
            b (float): Length normalization parameter
        """
        self.k1 = k1
        self.b = b
    
    @staticmethod
    def extract_all_urls(index):
        """
        Extract unique URLs from an inverted index
        
        Args:
            index (dict): Inverted index
            
        Returns:
            set: All unique URLs in the index
        """
        urls = set()
        for posting_list in index.values():
            urls.update(posting_list.keys())
        return urls
    
    @staticmethod
    def calculate_doc_lengths(index):
        """
        Compute document lengths based on token positions
        
        Args:
            index (dict): Positional inverted index
            
        Returns:
            dict: URL to document length mapping
        """
        doc_lengths = {}
        
        for token, postings in index.items():
            for url, positions in postings.items():
                doc_lengths[url] = doc_lengths.get(url, 0) + len(positions)
        
        return doc_lengths
    
    def compute_idf_score(self, token, index, total_docs):
        """
        Calculate IDF (Inverse Document Frequency) for a token
        
        Args:
            token (str): Token to calculate IDF for
            index (dict): Inverted index
            total_docs (int): Total number of documents
            
        Returns:
            float: IDF score
        """
        doc_freq = len(index.get(token, {}))
        
        if doc_freq == 0:
            return 0.0
        
        return math.log(1 + (total_docs - doc_freq + 0.5) / (doc_freq + 0.5))
    
    def score_document(self, query_tokens, url, index):
        """
        Calculate BM25 score for a document given query tokens
        
        Args:
            query_tokens (list): Tokens from query
            url (str): Document URL to score
            index (dict): Positional inverted index
            
        Returns:
            float: BM25 score
        """
        total_docs = len(self.extract_all_urls(index))
        doc_lengths = self.calculate_doc_lengths(index)
        
        if url not in doc_lengths:
            return 0.0
        
        current_doc_length = doc_lengths[url]
        avg_doc_length = sum(doc_lengths.values()) / len(doc_lengths)
        
        bm25_score = 0.0
        
        for token in query_tokens:
            if token in index and url in index[token]:
                term_freq = len(index[token][url])
                idf = self.compute_idf_score(token, index, total_docs)
                
                numerator = term_freq * (self.k1 + 1)
                denominator = term_freq + self.k1 * (
                    1 - self.b + self.b * current_doc_length / avg_doc_length
                )
                
                bm25_score += idf * (numerator / denominator)
        
        return bm25_score


class ExactMatcher:
    """Handles exact phrase matching using positional information"""
    
    @staticmethod
    def verify_exact_phrase(tokens, url, positional_index):
        """
        Check if tokens appear as consecutive phrase in document
        
        Args:
            tokens (list): Query tokens in order
            url (str): Document URL to check
            positional_index (dict): Positional inverted index
            
        Returns:
            bool: True if exact phrase match found
        """
        if not tokens:
            return False
        
        # Verify all tokens exist in document
        for token in tokens:
            if token not in positional_index or url not in positional_index[token]:
                return False
        
        # Check for consecutive positions
        first_token_positions = positional_index[tokens[0]][url]
        
        for start_pos in first_token_positions:
            match_found = True
            
            for offset, token in enumerate(tokens):
                expected_pos = start_pos + offset
                if expected_pos not in positional_index[token][url]:
                    match_found = False
                    break
            
            if match_found:
                return True
        
        return False


class RankingWeights:
    """Configuration for ranking signal weights"""
    
    TITLE_BM25 = 10.0
    DESCRIPTION_BM25 = 1.0
    EXACT_MATCH_BONUS = 50.0
    POSITION_ZERO_BONUS = 20.0
    REVIEW_SCORE = 2.0
    REVIEW_COUNT = 0.1


class DocumentRanker:
    """Combines multiple signals to rank search results"""
    
    def __init__(self, bm25_calculator, exact_matcher):
        """
        Initialize ranker with scoring components
        
        Args:
            bm25_calculator (BM25Calculator): BM25 scoring instance
            exact_matcher (ExactMatcher): Exact matching instance
        """
        self.bm25 = bm25_calculator
        self.matcher = exact_matcher
    
    def compute_relevance_score(self, original_tokens, expanded_tokens, url,
                                title_idx, desc_idx, review_idx):
        """
        Calculate comprehensive relevance score for document
        
        Args:
            original_tokens (list): Original query tokens (for exact match)
            expanded_tokens (list): Expanded tokens with synonyms (for BM25)
            url (str): Document URL
            title_idx (dict): Title positional index
            desc_idx (dict): Description positional index
            review_idx (dict): Review statistics index
            
        Returns:
            float: Combined relevance score
        """
        score = 0.0
        
        # BM25 scores for title and description
        score += RankingWeights.TITLE_BM25 * self.bm25.score_document(
            expanded_tokens, url, title_idx
        )
        score += RankingWeights.DESCRIPTION_BM25 * self.bm25.score_document(
            expanded_tokens, url, desc_idx
        )
        
        # Exact match bonus
        title_exact = self.matcher.verify_exact_phrase(original_tokens, url, title_idx)
        desc_exact = self.matcher.verify_exact_phrase(original_tokens, url, desc_idx)
        
        if title_exact or desc_exact:
            score += RankingWeights.EXACT_MATCH_BONUS
        
        # Position zero bonus (phrase at start of title)
        if title_exact and original_tokens:
            first_token_positions = title_idx[original_tokens[0]][url]
            if 0 in first_token_positions:
                score += RankingWeights.POSITION_ZERO_BONUS
        
        # Review-based signals
        if url in review_idx:
            score += RankingWeights.REVIEW_SCORE * review_idx[url]["mean_mark"]
            score += RankingWeights.REVIEW_COUNT * review_idx[url]["total_reviews"]
        
        return score


class SearchEngine:
    """Main search engine orchestrating all components"""
    
    def __init__(self, title_idx, desc_idx, review_idx, synonym_dict=None):
        """
        Initialize search engine with indexes
        
        Args:
            title_idx (dict): Title positional index
            desc_idx (dict): Description positional index
            review_idx (dict): Review statistics index
            synonym_dict (dict): Optional synonym dictionary
        """
        self.title_index = title_idx
        self.description_index = desc_idx
        self.review_index = review_idx
        self.synonyms = synonym_dict
        
        self.filter = DocumentFilter()
        self.bm25 = BM25Calculator()
        self.matcher = ExactMatcher()
        self.ranker = DocumentRanker(self.bm25, self.matcher)
    
    def execute_search(self, query_text):
        """
        Execute search query and return ranked results
        
        Args:
            query_text (str): Raw search query
            
        Returns:
            list: Tuples of (url, score) sorted by relevance
        """
        # Tokenize query
        original_tokens = input_text(query_text)
        
        # Expand with synonyms if available
        if self.synonyms:
            expanded_tokens = expand_with_synonyms(original_tokens, self.synonyms)
        else:
            expanded_tokens = original_tokens.copy()
        
        # Filter candidate documents
        candidate_urls = self.filter.find_documents_with_any_token(
            expanded_tokens, self.title_index, self.description_index
        )
        
        # Score and rank candidates
        scored_results = []
        for url in candidate_urls:
            relevance_score = self.ranker.compute_relevance_score(
                original_tokens, expanded_tokens, url,
                self.title_index, self.description_index, self.review_index
            )
            scored_results.append((url, relevance_score))
        
        # Sort by score descending
        scored_results.sort(key=lambda x: x[1], reverse=True)
        
        return scored_results


class ResultFormatter:
    """Formats search results into structured JSON output"""
    
    @staticmethod
    def build_json_response(ranked_results, query, product_catalog, corpus_size):
        """
        Format ranked results as JSON with metadata
        
        Args:
            ranked_results (list): List of (url, score) tuples
            query (str): Original query string
            product_catalog (dict): Product metadata
            corpus_size (int): Total documents in corpus
            
        Returns:
            dict: Structured JSON response
        """
        output = {
            "query": query,
            "metadata": {
                "total_documents": corpus_size,
                "filtered_documents": len(ranked_results),
                "returned_results": min(len(ranked_results), 20)
            },
            "results": []
        }
        
        for url, score in ranked_results[:20]:
            if url not in product_catalog:
                continue
            
            product = product_catalog[url]
            output["results"].append({
                "url": url,
                "title": product["title"],
                "description": product["description"],
                "score": round(score, 2)
            })
        
        return output


def evaluate_search_quality(engine, product_catalog):
    """
    Run test queries to evaluate search quality
    
    Args:
        engine (SearchEngine): Initialized search engine
        product_catalog (dict): Product metadata for display
    """
    test_cases = [
        "smartphone usa",
        "chocolat white italy",
        "running shoes",
    ]
    
    print("=" * 60)
    print("Search Engine Quality Evaluation")
    print("=" * 60)
    
    for query in test_cases:
        print(f"\nTest Query: '{query}'")
        results = engine.execute_search(query)
        print(f"Documents found: {len(results)}")
        
        print("\nTop 5 Results:")
        for rank, (url, score) in enumerate(results[:5], 1):
            title = product_catalog.get(url, {}).get("title", "Unknown")
            print(f"  {rank}. [{score:.2f}] {title[:65]}...")
        print("-" * 60)


def interactive_search_session(engine, product_catalog, corpus_size):
    """
    Run interactive search session with user input
    
    Args:
        engine (SearchEngine): Initialized search engine
        product_catalog (dict): Product metadata
        corpus_size (int): Total documents in corpus
    """
    formatter = ResultFormatter()
    
    print("\n" + "=" * 60)
    print("Interactive Search Mode")
    print("=" * 60)
    print("Enter your queries (type 'quit' to exit)\n")
    
    while True:
        query = input("Search query: ").strip()
        
        if query.lower() == "quit":
            print("Exiting search session.")
            break
        
        if not query:
            continue
        
        # Execute search
        results = engine.execute_search(query)
        formatted_output = formatter.build_json_response(
            results, query, product_catalog, corpus_size
        )
        
        # Display top results
        print(f"\nShowing top {len(formatted_output['results'])} results:")
        for idx, result in enumerate(formatted_output["results"][:10], 1):
            print(f"{idx}. {result['title']} (score: {result['score']})")
        
        # Offer to save results
        save_choice = input("\nSave results to file? (y/n): ").strip().lower()
        
        if save_choice == 'y':
            os.makedirs(RESULTS_DIR, exist_ok=True)
            filename = f"{RESULTS_DIR}/search_{query.replace(' ', '_')}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(formatted_output, f, indent=2, ensure_ascii=False)
            
            print(f"Results saved to: {filename}")
        
        print()


def main():
    """Main entry point for search engine"""
    
    # Load indexes and product data
    print("Loading indexes...")
    loader = IndexLoader()
    indexes = loader.retrieve_indexes()
    product_catalog = loader.retrieve_products()
    
    # Extract individual indexes
    title_idx = indexes["title_index"]
    description_idx = indexes["description_index"]
    review_idx = indexes["reviews_index"]
    synonym_dict = indexes["origin_synonyms"]
    
    # Initialize search engine
    print("Initializing search engine...")
    engine = SearchEngine(title_idx, description_idx, review_idx, synonym_dict)
    
    # Calculate corpus size
    all_urls = BM25Calculator.extract_all_urls(title_idx) | \
               BM25Calculator.extract_all_urls(description_idx)
    corpus_size = len(all_urls)
    
    print(f"Corpus contains {corpus_size} documents")
    
    # Run quality evaluation
    evaluate_search_quality(engine, product_catalog)
    
    # Start interactive session
    interactive_search_session(engine, product_catalog, corpus_size)


if __name__ == "__main__":
    main()