import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.link_finder import LinkFinder

def test_link_finder():
    # Initialize the link finder
    finder = LinkFinder()
    
    # Test exact matches
    netflix_link = finder.get_cancellation_link("Netflix")
    assert netflix_link == "https://www.netflix.com/cancelplan", "Netflix link not found"
    print("✓ Exact match test passed")
    
    # Test fuzzy matches
    netflix_sub_link = finder.get_cancellation_link("NETFLIX SUBSCRIPTION")
    assert netflix_sub_link == "https://www.netflix.com/cancelplan", "Netflix fuzzy match failed"
    
    amazon_link = finder.get_cancellation_link("AMZN Prime")
    assert amazon_link == "https://www.amazon.com/gp/primecentral", "Amazon fuzzy match failed"
    print("✓ Fuzzy match test passed")
    
    # Test unknown merchant
    unknown_link = finder.get_cancellation_link("Unknown Service")
    assert unknown_link == "https://www.google.com/search?q=how+to+cancel+Unknown+Service", "Fallback link incorrect"
    print("✓ Unknown merchant test passed")
    
    # Test adding a new merchant
    finder.add_merchant("Test Service", "https://test.com/cancel", save=False)
    test_link = finder.get_cancellation_link("Test Service")
    assert test_link == "https://test.com/cancel", "Added merchant link not found"
    print("✓ Add merchant test passed")
    
    # Print all results
    print("\nTest Results:")
    print(f"\nNetflix -> {netflix_link}")
    print(f"Netflix Subscription -> {netflix_sub_link}")
    print(f"Amazon Prime -> {amazon_link}")
    print(f"Unknown Service -> {unknown_link}")
    print(f"Test Service -> {test_link}")

if __name__ == "__main__":
    print("Running link finder tests...")
    test_link_finder() 