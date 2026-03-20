"""Debug what links Bing actually returns."""
import time
import sys
import io
from playwright.sync_api import sync_playwright

# Fix encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

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

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(user_agent=USER_AGENT)
    context.add_init_script(STEALTH_JS)
    page = context.new_page()
    
    try:
        query = "HEOR director linkedin"
        url = f"https://www.bing.com/search?q={query.replace(' ', '+')}&count=50"
        print(f"Query: {query}\n")
        
        page.goto(url, wait_until="domcontentloaded", timeout=15000)
        time.sleep(3)
        
        ol_results = page.locator("ol#b_results li")
        print(f"Results: {ol_results.count()}\n")
        
        print("First 5 results:")
        for i in range(min(5, ol_results.count())):
            item = ol_results.nth(i)
            text = item.inner_text()[:200]
            print(f"\n--- Result {i+1} ---")
            print(text)
            
            # Get all links
            all_links = item.locator("a")
            print(f"Links in result: {all_links.count()}")
            for j in range(min(3, all_links.count())):
                href = all_links.nth(j).get_attribute("href")
                link_text = all_links.nth(j).inner_text()
                print(f"  {j+1}. [{link_text}] {href[:80]}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        browser.close()
