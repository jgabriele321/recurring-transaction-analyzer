import json
import os
from typing import Optional
import logging
from thefuzz import process
import requests
from bs4 import BeautifulSoup
import time
import re

logger = logging.getLogger(__name__)

class LinkFinder:
    """
    Service to find cancellation links for merchants.
    """
    def __init__(self, merchants_file: str = None):
        """
        Initialize the LinkFinder with a known merchants database.
        
        Args:
            merchants_file (str, optional): Path to the JSON file containing merchant -> link mappings
        """
        self.known_merchants = {}
        self.cache = {}  # Cache for scraped results
        self.last_request_time = 0  # For rate limiting
        self.min_request_interval = 1  # Minimum seconds between requests
        
        if merchants_file is None:
            # Default to the merchants file in the data directory
            merchants_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'known_merchants.json')
        
        if os.path.exists(merchants_file):
            try:
                with open(merchants_file) as f:
                    self.known_merchants = json.load(f)
                logger.info(f"Loaded {len(self.known_merchants)} merchants from {merchants_file}")
            except Exception as e:
                logger.error(f"Failed to load merchants file {merchants_file}: {str(e)}")
    
    def _normalize_merchant(self, merchant: str) -> str:
        """Normalize merchant name for comparison."""
        # Remove common prefixes and suffixes
        merchant = re.sub(r'^(AplPay|APLPAY)\s+', '', merchant, flags=re.IGNORECASE)
        merchant = re.sub(r'\s*(Inc\.|LLC|Ltd\.|Corp\.|#\d+).*$', '', merchant, flags=re.IGNORECASE)
        # Remove location information
        merchant = re.sub(r'\s+(?:in|at)\s+.*$', '', merchant, flags=re.IGNORECASE)
        merchant = re.sub(r'\s+[A-Z]{2}(?:\s+|$)', ' ', merchant)  # Remove state codes
        return merchant.strip()
    
    def _search_google(self, merchant: str) -> Optional[str]:
        """
        Search Google for cancellation instructions.
        Implements rate limiting and caching.
        """
        # Check cache first
        if merchant in self.cache:
            return self.cache[merchant]
            
        # Rate limiting
        current_time = time.time()
        if current_time - self.last_request_time < self.min_request_interval:
            time.sleep(self.min_request_interval)
        
        try:
            # Construct search query
            query = f"how to cancel {merchant} subscription"
            search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
            
            # Send request with headers to avoid blocking
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(search_url, headers=headers)
            self.last_request_time = time.time()
            
            if response.status_code == 200:
                # Parse the response
                soup = BeautifulSoup(response.text, 'lxml')
                
                # Look for relevant results
                for result in soup.select('.g'):
                    title = result.select_one('h3')
                    link = result.select_one('a')
                    
                    if title and link:
                        title_text = title.get_text().lower()
                        if any(keyword in title_text for keyword in ['cancel', 'subscription', 'account']):
                            url = link['href']
                            # Cache the result
                            self.cache[merchant] = url
                            return url
            
            # If no specific result found, return a Google search link
            fallback_url = f"https://www.google.com/search?q=how+to+cancel+{merchant.replace(' ', '+')}"
            self.cache[merchant] = fallback_url
            return fallback_url
            
        except Exception as e:
            logger.error(f"Error searching for {merchant}: {str(e)}")
            return None
    
    def get_cancellation_link(self, merchant: str, similarity_threshold: int = 80) -> Optional[str]:
        """
        Get the cancellation link for a merchant.
        
        Args:
            merchant (str): Merchant name to look up
            similarity_threshold (int): Minimum similarity score (0-100) to consider a match
            
        Returns:
            Optional[str]: Cancellation link if found, None if no match
        """
        if not merchant:
            return None
            
        # Normalize merchant name
        normalized_merchant = self._normalize_merchant(merchant)
        
        # Try to find the best match in known merchants
        best_match, score = process.extractOne(normalized_merchant, self.known_merchants.keys())
        logger.debug(f"Best match for {merchant}: {best_match} (score: {score})")
        
        if score >= similarity_threshold:
            return self.known_merchants[best_match]
        
        # If no good match found, try web search
        return self._search_google(normalized_merchant)
    
    def add_merchant(self, merchant: str, link: str, save: bool = True) -> None:
        """
        Add a new merchant and cancellation link to the database.
        
        Args:
            merchant (str): Merchant name
            link (str): Cancellation link
            save (bool): Whether to save changes to the merchants file
        """
        self.known_merchants[merchant] = link
        
        if save:
            merchants_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'known_merchants.json')
            try:
                with open(merchants_file, 'w') as f:
                    json.dump(self.known_merchants, f, indent=4)
                logger.info(f"Added merchant {merchant} and saved to {merchants_file}")
            except Exception as e:
                logger.error(f"Failed to save merchants file: {str(e)}")

if __name__ == "__main__":
    # Example usage
    finder = LinkFinder()
    
    # Test with some variations of known merchants
    test_merchants = [
        "Netflix",
        "NETFLIX SUBSCRIPTION",
        "Amazon Prime",
        "AMZN Prime",
        "Unknown Service",
        "ChatGPT Plus",
        "Spotify Premium",
        "OPENAI *CHATGPT"
    ]
    
    print("\nTesting Link Finder:")
    for merchant in test_merchants:
        link = finder.get_cancellation_link(merchant)
        print(f"\n{merchant}:")
        print(f"  -> {link}") 