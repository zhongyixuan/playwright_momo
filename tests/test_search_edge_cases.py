"""
Edge-case and boundary tests for momo search.
"""

import pytest

from pages.search_page import SearchPage

@pytest.mark.edge
@pytest.mark.search
class TestSearchEdgeCases:

    def test_empty_search_does_not_crash(self, search_page: SearchPage):
        """
        Given an empty search input
        When the user submits
        Then the page does not show an unhandled error / white screen.
        """
        search_page.search("")
        title = search_page.page.title()
        assert title, "Page title is empty after empty search — possible error page"
    
    def test_whitespace_only_search(self, search_page: SearchPage):
        """
        Given a keyword that is only whitespace
        When the user submits
        Then the site either trims the query or shows a no-results but does NOT crash.
        """
        search_page.search(" ")
        no_product_cards = search_page.get_result_count() == 0
        has_no_result_msg = search_page.has_no_results()
        assert no_product_cards or has_no_result_msg, "Page crashed on whitespace-only search"
    
    def test_numeric_keyword_search(self, search_page: SearchPage):
        """
        Given a numeric keyword ('123')
        When the user submits
        Then the site responds without error.
        """
        search_page.search("123")
        title = search_page.page.title()
        assert title, "Page appears broken after numeric search"

    def test_nonexistent_keyword_shows_no_results(self, search_page: SearchPage):
        """
        Given a query that is extremely unlikely to match any product('zzz_fake_product_xyz')
        When the user submits
        Then a no-results message is shown.
        """
        search_page.search("zzz_fake_product_xyz")
        # Either a dedicated no-result component or simply zero product cards
        no_product_cards = search_page.get_result_count() == 0
        has_no_result_msg = search_page.has_no_results()
        assert no_product_cards or has_no_result_msg, (
            "Expected zero results or a no-results message for a nonsense query"
        )

    @pytest.mark.xfail(
        reason="Known bug: momo does not handle extremely long input, page title is empty after submission",
        strict=True)
    def test_very_long_keyword(self, search_page: SearchPage):
        """
        Given an unusually long query
        When the user submits
        Then the site handles it without a server error.
        """
        long_keyword = "phone" * 100
        inp = search_page._get_search_input()
        inp.fill(long_keyword)
        search_page.page.keyboard.press("Enter")
        search_page.page.wait_for_timeout(3000)
        title = search_page.page.title()
        assert title, "Page crashed on a very long keyword"

    @pytest.mark.xfail(
        reason="Known bug: momo does not sanitize special characters, page title is empty after XSS payload submission",
        strict=True)
    def test_special_characters_search(self, search_page: SearchPage):
        """
        Given a query containing special characters ('<script>', '& % $')
        When the user submits
        Then the page does NOT execute injected script and shows a safe response.
        """
        xss_payload = "<script>alert('xss')</script>"
        input = search_page._get_search_input()
        input.fill(xss_payload)
        search_page.page.keyboard.press("Enter")
        search_page.page.wait_for_timeout(3000)
        title = search_page.page.title()
        assert title, "Page appears broken after XSS payload"
        assert not search_page.page.locator("dialog").is_visible()