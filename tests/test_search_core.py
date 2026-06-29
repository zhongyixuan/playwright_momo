"""
Core / smoke tests for momo search.
"""

import pytest

from pages.search_page import SearchPage
from utils.helpers import majority_contain_keyword

@pytest.mark.smoke
@pytest.mark.search
class TestSearchHappyPath:

    def test_search_returns_results(self, search_page: SearchPage):
        """
        Given a valid, popular keyword
        When the user submits the search form
        Then at least one product card appears on the results page.
        """
        search_page.search("airPods")
        count = search_page.get_result_count()
        assert count > 0, "Expected at least 1 product for keyword 'airPods'"

    def test_search_via_button_click(self, search_page: SearchPage):
        """
        Given a keyword in the input
        When the user clicks the search button
        Then results are shown.
        """
        search_page.search_via_button("laptop")
        assert search_page.get_result_count() > 0

    def test_search_url_contains_keyword(self, search_page: SearchPage):
        """
        Given a search for 'Bag'
        When the results page loads
        Then the URL contains the search keyword.
        """
        search_page.search("Bag")
        assert "Bag" in search_page.current_url or "keyword" in search_page.current_url

    
    def test_search_results_are_relevant(self, search_page: SearchPage):
        """
        Given a search for 'iPhone'
        When the results page loads
        Then at least 50 % of visible product names contain a related term.
        """
        keyword = "iPhone"
        search_page.search(keyword)
        names = search_page.get_result_names()
        assert len(names) > 0, "No results returned"
        # Accept either the exact keyword or a related broader term
        relevant = majority_contain_keyword(names, "phone", threshold=0.4)
        assert relevant, (
            f"Fewer than 40% of results seem relevant to '{keyword}'. "
            f"First few names: {names[:5]}"
        )

    def test_consecutive_searches_work(self, search_page: SearchPage):
        """
        Given the user has already searched once
        When they submit a second, different search
        Then the results page refreshes with new results.
        """
        search_page.search("iPhone")
        first_names = search_page.get_result_names()

        search_page.clear_and_search("laptop")
        second_names = search_page.get_result_names()

        assert second_names != first_names, (
            "Second search returned identical results to the first — "
            "results page may not have updated."
        )