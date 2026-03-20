"""Test with better, more specific queries."""
import time
import sys
import io
from playwright.sync_api import sync_playwright

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

queries = [
    "health economist linkedin",
    "health economics research linkedin",
    "HEOR analyst linkedin",
    "pharmaceutical outcomes research linkedin",
]

for query in queries:
    print(f"\n{'='*70}")
    print(f"Query: {query}")
    print('='*70)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent=USER_AGENT)
        context.add_init_script(STEALTH_JS)
        page = context.new_page()
        
        try:
            url = f"https://www.bing.com/search?q={query.replace(' ', '+')}&count=50"
            page.goto(url, wait_until="domcontentloaded", timeout=15000)
            time.sleep(3)
            
            ol_results = page.locator("ol#b_results li")
            print(f"Results: {ol_results.count()}")
            
            linkedin_count = 0
            for i in range(min(15, ol_results.count())):
                item = ol_results.nth(i)
                links = item.locator("a[href*='linkedin.com/in/']")
                
                if links.count() > 0:
                    for j in range(links.count()):
                        href = links.nth(j).get_attribute("href")
                        linkedin_count += 1
                        print(f"  {linkedin_count}. {href[:75]}")
                        if linkedin_count >= 5:
                            break
                if linkedin_count >= 5:
                    break
            
            if linkedin_count == 0:
                print("  (No LinkedIn /in/ links found in first 15 results)")
            
        except Exception as e:
            print(f"Error: {e}")
        finally:
            browser.close()

print("\n" + "="*70)
print("Testing complete")
