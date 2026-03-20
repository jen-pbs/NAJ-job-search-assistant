"""Debug Bing search selector issues."""
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

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(user_agent=USER_AGENT)
    context.add_init_script(STEALTH_JS)
    page = context.new_page()
    
    try:
        query = "HEOR director site:linkedin.com/in"
        url = f"https://www.bing.com/search?q={query.replace(' ', '+')}&count=30"
        print(f"Searching: {url}\n")
        page.goto(url, wait_until="domcontentloaded", timeout=15000)
        time.sleep(4)
        
        # Try to find LinkedIn links with different selectors
        print("--- Selector Tests ---")
        
        selectors = [
            ("a[href*='linkedin.com/in/']", "Direct LinkedIn links"),
            ("ol#b_results li a[href*='linkedin.com/in/']", "LinkedIn links in ol#b_results"),
            ("li a[href*='linkedin.com/in/']", "LinkedIn links in any li"),
            ("a[href*='linkedin.com']", "All LinkedIn links"),
            ("li", "All li elements"),
        ]
        
        for selector, desc in selectors:
            count = page.locator(selector).count()
            print(f"{desc:40} ({selector:40}): {count}")
        
        # If we found links, show first 3
        all_links = page.locator("a[href*='linkedin.com/in/']")
        if all_links.count() > 0:
            print(f"\n✓ Found {all_links.count()} LinkedIn links!")
            print("\nFirst 3 links:")
            for i in range(min(3, all_links.count())):
                href = all_links.nth(i).get_attribute("href")
                print(f"  {i+1}. {href}")
        else:
            print("\n✗ No LinkedIn links found!")
            print("\nDebugging HTML structure...")
            # Get some sample HTML
            lis = page.locator("li").count()
            print(f"Total <li> elements: {lis}")
            
            if lis > 0:
                print("\nFirst <li> content:")
                first_li = page.locator("li").first
                print(first_li.inner_text()[:300])
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        browser.close()

print("\nDone!")
