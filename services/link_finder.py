import json
import os
from typing import Optional
import logging
from thefuzz import process

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
    
    def get_cancellation_link(self, merchant: str, similarity_threshold: int = 80) -> Optional[str]:
        """
        Get the cancellation link for a merchant.
        
        Args:
            merchant (str): Merchant name to look up
            similarity_threshold (int): Minimum similarity score (0-100) to consider a match
            
        Returns:
            Optional[str]: Cancellation link if found, None if no match
        """
        if not merchant or not self.known_merchants:
            return None
            
        # Try to find the best match
        best_match, score = process.extractOne(merchant, self.known_merchants.keys())
        logger.debug(f"Best match for {merchant}: {best_match} (score: {score})")
        
        if score >= similarity_threshold:
            return self.known_merchants[best_match]
        
        # If no good match found, return a Google search link
        return f"https://www.google.com/search?q=how+to+cancel+{merchant.replace(' ', '+')}"
    
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
        "Unknown Service"
    ]
    
    print("\nTesting Link Finder:")
    for merchant in test_merchants:
        link = finder.get_cancellation_link(merchant)
        print(f"\n{merchant}:")
        print(f"  -> {link}") 