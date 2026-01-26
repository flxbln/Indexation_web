import json
import pandas as pd
import re
import os
import nltk
from nltk.corpus import stopwords

nltk.download("stopwords", quiet=True)
ENGLISH_STOPWORDS = set(stopwords.words("english"))


class ProductURLParser:
    """Handles extraction of product information from URLs"""
    
    @staticmethod
    def get_product_id(url_string):
        """
        Retrieves product identifier from URL path containing 'product' or 'products'
        
        Args:
            url_string (str): URL to parse
            
        Returns:
            str or None: Product ID if found
        """
        match = re.search(r'products?/(\d+)', url_string)
        return match.group(1) if match else None
    
    @staticmethod
    def get_variant_id(url_string):
        """
        Extracts variant parameter from URL query string
        
        Args:
            url_string (str): URL to parse
            
        Returns:
            str or None: Variant ID if present
        """
        match = re.search(r'variant=([^&]+)', url_string)
        return match.group(1) if match else None


class TextProcessor:
    """Utilities for text cleaning and tokenization"""
    
    @staticmethod
    def tokenize_and_clean(text_input):
        """
        Splits text into tokens, removes punctuation and stopwords
        
        Args:
            text_input (str): Raw text to process
            
        Returns:
            list: Cleaned tokens
        """
        words = text_input.lower().split()
        cleaned = []
        
        for word in words:
            word = re.sub(r'[^a-z0-9]', '', word)
            if word and word not in ENGLISH_STOPWORDS:
                cleaned.append(word)
        
        return cleaned


class InvertedIndexBuilder:
    """Creates various inverted indexes for product search"""
    
    def __init__(self, dataframe):
        self.df = dataframe
    
    def build_text_index(self, field_name):
        """
        Generates inverted index mapping tokens to URLs for a given field
        
        Args:
            field_name (str): Column name to index ('title' or 'description')
            
        Returns:
            dict: Mapping from token to list of URLs
        """
        idx = {}
        
        for _, record in self.df.iterrows():
            tokens = TextProcessor.tokenize_and_clean(record[field_name])
            page_url = record['url']
            
            for token in tokens:
                idx.setdefault(token, [])
                if page_url not in idx[token]:
                    idx[token].append(page_url)
        
        return idx
    
    def build_positional_index(self, field_name):
        """
        Creates positional inverted index tracking token positions
        
        Args:
            field_name (str): Column to index
            
        Returns:
            dict: Nested dict {token: {url: [position_list]}}
        """
        idx = {}
        
        for _, record in self.df.iterrows():
            tokens = TextProcessor.tokenize_and_clean(record[field_name])
            page_url = record['url']
            
            for position, token in enumerate(tokens):
                if token not in idx:
                    idx[token] = {}
                if page_url not in idx[token]:
                    idx[token][page_url] = []
                idx[token][page_url].append(position)
        
        return idx
    
    def build_brand_index(self):
        """
        Maps brand names to product URLs
        
        Returns:
            dict: Brand to URL list mapping
        """
        idx = {}
        
        for _, record in self.df.iterrows():
            features = record.get('product_features', {})
            if 'brand' not in features:
                continue
            
            brand_name = features['brand']
            page_url = record['url']
            
            idx.setdefault(brand_name, [])
            if page_url not in idx[brand_name]:
                idx[brand_name].append(page_url)
        
        return idx
    
    def build_origin_index(self):
        """
        Maps country of origin to product URLs
        
        Returns:
            dict: Origin to URL list mapping
        """
        idx = {}
        
        for _, record in self.df.iterrows():
            features = record.get('product_features', {})
            if 'made in' not in features:
                continue
            
            country = features['made in'].lower()
            page_url = record['url']
            
            idx.setdefault(country, [])
            if page_url not in idx[country]:
                idx[country].append(page_url)
        
        return idx
    
    def build_review_metadata(self):
        """
        Aggregates review statistics per product URL
        
        Returns:
            dict: URL to review metrics mapping
        """
        metadata = {}
        
        for _, record in self.df.iterrows():
            reviews = record.get('product_reviews', [])
            count = len(reviews)
            
            if count > 0:
                avg_rating = sum(int(r['rating']) for r in reviews) / count
                latest_rating = reviews[-1]['rating']
            else:
                avg_rating = 0
                latest_rating = None
            
            metadata[record['url']] = {
                'review_count': count,
                'avg_rating': avg_rating,
                'latest_rating': latest_rating
            }
        
        return metadata


def process_and_export(input_filepath, output_folder):
    """
    Main pipeline: reads product data, builds indexes, writes JSON files
    
    Args:
        input_filepath (str): Path to JSONL input file
        output_folder (str): Directory for output JSON files
    """
    # Load data
    df = pd.read_json(input_filepath, lines=True)
    
    # Parse URL components
    parser = ProductURLParser()
    df['id_product'] = df['url'].apply(parser.get_product_id)
    df['variant'] = df['url'].apply(parser.get_variant_id)
    
    # Build all indexes
    builder = InvertedIndexBuilder(df)
    
    indexes = {
        'title_index.json': builder.build_positional_index('title'),
        'description_index.json': builder.build_positional_index('description'),
        'brand_index.json': builder.build_brand_index(),
        'origin_index.json': builder.build_origin_index(),
        'reviews_index.json': builder.build_review_metadata()
    }
    
    # Export to JSON files
    os.makedirs(output_folder, exist_ok=True)
    
    for filename, index_data in indexes.items():
        filepath = os.path.join(output_folder, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(index_data, f, indent=2, ensure_ascii=False)
    
    print(f"Successfully generated {len(indexes)} index files in '{output_folder}'")


if __name__ == "__main__":
    process_and_export('TP2/products.jsonl', 'TP2/indexes')