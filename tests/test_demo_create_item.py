import pytest
from playwright.sync_api import sync_playwright

@pytest.fixture(scope="session")
def browser_context():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        yield context
        browser.close()

def test_create_item_button_present(browser_context):
    page = browser_context.new_page()
    # Adjust the URL as necessary (e.g., if using port-forwarding or a service DNS)
    page.goto("http://localhost:5000")
    # Look for the "Create Item" button on the page
    create_button = page.query_selector("button:has-text('Create Item')")
    assert create_button, "Create Item button not found on the page."
