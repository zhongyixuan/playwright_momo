from playwright.sync_api import Page

class BasePage:
    """
    Base clasee for all Page Objects.
    """

    BASE_URL = "https://www.momoshop.com.tw/"

    def __init__(self, page:Page):
        self.page = page

    # Navigation
    def goto(self, path: str = "") -> None:
        url = (self.BASE_URL if not path else path).rstrip("/")
        self.page.goto(url, wait_until="networkidle", timeout=30_000)

    @property
    def current_url(self) -> str:
        return self.page.url
    
    @property
    def title(self) -> str:
        return self.page.title
    
    # Safe Interactions
    def safe_click(self, selector: str, timeout: int = 10_000):
        locator = self.page.locator(selector)
        locator.wait_for(state="visible", timeout=timeout)
        locator.click()
    
    def safe_fill(self, selector: str, value: str, timeout: int = 10_000):
        locator = self.page.locator(selector)
        locator.wait_for(state="visible", timeout=timeout)
        locator.fill(value)