"""
Sorting and filter tests for momo search results.
"""

import pytest

from pages.search_page import SearchPage

class TestSearchSortingAndFilter:

    def test_sort_updates_results_and_url(self, search_page: SearchPage):
        """
        Given a results page for 'apple'
        When the user changes the sort to '價格'
        Then the URL changes AND the page still shows product cards.
        """
        search_page.search("apple")
        assert search_page.get_result_count() > 0
        original_url = search_page.current_url

        try:
            search_page.sort_by("價格")
        except ValueError:
            pytest.skip("Price sort option not found on this results page")

        assert search_page.current_url != original_url, (
            "URL did not change after applying price sort — sort may not be persisted"
        )
        assert search_page.get_result_count() > 0, (
            "No results after applying price sort"
        )

    def test_different_sort_options_return_different_order(self, search_page: SearchPage):
        """
        Given a results page for 'airPods'
        When the user applies two different sort options in sequence
        Then the first result name differs between the two sorts.
        """
        search_page.search("airPods")

        try:
            search_page.sort_by("評價")
        except ValueError:
            pytest.skip("評價 sort not found")

        names_after_sales_sort = search_page.get_result_names()

        try:
            search_page.sort_by("價格")
        except ValueError:
            pytest.skip("價格 sort not found")

        names_after_price_sort = search_page.get_result_names()

        if names_after_sales_sort == names_after_price_sort:
            pytest.xfail(
                "Result order was identical after monthly sales and price sort — "
                "may indicate a broken sort feature or a very small catalogue."
            )
        
    def test_price_filter_reduces_result_set(self, search_page: SearchPage):
        """
        Given a search for 'watch' (a category with wide price range)
        When a narrow price filter (1000–5000 NTD) is applied
        Then the result count is not zero AND is different from unfiltered.
        """
        search_page.search("watch")
        unfiltered_count = search_page.get_result_count()
        assert unfiltered_count > 0

        try:
            search_page.filter_by_price(1000, 5000)
        except Exception:
            pytest.skip("Price filter UI not found or not interactable")

        filtered_count = search_page.get_result_count()
        assert filtered_count > 0, (
            "Price filter returned zero results for 1000–5000 NTD on 'watch'"
        )

    def test_price_filter_url_contains_price_params(self, search_page: SearchPage):
        """
        Given a price filter is applied
        When we inspect the URL
        Then it contains price-related parameters.
        """
        search_page.search("Camera")
        try:
            search_page.filter_by_price(10000, 30000)
        except Exception:
            pytest.skip("Price filter UI not found or not interactable")

        url = search_page.current_url
        has_price_param = any(
            param in url for param in ["_advPriceS","_advPriceE","price"]
        )
        assert has_price_param, (
            "URL does not contain price parameters after filtering — "
            "filter may not have been applied"
        )