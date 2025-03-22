import sys
import os
import pytest
from unittest.mock import patch, MagicMock
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.link_finder import LinkFinder

def test_exact_match():
    """Test exact merchant name matches."""
    finder = LinkFinder()
    netflix_link = finder.get_cancellation_link("Netflix")
    assert netflix_link == "https://www.netflix.com/cancelplan"

def test_fuzzy_match():
    """Test fuzzy matching of merchant names."""
    finder = LinkFinder()
    test_cases = [
        ("NETFLIX SUBSCRIPTION", "https://www.netflix.com/cancelplan"),
        ("Amazon Prime*123", "https://www.amazon.com/gp/primecentral"),
        ("SPOTIFY USA", "https://www.spotify.com/us/account/subscription/"),
        ("ChatGPT Plus Subscription", "https://chat.openai.com/payments")
    ]
    
    for merchant, expected_link in test_cases:
        link = finder.get_cancellation_link(merchant)
        assert link == expected_link, f"Failed to match {merchant}"

def test_merchant_normalization():
    """Test merchant name normalization."""
    finder = LinkFinder()
    test_cases = [
        "AplPay NETFLIX INC.",
        "APLPAY NETFLIX LLC",
        "Netflix Corp. in NEW YORK",
        "NETFLIX #123 NY"
    ]
    
    for merchant in test_cases:
        link = finder.get_cancellation_link(merchant)
        assert link == "https://www.netflix.com/cancelplan", f"Failed to normalize {merchant}"

@patch('services.link_finder.requests.get')
def test_web_search(mock_get):
    """Test web search for unknown merchants."""
    # Mock successful response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = """
    <html>
        <div class="g">
            <h3>How to Cancel Unknown Service Subscription</h3>
            <a href="https://unknown-service.com/cancel">Cancel Subscription</a>
        </div>
    </html>
    """
    mock_get.return_value = mock_response
    
    finder = LinkFinder()
    link = finder.get_cancellation_link("Unknown Service")
    
    assert "unknown-service.com/cancel" in link
    mock_get.assert_called_once()

@patch('services.link_finder.requests.get')
def test_web_search_fallback(mock_get):
    """Test web search fallback when no specific result found."""
    # Mock response with no relevant results
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = "<html><body>No results found</body></html>"
    mock_get.return_value = mock_response
    
    finder = LinkFinder()
    link = finder.get_cancellation_link("Very Unknown Service")
    
    assert "google.com/search" in link
    assert "how+to+cancel+Very+Unknown+Service" in link

def test_cache_usage():
    """Test that web search results are cached."""
    finder = LinkFinder()
    
    # First call should do web search
    with patch('services.link_finder.requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html><body>Some results</body></html>"
        mock_get.return_value = mock_response
        
        finder.get_cancellation_link("Test Service")
        assert mock_get.call_count == 1
        
        # Second call should use cache
        finder.get_cancellation_link("Test Service")
        assert mock_get.call_count == 1  # Should not increase

def test_rate_limiting():
    """Test rate limiting for web searches."""
    finder = LinkFinder()
    finder.min_request_interval = 0.1  # Set small interval for testing
    
    with patch('services.link_finder.requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html><body>Some results</body></html>"
        mock_get.return_value = mock_response
        
        start_time = time.time()
        finder.get_cancellation_link("Service 1")
        finder.get_cancellation_link("Service 2")
        end_time = time.time()
        
        assert end_time - start_time >= 0.1  # Should have waited

def test_add_merchant():
    """Test adding new merchants to the database."""
    finder = LinkFinder()
    finder.add_merchant("Test Service", "https://test.com/cancel", save=False)
    
    link = finder.get_cancellation_link("Test Service")
    assert link == "https://test.com/cancel"

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 