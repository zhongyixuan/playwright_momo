import pytest
from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext
from pages.search_page import SearchPage

# Browser / context fixtures

@pytest.fixture(scope="session")
def browser_type_launch_args():
    return {
        "headless": False,
        "slow_mo": 500,
        "args": ["--lang=zh-TW"],
    }


@pytest.fixture(scope="session")
def browser_context_args():
    # NOTE: do NOT set base_url here — it causes Playwright to append a "/"
    return {
        "viewport": {"width": 1280, "height": 800},
        "locale": "zh-TW",
        "timezone_id": "Asia/Taipei",
    }


@pytest.fixture(scope="function")
def page(browser: Browser, browser_context_args: dict):
    context: BrowserContext = browser.new_context(**browser_context_args)
    context.set_default_timeout(20_000)
    context.set_default_navigation_timeout(30_000)
    page: Page = context.new_page()
    yield page
    context.close()

# Page-object fixtures

@pytest.fixture
def search_page(page: Page) -> SearchPage:
    sp = SearchPage(page)
    sp.goto()
    return sp