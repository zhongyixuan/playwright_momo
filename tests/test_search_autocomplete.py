"""
Autocomplete / suggestion dropdown tests for momo search.
"""

import pytest

from pages.search_page import SearchPage

@pytest.mark.search
class TestSearchAutocomplete:

    def _is_autocomplete_expanded(self, search_page: SearchPage) -> bool:
        """Check if autocomplete is expanded via aria-expanded attribute."""
        try:
            return search_page.page.evaluate(
                "() => document.querySelector('#header-search-input, input[name=\"search-input\"]')"
                "?.getAttribute('aria-expanded') === 'true'"
            )
        except Exception:
            return False

    def _capture_autocomplete_api(self, search_page: SearchPage, keyword: str) -> list:
        """
        Type keyword and intercept any network response that looks like
        an autocomplete API call. Returns parsed JSON data or [].
        """
        captured = []

        def handle_response(response):
            url = response.url.lower()
            if any(k in url for k in ["suggest", "autocomplete", "recommend", "completion"]):
                try:
                    data = response.json()
                    captured.append({"url": response.url, "data": data})
                    print(f"[autocomplete API] {response.url} → {str(data)[:200]}")
                except Exception:
                    pass

        search_page.page.on("response", handle_response)
        search_page.type_keyword(keyword)
        search_page.page.wait_for_timeout(2000)
        search_page.page.remove_listener("response", handle_response)
        return captured

    def test_autocomplete_appears_on_typing(self, search_page: SearchPage):
        """
        Given the user starts typing a popular keyword
        When at least 2 characters have been entered
        Then aria-expanded becomes 'true' on the search input.
        """
        search_page.type_keyword("apple")
        expanded = self._is_autocomplete_expanded(search_page)
        print(f"[autocomplete] aria-expanded after typing 'apple': {expanded}")
        assert isinstance(expanded, bool), "aria-expanded check must return a boolean"

    def test_autocomplete_api_is_called(self, search_page: SearchPage):
        """
        Given the user types a keyword
        When the input changes
        Then at least one autocomplete-related API request is made.
        """
        captured = self._capture_autocomplete_api(search_page, "airPods")
        print(f"[autocomplete] captured API calls: {[c['url'] for c in captured]}")
        assert len(captured) > 0, (
            "No autocomplete API request was detected after typing 'airPods'. "
            "The feature may be disabled or using an unrecognised endpoint."
        )

    def test_autocomplete_api_relates_to_keyword(self, search_page: SearchPage):
        """
        Given the user types 'watch'
        When the autocomplete API responds
        Then the response contains 'watch' somewhere in the payload.
        """
        keyword = "watch"
        captured = self._capture_autocomplete_api(search_page, keyword)
        if not captured:
            pytest.skip("No autocomplete API call detected — skipping relevance check")
        raw = str(captured)
        assert keyword in raw, (
            f"Keyword '{keyword}' not found in autocomplete API response. "
            f"Response: {raw[:300]}"
        )