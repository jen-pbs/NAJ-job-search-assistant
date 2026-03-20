"""Debug Bing with simpler queries."""
import time
import random
from playwright.sync_api import sync_playwright

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)

STEALTH_JS = """
Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
window.chrome = {runtime: {}};
"""

queries = [
    "HEOR director site:linkedin.com/in",
    "health economist linkedin",
    "HEOR linkedin",
]

for query in queries:
    print(f"\n{'='*60}")
    print(f"Testing: {query}")
    print('='*60)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent=USER_AGENT)
        context.add_init_script(STEALTH_JS)
        page = context.new_page()
        
        try:
            url = f"https://www.bing.com/search?q={query.replace(' ', '+')}&count=30"
            print(f"URL: {url}")
            page.goto(url, wait_until="domcontentloaded", timeout=15000)
            time.sleep(3)
            
            # Check different selectors
            li_count = page.locator("li").count()
            div_count = page.locator("div[data-bm]").count()
            results_ol = page.locator("ol#b_results").count()
            linkedin_links = page.locator("a[href*='linkedin.com/in/']").count()
            
            print(f"  <li> elements: {li_count}")
            print(f"  <div[data-bm]> elements: {div_count}")
            print(f"  <ol#b_results>: {results_ol}")
            print(f"  LinkedIn links (a[href*='linkedin.com/in/']): {linkedin_links}")
            
            # Try alternative selectors
            alt_links = page.locator("a[href*='linkedin']").count()
            print(f"  Links with 'linkedin': {alt_links}")
            
            # Check page title/status
            title = page.title()
            print(f"  Page title: {title}")
            
        except Exception as e:
            print(f"  Error: {e}")
        finally:
            browser.close()

print("\nDone!")
