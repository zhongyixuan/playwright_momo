# momo Search Automation

Playwright + pytest test suite for the [momo shopping site](https://www.momoshop.com.tw/) search feature.

---

## Table of Contents

1. [Project Structure](#project-structure)
2. [Setup](#setup)
3. [Running the Tests](#running-the-tests)
4. [Test Strategy](#test-strategy)
5. [Known Issues](#known-issues)
6. [Design Decisions](#design-decisions)

---

## Project Structure

```
playwright_momo/
├── conftest.py                     # Shared pytest fixtures (browser, page, search_page)
│
├── pages/                          # Page Object Model
│   ├── base_page.py                # Shared navigation / interaction helpers
│   └── search_page.py              # All search-feature selectors & actions
│
├── utils/
│   └── helpers.py                  # Pure helper functions (relevance checks)
│
└── tests/
    ├── test_search_core.py         # Smoke: basic happy-path scenarios
    ├── test_search_edge_cases.py   # Edge: empty, special chars, very long input, XSS
    ├── test_search_autocomplete.py # Autocomplete dropdown behaviour
```

---

## Setup

### Prerequisites

- Python 3.11+
- pip

### Install

```bash
# 1. Clone / unzip the project
cd playwright_momo

# 2. (Recommended) create a virtual environment
python -m venv .venv
source .venv/bin/activate

# 3. Install Python dependencies
pip install playwright pytest pytest-playwright

# 4. Install Playwright browsers
playwright install
```

---

## Running the Tests

### Run the full suite

```bash
pytest
```

### Run a specific test file

```bash
pytest tests/test_search_core.py -v
```

### Run a specific test case

```bash
pytest tests/test_search_core.py::TestSearchHappyPath::test_consecutive_searches_work 
```

### Run in headed mode (watch the browser)

```bash
pytest --headed
```

---

## Test Strategy

### Why these scenarios?

The search feature is the **primary discovery mechanism** on an e-commerce platform. A broken or degraded search directly impacts revenue. I prioritised test scenarios that:

1. **Block all other functionality if broken** — smoke tests first.
2. **Represent real user behaviour** — the way humans actually type, click, and navigate.
3. **Cover the silent failure modes** — cases that don't throw errors but return wrong results.

### Coverage breakdown

| File | Category | Key scenarios |
|---|---|---|
| `test_search_core.py` | Smoke / Happy-path | Returns Enter results, Return Button results, URL updates, relevance, consecutive searches |
| `test_search_edge_cases.py` | Edge / Boundary | Empty query, whitespace, numbers, nonsense query, 200-char input, XSS payload |
| `test_search_autocomplete.py` | Autocomplete | `aria-expanded` signals dropdown open, autocomplete API is triggered, API response contains the keyword |

---

## Known Issues

The following bugs were discovered during test execution and are tracked as `xfail` — they are **expected to fail** until fixed by the momo engineering team.

| Test | Status | Bug Description |
|---|---|---|
| `test_very_long_keyword` | `XFAIL` | Submitting a query of 200+ characters returns a blank page title, indicating the server does not handle oversized input gracefully. |
| `test_special_characters_search` | `XFAIL` | Submitting a query containing `<script>` tags returns a blank page title, indicating special characters are not properly sanitized before being processed. |

These tests are marked with `@pytest.mark.xfail(strict=True)`. If momo resolves these issues and the tests begin passing, pytest will report them as `XPASS` as a signal to remove the marker.

---

## Design Decisions

### Page Object Model (POM)

All selectors live in `pages/search_page.py`. Tests never use raw CSS or XPath strings. This means:
- Selector changes require edits in **one** place.
- Tests read like specifications, not implementation detail.

### Lenient relevance threshold

The relevance test uses a 40–50% threshold rather than 100%. momo shows sponsored listings, category cross-sells, and bundled products alongside direct matches. A 100% threshold would produce false failures; 40–50% still catches a completely broken relevance algorithm.

### No `time.sleep()`

All waiting is done via Playwright's built-in `wait_for_selector` / `wait_for_load_state`. This avoids arbitrary delays and keeps the suite as fast as the site allows.

### Autocomplete testing strategy

momo's autocomplete dropdown is rendered outside the standard DOM (via MUI portal), so CSS selectors cannot reliably locate it. Two alternative strategies are used instead:

1. **`aria-expanded` attribute** — the search input toggles `aria-expanded="true"` when the dropdown opens, providing a stable signal without touching the DOM.
2. **Network interception** — Playwright listens to all HTTP responses and captures any that match autocomplete-related URL patterns (`suggest`, `recommend`, etc.), verifying the feature is active at the API level.

DOM-based tests were intentionally excluded to avoid false negatives caused by the non-standard rendering.