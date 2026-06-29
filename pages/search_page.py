from __future__ import annotations

import re
from typing import List, Optional

from playwright.sync_api import Page, Locator, expect

from pages.base_page import BasePage

class SearchPage(BasePage):
    """
    Page object for momo search function.
    """
    # Search bar
    SEARCH_INPUT_CANDIDATES = [
        "input[name='search-input']",
        "#header-search-input",
        "input[name*='search']",
        "input[placeholder*='搜尋']",
    ]

    SEARCH_BUTTON_CANDIDATES = [
        "[data-testid='header-search-button']",
        "button.searchbtn",
        "button[type='submit']",
    ]

    # Result page
    RESULT_ITEM_CANDIDATES = [
        "li.goodsUrl",
        "li[class*='goods']",
        "div[class*='goods']",
        "ul.goodsList > li",
        ".searchPrdList li",
    ]

    RESULT_ITEM_NAME_CANDIDATES = [
        "h3.prdName",
        "h3[class*='prd']",
        "p.prdName",
        "[class*='prdName']",
    ]

    NO_RESULT_CANDIDATES = [
        ".noSearchResultWrapper"
        "[class*='noSearchResult']",
    ]

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self._search_input_selector: Optional[str] = None
        self._result_item_selector: Optional[str] = None
        self._result_name_selector: Optional[str] = None
    
    """Try each selector; return the first one that finds a visible element."""
    def _resolve(self, candidates: List[str], timeout: int = 5_000) -> Optional[str]:
        for selector in candidates:
            try:
                loc = self.page.locator(selector).first
                loc.wait_for(state="attached", timeout=timeout)
                return selector
            except Exception:
                continue
        return None

    def _get_search_input(self) -> Locator:
        if not self._search_input_selector:
            self._search_input_selector = self._resolve(self.SEARCH_INPUT_CANDIDATES, timeout=8_000)
            # Collect all actual inputs on the page for diagnostics
            if not self._search_input_selector:
                actual = []
                for inp in self.page.locator("input").all()[:20]:
                    attrs = {}
                    for a in ["id", "name", "type", "placeholder", "class"]:
                        v = inp.get_attribute(a)
                        if v:
                            attrs[a] = v
                    actual.append(str(attrs))
                raise RuntimeError(
                    f"Could not find search input.\n"
                    f"  Tried : {self.SEARCH_INPUT_CANDIDATES}\n"
                    f"  Actual inputs found on page:\n    "
                    + "\n    ".join(actual or ["(none)"])
                    + "\n  → Update SEARCH_INPUT_CANDIDATES in search_page.py with one of the above."
                )
        return self.page.locator(self._search_input_selector).first

    def _get_result_item_selector(self) -> str:
        if not self._result_item_selector:
            self._result_item_selector = self._resolve(self.RESULT_ITEM_CANDIDATES, timeout=10_000)
            # Fall back to first candidate so callers get an empty count
            if not self._result_item_selector:
                self._result_item_selector = self.RESULT_ITEM_CANDIDATES[0]
        return self._result_item_selector

    def _get_result_name_selector(self) -> str:
        if not self._result_name_selector:
            for item_selector in self.RESULT_ITEM_CANDIDATES:
                for name_selector in self.RESULT_ITEM_NAME_CANDIDATES:
                    combined = f"{item_selector} {name_selector}"
                    try:
                        loc = self.page.locator(combined).first
                        loc.wait_for(state="attached", timeout=3_000)
                        self._result_name_selector = combined
                        return self._result_name_selector
                    except Exception:
                        continue
            self._result_name_selector = f"{self.RESULT_ITEM_CANDIDATES[0]} {self.RESULT_ITEM_NAME_CANDIDATES[0]}"
        return self._result_name_selector

    #Core search actions

    def search(self, keyword: str):
        input = self._get_search_input()
        input.click()
        input.fill(keyword)
        self.page.keyboard.press("Enter")
        self._wait_for_results()

    def search_via_button(self, keyword: str):
        input = self._get_search_input()
        input.click()
        input.fill(keyword)
        btn_selector = self._resolve(self.SEARCH_BUTTON_CANDIDATES, timeout=3_000)
        if btn_selector:
            self.page.locator(btn_selector).first.click()
        else:
            self.page.keyboard.press("Enter")
        self._wait_for_results()

    def clear_and_search(self, keyword: str) -> None:
        old_url = self.page.url
        self._search_input_selector = None
        try:
            input = self._get_search_input()
        except RuntimeError:
            self.goto()                    # back homePage
            self._search_input_sel = None
            input = self._get_search_input()
        input.click()
        input.fill("")
        input.fill(keyword)
        self.page.keyboard.press("Enter")
        self.page.wait_for_function(
            f"() => window.location.href !== {repr(old_url)}",
            timeout=10_000,
        )
        self._wait_for_results()

    # Autocomplete

    def type_keyword(self, keyword: str) -> None:
        input = self._get_search_input()
        input.click()
        input.fill(keyword)
        # Wait for autocomplete to expand
        try:
            self.page.wait_for_function(
                "() => document.querySelector('#header-search-input, input[name=\"search-input\"]')"
                "?.getAttribute('aria-expanded') === 'true'",
                timeout=5_000,
            )
        except Exception:
            pass

    # Result inspection

    def get_result_count(self) -> int:
        """Return the number of product cards visible in the current page."""
        try:
            self._get_result_item_selector()
            return self.page.locator(self._result_item_selector).count()
        except Exception:
            return 0

    def get_result_names(self) -> List[str]:
        selector = self._get_result_name_selector()
        items = self.page.locator(selector)
        count = items.count()
        return [items.nth(i).inner_text().strip() for i in range(count)]

    def has_no_results(self) -> bool:
        for selector in self.NO_RESULT_CANDIDATES:
            if self.page.locator(selector).is_visible():
                return True
        return False

    # Private helpers

    def _wait_for_results(self, timeout: int = 15_000) -> None:
        """Wait until either product cards or a no-results notice is visible."""
        self.page.wait_for_load_state("domcontentloaded", timeout=timeout)

        # Reset cached selectors so they are re-resolved on the new page
        self._result_item_selector = None
        self._result_name_selector = None

        # Build a combined selector of all candidates
        all_result_candidates = ", ".join(self.RESULT_ITEM_CANDIDATES)
        all_no_result = ", ".join(self.NO_RESULT_CANDIDATES)
        combined = f"{all_result_candidates}, {all_no_result}"

        try:
            self.page.wait_for_selector(combined, state="attached", timeout=timeout)
        except Exception:
            # Diagnostic output so the developer knows what the page looks like
            raise TimeoutError(
                f"\n[SearchPage] _wait_for_results timed out after {timeout}ms.\n"
                f"  Tried : {combined}\n"
                "  Tip   : Open the URL in a browser, inspect the product list "
                "element, and update RESULT_ITEM_CANDIDATES in search_page.py."
            )